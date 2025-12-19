#!/usr/bin/env python3
"""
Module 03: Relationship Extraction for Lorraine Witchcraft Trials
Extracts multi-type edges with confidence scoring from trial records.

Edge Types:
- SPOUSE_OF, WIDOW_OF, CHILD_OF (kinship - from name patterns)
- TESTIFIED_AGAINST (formal testimony)
- NAMED_AS_WITCH, SEEN_AT_SABBAT (accusation)
- QUARRELED_WITH, THREATENED (conflict)
- JUDGED_BY (institutional)
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Configuration
DATA_DIR = Path("/Users/natebaker/Desktop/analysis/extracted_data/intermediate")
ENTITY_DIR = Path("/Users/natebaker/Desktop/analysis/sna_pipeline/output/entities")
OUTPUT_DIR = Path("/Users/natebaker/Desktop/analysis/sna_pipeline/output")
(OUTPUT_DIR / "edges").mkdir(exist_ok=True, parents=True)


@dataclass
class Edge:
    """Represents an extracted relationship edge."""
    source: str  # canonical_id or name
    target: str
    relationship_type: str
    trial_id: str
    confidence: float = 1.0
    evidence_text: str = ''
    direction: str = 'directed'  # 'directed' or 'undirected'
    temporal_marker: Optional[int] = None  # year if available
    attributes: Dict = field(default_factory=dict)


class RelationshipExtractor:
    """
    Extract multi-type edges from trial records.
    """

    # Relationship type configurations
    RELATIONSHIP_CONFIG = {
        'SPOUSE_OF': {'confidence_base': 1.0, 'directed': False},
        'WIDOW_OF': {'confidence_base': 1.0, 'directed': True},
        'CHILD_OF': {'confidence_base': 1.0, 'directed': True},
        'SIBLING_OF': {'confidence_base': 0.9, 'directed': False},
        'TESTIFIED_AGAINST': {'confidence_base': 0.95, 'directed': True},
        'NAMED_AS_WITCH': {'confidence_base': 0.85, 'directed': True},
        'SEEN_AT_SABBAT': {'confidence_base': 0.80, 'directed': True},
        'QUARRELED_WITH': {'confidence_base': 0.75, 'directed': False},
        'THREATENED': {'confidence_base': 0.70, 'directed': True},
        'JUDGED_BY': {'confidence_base': 0.95, 'directed': True},
        'CO_ACCUSED': {'confidence_base': 0.90, 'directed': False},
        'CO_WITNESS': {'confidence_base': 0.60, 'directed': False},
    }

    def __init__(self):
        self.edges: List[Edge] = []
        self.edge_counts = defaultdict(int)

    def load_data(self) -> Tuple[Dict, Dict, pd.DataFrame, pd.DataFrame, List[Dict]]:
        """Load all source data."""
        print("Loading data...")

        # Load canonical entities
        with open(ENTITY_DIR / "canonical_entities.json") as f:
            canonical_entities = json.load(f)
        print(f"  Loaded {len(canonical_entities)} canonical entities")

        # Load entity mappings
        with open(ENTITY_DIR / "entity_mappings.json") as f:
            entity_mappings = json.load(f)
        print(f"  Loaded {len(entity_mappings)} entity mappings")

        # Load trials
        with open(DATA_DIR / "trials.json") as f:
            trials = json.load(f)
        df_trials = pd.DataFrame(trials)
        print(f"  Loaded {len(df_trials)} trials")

        # Load witnesses
        with open(DATA_DIR / "witnesses.json") as f:
            witnesses = json.load(f)
        df_witnesses = pd.DataFrame(witnesses)
        print(f"  Loaded {len(df_witnesses)} witness records")

        # Load kinship relations from Module 01
        with open(ENTITY_DIR / "kinship_relations.json") as f:
            kinship = json.load(f)
        print(f"  Loaded {len(kinship)} kinship relations")

        # Load existing network edges
        with open(DATA_DIR / "network_edges.json") as f:
            existing_edges = json.load(f)
        print(f"  Loaded {len(existing_edges)} existing network edges")

        return canonical_entities, entity_mappings, df_trials, df_witnesses, kinship, existing_edges

    def extract_testimony_edges(self, df_trials: pd.DataFrame,
                                df_witnesses: pd.DataFrame) -> List[Edge]:
        """Extract TESTIFIED_AGAINST edges from witness records."""
        print("\n=== Extracting Testimony Edges ===")

        edges = []

        # Group witnesses by trial
        for trial_id, group in df_witnesses.groupby('trial_id'):
            # Get accused for this trial
            trial_row = df_trials[df_trials['trial_id'] == trial_id]
            if trial_row.empty:
                continue

            accused_name = trial_row['accused_name'].values[0]
            year = self._extract_year(trial_row['trial_date'].values[0])

            # Each witness testified against the accused
            for _, witness_row in group.iterrows():
                witness_name = witness_row.get('witness_name', '')
                if not witness_name:
                    continue

                # Create testimony edge
                edge = Edge(
                    source=witness_name,
                    target=accused_name,
                    relationship_type='TESTIFIED_AGAINST',
                    trial_id=trial_id,
                    confidence=0.95,
                    evidence_text=f"Witness {witness_row.get('witness_num', 'N/A')} in trial {trial_id}",
                    direction='directed',
                    temporal_marker=year,
                    attributes={
                        'personal_suspicion': witness_row.get('personal_suspicion', False),
                        'testimony_length': witness_row.get('testimony_length', 0),
                        'reputation_years': witness_row.get('reputation_years'),
                    }
                )
                edges.append(edge)

        print(f"  Extracted {len(edges)} TESTIFIED_AGAINST edges")
        return edges

    def extract_kinship_edges(self, kinship_relations: List[Dict]) -> List[Edge]:
        """Convert kinship relations to edges."""
        print("\n=== Extracting Kinship Edges ===")

        edges = []
        type_mapping = {
            'spouse_wife': 'SPOUSE_OF',
            'spouse_widow': 'WIDOW_OF',
            'child_son': 'CHILD_OF',
            'child_daughter': 'CHILD_OF',
            'preceding_wife': 'SPOUSE_OF',
        }

        for rel in kinship_relations:
            rel_type = type_mapping.get(rel.get('relationship_type'), 'KINSHIP')

            edge = Edge(
                source=rel.get('person1', ''),
                target=rel.get('person2', ''),
                relationship_type=rel_type,
                trial_id=rel.get('trial_id', ''),
                confidence=rel.get('confidence', 1.0),
                evidence_text=rel.get('evidence_text', ''),
                direction='undirected' if rel_type == 'SPOUSE_OF' else 'directed',
            )
            edges.append(edge)

        print(f"  Extracted {len(edges)} kinship edges")

        # Count by type
        type_counts = defaultdict(int)
        for e in edges:
            type_counts[e.relationship_type] += 1
        for t, c in sorted(type_counts.items()):
            print(f"    {t}: {c}")

        return edges

    def extract_accusation_edges(self, existing_edges: List[Dict]) -> List[Edge]:
        """Convert existing network edges to standardized format."""
        print("\n=== Extracting Accusation Edges ===")

        edges = []
        type_mapping = {
            'seen_at_sabbat': 'SEEN_AT_SABBAT',
            'named_as_witch': 'NAMED_AS_WITCH',
        }

        for edge_data in existing_edges:
            rel_type = type_mapping.get(edge_data.get('relationship', ''), 'ACCUSATION')

            # Skip edges with incomplete targets
            target = edge_data.get('target', '')
            if not target or target in ['at', 'her at', 'him at', 'at the']:
                continue

            edge = Edge(
                source=edge_data.get('source', ''),
                target=target,
                relationship_type=rel_type,
                trial_id=edge_data.get('trial_id', ''),
                confidence=0.8,
                direction='directed',
            )
            edges.append(edge)

        print(f"  Extracted {len(edges)} accusation edges (filtered from {len(existing_edges)})")
        return edges

    def extract_co_accused_edges(self, df_trials: pd.DataFrame) -> List[Edge]:
        """Extract edges between co-accused in same trial."""
        print("\n=== Extracting Co-Accused Edges ===")

        edges = []

        for _, row in df_trials.iterrows():
            accused_name = row.get('accused_name', '') or ''
            trial_id = row['trial_id']
            year = self._extract_year(row.get('trial_date', ''))

            # Check for multiple accused (indicated by "et" or comma)
            if accused_name and (' et ' in accused_name or ',' in accused_name):
                # Try to split names
                names = re.split(r'\s+et\s+|,\s*', accused_name)
                names = [n.strip() for n in names if n.strip() and len(n.strip()) > 3]

                # Create edges between all pairs
                for i, name1 in enumerate(names):
                    for name2 in names[i+1:]:
                        edge = Edge(
                            source=name1,
                            target=name2,
                            relationship_type='CO_ACCUSED',
                            trial_id=trial_id,
                            confidence=0.90,
                            evidence_text=f"Co-accused in {trial_id}",
                            direction='undirected',
                            temporal_marker=year,
                        )
                        edges.append(edge)

        print(f"  Extracted {len(edges)} CO_ACCUSED edges")
        return edges

    def extract_co_witness_edges(self, df_witnesses: pd.DataFrame,
                                 max_witnesses_per_trial: int = 20) -> List[Edge]:
        """Extract edges between witnesses in same trial (selective)."""
        print("\n=== Extracting Co-Witness Edges ===")

        edges = []
        skipped_trials = 0

        for trial_id, group in df_witnesses.groupby('trial_id'):
            witnesses = group['witness_name'].dropna().unique().tolist()

            # Skip trials with too many witnesses (would create too many edges)
            if len(witnesses) > max_witnesses_per_trial:
                skipped_trials += 1
                continue

            # Create edges between first 10 witnesses only
            witnesses = witnesses[:10]

            for i, w1 in enumerate(witnesses):
                for w2 in witnesses[i+1:]:
                    edge = Edge(
                        source=w1,
                        target=w2,
                        relationship_type='CO_WITNESS',
                        trial_id=trial_id,
                        confidence=0.50,
                        evidence_text=f"Both witnessed in {trial_id}",
                        direction='undirected',
                    )
                    edges.append(edge)

        print(f"  Extracted {len(edges)} CO_WITNESS edges (skipped {skipped_trials} large trials)")
        return edges

    def _extract_year(self, date_str) -> Optional[int]:
        """Extract year from date string."""
        if not date_str or pd.isna(date_str):
            return None
        match = re.search(r'\b(1[5-6]\d{2})\b', str(date_str))
        return int(match.group(1)) if match else None

    def deduplicate_edges(self, edges: List[Edge]) -> List[Edge]:
        """Remove duplicate edges, keeping highest confidence."""
        print("\n=== Deduplicating Edges ===")

        # Create unique key for each edge
        edge_dict = {}

        for edge in edges:
            # Normalize key (for undirected, sort names)
            if edge.direction == 'undirected':
                key = (min(edge.source, edge.target),
                       max(edge.source, edge.target),
                       edge.relationship_type,
                       edge.trial_id)
            else:
                key = (edge.source, edge.target, edge.relationship_type, edge.trial_id)

            # Keep edge with highest confidence
            if key not in edge_dict or edge.confidence > edge_dict[key].confidence:
                edge_dict[key] = edge

        deduped = list(edge_dict.values())
        print(f"  Deduplicated {len(edges)} edges to {len(deduped)}")
        return deduped

    def compute_edge_statistics(self, edges: List[Edge]) -> Dict:
        """Compute statistics about extracted edges."""
        stats = {
            'total_edges': len(edges),
        }

        # Count by type
        type_counts = defaultdict(int)
        for edge in edges:
            type_counts[edge.relationship_type] += 1
        stats['by_type'] = dict(type_counts)

        # Count by direction
        directed_count = sum(1 for e in edges if e.direction == 'directed')
        stats['directed'] = directed_count
        stats['undirected'] = len(edges) - directed_count

        # Confidence distribution
        confidences = [e.confidence for e in edges]
        stats['confidence_mean'] = np.mean(confidences)
        stats['confidence_std'] = np.std(confidences)
        stats['confidence_min'] = np.min(confidences)
        stats['confidence_max'] = np.max(confidences)

        # Unique nodes
        nodes = set()
        for edge in edges:
            nodes.add(edge.source)
            nodes.add(edge.target)
        stats['unique_nodes'] = len(nodes)

        # Temporal coverage
        years = [e.temporal_marker for e in edges if e.temporal_marker]
        if years:
            stats['year_min'] = min(years)
            stats['year_max'] = max(years)
            stats['edges_with_year'] = len(years)

        return stats

    def save_outputs(self, edges: List[Edge], stats: Dict):
        """Save extracted edges and statistics."""
        print("\n=== Saving Outputs ===")

        output_dir = OUTPUT_DIR / "edges"

        # Save all edges as JSON
        edges_json = [asdict(e) for e in edges]
        with open(output_dir / "all_edges.json", 'w') as f:
            json.dump(edges_json, f, indent=2)
        print(f"  Saved all_edges.json ({len(edges)} edges)")

        # Save as CSV for easier analysis
        df = pd.DataFrame(edges_json)
        df.to_csv(output_dir / "all_edges.csv", index=False)
        print(f"  Saved all_edges.csv")

        # Save by relationship type
        for rel_type in df['relationship_type'].unique():
            subset = df[df['relationship_type'] == rel_type]
            filename = f"edges_{rel_type.lower()}.csv"
            subset.to_csv(output_dir / filename, index=False)

        # Save statistics
        with open(output_dir / "edge_statistics.json", 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"  Saved edge_statistics.json")

        # Print summary by type
        print("\n  Edge counts by type:")
        for rel_type, count in sorted(stats['by_type'].items()):
            print(f"    {rel_type}: {count}")

    def run(self):
        """Execute the full relationship extraction pipeline."""
        print("=" * 70)
        print("RELATIONSHIP EXTRACTION PIPELINE")
        print("=" * 70)

        # Load data
        (canonical_entities, entity_mappings, df_trials,
         df_witnesses, kinship, existing_edges) = self.load_data()

        # Extract different edge types
        all_edges = []

        # 1. Testimony edges (witness -> accused)
        testimony_edges = self.extract_testimony_edges(df_trials, df_witnesses)
        all_edges.extend(testimony_edges)

        # 2. Kinship edges (from name patterns)
        kinship_edges = self.extract_kinship_edges(kinship)
        all_edges.extend(kinship_edges)

        # 3. Accusation edges (from existing network data)
        accusation_edges = self.extract_accusation_edges(existing_edges)
        all_edges.extend(accusation_edges)

        # 4. Co-accused edges
        co_accused_edges = self.extract_co_accused_edges(df_trials)
        all_edges.extend(co_accused_edges)

        # 5. Co-witness edges (selective)
        co_witness_edges = self.extract_co_witness_edges(df_witnesses)
        all_edges.extend(co_witness_edges)

        # Deduplicate
        deduped_edges = self.deduplicate_edges(all_edges)

        # Compute statistics
        stats = self.compute_edge_statistics(deduped_edges)

        # Save outputs
        self.save_outputs(deduped_edges, stats)

        print("\n" + "=" * 70)
        print("EXTRACTION COMPLETE")
        print("=" * 70)
        print(f"\nSummary:")
        print(f"  Total edges: {stats['total_edges']}")
        print(f"  Unique nodes: {stats['unique_nodes']}")
        print(f"  Directed: {stats['directed']}, Undirected: {stats['undirected']}")
        if 'year_min' in stats:
            print(f"  Temporal range: {stats['year_min']}-{stats['year_max']}")
        print(f"\nOutputs saved to: {OUTPUT_DIR / 'edges'}")

        return deduped_edges, stats


if __name__ == "__main__":
    extractor = RelationshipExtractor()
    edges, stats = extractor.run()
