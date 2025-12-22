# Witch Trial PDF Extraction Plan

## Overview
Extract structured data from 368 witch trial PDFs from the Lorraine archive for PhD research using parallel NL-parsing subagents.

## Source Files
- **Location**: `/Users/sarahbonanno/Desktop/Witchcraft/Archive_Complete/`
- **Total PDFs**: 368 (w001.pdf through w350.pdf, with variants like w022A, w055A, w065A-D, w068A, w081A, w277A-E, w333A-F)

## Output Structure
```
extracted_data/
├── trials/           # One JSON file per trial (canonical source)
│   ├── w001.json
│   ├── w002.json
│   └── ...
└── derived/          # CSVs derived from JSON for analysis
    ├── persons.csv
    ├── relationships.csv
    ├── harms.csv
    ├── confessions.csv
    └── timeline.csv
```

## JSON Schema (per trial)
Each trial JSON will contain:

### Core Fields
- `trial_id`: Unique identifier (e.g., "w001")
- `source_file`: Original PDF filename
- `extraction_date`: When extracted

### Accused
- `name`, `gender`, `age`, `occupation`, `location`
- `marital_status`, `spouse_name`
- `parents` (father, mother names)
- `previous_reputation`
- `outcome` (death, released, banished, unknown)

### Witnesses
Array of witnesses, each with:
- `name`, `gender`, `age`, `occupation`, `location`
- `relationship_to_accused`
- `testimony_summary`
- `specific_accusations` (array)
- `dates_mentioned`

### Harms Catalog
Array of alleged harms:
- `victim_name`, `victim_type` (person, animal, property)
- `harm_type` (death, illness, crop failure, etc.)
- `method_alleged`
- `date_of_harm`, `date_reported`
- `quarrel_context` (what triggered the accusation)

### Relationships
- Kinship (spouse, parent, child, sibling)
- Social (neighbor, creditor/debtor, employer/employee)
- Conflict (quarrel, threat)

### Timeline
Key events with dates:
- Initial accusation
- Witness depositions
- Interrogations
- Torture sessions
- Confessions
- Sentencing
- Execution/release

### Confessions
- `obtained`: boolean
- `under_torture`: boolean
- `retracted`: boolean
- `renewed`: boolean
- `sabbat_confessed`: boolean
- `devil_details` (name given, appearance, pact details)
- `accomplices_named`: array of names

### Material Culture
Objects mentioned (powders, ointments, wax figures, etc.)

### Spatial References
Locations mentioned (sabbat sites, crime locations)

### Notable Quotes
French quotes with English translations for key passages

## Extraction Process

### Phase 1: Setup
1. Create directory structure
2. Define JSON schema file
3. Test extraction on 1-2 PDFs

### Phase 2: Batch Extraction
Run parallel subagents in batches of 10:
- Batch 1: w001-w010
- Batch 2: w011-w020
- Batch 3: w021-w030
- ... (37 batches total)

Each subagent:
1. Reads PDF using NL understanding
2. Reads schema for structure
3. Extracts all fields
4. Writes JSON to output directory

### Phase 3: Validation
1. Check all 368 JSONs created
2. Validate against schema
3. Spot-check random samples
4. Generate summary statistics

### Phase 4: Derive CSVs
Aggregate JSON data into analysis-ready CSVs:
- `persons.csv`: All people across all trials
- `relationships.csv`: All relationship edges
- `harms.csv`: All alleged harms
- `confessions.csv`: Confession details
- `timeline.csv`: All dated events

## Commands to Execute

### Create directories:
```bash
mkdir -p extracted_data/trials extracted_data/derived extraction_pipeline
```

### Launch extraction (per batch):
Each subagent receives prompt:
```
Extract witch trial data from PDF to JSON.

1. Read: /path/to/Archive_Complete/w[XXX].pdf
2. Read schema: /path/to/extraction_pipeline/trial_schema.json
3. Extract all data using NL understanding
4. Write JSON to: /path/to/extracted_data/trials/w[XXX].json

Be thorough. This is for PhD research on Lorraine witch trials.
```

## Expected Output
- 368 JSON files (one per trial)
- ~50-150KB per JSON depending on trial length
- Total: ~20-50MB of structured data

## Timeline
- Setup: Immediate
- Extraction: 3-6 hours (parallel processing)
- Validation: 30 minutes
- CSV derivation: 15 minutes

## Notes
- Use NL parsing (not regex) for better accuracy with historical documents
- Preserve original French terminology where meaningful
- Flag uncertain extractions with confidence scores
- Some PDFs may be incomplete or damaged - document these
