#!/usr/bin/env python3
"""
Module 03a: Enhanced Kinship Extraction for Lorraine Witchcraft Trials

Extracts ALL kinship and family relationships from trial text, not just from name patterns.

This module supplements 01_entity_extraction.py by:
1. Parsing kinship terms in testimony (his father, her brother, their son)
2. Extracting extended family (nephew, cousin, uncle, aunt)
3. Capturing in-law relationships
4. Building family clusters for network analysis

Kinship types extracted:
- SPOUSE_OF (bidirectional)
- WIDOW_OF (directional)
- PARENT_OF / CHILD_OF (directional)
- SIBLING_OF (bidirectional)
- GRANDPARENT_OF / GRANDCHILD_OF (directional)
- UNCLE_AUNT_OF / NEPHEW_NIECE_OF (directional)
- COUSIN_OF (bidirectional)
- IN_LAW_OF (bidirectional)
- GODPARENT_OF (directional)
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
import pandas as pd

# Configuration - update these paths for your system
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "extracted_data" / "trials"  # JSON trial files
OUTPUT_DIR = BASE_DIR / "social network data" / "output" / "edges"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)


@dataclass
class KinshipEdge:
    """Represents an extracted kinship relationship."""
    source: str
    target: str
    relationship_type: str
    trial_id: str
    evidence_text: str
    direction: str = "directed"  # "directed" or "undirected"
    confidence: float = 0.8
    source_role: str = ""  # accused, witness, victim, other
    target_role: str = ""
    extraction_method: str = "text_pattern"


class KinshipExtractor:
    """
    Extract kinship relationships from trial text.

    Uses pattern matching on both French and English terms commonly
    found in the Lorraine trial transcriptions.
    """

    # Kinship patterns with relationship type and directionality
    # Format: (pattern, relationship_type, direction, source_is_first)
    KINSHIP_PATTERNS = [
        # === SPOUSE relationships (undirected) ===
        # "X femme Y" - X is wife of Y
        (r"([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)\s+femme\s+(?:de\s+)?([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "SPOUSE_OF", "undirected", True),
        # "wife of X"
        (r"wife\s+(?:of\s+)?([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "SPOUSE_OF", "undirected", False),
        # "husband X" or "her husband X"
        (r"(?:his|her|their)\s+husband\s+([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "SPOUSE_OF", "undirected", False),
        # "married to X"
        (r"married\s+(?:to\s+)?([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "SPOUSE_OF", "undirected", False),

        # === WIDOW relationships (directed) ===
        # "X veuve Y" - X is widow of Y
        (r"([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)\s+veuve\s+(?:de\s+)?([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "WIDOW_OF", "directed", True),
        # "widow of X"
        (r"widow\s+(?:of\s+)?([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "WIDOW_OF", "directed", False),

        # === CHILD relationships (directed: child -> parent) ===
        # "X fils Y" - X is son of Y
        (r"([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)\s+fils\s+(?:de\s+)?([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "CHILD_OF", "directed", True),
        # "X fille Y" - X is daughter of Y
        (r"([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)\s+fille\s+(?:de\s+)?([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "CHILD_OF", "directed", True),
        # "son of X"
        (r"son\s+(?:of\s+)?([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "CHILD_OF", "directed", False),
        # "daughter of X"
        (r"daughter\s+(?:of\s+)?([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "CHILD_OF", "directed", False),
        # "child of X"
        (r"child\s+(?:of\s+)?([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "CHILD_OF", "directed", False),

        # === PARENT relationships (directed: parent -> child) ===
        # "his/her father X"
        (r"(?:his|her|their)\s+(?:late\s+)?father\s+([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)?",
         "PARENT_OF", "directed", False),
        # "his/her mother X"
        (r"(?:his|her|their)\s+(?:late\s+)?mother\s+([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)?",
         "PARENT_OF", "directed", False),
        # "son X" (possessive context)
        (r"(?:his|her|their)\s+son\s+([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "PARENT_OF", "directed", True),
        # "daughter X" (possessive context)
        (r"(?:his|her|their)\s+daughter\s+([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "PARENT_OF", "directed", True),
        # "son X, aged Y"
        (r"son\s+([A-Z][a-zéèêë]+),?\s+aged\s+\d+",
         "PARENT_OF", "directed", True),
        # French "son fils X"
        (r"son\s+fils\s+([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "PARENT_OF", "directed", True),
        # French "sa fille X"
        (r"sa\s+fille\s+([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "PARENT_OF", "directed", True),

        # === SIBLING relationships (undirected) ===
        # "his/her brother X"
        (r"(?:his|her|their)\s+brother\s+([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "SIBLING_OF", "undirected", False),
        # "his/her sister X"
        (r"(?:his|her|their)\s+sister\s+([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "SIBLING_OF", "undirected", False),
        # "brother of X"
        (r"brother\s+(?:of\s+)?([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "SIBLING_OF", "undirected", False),
        # "sister of X"
        (r"sister\s+(?:of\s+)?([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "SIBLING_OF", "undirected", False),
        # French "son frère X"
        (r"son\s+frère\s+([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "SIBLING_OF", "undirected", False),
        # French "sa soeur X"
        (r"sa\s+soeur\s+([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "SIBLING_OF", "undirected", False),

        # === NEPHEW/NIECE relationships (directed: uncle/aunt -> nephew/niece) ===
        # "his/her nephew X"
        (r"(?:his|her|their)\s+(?:small\s+)?nephew\s+([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)?",
         "UNCLE_AUNT_OF", "directed", True),
        # "his/her niece X"
        (r"(?:his|her|their)\s+niece\s+([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)?",
         "UNCLE_AUNT_OF", "directed", True),
        # "nephew of X" (X is uncle/aunt)
        (r"nephew\s+(?:of\s+)?([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "NEPHEW_NIECE_OF", "directed", False),
        # French "son neveu"
        (r"son\s+neveu\s+([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)?",
         "UNCLE_AUNT_OF", "directed", True),

        # === UNCLE/AUNT relationships ===
        # "his/her uncle X"
        (r"(?:his|her|their)\s+uncle\s+([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "NEPHEW_NIECE_OF", "directed", False),
        # "his/her aunt X"
        (r"(?:his|her|their)\s+aunt\s+([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "NEPHEW_NIECE_OF", "directed", False),

        # === COUSIN relationships (undirected) ===
        # "his/her cousin X"
        (r"(?:his|her|their)\s+cousin\s+([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "COUSIN_OF", "undirected", False),
        # "cousin of X"
        (r"cousin\s+(?:of\s+)?([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "COUSIN_OF", "undirected", False),

        # === IN-LAW relationships (undirected) ===
        # "son-in-law", "daughter-in-law", "father-in-law", "mother-in-law"
        (r"(?:his|her|their)\s+(?:son|daughter|father|mother)-in-law\s+([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)?",
         "IN_LAW_OF", "undirected", False),
        # French "beau-père", "belle-mère", etc.
        (r"(?:son|sa)\s+(?:beau-père|belle-mère|beau-frère|belle-soeur)\s+([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)?",
         "IN_LAW_OF", "undirected", False),

        # === GODPARENT relationships (directed) ===
        # "godfather X"
        (r"(?:his|her|their)\s+godfather\s+([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "GODPARENT_OF", "directed", False),
        # "godmother X"
        (r"(?:his|her|their)\s+godmother\s+([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "GODPARENT_OF", "directed", False),
        # French "parrain"
        (r"(?:son|sa)\s+parrain\s+([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "GODPARENT_OF", "directed", False),
        # French "marraine"
        (r"(?:son|sa)\s+marraine\s+([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "GODPARENT_OF", "directed", False),

        # === RELATIVE (generic) ===
        # "a relative" with name
        (r"a\s+relative\s+([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "KIN_OF", "undirected", False),
        # "relative of X"
        (r"relative\s+(?:of\s+)?([A-Z][a-zéèêë]+(?:\s+[A-Z][a-zéèêë]+)?)",
         "KIN_OF", "undirected", False),
    ]

    # Possessive pronouns to subject mapping
    POSSESSIVES = {
        'his': 'male',
        'her': 'female',
        'their': 'unknown',
        'son': 'male',  # French possessive
        'sa': 'female',  # French possessive
    }

    def __init__(self):
        self.edges: List[KinshipEdge] = []
        self.compiled_patterns = []
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile all regex patterns."""
        for pattern_str, rel_type, direction, source_first in self.KINSHIP_PATTERNS:
            try:
                compiled = re.compile(pattern_str, re.IGNORECASE | re.UNICODE)
                self.compiled_patterns.append((compiled, rel_type, direction, source_first))
            except re.error as e:
                print(f"Warning: Could not compile pattern '{pattern_str}': {e}")

    def extract_from_text(self, text: str, trial_id: str,
                          context_person: str = "",
                          context_role: str = "") -> List[KinshipEdge]:
        """
        Extract kinship relationships from a block of text.

        Args:
            text: The text to search
            trial_id: The trial ID for provenance
            context_person: The person this text is about (e.g., witness name)
            context_role: The role of context_person (e.g., "witness", "accused")

        Returns:
            List of extracted KinshipEdge objects
        """
        edges = []

        for compiled_pattern, rel_type, direction, source_first in self.compiled_patterns:
            for match in compiled_pattern.finditer(text):
                # Get the matched name(s)
                groups = match.groups()

                # Filter out None groups
                names = [g for g in groups if g and len(g) > 2]

                if not names:
                    continue

                # Determine source and target
                if len(names) >= 2:
                    # Pattern captured both names
                    if source_first:
                        source, target = names[0], names[1]
                    else:
                        source, target = names[1], names[0]
                elif len(names) == 1 and context_person:
                    # Pattern captured one name, use context for other
                    target = names[0]
                    source = context_person

                    # Adjust based on relationship semantics
                    if rel_type in ["CHILD_OF", "NEPHEW_NIECE_OF"] and not source_first:
                        # Context person is the child/nephew
                        source, target = context_person, names[0]
                    elif rel_type in ["PARENT_OF", "UNCLE_AUNT_OF"] and source_first:
                        # Context person is the parent/uncle
                        source, target = context_person, names[0]
                else:
                    continue

                # Get surrounding context for evidence
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                evidence = text[start:end].strip()

                edge = KinshipEdge(
                    source=source.strip(),
                    target=target.strip(),
                    relationship_type=rel_type,
                    trial_id=trial_id,
                    evidence_text=evidence,
                    direction=direction,
                    confidence=0.8,
                    source_role=context_role,
                    target_role="",
                    extraction_method="text_pattern"
                )
                edges.append(edge)

        return edges

    def extract_from_trial_json(self, trial_data: dict) -> List[KinshipEdge]:
        """
        Extract kinship from a trial JSON file (our new format).

        Searches through:
        - Witness testimonies
        - Accused biographical info
        - Notable quotes
        - Timeline events
        """
        edges = []
        trial_id = trial_data.get("trial_id", "")

        # 1. Extract from accused section
        for accused in trial_data.get("accused", []):
            name = accused.get("name", "")

            # Parents explicitly listed
            parents = accused.get("parents", {})
            if parents.get("father"):
                edges.append(KinshipEdge(
                    source=name,
                    target=parents["father"],
                    relationship_type="CHILD_OF",
                    trial_id=trial_id,
                    evidence_text=f"Father of {name}: {parents['father']}",
                    direction="directed",
                    confidence=1.0,
                    source_role="accused",
                    target_role="other",
                    extraction_method="explicit_field"
                ))
            if parents.get("mother"):
                edges.append(KinshipEdge(
                    source=name,
                    target=parents["mother"],
                    relationship_type="CHILD_OF",
                    trial_id=trial_id,
                    evidence_text=f"Mother of {name}: {parents['mother']}",
                    direction="directed",
                    confidence=1.0,
                    source_role="accused",
                    target_role="other",
                    extraction_method="explicit_field"
                ))

            # Spouse explicitly listed
            if accused.get("spouse_name"):
                edges.append(KinshipEdge(
                    source=name,
                    target=accused["spouse_name"],
                    relationship_type="SPOUSE_OF",
                    trial_id=trial_id,
                    evidence_text=f"Spouse of {name}: {accused['spouse_name']}",
                    direction="undirected",
                    confidence=1.0,
                    source_role="accused",
                    target_role="accused" if any(a.get("name") == accused["spouse_name"]
                                                  for a in trial_data.get("accused", [])) else "other",
                    extraction_method="explicit_field"
                ))

        # 2. Extract from witnesses section
        for witness in trial_data.get("witnesses", []):
            w_name = witness.get("name", "")

            # Search witness name for kinship patterns (e.g., "Catherine femme Jean")
            name_edges = self.extract_from_text(w_name, trial_id, "", "witness")
            for e in name_edges:
                e.source_role = "witness"
            edges.extend(name_edges)

            # Search testimony for kinship patterns
            testimony = witness.get("testimony", {})

            # Quarrel subject often mentions family
            quarrel = testimony.get("quarrel_subject", "")
            if quarrel:
                qe = self.extract_from_text(quarrel, trial_id, w_name, "witness")
                edges.extend(qe)

            # Threat quotes
            threat = testimony.get("threat_quote", "")
            if threat:
                te = self.extract_from_text(threat, trial_id, w_name, "witness")
                edges.extend(te)

            # Harms alleged - victim relationships
            for harm in testimony.get("harms_alleged", []):
                victim_rel = harm.get("target_relationship", "")
                target = harm.get("target", "")

                if victim_rel and target:
                    # Map relationship strings to types
                    rel_map = {
                        "husband": "SPOUSE_OF",
                        "wife": "SPOUSE_OF",
                        "father": "CHILD_OF",
                        "mother": "CHILD_OF",
                        "son": "PARENT_OF",
                        "daughter": "PARENT_OF",
                        "child": "PARENT_OF",
                        "brother": "SIBLING_OF",
                        "sister": "SIBLING_OF",
                        "nephew": "UNCLE_AUNT_OF",
                        "niece": "UNCLE_AUNT_OF",
                    }

                    for rel_word, rel_type in rel_map.items():
                        if rel_word in victim_rel.lower():
                            edges.append(KinshipEdge(
                                source=w_name,
                                target=target,
                                relationship_type=rel_type,
                                trial_id=trial_id,
                                evidence_text=f"Harm victim: {victim_rel}",
                                direction="directed" if rel_type not in ["SPOUSE_OF", "SIBLING_OF"] else "undirected",
                                confidence=0.9,
                                source_role="witness",
                                target_role="victim",
                                extraction_method="harm_victim_field"
                            ))
                            break

        # 3. Extract from relationships field (if pre-populated)
        for rel in trial_data.get("relationships", []):
            edges.append(KinshipEdge(
                source=rel.get("person1", ""),
                target=rel.get("person2", ""),
                relationship_type=rel.get("relationship_type", "").upper(),
                trial_id=trial_id,
                evidence_text=rel.get("evidence_text", ""),
                direction=rel.get("direction", "undirected"),
                confidence=1.0 if not rel.get("inferred") else 0.7,
                source_role=rel.get("person1_role", ""),
                target_role=rel.get("person2_role", ""),
                extraction_method="explicit_relationship_field"
            ))

        # 4. Extract from third_parties
        for tp in trial_data.get("third_parties", []):
            rel_to_accused = tp.get("relationship_to_accused", "")
            rel_to_witness = tp.get("relationship_to_witness", "")
            tp_name = tp.get("name", "")

            # Check relationship strings for family terms
            for rel_str, role in [(rel_to_accused, "accused"), (rel_to_witness, "witness")]:
                if not rel_str:
                    continue
                te = self.extract_from_text(rel_str, trial_id, tp_name, tp.get("role_in_narrative", ""))
                edges.extend(te)

        # 5. Extract from notable quotes
        for quote in trial_data.get("notable_quotes", []):
            french = quote.get("french", "")
            english = quote.get("english", "")
            context = quote.get("context", "")

            for text in [french, english, context]:
                if text:
                    qe = self.extract_from_text(text, trial_id, quote.get("speaker", ""), "")
                    edges.extend(qe)

        return edges

    def deduplicate_edges(self, edges: List[KinshipEdge]) -> List[KinshipEdge]:
        """Remove duplicate edges, keeping highest confidence."""
        seen = {}

        for edge in edges:
            # Create normalized key
            if edge.direction == "undirected":
                key = (min(edge.source, edge.target), max(edge.source, edge.target),
                       edge.relationship_type, edge.trial_id)
            else:
                key = (edge.source, edge.target, edge.relationship_type, edge.trial_id)

            if key not in seen or edge.confidence > seen[key].confidence:
                seen[key] = edge

        return list(seen.values())

    def run(self, trial_json_dir: Path = None) -> List[KinshipEdge]:
        """
        Run extraction on all trial JSON files.

        Args:
            trial_json_dir: Directory containing trial JSON files

        Returns:
            List of all extracted kinship edges
        """
        if trial_json_dir is None:
            trial_json_dir = DATA_DIR

        print("=" * 70)
        print("KINSHIP EXTRACTION PIPELINE")
        print("=" * 70)
        print(f"Source directory: {trial_json_dir}")

        all_edges = []
        json_files = list(trial_json_dir.glob("*.json"))

        print(f"Found {len(json_files)} trial JSON files")

        for json_file in sorted(json_files):
            with open(json_file) as f:
                trial_data = json.load(f)

            trial_id = trial_data.get("trial_id", json_file.stem)
            edges = self.extract_from_trial_json(trial_data)

            if edges:
                print(f"  {trial_id}: {len(edges)} kinship edges")
                all_edges.extend(edges)

        # Deduplicate
        print(f"\nTotal edges before deduplication: {len(all_edges)}")
        all_edges = self.deduplicate_edges(all_edges)
        print(f"Total edges after deduplication: {len(all_edges)}")

        # Compute statistics
        type_counts = defaultdict(int)
        for e in all_edges:
            type_counts[e.relationship_type] += 1

        print("\nEdges by type:")
        for rel_type, count in sorted(type_counts.items()):
            print(f"  {rel_type}: {count}")

        # Save outputs
        self._save_outputs(all_edges)

        return all_edges

    def _save_outputs(self, edges: List[KinshipEdge]):
        """Save extraction outputs."""
        print(f"\n=== Saving Outputs to {OUTPUT_DIR} ===")

        # Save as JSON
        edges_json = [asdict(e) for e in edges]
        with open(OUTPUT_DIR / "kinship_edges_enhanced.json", "w") as f:
            json.dump(edges_json, f, indent=2)
        print(f"  Saved kinship_edges_enhanced.json ({len(edges)} edges)")

        # Save as CSV
        df = pd.DataFrame(edges_json)
        df.to_csv(OUTPUT_DIR / "kinship_edges_enhanced.csv", index=False)
        print(f"  Saved kinship_edges_enhanced.csv")

        # Save statistics
        stats = {
            "total_edges": len(edges),
            "by_type": {k: int(v) for k, v in df["relationship_type"].value_counts().items()},
            "by_direction": {k: int(v) for k, v in df["direction"].value_counts().items()},
            "by_method": {k: int(v) for k, v in df["extraction_method"].value_counts().items()},
            "unique_sources": int(df["source"].nunique()),
            "unique_targets": int(df["target"].nunique()),
        }
        with open(OUTPUT_DIR / "kinship_extraction_stats.json", "w") as f:
            json.dump(stats, f, indent=2)
        print(f"  Saved kinship_extraction_stats.json")


if __name__ == "__main__":
    extractor = KinshipExtractor()
    edges = extractor.run()
