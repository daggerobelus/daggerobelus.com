#!/usr/bin/env python3
"""
Extract structured data from Lorraine witch trial PDFs.

This script:
1. Reads PDF text for analysis
2. Provides JSON templates
3. Validates extracted JSON against schema
4. Generates statistics on extraction progress

Usage:
    # Extract text from a single PDF:
    python extract_trial.py w001 --text

    # Output empty JSON template:
    python extract_trial.py w001 --template

    # Validate an extracted JSON file:
    python extract_trial.py w001 --validate

    # List PDFs not yet extracted:
    python extract_trial.py --missing

    # Show extraction statistics:
    python extract_trial.py --stats

Requirements:
    pip install PyPDF2 jsonschema
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List

try:
    from PyPDF2 import PdfReader
except ImportError:
    print("ERROR: pip install PyPDF2")
    sys.exit(1)

try:
    import jsonschema
except ImportError:
    print("WARNING: jsonschema not installed, validation disabled")
    print("  pip install jsonschema")
    jsonschema = None

# Paths
BASE_DIR = Path(__file__).parent.parent
ARCHIVE_DIR = BASE_DIR / "Archive_Complete"
TRIALS_DIR = BASE_DIR / "extracted_data" / "trials"
SCHEMA_PATH = Path(__file__).parent / "trial_schema.json"

# Ensure output directory exists
TRIALS_DIR.mkdir(parents=True, exist_ok=True)


def find_pdf(trial_id: str) -> Optional[Path]:
    """Find PDF file for a trial ID."""
    trial_id = trial_id.lower()
    if not trial_id.startswith('w'):
        trial_id = f"w{trial_id}"

    patterns = [
        f"{trial_id}.pdf",
        f"{trial_id.upper()}.pdf",
    ]

    for pattern in patterns:
        path = ARCHIVE_DIR / pattern
        if path.exists():
            return path

    # Try glob for variants like w022A.pdf
    matches = list(ARCHIVE_DIR.glob(f"{trial_id}*.pdf"))
    if matches:
        return sorted(matches)[0]

    return None


def extract_text(pdf_path: Path) -> str:
    """Extract text from PDF."""
    reader = PdfReader(pdf_path)
    text = ""
    for i, page in enumerate(reader.pages, 1):
        text += f"\n{'='*60}\n"
        text += f"PAGE {i}\n"
        text += f"{'='*60}\n\n"
        text += page.extract_text() or ""
        text += "\n"
    return text


def get_template(trial_id: str = "") -> dict:
    """Return empty template matching schema."""
    return {
        "trial_id": trial_id,
        "archive_ref": "",
        "location": "",
        "court": "",
        "dates": {
            "start": "",
            "end": "",
            "duration_days": None
        },
        "outcome": "unknown",
        "accused": [
            {
                "name": "",
                "gender": "unknown",
                "age": None,
                "age_approximate": False,
                "occupation": [],
                "origin": "",
                "residence": "",
                "marital_status": "unknown",
                "spouse_name": "",
                "parents": {"father": "", "mother": ""},
                "confession": {
                    "confessed": False,
                    "under_torture": False,
                    "retracted": False,
                    "retraction_renewed": False,
                    "devil_name": "",
                    "devil_appearance": "",
                    "seduction_date": "",
                    "seduction_context": "",
                    "devil_mark": {"present": False, "location": "", "description": ""},
                    "powder_types": [],
                    "sabbat_attended": False,
                    "sabbat_locations": [],
                    "sabbat_activities": [],
                    "sexual_relations_with_devil": False
                }
            }
        ],
        "witnesses": [],
        "timeline": [],
        "torture": {
            "used": False,
            "methods": [],
            "requesting_official": "",
            "approving_court": "",
            "restrictions": ""
        },
        "accomplices_named": [],
        "prior_accusations": [],
        "notable_quotes": [],
        "relationships": [],
        "economic_context": {
            "accused_occupation_disputes": False,
            "debt_disputes": False,
            "property_disputes": False,
            "details": ""
        },
        "harms_catalog": [],
        "material_culture": [],
        "spatial_references": [],
        "historical_context": {
            "military_presence": False,
            "military_details": "",
            "weather_events": [],
            "animal_predation": [],
            "economic_hardship_indicators": [],
            "religious_calendar_references": []
        },
        "legal_context": {
            "officials_named": [],
            "prior_legal_disputes": [],
            "accused_sought_redress": False,
            "redress_outcome": "",
            "imprisonment_conditions": "",
            "appeal_to_change_de_nancy": False,
            "property_confiscation_mentioned": False
        },
        "evidence_quality": {
            "firsthand_testimony_count": 0,
            "hearsay_testimony_count": 0,
            "hearsay_chains": [],
            "oldest_accusation_years": None,
            "corroboration_groups": []
        },
        "defense_and_behavior": {
            "defense_strategies": [],
            "emotional_state_notes": [],
            "reproaches_to_witnesses": []
        },
        "third_parties": [],
        "extraction_metadata": {
            "extracted_date": datetime.now().strftime("%Y-%m-%d"),
            "extractor": "claude",
            "confidence": "medium",
            "notes": "",
            "pdf_pages": 0
        }
    }


def get_witness_template() -> dict:
    """Return template for a single witness."""
    return {
        "number": 0,
        "name": "",
        "gender": "unknown",
        "age": None,
        "occupation": "",
        "location": "",
        "relationship_to_accused": "",
        "testimony": {
            "reputation_mentioned": False,
            "reputation_duration_years": None,
            "quarrel_mentioned": False,
            "quarrel_subject": "",
            "threat_received": False,
            "threat_quote": "",
            "harms_alleged": [],
            "theft_mentioned": False,
            "called_witch_publicly": False,
            "sought_legal_redress": False
        }
    }


def validate_json(data: dict) -> Tuple[bool, List[str]]:
    """Validate JSON against schema."""
    if jsonschema is None:
        return True, ["jsonschema not installed - validation skipped"]

    if not SCHEMA_PATH.exists():
        return True, ["Schema file not found - validation skipped"]

    with open(SCHEMA_PATH) as f:
        schema = json.load(f)

    errors = []
    validator = jsonschema.Draft7Validator(schema)
    for error in validator.iter_errors(data):
        path = " -> ".join(str(p) for p in error.absolute_path)
        errors.append(f"{path}: {error.message}")

    return len(errors) == 0, errors


def count_witnesses_in_text(text: str) -> int:
    """Estimate number of witnesses from text."""
    matches = re.findall(r'\((\d+)\)\s+[A-Z]', text)
    if matches:
        return max(int(m) for m in matches)
    return 0


def extract_dates_from_text(text: str) -> list[str]:
    """Extract dates from text."""
    patterns = [
        r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
        r'\d{1,2}/\d{1,2}/\d{4}',
    ]
    dates = []
    for pattern in patterns:
        dates.extend(re.findall(pattern, text, re.IGNORECASE))
    return sorted(set(dates))


def cmd_text(trial_id: str):
    """Extract and print text from PDF."""
    pdf_path = find_pdf(trial_id)
    if not pdf_path:
        print(f"ERROR: PDF not found for {trial_id}")
        print(f"  Searched in: {ARCHIVE_DIR}")
        sys.exit(1)

    text = extract_text(pdf_path)

    print(f"{'#'*70}")
    print(f"# TRIAL: {trial_id.upper()}")
    print(f"# PDF: {pdf_path.name}")
    print(f"{'#'*70}")
    print(text)
    print()
    print(f"{'#'*70}")
    print(f"# EXTRACTION HINTS")
    print(f"{'#'*70}")
    print(f"Estimated witnesses: {count_witnesses_in_text(text)}")
    print(f"Dates found: {extract_dates_from_text(text)}")
    print(f"Text length: {len(text):,} characters")
    print(f"PDF pages: {len(PdfReader(pdf_path).pages)}")


def cmd_template(trial_id: str):
    """Output JSON template for trial."""
    template = get_template(trial_id.lower())

    pdf_path = find_pdf(trial_id)
    if pdf_path:
        reader = PdfReader(pdf_path)
        template["extraction_metadata"]["pdf_pages"] = len(reader.pages)

        # Try to estimate witness count
        text = extract_text(pdf_path)
        witness_count = count_witnesses_in_text(text)
        if witness_count > 0:
            template["witnesses"] = [get_witness_template() for _ in range(witness_count)]
            for i, w in enumerate(template["witnesses"], 1):
                w["number"] = i

    print(json.dumps(template, indent=2))


def cmd_validate(trial_id: str):
    """Validate extracted JSON for trial."""
    json_path = TRIALS_DIR / f"{trial_id.lower()}.json"

    if not json_path.exists():
        print(f"ERROR: {json_path} not found")
        sys.exit(1)

    with open(json_path) as f:
        data = json.load(f)

    is_valid, errors = validate_json(data)

    if is_valid:
        print(f"VALID: {json_path.name}")
        print(f"  Accused: {len(data.get('accused', []))}")
        print(f"  Witnesses: {len(data.get('witnesses', []))}")
        print(f"  Timeline events: {len(data.get('timeline', []))}")
        print(f"  Harms cataloged: {len(data.get('harms_catalog', []))}")
        print(f"  Relationships: {len(data.get('relationships', []))}")
        print(f"  Outcome: {data.get('outcome', 'unknown')}")
    else:
        print(f"INVALID: {json_path.name}")
        print(f"Errors ({len(errors)}):")
        for error in errors[:20]:
            print(f"  - {error}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more errors")
        sys.exit(1)


def cmd_missing():
    """List PDFs without extracted JSON."""
    extracted = {p.stem.lower() for p in TRIALS_DIR.glob("*.json")}
    pdfs = sorted(ARCHIVE_DIR.glob("w*.pdf"))

    missing = []
    for pdf in pdfs:
        trial_id = pdf.stem.lower()
        if trial_id not in extracted:
            missing.append(trial_id)

    print(f"Total PDFs: {len(pdfs)}")
    print(f"Extracted: {len(extracted)}")
    print(f"Missing: {len(missing)}")
    print()

    if missing:
        print("Missing trials:")
        for tid in missing:
            print(f"  {tid}")


def cmd_stats():
    """Show extraction statistics."""
    json_files = list(TRIALS_DIR.glob("*.json"))

    if not json_files:
        print("No extracted trials yet.")
        return

    outcomes = {}
    total_witnesses = 0
    total_accused = 0
    total_harms = 0
    total_relationships = 0
    confessions = 0
    torture_used = 0

    for jf in json_files:
        with open(jf) as f:
            data = json.load(f)

        outcome = data.get("outcome", "unknown")
        outcomes[outcome] = outcomes.get(outcome, 0) + 1

        total_witnesses += len(data.get("witnesses", []))
        total_accused += len(data.get("accused", []))
        total_harms += len(data.get("harms_catalog", []))
        total_relationships += len(data.get("relationships", []))

        for acc in data.get("accused", []):
            if acc.get("confession", {}).get("confessed"):
                confessions += 1

        if data.get("torture", {}).get("used"):
            torture_used += 1

    pdfs = list(ARCHIVE_DIR.glob("w*.pdf"))

    print(f"{'='*50}")
    print(f"EXTRACTION STATISTICS")
    print(f"{'='*50}")
    print(f"\nProgress:")
    print(f"  Trials extracted: {len(json_files)} / {len(pdfs)} ({100*len(json_files)/len(pdfs):.1f}%)")
    print(f"\nTotals:")
    print(f"  Accused persons: {total_accused}")
    print(f"  Witnesses: {total_witnesses}")
    print(f"  Harms cataloged: {total_harms}")
    print(f"  Relationships: {total_relationships}")
    print(f"\nAverages per trial:")
    print(f"  Witnesses: {total_witnesses / len(json_files):.1f}")
    print(f"  Harms: {total_harms / len(json_files):.1f}")
    print(f"  Relationships: {total_relationships / len(json_files):.1f}")
    print(f"\nOutcomes:")
    for outcome, count in sorted(outcomes.items()):
        print(f"  {outcome}: {count}")
    print(f"\nProcedural:")
    print(f"  Confessions: {confessions}")
    print(f"  Torture used: {torture_used}")


def cmd_batch_validate():
    """Validate all extracted JSONs."""
    json_files = list(TRIALS_DIR.glob("*.json"))

    if not json_files:
        print("No extracted trials to validate.")
        return

    valid_count = 0
    invalid_files = []

    for jf in sorted(json_files):
        with open(jf) as f:
            data = json.load(f)

        is_valid, errors = validate_json(data)
        if is_valid:
            valid_count += 1
        else:
            invalid_files.append((jf.stem, len(errors)))

    print(f"Validated {len(json_files)} files")
    print(f"  Valid: {valid_count}")
    print(f"  Invalid: {len(invalid_files)}")

    if invalid_files:
        print(f"\nInvalid files:")
        for name, error_count in invalid_files:
            print(f"  {name}: {error_count} errors")


def main():
    parser = argparse.ArgumentParser(
        description="Extract structured data from witch trial PDFs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python extract_trial.py w001 --text      # Show PDF text
  python extract_trial.py w001 --template  # Output JSON template
  python extract_trial.py w001 --validate  # Validate extracted JSON
  python extract_trial.py --missing        # List unextracted trials
  python extract_trial.py --stats          # Show statistics
        """
    )
    parser.add_argument(
        "trial_id",
        nargs="?",
        help="Trial ID (e.g., w001, 001)"
    )
    parser.add_argument(
        "--text", "-t",
        action="store_true",
        help="Extract and print PDF text"
    )
    parser.add_argument(
        "--template",
        action="store_true",
        help="Output empty JSON template"
    )
    parser.add_argument(
        "--validate", "-v",
        action="store_true",
        help="Validate extracted JSON"
    )
    parser.add_argument(
        "--missing", "-m",
        action="store_true",
        help="List PDFs without extracted JSON"
    )
    parser.add_argument(
        "--stats", "-s",
        action="store_true",
        help="Show extraction statistics"
    )
    parser.add_argument(
        "--batch-validate",
        action="store_true",
        help="Validate all extracted JSONs"
    )

    args = parser.parse_args()

    if args.missing:
        cmd_missing()
    elif args.stats:
        cmd_stats()
    elif args.batch_validate:
        cmd_batch_validate()
    elif args.trial_id:
        if args.text:
            cmd_text(args.trial_id)
        elif args.template:
            cmd_template(args.trial_id)
        elif args.validate:
            cmd_validate(args.trial_id)
        else:
            cmd_text(args.trial_id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
