# Witch Trial Extraction Execution Plan

## Status: Ready to Execute
**Created:** 2025-12-21
**Last Updated:** 2025-12-21

---

## Current State

| Metric | Count |
|--------|-------|
| Total PDFs | 368 |
| Already extracted | 157 (including w003 test) |
| Remaining to extract | 211 |
| Schema version | Updated with new fields |

### Extracted Trials Location
- PDFs: `projects/witchcraft/ingest/archive/`
- JSONs: `projects/witchcraft/extracted/trials/`
- Schema: `projects/witchcraft/extracted/schema/trial_schema.json`

---

## Schema Updates (Completed)

New fields added to enable core research questions:

### Trial-level
| Field | Type | Purpose |
|-------|------|---------|
| `language_region` | enum: french/german/mixed/unknown | Regional confession pattern analysis |
| `formal_accuser` | object | Network analysis - who initiates trials |

### Accused-level
| Field | Type | Purpose |
|-------|------|---------|
| `person_id` | string \| null | Entity resolution (Phase 2) |
| `economic_status` | enum: destitute/poor/middling/comfortable/wealthy/unknown | Social vulnerability analysis |
| `practiced_healing` | boolean | Cunning folk identification |
| `healing_types` | array of enum | Healing practice categorization |

### Witness & Third-party level
| Field | Type | Purpose |
|-------|------|---------|
| `person_id` | string \| null | Entity resolution (Phase 2) |

### Legal Context (expanded)
| Field | Type | Purpose |
|-------|------|---------|
| `change_de_nancy.consulted` | boolean | Appellate involvement |
| `change_de_nancy.ruling` | enum | Court decision type |
| `change_de_nancy.modification_details` | string | What was changed |
| `change_de_nancy.local_court_followed` | boolean | Compliance tracking |

---

## Phase 1: Extract Remaining Trials (211)

### Approach
- Run parallel subagents in batches of 5
- Each subagent extracts one trial completely
- ~42 batches total

### Trials to Extract
```
Scattered gaps: w073, w100, w107, w109, w133 (5 trials)
Contiguous block: w153-w350 with variants (206 trials)
```

Full list saved to: `projects/witchcraft/extracted/remaining_trials.txt`

### Subagent Prompt Template
```
Extract witch trial data from PDF to JSON for PhD research on Lorraine witch trials.

TRIAL: {trial_id}
PDF: /Users/sarahbonanno/daggerobelus.com/projects/witchcraft/ingest/archive/{trial_id}.pdf
SCHEMA: /Users/sarahbonanno/daggerobelus.com/projects/witchcraft/extracted/schema/trial_schema.json
OUTPUT: /Users/sarahbonanno/daggerobelus.com/projects/witchcraft/extracted/trials/{trial_id}.json

Instructions:
1. Read the PDF thoroughly
2. Read the schema for field definitions
3. Extract ALL data following the schema exactly
4. Set person_id to null for all people (populated later during entity resolution)
5. Write valid JSON to the output path

Key fields to prioritize:
- economic_status (destitute/poor/middling/comfortable/wealthy/unknown)
- practiced_healing (boolean) + healing_types (array)
- formal_accuser (who initiated the trial)
- language_region (french/german/mixed/unknown - most Lorraine trials are french)
- change_de_nancy details (consulted, ruling, modification)
- All witnesses with testimony details
- All harms in harms_catalog
- All relationships
- Timeline events with dates

Be thorough. This is for PhD research. Flag uncertainties in extraction_metadata.notes.
```

### Batch Organization
```
Batch 1:  w073, w100, w107, w109, w133 (scattered gaps)
Batch 2:  w153, w154, w155, w156, w157
Batch 3:  w158, w159, w160, w161, w162
...
Batch 42: w346, w350
```

### Verification After Each Batch
1. Confirm JSON files created
2. Validate JSON syntax
3. Spot-check one extraction per batch

---

## Phase 2: Backfill Existing Trials (156)

### Approach
- Run after Phase 1 completes
- Subagents read existing JSON + original PDF
- Extract ONLY new fields, merge into existing JSON
- Faster than full re-extraction

### Fields to Backfill
- `language_region`
- `formal_accuser`
- `economic_status` (in accused)
- `practiced_healing` + `healing_types` (in accused)
- `change_de_nancy` (expanded object replacing boolean)
- `person_id: null` (all people arrays)

### Backfill Prompt Template
```
Backfill new schema fields for existing witch trial extraction.

TRIAL: {trial_id}
EXISTING JSON: /Users/sarahbonanno/daggerobelus.com/projects/witchcraft/extracted/trials/{trial_id}.json
PDF: /Users/sarahbonanno/daggerobelus.com/projects/witchcraft/ingest/archive/{trial_id}.pdf
SCHEMA: /Users/sarahbonanno/daggerobelus.com/projects/witchcraft/extracted/schema/trial_schema.json

Instructions:
1. Read the existing JSON
2. Read the PDF to extract missing fields
3. Add/update these fields:
   - language_region (french/german/mixed/unknown)
   - formal_accuser (object with name, occupation, location, relationship_to_accused)
   - accused[].economic_status
   - accused[].practiced_healing + healing_types
   - accused[].person_id: null
   - witnesses[].person_id: null
   - third_parties[].person_id: null
   - legal_context.change_de_nancy (expanded object)
4. Preserve ALL existing data
5. Write updated JSON back to same path

Do NOT re-extract fields that already exist and are correct.
```

---

## Phase 3: Entity Resolution (Future)

After all extractions complete:
1. Generate persons index from all JSONs
2. Fuzzy match names + location + time
3. Assign canonical person_ids
4. Update all JSONs with resolved IDs
5. Generate `derived/persons.csv`

---

## Phase 4: Derive CSVs (Future)

Aggregate JSON data into analysis-ready CSVs:
- `persons.csv` - All people across all trials with canonical IDs
- `relationships.csv` - All relationship edges
- `harms.csv` - All alleged harms/maleficia
- `confessions.csv` - Confession details
- `timeline.csv` - All dated events
- `trials_summary.csv` - One row per trial with key metrics

---

## Quality Assurance

### During Extraction
- Validate JSON after each batch
- Spot-check 1 extraction per batch against PDF
- Track extraction_metadata.confidence

### After All Extractions
- Run schema validation on all 368 JSONs
- Generate coverage report (which fields populated)
- Identify low-confidence extractions for review
- Compare statistics with existing 156 for consistency

---

## Progress Tracking

### Phase 1 Progress
| Batch | Trials | Status |
|-------|--------|--------|
| 1 | w073, w100, w107, w109, w133 | Pending |
| 2 | w153-w157 | Pending |
| 3 | w158-w162 | Pending |
| ... | ... | ... |

### Metrics to Track
- Trials extracted: 0/211
- Extraction errors: 0
- Low confidence extractions: TBD
- Average JSON size: ~40KB (based on w003)

---

## Notes

- PDFs are scholarly transcriptions (English summaries), not raw OCR - high quality source
- Most trials are French-speaking Lorraine region
- w003 test extraction took ~40KB, expect similar sizes
- Some PDFs may be incomplete (noted in extraction_metadata)
- Photographer occasionally missed pages (document in notes)
