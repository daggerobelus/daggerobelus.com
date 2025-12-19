#!/usr/bin/env python3
"""
Derive analysis-ready CSVs from extracted JSON trial files.

Generates:
- trials.csv - One row per trial (metadata, outcomes)
- accused.csv - One row per accused person
- witnesses.csv - One row per witness testimony
- harms.csv - One row per alleged harm/maleficium
- relationships.csv - All kinship and social relationships (for network analysis)
- timeline.csv - All procedural events
- quotes.csv - Notable quotes with original French

Usage:
    python derive_csvs.py
    python derive_csvs.py --output /custom/path

Requirements:
    pip install pandas
"""

import argparse
import json
from pathlib import Path
from datetime import datetime

try:
    import pandas as pd
except ImportError:
    print("ERROR: pip install pandas")
    exit(1)

# Paths
BASE_DIR = Path(__file__).parent.parent
TRIALS_DIR = BASE_DIR / "extracted_data" / "trials"
OUTPUT_DIR = BASE_DIR / "extracted_data" / "derived"


def load_all_trials() -> list[dict]:
    """Load all extracted JSON trials."""
    trials = []
    for json_path in sorted(TRIALS_DIR.glob("*.json")):
        with open(json_path) as f:
            trials.append(json.load(f))
    return trials


def derive_trials_csv(trials: list[dict]) -> pd.DataFrame:
    """Generate trials.csv - one row per trial."""
    rows = []
    for t in trials:
        dates = t.get("dates", {})
        torture = t.get("torture", {})
        legal = t.get("legal_context", {})
        hist = t.get("historical_context", {})
        econ = t.get("economic_context", {})
        evidence = t.get("evidence_quality", {})

        row = {
            "trial_id": t.get("trial_id", ""),
            "archive_ref": t.get("archive_ref", ""),
            "location": t.get("location", ""),
            "court": t.get("court", ""),
            "start_date": dates.get("start", ""),
            "end_date": dates.get("end", ""),
            "duration_days": dates.get("duration_days"),
            "outcome": t.get("outcome", "unknown"),
            "accused_count": len(t.get("accused", [])),
            "witness_count": len(t.get("witnesses", [])),
            "harms_count": len(t.get("harms_catalog", [])),
            "relationships_count": len(t.get("relationships", [])),
            "torture_used": torture.get("used", False),
            "torture_methods": "; ".join(torture.get("methods", [])),
            "appeal_to_change_de_nancy": legal.get("appeal_to_change_de_nancy", False),
            "accused_sought_redress": legal.get("accused_sought_redress", False),
            "military_presence": hist.get("military_presence", False),
            "occupation_disputes": econ.get("accused_occupation_disputes", False),
            "debt_disputes": econ.get("debt_disputes", False),
            "firsthand_testimony_count": evidence.get("firsthand_testimony_count", 0),
            "hearsay_testimony_count": evidence.get("hearsay_testimony_count", 0),
            "oldest_accusation_years": evidence.get("oldest_accusation_years"),
            "accomplices_named_count": len(t.get("accomplices_named", [])),
            "pdf_pages": t.get("extraction_metadata", {}).get("pdf_pages", 0),
            "extraction_confidence": t.get("extraction_metadata", {}).get("confidence", ""),
        }
        rows.append(row)

    return pd.DataFrame(rows)


def derive_accused_csv(trials: list[dict]) -> pd.DataFrame:
    """Generate accused.csv - one row per accused person."""
    rows = []
    for t in trials:
        trial_id = t.get("trial_id", "")
        outcome = t.get("outcome", "unknown")

        for i, acc in enumerate(t.get("accused", []), 1):
            conf = acc.get("confession", {})
            parents = acc.get("parents", {})

            row = {
                "trial_id": trial_id,
                "accused_num": i,
                "name": acc.get("name", ""),
                "gender": acc.get("gender", "unknown"),
                "age": acc.get("age"),
                "age_approximate": acc.get("age_approximate", False),
                "occupation": "; ".join(acc.get("occupation", [])),
                "origin": acc.get("origin", ""),
                "residence": acc.get("residence", ""),
                "marital_status": acc.get("marital_status", "unknown"),
                "spouse_name": acc.get("spouse_name", ""),
                "father": parents.get("father", ""),
                "mother": parents.get("mother", ""),
                "outcome": outcome,
                "confessed": conf.get("confessed", False),
                "confession_under_torture": conf.get("under_torture", False),
                "confession_retracted": conf.get("retracted", False),
                "confession_renewed": conf.get("retraction_renewed", False),
                "devil_name": conf.get("devil_name", ""),
                "devil_appearance": conf.get("devil_appearance", ""),
                "seduction_context": conf.get("seduction_context", ""),
                "sabbat_attended": conf.get("sabbat_attended", False),
                "sabbat_locations": "; ".join(conf.get("sabbat_locations", [])),
                "powder_types": "; ".join(conf.get("powder_types", [])),
                "sexual_relations_with_devil": conf.get("sexual_relations_with_devil", False),
                "devil_mark_present": conf.get("devil_mark", {}).get("present", False),
            }
            rows.append(row)

    return pd.DataFrame(rows)


def derive_witnesses_csv(trials: list[dict]) -> pd.DataFrame:
    """Generate witnesses.csv - one row per witness testimony."""
    rows = []
    for t in trials:
        trial_id = t.get("trial_id", "")

        for w in t.get("witnesses", []):
            test = w.get("testimony", {})

            row = {
                "trial_id": trial_id,
                "witness_num": w.get("number"),
                "name": w.get("name", ""),
                "gender": w.get("gender", "unknown"),
                "age": w.get("age"),
                "occupation": w.get("occupation", ""),
                "location": w.get("location", ""),
                "relationship_to_accused": w.get("relationship_to_accused", ""),
                "reputation_mentioned": test.get("reputation_mentioned", False),
                "reputation_duration_years": test.get("reputation_duration_years"),
                "quarrel_mentioned": test.get("quarrel_mentioned", False),
                "quarrel_subject": test.get("quarrel_subject", ""),
                "threat_received": test.get("threat_received", False),
                "threat_quote": test.get("threat_quote", ""),
                "harms_count": len(test.get("harms_alleged", [])),
                "theft_mentioned": test.get("theft_mentioned", False),
                "called_witch_publicly": test.get("called_witch_publicly", False),
                "sought_legal_redress": test.get("sought_legal_redress", False),
            }
            rows.append(row)

    return pd.DataFrame(rows)


def derive_harms_csv(trials: list[dict]) -> pd.DataFrame:
    """Generate harms.csv - one row per alleged harm."""
    rows = []
    for t in trials:
        trial_id = t.get("trial_id", "")

        for harm in t.get("harms_catalog", []):
            row = {
                "trial_id": trial_id,
                "witness_num": harm.get("witness_number"),
                "victim_name": harm.get("victim_name", ""),
                "victim_relationship": harm.get("victim_relationship_to_witness", ""),
                "harm_category": harm.get("harm_category", ""),
                "harm_description": harm.get("harm_description", ""),
                "animal_type": harm.get("animal_type", ""),
                "animal_count": harm.get("animal_count"),
                "economic_value": harm.get("economic_value", ""),
                "attributed_to": harm.get("attributed_to", ""),
                "precipitating_quarrel": harm.get("precipitating_quarrel", ""),
                "time_between_quarrel_and_harm": harm.get("time_between_quarrel_and_harm", ""),
                "method_alleged": harm.get("method_alleged", ""),
            }
            rows.append(row)

    return pd.DataFrame(rows)


def derive_relationships_csv(trials: list[dict]) -> pd.DataFrame:
    """Generate relationships.csv - all kinship/social relationships for network analysis."""
    rows = []
    for t in trials:
        trial_id = t.get("trial_id", "")

        for rel in t.get("relationships", []):
            row = {
                "trial_id": trial_id,
                "person1": rel.get("person1", ""),
                "person2": rel.get("person2", ""),
                "relationship_type": rel.get("relationship_type", ""),
                "direction": rel.get("direction", "undirected"),
                "person1_role": rel.get("person1_role", ""),
                "person2_role": rel.get("person2_role", ""),
                "evidence_text": rel.get("evidence_text", ""),
                "inferred": rel.get("inferred", False),
            }
            rows.append(row)

    return pd.DataFrame(rows)


def derive_timeline_csv(trials: list[dict]) -> pd.DataFrame:
    """Generate timeline.csv - all procedural events."""
    rows = []
    for t in trials:
        trial_id = t.get("trial_id", "")

        for event in t.get("timeline", []):
            row = {
                "trial_id": trial_id,
                "date": event.get("date", ""),
                "event": event.get("event", ""),
                "subject": event.get("subject", ""),
                "details": event.get("details", ""),
            }
            rows.append(row)

    return pd.DataFrame(rows)


def derive_quotes_csv(trials: list[dict]) -> pd.DataFrame:
    """Generate quotes.csv - notable quotes with original French."""
    rows = []
    for t in trials:
        trial_id = t.get("trial_id", "")

        for quote in t.get("notable_quotes", []):
            row = {
                "trial_id": trial_id,
                "speaker": quote.get("speaker", ""),
                "french": quote.get("french", ""),
                "english": quote.get("english", ""),
                "context": quote.get("context", ""),
            }
            rows.append(row)

    return pd.DataFrame(rows)


def derive_spatial_csv(trials: list[dict]) -> pd.DataFrame:
    """Generate spatial.csv - all place references."""
    rows = []
    for t in trials:
        trial_id = t.get("trial_id", "")

        for place in t.get("spatial_references", []):
            row = {
                "trial_id": trial_id,
                "place_name": place.get("place_name", ""),
                "place_type": place.get("place_type", ""),
                "context": place.get("context", ""),
            }
            rows.append(row)

    return pd.DataFrame(rows)


def derive_material_culture_csv(trials: list[dict]) -> pd.DataFrame:
    """Generate material_culture.csv - objects mentioned."""
    rows = []
    for t in trials:
        trial_id = t.get("trial_id", "")

        for obj in t.get("material_culture", []):
            row = {
                "trial_id": trial_id,
                "object": obj.get("object", ""),
                "category": obj.get("category", ""),
                "context": obj.get("context", ""),
            }
            rows.append(row)

    return pd.DataFrame(rows)


def derive_persons_csv(trials: list[dict]) -> pd.DataFrame:
    """
    Generate persons.csv - unified view of ALL people mentioned in trials.

    Each row is a unique (trial_id, person_name) with their role(s) and
    relationship to the accused. This is the key file for network analysis.
    """
    rows = []

    for t in trials:
        trial_id = t.get("trial_id", "")

        # Track accused names for relationship mapping
        accused_names = [a.get("name", "") for a in t.get("accused", [])]

        # 1. Add all accused persons
        for acc in t.get("accused", []):
            row = {
                "trial_id": trial_id,
                "name": acc.get("name", ""),
                "role": "accused",
                "gender": acc.get("gender", "unknown"),
                "age": acc.get("age"),
                "occupation": "; ".join(acc.get("occupation", [])) if isinstance(acc.get("occupation"), list) else acc.get("occupation", ""),
                "location": acc.get("residence", "") or acc.get("origin", ""),
                "relationship_to_accused": "self",
                "confessed": acc.get("confession", {}).get("confessed", False),
                "outcome": t.get("outcome", "unknown"),
            }
            rows.append(row)

        # 2. Add all witnesses
        for w in t.get("witnesses", []):
            row = {
                "trial_id": trial_id,
                "name": w.get("name", ""),
                "role": "witness",
                "gender": w.get("gender", "unknown"),
                "age": w.get("age"),
                "occupation": w.get("occupation", ""),
                "location": w.get("location", ""),
                "relationship_to_accused": w.get("relationship_to_accused", ""),
                "confessed": None,
                "outcome": None,
            }
            rows.append(row)

        # 3. Add accomplices named (role: accomplice/co-accused)
        for acc in t.get("accomplices_named", []):
            row = {
                "trial_id": trial_id,
                "name": acc.get("name", ""),
                "role": "accomplice_named",
                "gender": "unknown",
                "age": None,
                "occupation": "",
                "location": acc.get("location", ""),
                "relationship_to_accused": acc.get("context", ""),
                "confessed": None,
                "outcome": None,
            }
            rows.append(row)

        # 4. Add third parties (victims, family, hearsay sources)
        for tp in t.get("third_parties", []):
            row = {
                "trial_id": trial_id,
                "name": tp.get("name", ""),
                "role": tp.get("role_in_narrative", "other"),
                "gender": "unknown",
                "age": None,
                "occupation": "",
                "location": "",
                "relationship_to_accused": tp.get("relationship_to_accused", ""),
                "confessed": None,
                "outcome": None,
            }
            rows.append(row)

        # 5. Add people from relationships who might not be elsewhere
        for rel in t.get("relationships", []):
            for person_key, role_key in [("person1", "person1_role"), ("person2", "person2_role")]:
                name = rel.get(person_key, "")
                role = rel.get(role_key, "other")

                # Skip if already added (check by name)
                existing_names = [r["name"] for r in rows if r["trial_id"] == trial_id]
                if name and name not in existing_names:
                    row = {
                        "trial_id": trial_id,
                        "name": name,
                        "role": role,
                        "gender": "unknown",
                        "age": None,
                        "occupation": "",
                        "location": "",
                        "relationship_to_accused": rel.get("relationship_type", ""),
                        "confessed": None,
                        "outcome": None,
                    }
                    rows.append(row)

    df = pd.DataFrame(rows)

    # Deduplicate by (trial_id, name), keeping first occurrence (usually most complete)
    if not df.empty:
        df = df.drop_duplicates(subset=["trial_id", "name"], keep="first")

    return df


def derive_confessions_summary_csv(trials: list[dict]) -> pd.DataFrame:
    """
    Generate confessions_summary.csv - trial-level confession statistics.
    """
    rows = []

    for t in trials:
        accused_list = t.get("accused", [])

        total_accused = len(accused_list)
        confessed_count = sum(1 for a in accused_list if a.get("confession", {}).get("confessed", False))
        under_torture_count = sum(1 for a in accused_list if a.get("confession", {}).get("under_torture", False))
        retracted_count = sum(1 for a in accused_list if a.get("confession", {}).get("retracted", False))
        renewed_count = sum(1 for a in accused_list if a.get("confession", {}).get("retraction_renewed", False))
        sabbat_count = sum(1 for a in accused_list if a.get("confession", {}).get("sabbat_attended", False))
        devil_named_count = sum(1 for a in accused_list if a.get("confession", {}).get("devil_name", ""))

        row = {
            "trial_id": t.get("trial_id", ""),
            "outcome": t.get("outcome", "unknown"),
            "total_accused": total_accused,
            "confessed_count": confessed_count,
            "confession_rate": confessed_count / total_accused if total_accused > 0 else 0,
            "confessed_under_torture": under_torture_count,
            "confessions_retracted": retracted_count,
            "confessions_renewed": renewed_count,
            "sabbat_confessed": sabbat_count,
            "devil_named": devil_named_count,
            "torture_used": t.get("torture", {}).get("used", False),
        }
        rows.append(row)

    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description="Derive CSVs from extracted trial JSONs")
    parser.add_argument("--output", "-o", type=Path, default=OUTPUT_DIR,
                        help="Output directory for CSVs")
    args = parser.parse_args()

    output_dir = args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading trials from: {TRIALS_DIR}")
    trials = load_all_trials()

    if not trials:
        print("No extracted trials found.")
        print(f"  Expected JSON files in: {TRIALS_DIR}")
        return

    print(f"Loaded {len(trials)} trials")
    print(f"Output directory: {output_dir}")
    print()

    # Generate all CSVs
    derivations = [
        ("trials.csv", derive_trials_csv),
        ("accused.csv", derive_accused_csv),
        ("witnesses.csv", derive_witnesses_csv),
        ("harms.csv", derive_harms_csv),
        ("relationships.csv", derive_relationships_csv),
        ("timeline.csv", derive_timeline_csv),
        ("quotes.csv", derive_quotes_csv),
        ("spatial.csv", derive_spatial_csv),
        ("material_culture.csv", derive_material_culture_csv),
        ("persons.csv", derive_persons_csv),
        ("confessions_summary.csv", derive_confessions_summary_csv),
    ]

    for filename, derive_func in derivations:
        df = derive_func(trials)
        output_path = output_dir / filename
        df.to_csv(output_path, index=False)
        print(f"  {filename}: {len(df)} rows")

    print()
    print(f"Done! CSVs saved to: {output_dir}")

    # Print summary
    print()
    print("=" * 50)
    print("SUMMARY")
    print("=" * 50)
    trials_df = pd.read_csv(output_dir / "trials.csv")
    print(f"Trials: {len(trials_df)}")
    print(f"Outcomes: {dict(trials_df['outcome'].value_counts())}")


if __name__ == "__main__":
    main()
