#!/usr/bin/env python3
"""
Module 01: Entity Extraction for Lorraine Witchcraft Trials
Extracts entities (persons, authorities, locations) from trial records using pattern-based NLP.

Research Focus: Power & Authority - identifying super-witnesses and institutional actors.
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
import pandas as pd
from rapidfuzz import fuzz
import warnings
warnings.filterwarnings('ignore')

# Configuration
DATA_DIR = Path("/Users/natebaker/Desktop/analysis/extracted_data/intermediate")
BATCH_DIR = Path("/Users/natebaker/Desktop/analysis/extracted_data/batches")
OUTPUT_DIR = Path("/Users/natebaker/Desktop/analysis/sna_pipeline/output/entities")
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


@dataclass
class Entity:
    """Represents an extracted entity (person, authority, location)."""
    raw_name: str
    entity_type: str  # 'person', 'authority', 'location', 'accused', 'witness'
    normalized_name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    gender: Optional[str] = None  # 'male', 'female', 'unknown'
    location: Optional[str] = None
    occupation: Optional[str] = None
    authority_role: Optional[str] = None  # 'mayor', 'procureur', etc.
    trial_ids: List[str] = field(default_factory=list)
    roles_in_trials: Dict[str, str] = field(default_factory=dict)  # trial_id -> role
    confidence: float = 1.0
    extraction_source: str = ''
    attributes: Dict = field(default_factory=dict)


@dataclass
class KinshipRelation:
    """Represents an extracted kinship relationship."""
    person1: str
    person2: str
    relationship_type: str  # 'spouse_of', 'widow_of', 'child_of', 'sibling_of'
    trial_id: str
    evidence_text: str
    confidence: float = 1.0


class EntityExtractor:
    """
    Multi-pass entity extraction with confidence scoring.

    Pass 1: Structural extraction (witnesses from trial format)
    Pass 2: Pattern-based extraction (kinship, authority markers)
    Pass 3: Name normalization and gender inference
    """

    # Kinship patterns (French Early Modern naming conventions)
    KINSHIP_PATTERNS = {
        'spouse_wife': re.compile(
            r'([A-Z][a-zé]+(?:\s+[A-Z][a-zé]+)?)\s+femme\s+(?:de\s+)?([A-Z][a-zé]+(?:\s+[A-Z][a-zé]+)?)',
            re.UNICODE
        ),
        'spouse_widow': re.compile(
            r'([A-Z][a-zé]+(?:\s+[A-Z][a-zé]+)?)\s+veuve\s+(?:de\s+)?([A-Z][a-zé]+(?:\s+[A-Z][a-zé]+)?)',
            re.UNICODE
        ),
        'child_son': re.compile(
            r'([A-Z][a-zé]+(?:\s+[A-Z][a-zé]+)?)\s+fils\s+(?:de\s+)?([A-Z][a-zé]+(?:\s+[A-Z][a-zé]+)?)',
            re.UNICODE
        ),
        'child_daughter': re.compile(
            r'([A-Z][a-zé]+(?:\s+[A-Z][a-zé]+)?)\s+fille\s+(?:de\s+)?([A-Z][a-zé]+(?:\s+[A-Z][a-zé]+)?)',
            re.UNICODE
        ),
        'preceding_wife': re.compile(
            r'([A-Z][a-zé]+(?:\s+[A-Z][a-zé]+)?)\s+femme\s+du\s+precedent',
            re.UNICODE | re.IGNORECASE
        ),
    }

    # Authority patterns
    AUTHORITY_PATTERNS = {
        'mayor': re.compile(
            r'[Ll]e\s+maire\s+([A-Z][a-zé]+(?:\s+[A-Z][a-zé]+)?)',
            re.UNICODE
        ),
        'procureur': re.compile(
            r'PG\s+(?:de\s+Lorraine|\(Maimbourg\))',
            re.UNICODE
        ),
        'change_nancy': re.compile(
            r'Change\s+de\s+Nancy',
            re.UNICODE
        ),
        'laboureur': re.compile(
            r'([A-Z][a-zé]+(?:\s+[A-Z][a-zé]+)?),?\s+laboureur',
            re.UNICODE
        ),
    }

    # Location patterns
    LOCATION_PATTERNS = {
        'de_location': re.compile(
            r',?\s+d[eu\']\s*([A-Z][a-zé\-]+(?:\s+[A-Z][a-zé\-]+)?)',
            re.UNICODE
        ),
        'of_location': re.compile(
            r',?\s+of\s+([A-Z][a-zé\-]+(?:\s+[A-Z][a-zé\-]+)?)',
            re.UNICODE
        ),
    }

    # Gender indicators
    FEMALE_INDICATORS = {'femme', 'veuve', 'fille', 'Catherine', 'Marie', 'Jeanne',
                         'Marguerite', 'Anne', 'Barbe', 'Claudatte', 'Jennon',
                         'Odille', 'Collatte', 'Didiere', 'Mengeotte', 'Mariette'}
    MALE_INDICATORS = {'fils', 'Jean', 'Claude', 'Nicolas', 'Pierre', 'Antoine',
                       'Jacques', 'Demenge', 'Claudon', 'Bastien'}

    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.kinship_relations: List[KinshipRelation] = []
        self.witness_to_accused_transitions: List[Dict] = []

    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, List[Dict]]:
        """Load all source data."""
        print("Loading data...")

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

        # Load batch data for raw text
        batch_data = []
        for batch_file in sorted(BATCH_DIR.glob("batch_*.json")):
            with open(batch_file) as f:
                data = json.load(f)
                # Handle nested structure (trials key at root)
                if isinstance(data, dict) and 'trials' in data:
                    batch_data.extend(data['trials'])
                elif isinstance(data, list):
                    batch_data.extend(data)
        print(f"  Loaded {len(batch_data)} batch records")

        return df_trials, df_witnesses, batch_data

    def extract_from_accused_names(self, df_trials: pd.DataFrame) -> List[Entity]:
        """Extract entities from accused_name field."""
        print("\n=== Extracting from Accused Names ===")

        entities = []
        for _, row in df_trials.iterrows():
            trial_id = row['trial_id']
            accused_name = row.get('accused_name', '')

            if not accused_name or pd.isna(accused_name):
                continue

            # Parse the accused name field
            entity = self._parse_accused_name(accused_name, trial_id)
            if entity:
                entities.append(entity)

            # Extract kinship from accused name
            kinship = self._extract_kinship_from_name(accused_name, trial_id)
            self.kinship_relations.extend(kinship)

        print(f"  Extracted {len(entities)} accused entities")
        print(f"  Found {len(self.kinship_relations)} kinship relations so far")
        return entities

    def _parse_accused_name(self, accused_name: str, trial_id: str) -> Optional[Entity]:
        """Parse accused_name field to extract entity."""
        # Format: "B 2148; witch 001; Jean Bulme et Didiere sa femme, de Mazerulles"

        # Extract the actual name part (after "witch XXX;")
        parts = accused_name.split(';')
        if len(parts) >= 3:
            name_part = parts[-1].strip()
        else:
            name_part = accused_name

        # Extract location
        location = None
        for pattern in self.LOCATION_PATTERNS.values():
            match = pattern.search(name_part)
            if match:
                location = match.group(1)
                break

        # Detect gender
        gender = self._infer_gender(name_part)

        entity = Entity(
            raw_name=accused_name,
            entity_type='accused',
            normalized_name=name_part.split(',')[0].strip() if ',' in name_part else name_part,
            gender=gender,
            location=location,
            trial_ids=[trial_id],
            roles_in_trials={trial_id: 'accused'},
            extraction_source='accused_name_field',
            confidence=1.0
        )

        return entity

    def _extract_kinship_from_name(self, name: str, trial_id: str) -> List[KinshipRelation]:
        """Extract kinship relationships from a name string."""
        relations = []

        for rel_type, pattern in self.KINSHIP_PATTERNS.items():
            matches = pattern.findall(name)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    relations.append(KinshipRelation(
                        person1=match[0],
                        person2=match[1],
                        relationship_type=rel_type,
                        trial_id=trial_id,
                        evidence_text=name,
                        confidence=1.0
                    ))

        return relations

    def extract_from_witnesses(self, df_witnesses: pd.DataFrame) -> List[Entity]:
        """Extract entities from witness records."""
        print("\n=== Extracting from Witness Records ===")

        entities = []
        witness_name_counts = defaultdict(list)

        for _, row in df_witnesses.iterrows():
            trial_id = row['trial_id']
            witness_name = row.get('witness_name', '')

            if not witness_name or pd.isna(witness_name):
                continue

            # Track multi-trial witnesses
            witness_name_counts[witness_name].append(trial_id)

            # Parse witness name
            entity = self._parse_witness_name(row)
            if entity:
                entities.append(entity)

            # Extract kinship
            kinship = self._extract_kinship_from_name(witness_name, trial_id)
            self.kinship_relations.extend(kinship)

        # Identify super-witnesses (3+ trials)
        super_witnesses = {name: trials for name, trials in witness_name_counts.items()
                          if len(trials) >= 3}

        print(f"  Extracted {len(entities)} witness entities")
        print(f"  Found {len(super_witnesses)} super-witnesses (3+ trials)")
        print(f"  Total kinship relations: {len(self.kinship_relations)}")

        # Mark super-witnesses
        for entity in entities:
            if entity.raw_name in super_witnesses:
                entity.attributes['super_witness'] = True
                entity.attributes['trial_count'] = len(super_witnesses[entity.raw_name])

        return entities

    def _parse_witness_name(self, row: pd.Series) -> Optional[Entity]:
        """Parse a witness record to extract entity."""
        witness_name = row['witness_name']
        trial_id = row['trial_id']

        # Extract location from name
        location = None
        for pattern in self.LOCATION_PATTERNS.values():
            match = pattern.search(witness_name)
            if match:
                location = match.group(1)
                break

        # Detect gender
        gender = self._infer_gender(witness_name)

        # Check for authority markers
        authority_role = None
        for role, pattern in self.AUTHORITY_PATTERNS.items():
            if pattern.search(witness_name):
                authority_role = role
                break

        # Check for personal suspicion flag
        personal_suspicion = row.get('personal_suspicion', False)

        entity = Entity(
            raw_name=witness_name,
            entity_type='witness',
            normalized_name=self._normalize_name(witness_name),
            gender=gender,
            location=location,
            authority_role=authority_role,
            trial_ids=[trial_id],
            roles_in_trials={trial_id: 'witness'},
            extraction_source='witness_record',
            confidence=1.0,
            attributes={
                'witness_num': row.get('witness_num'),
                'reputation_years': row.get('reputation_years'),
                'personal_suspicion': personal_suspicion,
                'testimony_length': row.get('testimony_length'),
            }
        )

        return entity

    def _normalize_name(self, name: str) -> str:
        """Normalize a name for matching."""
        # Remove location suffixes
        name = re.sub(r',?\s+d[eu\']\s*[A-Z][a-zé\-]+.*$', '', name)
        name = re.sub(r',?\s+of\s+[A-Z][a-zé\-]+.*$', '', name)

        # Remove age indicators
        name = re.sub(r',?\s+\d+\s*$', '', name)

        # Remove occupations
        name = re.sub(r',?\s+laboureur.*$', '', name, flags=re.IGNORECASE)

        # Clean up
        name = name.strip()
        return name

    def _infer_gender(self, name: str) -> str:
        """Infer gender from name patterns."""
        name_lower = name.lower()

        # Check for explicit female indicators
        for indicator in self.FEMALE_INDICATORS:
            if indicator.lower() in name_lower:
                return 'female'

        # Check for explicit male indicators
        for indicator in self.MALE_INDICATORS:
            if indicator.lower() in name_lower:
                return 'male'

        return 'unknown'

    def extract_authority_figures(self, batch_data: List[Dict]) -> List[Entity]:
        """Extract authority figures from trial texts."""
        print("\n=== Extracting Authority Figures ===")

        authority_entities = []
        authority_mentions = defaultdict(lambda: {'trials': set(), 'role': None})

        # Note: batch_data may not contain full text, so we work with what we have
        # This extracts from any available text fields

        for record in batch_data:
            trial_id = record.get('trial_id', '')

            # Check accused_name for authority references
            accused_name = record.get('accused_name', '') or ''

            # Look for mayor mentions
            mayor_match = self.AUTHORITY_PATTERNS['mayor'].search(accused_name)
            if mayor_match:
                mayor_name = mayor_match.group(1)
                authority_mentions[mayor_name]['trials'].add(trial_id)
                authority_mentions[mayor_name]['role'] = 'mayor'

            # Procureur and Change de Nancy are institutional, not individual
            if self.AUTHORITY_PATTERNS['procureur'].search(accused_name):
                authority_mentions['Procureur General de Lorraine']['trials'].add(trial_id)
                authority_mentions['Procureur General de Lorraine']['role'] = 'procureur'

            if self.AUTHORITY_PATTERNS['change_nancy'].search(accused_name):
                authority_mentions['Change de Nancy']['trials'].add(trial_id)
                authority_mentions['Change de Nancy']['role'] = 'appellate_court'

        # Create entities for authorities
        for name, info in authority_mentions.items():
            entity = Entity(
                raw_name=name,
                entity_type='authority',
                normalized_name=name,
                authority_role=info['role'],
                trial_ids=list(info['trials']),
                roles_in_trials={t: 'authority' for t in info['trials']},
                extraction_source='text_pattern',
                confidence=0.9
            )
            authority_entities.append(entity)

        print(f"  Extracted {len(authority_entities)} authority figures")
        return authority_entities

    def find_witness_to_accused_transitions(self,
                                            witness_entities: List[Entity],
                                            accused_entities: List[Entity]) -> List[Dict]:
        """Identify individuals who were witnesses then became accused."""
        print("\n=== Finding Witness-to-Accused Transitions ===")

        transitions = []

        # Build lookup for accused names
        accused_names = {e.normalized_name: e for e in accused_entities if e.normalized_name}

        for witness in witness_entities:
            if not witness.normalized_name:
                continue

            # Check for exact match
            if witness.normalized_name in accused_names:
                accused = accused_names[witness.normalized_name]
                transitions.append({
                    'name': witness.normalized_name,
                    'witness_trials': witness.trial_ids,
                    'accused_trials': accused.trial_ids,
                    'witness_entity': witness,
                    'accused_entity': accused,
                })
                continue

            # Check for fuzzy match
            for accused_name, accused in accused_names.items():
                similarity = fuzz.ratio(witness.normalized_name, accused_name)
                if similarity > 85:
                    transitions.append({
                        'name': witness.normalized_name,
                        'accused_name': accused_name,
                        'similarity': similarity,
                        'witness_trials': witness.trial_ids,
                        'accused_trials': accused.trial_ids,
                        'witness_entity': witness,
                        'accused_entity': accused,
                    })

        print(f"  Found {len(transitions)} potential witness-to-accused transitions")

        self.witness_to_accused_transitions = transitions
        return transitions

    def merge_entities(self, all_entities: List[Entity]) -> Dict[str, Entity]:
        """Merge entities that refer to the same person."""
        print("\n=== Merging Duplicate Entities ===")

        merged = {}

        for entity in all_entities:
            key = entity.normalized_name or entity.raw_name

            if key in merged:
                # Merge trial appearances
                existing = merged[key]
                existing.trial_ids = list(set(existing.trial_ids + entity.trial_ids))
                existing.roles_in_trials.update(entity.roles_in_trials)

                # Merge attributes
                for k, v in entity.attributes.items():
                    if k not in existing.attributes:
                        existing.attributes[k] = v

                # Update entity type if upgraded to accused
                if entity.entity_type == 'accused':
                    existing.entity_type = 'accused'
                    existing.attributes['was_witness'] = True
            else:
                merged[key] = entity

        print(f"  Merged {len(all_entities)} entities into {len(merged)} unique entities")
        return merged

    def compute_entity_statistics(self, entities: Dict[str, Entity]) -> pd.DataFrame:
        """Compute statistics for entities."""
        print("\n=== Computing Entity Statistics ===")

        stats = []
        for name, entity in entities.items():
            stats.append({
                'name': name,
                'entity_type': entity.entity_type,
                'gender': entity.gender,
                'location': entity.location,
                'authority_role': entity.authority_role,
                'num_trial_appearances': len(entity.trial_ids),
                'is_super_witness': entity.attributes.get('super_witness', False),
                'personal_suspicion': entity.attributes.get('personal_suspicion', False),
                'was_witness_then_accused': entity.attributes.get('was_witness', False),
            })

        df_stats = pd.DataFrame(stats)

        print(f"\nEntity Type Distribution:")
        print(df_stats['entity_type'].value_counts())

        print(f"\nGender Distribution:")
        print(df_stats['gender'].value_counts())

        print(f"\nSuper-witnesses (3+ trials): {df_stats['is_super_witness'].sum()}")
        print(f"With personal suspicion: {df_stats['personal_suspicion'].sum()}")

        return df_stats

    def save_outputs(self,
                     entities: Dict[str, Entity],
                     entity_stats: pd.DataFrame,
                     kinship_relations: List[KinshipRelation],
                     transitions: List[Dict]):
        """Save all extraction outputs."""
        print("\n=== Saving Outputs ===")

        # Save entities as JSON
        entities_json = {k: asdict(v) for k, v in entities.items()}
        with open(OUTPUT_DIR / "extracted_entities.json", 'w') as f:
            json.dump(entities_json, f, indent=2, default=str)
        print(f"  Saved extracted_entities.json ({len(entities)} entities)")

        # Save entity statistics
        entity_stats.to_csv(OUTPUT_DIR / "entity_statistics.csv", index=False)
        print(f"  Saved entity_statistics.csv")

        # Save kinship relations
        kinship_data = [asdict(k) for k in kinship_relations]
        with open(OUTPUT_DIR / "kinship_relations.json", 'w') as f:
            json.dump(kinship_data, f, indent=2)
        print(f"  Saved kinship_relations.json ({len(kinship_relations)} relations)")

        # Save kinship as CSV for easier analysis
        kinship_df = pd.DataFrame(kinship_data)
        kinship_df.to_csv(OUTPUT_DIR / "kinship_relations.csv", index=False)

        # Save witness-to-accused transitions
        transitions_clean = []
        for t in transitions:
            transitions_clean.append({
                'name': t['name'],
                'accused_name': t.get('accused_name', t['name']),
                'similarity': t.get('similarity', 100),
                'witness_trials': t['witness_trials'],
                'accused_trials': t['accused_trials'],
            })
        with open(OUTPUT_DIR / "witness_to_accused_transitions.json", 'w') as f:
            json.dump(transitions_clean, f, indent=2)
        print(f"  Saved witness_to_accused_transitions.json ({len(transitions)} transitions)")

        # Save super-witnesses separately
        super_witnesses = entity_stats[entity_stats['is_super_witness'] == True]
        super_witnesses.to_csv(OUTPUT_DIR / "super_witnesses.csv", index=False)
        print(f"  Saved super_witnesses.csv ({len(super_witnesses)} super-witnesses)")

        # Save authority figures
        authorities = entity_stats[entity_stats['authority_role'].notna()]
        authorities.to_csv(OUTPUT_DIR / "authority_figures.csv", index=False)
        print(f"  Saved authority_figures.csv ({len(authorities)} authorities)")

    def run(self):
        """Execute the full extraction pipeline."""
        print("=" * 70)
        print("ENTITY EXTRACTION PIPELINE")
        print("=" * 70)

        # Load data
        df_trials, df_witnesses, batch_data = self.load_data()

        # Extract entities from different sources
        accused_entities = self.extract_from_accused_names(df_trials)
        witness_entities = self.extract_from_witnesses(df_witnesses)
        authority_entities = self.extract_authority_figures(batch_data)

        # Combine all entities
        all_entities = accused_entities + witness_entities + authority_entities

        # Find witness-to-accused transitions
        transitions = self.find_witness_to_accused_transitions(witness_entities, accused_entities)

        # Merge duplicates
        merged_entities = self.merge_entities(all_entities)

        # Compute statistics
        entity_stats = self.compute_entity_statistics(merged_entities)

        # Save outputs
        self.save_outputs(merged_entities, entity_stats, self.kinship_relations, transitions)

        print("\n" + "=" * 70)
        print("EXTRACTION COMPLETE")
        print("=" * 70)
        print(f"\nSummary:")
        print(f"  Total unique entities: {len(merged_entities)}")
        print(f"  Kinship relations: {len(self.kinship_relations)}")
        print(f"  Witness-to-accused transitions: {len(transitions)}")
        print(f"\nOutputs saved to: {OUTPUT_DIR}")

        return merged_entities, self.kinship_relations, transitions


if __name__ == "__main__":
    extractor = EntityExtractor()
    entities, kinship, transitions = extractor.run()
