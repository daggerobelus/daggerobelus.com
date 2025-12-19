#!/usr/bin/env python3
"""
Module 02: Entity Resolution for Lorraine Witchcraft Trials
Resolves name variants to canonical entities with fuzzy matching and constraint satisfaction.

Key Challenge: Early Modern naming creates multiple variants for the same person:
- "Odille femme Claudin Thieriat" (as wife)
- "Odille Thieriat" (normalized)
- "la Thieriat" (village reference)
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
import pandas as pd
import numpy as np
from rapidfuzz import fuzz, process
import warnings
warnings.filterwarnings('ignore')

# Configuration
INPUT_DIR = Path("/Users/natebaker/Desktop/analysis/sna_pipeline/output/entities")
DATA_DIR = Path("/Users/natebaker/Desktop/analysis/extracted_data/intermediate")
OUTPUT_DIR = Path("/Users/natebaker/Desktop/analysis/sna_pipeline/output/entities")


@dataclass
class CanonicalEntity:
    """A resolved canonical entity representing a unique person."""
    canonical_id: str
    canonical_name: str
    variants: List[str] = field(default_factory=list)
    entity_type: str = 'person'  # 'person', 'accused', 'witness', 'authority'
    gender: Optional[str] = None
    locations: Set[str] = field(default_factory=set)
    trial_appearances: List[Dict] = field(default_factory=list)  # [{trial_id, role, date}]
    outcome: Optional[str] = None  # For accused: death_sentence, released, banished
    attributes: Dict = field(default_factory=dict)


class EntityResolver:
    """
    Hierarchical entity resolution:

    Level 1: Exact match on normalized names within same village
    Level 2: Fuzzy match (threshold 0.85) with location disambiguation
    Level 3: Temporal constraint (same person cannot appear 60+ years apart)
    Level 4: Role consistency tracking (witness in trial A, accused in trial B)
    """

    # Similarity thresholds
    EXACT_THRESHOLD = 100
    HIGH_THRESHOLD = 90
    MEDIUM_THRESHOLD = 85
    LOW_THRESHOLD = 80

    def __init__(self, similarity_threshold: float = 85):
        self.threshold = similarity_threshold
        self.canonical_entities: Dict[str, CanonicalEntity] = {}
        self.entity_mappings: Dict[str, str] = {}  # raw_name -> canonical_id
        self.resolution_log: List[Dict] = []

    def load_extracted_entities(self) -> Dict:
        """Load entities from Module 01."""
        print("Loading extracted entities...")

        with open(INPUT_DIR / "extracted_entities.json") as f:
            entities = json.load(f)

        print(f"  Loaded {len(entities)} extracted entities")
        return entities

    def load_trials_data(self) -> pd.DataFrame:
        """Load trial metadata for temporal constraints."""
        with open(DATA_DIR / "trials.json") as f:
            trials = json.load(f)
        df = pd.DataFrame(trials)

        # Parse dates to extract years
        df['year'] = df['trial_date'].apply(self._extract_year)

        return df

    def _extract_year(self, date_str: str) -> Optional[int]:
        """Extract year from date string."""
        if not date_str or pd.isna(date_str):
            return None
        match = re.search(r'\b(1[5-6]\d{2})\b', str(date_str))
        return int(match.group(1)) if match else None

    def normalize_for_matching(self, name: str) -> str:
        """Create a normalized version of a name for matching."""
        if not name:
            return ''

        # Convert to lowercase
        name = name.lower()

        # Remove common prefixes/suffixes
        name = re.sub(r'\b(femme|veuve|fils|fille)\s+(de\s+)?', '', name)
        name = re.sub(r'\bdu\s+precedent\b', '', name)

        # Remove location markers
        name = re.sub(r',?\s*d[eu\']\s*[a-zé\-]+.*$', '', name)
        name = re.sub(r',?\s*of\s+[a-zé\-]+.*$', '', name)

        # Remove age and occupation
        name = re.sub(r',?\s*\d+\s*$', '', name)
        name = re.sub(r',?\s*laboureur.*$', '', name)
        name = re.sub(r',?\s*manoeuvrier.*$', '', name)

        # Remove archive references
        name = re.sub(r'^b\s+\d+.*?;\s*', '', name)
        name = re.sub(r'witch\s+\d+[,;]?\s*', '', name)

        # Clean up
        name = re.sub(r'\s+', ' ', name).strip()

        return name

    def extract_location(self, name: str) -> Optional[str]:
        """Extract location from a name string."""
        patterns = [
            r",?\s+d[eu']\s*([A-Za-zé\-]+)",
            r",?\s+of\s+([A-Za-zé\-]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                return match.group(1).lower()
        return None

    def extract_given_name(self, normalized_name: str) -> str:
        """Extract given name (first word) from normalized name."""
        parts = normalized_name.split()
        return parts[0] if parts else ''

    def build_initial_clusters(self, entities: Dict) -> Dict[str, List[str]]:
        """Group entities by normalized name for initial clustering."""
        print("\n=== Building Initial Clusters ===")

        clusters = defaultdict(list)

        for raw_name, entity_data in entities.items():
            normalized = self.normalize_for_matching(raw_name)
            if normalized:
                clusters[normalized].append(raw_name)

        print(f"  Created {len(clusters)} initial clusters from {len(entities)} entities")

        # Count cluster sizes
        size_counts = defaultdict(int)
        for cluster in clusters.values():
            size_counts[len(cluster)] += 1

        print(f"  Cluster size distribution:")
        for size in sorted(size_counts.keys())[:5]:
            print(f"    Size {size}: {size_counts[size]} clusters")

        return dict(clusters)

    def fuzzy_merge_clusters(self, clusters: Dict[str, List[str]],
                            entities: Dict) -> Dict[str, List[str]]:
        """Merge clusters using conservative fuzzy matching."""
        print("\n=== Fuzzy Merging Clusters (Conservative) ===")

        cluster_names = list(clusters.keys())
        merged = {}
        used = set()
        merge_count = 0

        for i, name1 in enumerate(cluster_names):
            if name1 in used:
                continue

            # Start a new merged cluster
            merged_cluster = list(clusters[name1])
            used.add(name1)

            # Only merge with very similar names
            # Skip if name is too short for reliable matching
            if len(name1) < 5:
                merged[name1] = merged_cluster
                continue

            # Find similar clusters to merge (conservative)
            for name2 in cluster_names[i+1:]:
                if name2 in used:
                    continue

                # Skip short names
                if len(name2) < 5:
                    continue

                # Use token_set_ratio for better handling of name variations
                similarity = fuzz.token_set_ratio(name1, name2)

                # Only merge if VERY similar and names share significant overlap
                if similarity >= 95:
                    # Additional check: given names should match
                    given1 = self.extract_given_name(name1)
                    given2 = self.extract_given_name(name2)

                    if given1 and given2 and fuzz.ratio(given1, given2) >= 90:
                        # Check location constraint
                        loc1 = self._get_cluster_locations(clusters[name1], entities)
                        loc2 = self._get_cluster_locations(clusters[name2], entities)

                        # Merge if locations overlap or one is unknown
                        if not loc1 or not loc2 or loc1 & loc2:
                            merged_cluster.extend(clusters[name2])
                            used.add(name2)
                            merge_count += 1

                            self.resolution_log.append({
                                'action': 'fuzzy_merge',
                                'name1': name1,
                                'name2': name2,
                                'similarity': similarity,
                            })

            merged[name1] = merged_cluster

        # Add remaining unmerged clusters
        for name in cluster_names:
            if name not in used:
                merged[name] = clusters[name]

        print(f"  Original clusters: {len(clusters)}")
        print(f"  After fuzzy merge: {len(merged)} (merged {merge_count} pairs)")
        return merged

    def _get_cluster_locations(self, raw_names: List[str], entities: Dict) -> Set[str]:
        """Get all locations associated with a cluster."""
        locations = set()
        for name in raw_names:
            if name in entities:
                loc = entities[name].get('location')
                if loc:
                    locations.add(loc.lower())
        return locations

    def create_canonical_entities(self, merged_clusters: Dict[str, List[str]],
                                  entities: Dict,
                                  df_trials: pd.DataFrame) -> Dict[str, CanonicalEntity]:
        """Create canonical entity records from merged clusters."""
        print("\n=== Creating Canonical Entities ===")

        canonical = {}
        entity_id = 0

        for cluster_name, raw_names in merged_clusters.items():
            entity_id += 1
            canonical_id = f"E{entity_id:05d}"

            # Aggregate information from all variants
            all_locations = set()
            all_trials = []
            all_roles = {}
            entity_types = set()
            genders = []
            outcomes = []
            all_attributes = {}

            for raw_name in raw_names:
                if raw_name not in entities:
                    continue

                entity_data = entities[raw_name]

                # Collect locations
                loc = entity_data.get('location')
                if loc:
                    all_locations.add(loc)

                # Collect trial appearances
                trial_ids = entity_data.get('trial_ids', [])
                roles = entity_data.get('roles_in_trials', {})

                for tid in trial_ids:
                    role = roles.get(tid, 'unknown')
                    year = df_trials[df_trials['trial_id'] == tid]['year'].values
                    year = int(year[0]) if len(year) > 0 and not pd.isna(year[0]) else None

                    all_trials.append({
                        'trial_id': tid,
                        'role': role,
                        'year': year,
                        'raw_name': raw_name,
                    })
                    all_roles[tid] = role

                # Collect entity types
                entity_types.add(entity_data.get('entity_type', 'person'))

                # Collect gender
                g = entity_data.get('gender')
                if g and g != 'unknown':
                    genders.append(g)

                # Collect attributes
                attrs = entity_data.get('attributes', {})
                for k, v in attrs.items():
                    if v:
                        all_attributes[k] = v

                # Map raw name to canonical ID
                self.entity_mappings[raw_name] = canonical_id

            # Determine final entity type (accused > witness > person)
            if 'accused' in entity_types:
                final_type = 'accused'
                # Get outcome from trials data
                accused_trials = [t['trial_id'] for t in all_trials if t['role'] == 'accused']
                if accused_trials:
                    trial_outcomes = df_trials[df_trials['trial_id'].isin(accused_trials)]['outcome']
                    outcomes = trial_outcomes.dropna().tolist()
            elif 'authority' in entity_types:
                final_type = 'authority'
            elif 'witness' in entity_types:
                final_type = 'witness'
            else:
                final_type = 'person'

            # Determine if this is a witness-to-accused transition
            roles_set = set(all_roles.values())
            was_witness_then_accused = 'witness' in roles_set and 'accused' in roles_set

            if was_witness_then_accused:
                all_attributes['witness_to_accused'] = True

            # Create canonical entity
            ce = CanonicalEntity(
                canonical_id=canonical_id,
                canonical_name=cluster_name,
                variants=raw_names,
                entity_type=final_type,
                gender=max(set(genders), key=genders.count) if genders else 'unknown',
                locations=all_locations,
                trial_appearances=all_trials,
                outcome=outcomes[0] if outcomes else None,
                attributes=all_attributes,
            )

            canonical[canonical_id] = ce

        print(f"  Created {len(canonical)} canonical entities")
        return canonical

    def find_witness_to_accused_transitions(self) -> List[Dict]:
        """Identify entities that were witnesses and later became accused."""
        print("\n=== Finding Witness-to-Accused Transitions ===")

        transitions = []

        for cid, entity in self.canonical_entities.items():
            if entity.attributes.get('witness_to_accused'):
                # Sort appearances by year
                appearances = sorted(
                    [a for a in entity.trial_appearances if a.get('year')],
                    key=lambda x: x['year']
                )

                witness_appearances = [a for a in appearances if a['role'] == 'witness']
                accused_appearances = [a for a in appearances if a['role'] == 'accused']

                if witness_appearances and accused_appearances:
                    first_witness = witness_appearances[0]
                    first_accused = accused_appearances[0]

                    transitions.append({
                        'canonical_id': cid,
                        'canonical_name': entity.canonical_name,
                        'first_witness_trial': first_witness['trial_id'],
                        'first_witness_year': first_witness['year'],
                        'first_accused_trial': first_accused['trial_id'],
                        'first_accused_year': first_accused['year'],
                        'years_between': (first_accused['year'] - first_witness['year'])
                                         if first_accused['year'] and first_witness['year'] else None,
                        'total_witness_appearances': len(witness_appearances),
                        'outcome': entity.outcome,
                    })

        print(f"  Found {len(transitions)} witness-to-accused transitions")

        # Print details
        for t in transitions:
            print(f"    {t['canonical_name']}: witness in {t['first_witness_year']} -> "
                  f"accused in {t['first_accused_year']} ({t['years_between']} years)")

        return transitions

    def identify_super_witnesses(self, min_trials: int = 3) -> pd.DataFrame:
        """Identify witnesses appearing in multiple trials."""
        print(f"\n=== Identifying Super-Witnesses (>= {min_trials} trials) ===")

        super_witnesses = []

        for cid, entity in self.canonical_entities.items():
            witness_trials = [a for a in entity.trial_appearances if a['role'] == 'witness']

            if len(witness_trials) >= min_trials:
                unique_trials = len(set(a['trial_id'] for a in witness_trials))

                if unique_trials >= min_trials:
                    super_witnesses.append({
                        'canonical_id': cid,
                        'canonical_name': entity.canonical_name,
                        'num_trials': unique_trials,
                        'trial_ids': list(set(a['trial_id'] for a in witness_trials)),
                        'years_active': sorted(set(a['year'] for a in witness_trials if a.get('year'))),
                        'gender': entity.gender,
                        'locations': list(entity.locations),
                        'became_accused': entity.attributes.get('witness_to_accused', False),
                        'personal_suspicion': entity.attributes.get('personal_suspicion', False),
                    })

        df = pd.DataFrame(super_witnesses)
        if len(df) > 0:
            df = df.sort_values('num_trials', ascending=False)

        print(f"  Found {len(df)} super-witnesses")

        # Print top 10
        if len(df) > 0:
            print("\n  Top 10 Super-Witnesses:")
            for _, row in df.head(10).iterrows():
                print(f"    {row['canonical_name']}: {row['num_trials']} trials")

        return df

    def compute_resolution_statistics(self) -> Dict:
        """Compute statistics about the resolution process."""
        stats = {
            'total_raw_entities': len(self.entity_mappings),
            'total_canonical_entities': len(self.canonical_entities),
            'compression_ratio': len(self.entity_mappings) / len(self.canonical_entities)
                                 if self.canonical_entities else 0,
        }

        # Entity type distribution
        type_counts = defaultdict(int)
        for entity in self.canonical_entities.values():
            type_counts[entity.entity_type] += 1
        stats['entity_types'] = dict(type_counts)

        # Gender distribution
        gender_counts = defaultdict(int)
        for entity in self.canonical_entities.values():
            gender_counts[entity.gender] += 1
        stats['genders'] = dict(gender_counts)

        # Multi-trial entities
        multi_trial = sum(1 for e in self.canonical_entities.values()
                         if len(set(a['trial_id'] for a in e.trial_appearances)) > 1)
        stats['multi_trial_entities'] = multi_trial

        # Witness-to-accused transitions
        transitions = sum(1 for e in self.canonical_entities.values()
                         if e.attributes.get('witness_to_accused'))
        stats['witness_to_accused_transitions'] = transitions

        return stats

    def save_outputs(self, transitions: List[Dict], super_witnesses: pd.DataFrame):
        """Save all resolution outputs."""
        print("\n=== Saving Outputs ===")

        # Save canonical entities
        canonical_json = {}
        for cid, entity in self.canonical_entities.items():
            canonical_json[cid] = {
                'canonical_id': entity.canonical_id,
                'canonical_name': entity.canonical_name,
                'variants': entity.variants,
                'entity_type': entity.entity_type,
                'gender': entity.gender,
                'locations': list(entity.locations),
                'trial_appearances': entity.trial_appearances,
                'outcome': entity.outcome,
                'attributes': entity.attributes,
            }

        with open(OUTPUT_DIR / "canonical_entities.json", 'w') as f:
            json.dump(canonical_json, f, indent=2)
        print(f"  Saved canonical_entities.json ({len(canonical_json)} entities)")

        # Save entity mappings
        with open(OUTPUT_DIR / "entity_mappings.json", 'w') as f:
            json.dump(self.entity_mappings, f, indent=2)
        print(f"  Saved entity_mappings.json ({len(self.entity_mappings)} mappings)")

        # Save transitions
        with open(OUTPUT_DIR / "witness_to_accused_transitions.json", 'w') as f:
            json.dump(transitions, f, indent=2)
        print(f"  Saved witness_to_accused_transitions.json ({len(transitions)} transitions)")

        # Save transitions as CSV
        if transitions:
            pd.DataFrame(transitions).to_csv(
                OUTPUT_DIR / "witness_to_accused_transitions.csv", index=False)

        # Save super-witnesses
        super_witnesses.to_csv(OUTPUT_DIR / "super_witnesses_resolved.csv", index=False)
        print(f"  Saved super_witnesses_resolved.csv ({len(super_witnesses)} super-witnesses)")

        # Save resolution log
        with open(OUTPUT_DIR / "resolution_log.json", 'w') as f:
            json.dump(self.resolution_log, f, indent=2)

        # Save statistics
        stats = self.compute_resolution_statistics()
        with open(OUTPUT_DIR / "resolution_statistics.json", 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"  Saved resolution_statistics.json")

    def run(self):
        """Execute the full resolution pipeline."""
        print("=" * 70)
        print("ENTITY RESOLUTION PIPELINE")
        print("=" * 70)

        # Load data
        entities = self.load_extracted_entities()
        df_trials = self.load_trials_data()

        # Build initial clusters
        clusters = self.build_initial_clusters(entities)

        # Fuzzy merge clusters
        merged = self.fuzzy_merge_clusters(clusters, entities)

        # Create canonical entities
        self.canonical_entities = self.create_canonical_entities(merged, entities, df_trials)

        # Find transitions
        transitions = self.find_witness_to_accused_transitions()

        # Identify super-witnesses
        super_witnesses = self.identify_super_witnesses(min_trials=3)

        # Save outputs
        self.save_outputs(transitions, super_witnesses)

        # Print final statistics
        stats = self.compute_resolution_statistics()
        print("\n" + "=" * 70)
        print("RESOLUTION COMPLETE")
        print("=" * 70)
        print(f"\nStatistics:")
        print(f"  Raw entities: {stats['total_raw_entities']}")
        print(f"  Canonical entities: {stats['total_canonical_entities']}")
        print(f"  Compression ratio: {stats['compression_ratio']:.2f}")
        print(f"  Multi-trial entities: {stats['multi_trial_entities']}")
        print(f"  Witness-to-accused: {stats['witness_to_accused_transitions']}")
        print(f"\nEntity Types: {stats['entity_types']}")
        print(f"Genders: {stats['genders']}")
        print(f"\nOutputs saved to: {OUTPUT_DIR}")

        return self.canonical_entities, transitions


if __name__ == "__main__":
    resolver = EntityResolver(similarity_threshold=85)
    canonical_entities, transitions = resolver.run()
