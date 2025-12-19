# Witchcraft Trial Data Extraction Status

**Date:** December 15, 2024
**Project:** Lorraine Witch Trials Database Extraction Pipeline

## Overview

This document tracks the progress of extracting structured data from the Lorraine witch trial archive PDFs into machine-readable JSON format for analysis.

## Archive Statistics

- **Total PDF Files:** 368 trial records in `/Archive_Complete/`
- **Extracted to JSON:** 1 trial (w001.json)
- **Completion Rate:** 0.3% (1/368)

## Extraction Pipeline

### 1. Manual/AI-Assisted Extraction (`extract_trial.py`)

The extraction process involves:

1. Reading PDF text using `python extraction_pipeline/extract_trial.py w001 --text`
2. Creating a detailed JSON file following the schema in `extraction_pipeline/trial_schema.json`
3. Validating the JSON using `python extraction_pipeline/extract_trial.py w001 --validate`

**Key Data Points Extracted per Trial:**
- Trial metadata (dates, location, court, outcome)
- Accused persons (name, age, gender, occupation, family, confession details)
- Witnesses (23 witnesses for w001, each with demographic and testimony details)
- Timeline of procedural events (arrests, interrogations, torture, sentencing)
- Harms catalog (alleged maleficium - deaths, illnesses, animal losses)
- Relationships (kinship, social connections for network analysis)
- Legal context (officials, prior disputes, appeals)
- Historical context (military presence, weather events, economic conditions)
- Material culture (objects mentioned - powders, clothing, food)
- Spatial references (villages, sabbat locations)
- Notable quotes (with original French and English translations)

### 2. Automated CSV Generation (`derive_csvs.py`)

Once JSON files are created, CSVs are automatically generated:

```bash
python extraction_pipeline/derive_csvs.py
```

**Generated CSVs** (currently in `/extracted_data/derived/`):
- `trials.csv` - One row per trial with metadata and statistics
- `accused.csv` - One row per accused person with confession details
- `witnesses.csv` - One row per witness testimony
- `harms.csv` - One row per alleged harm/maleficium
- `relationships.csv` - All kinship and social relationships
- `timeline.csv` - All procedural events chronologically
- `quotes.csv` - Notable quotes with French originals
- `spatial.csv` - Place references for geographic analysis
- `material_culture.csv` - Objects and artifacts mentioned
- `persons.csv` - Unified view of all people across trials
- `confessions_summary.csv` - Trial-level confession statistics

## Current Status: w001 (Jean and Didiere Bulme)

**Trial:** w001
**Location:** Mazerulles
**Court:** Amance
**Dates:** May 22 - July 16, 1591 (55 days)
**Outcome:** Death
**Accused:** 2 (married couple)
**Witnesses:** 23
**Extraction Quality:** High confidence, very detailed record

### Key Features of w001:
- Both accused confessed under torture
- Rich detail on sabbat, devil pact, and magical practices
- Central conflict: Jean's role as village herdsman
- Multiple economic disputes (debts, property, occupation)
- Extensive witness testimony with quarrels and threats
- 6 harms cataloged (human deaths and animal losses)
- Notable quotes including protest against forced confessions

This trial serves as an excellent template for extracting the remaining 367 trials.

## Next Steps

### Immediate Priorities
1. **Extract trials w002-w020** - Complete the first batch of 20 trials
2. **Validate schema consistency** - Ensure all extractions follow the same structure
3. **Document extraction decisions** - Create guidelines for ambiguous cases

### Medium-Term Goals
1. **Extract trials w021-w040** - Second batch of 20 trials
2. **Batch validate** - Run validation across all extracted JSONs
3. **Regenerate CSVs** - Update all derived CSVs with new data

### Long-Term Goals
1. **Complete full archive** - Extract all 368 trials
2. **Network analysis** - Build comprehensive social network graphs
3. **Statistical analysis** - Identify patterns in outcomes, confessions, torture use
4. **Geographic analysis** - Map spatial distribution of trials and accusations

## Extraction Challenges

### Time Investment
- Each trial takes 30-60 minutes to extract depending on complexity
- w001 had 8 PDF pages and 23 witnesses - one of the more detailed trials
- Some trials may be shorter with fewer witnesses

### Data Quality Issues
- PDF text extraction quality varies
- Handwriting interpretation for original documents
- French language barrier (16th century legal French)
- Missing or damaged sections in some records
- Inconsistent date formats and naming conventions

### Schema Decisions
- How to handle variant spellings of names
- Standardizing occupations and locations
- Dealing with incomplete information
- Coding relationships when context is ambiguous

## Tools Available

### Check Extraction Progress
```bash
# List missing trials
python extraction_pipeline/extract_trial.py --missing

# Show extraction statistics
python extraction_pipeline/extract_trial.py --stats

# Validate all extracted JSONs
python extraction_pipeline/extract_trial.py --batch-validate
```

### Extract a New Trial
```bash
# 1. View PDF text
python extraction_pipeline/extract_trial.py w002 --text

# 2. Get JSON template with estimated witness count
python extraction_pipeline/extract_trial.py w002 --template > temp_w002.json

# 3. Edit the JSON file with extracted data
# (Manual step using text editor or AI assistance)

# 4. Validate the JSON
python extraction_pipeline/extract_trial.py w002 --validate

# 5. Move to trials directory
mv temp_w002.json extracted_data/trials/w002.json

# 6. Regenerate CSVs
python extraction_pipeline/derive_csvs.py
```

## Research Value

This extraction effort enables:

1. **Quantitative Analysis:** Statistical patterns in witch trial outcomes, use of torture, confession rates
2. **Network Analysis:** Social connections, accusation chains, family relationships
3. **Geographic Analysis:** Spatial distribution of trials, sabbat locations, village networks
4. **Temporal Analysis:** Trial duration patterns, seasonal effects, procedural timelines
5. **Linguistic Analysis:** Threats, quotes, legal terminology, devil names
6. **Gender Analysis:** Gender patterns in accusations, witness roles, outcomes
7. **Economic Analysis:** Occupation disputes, debt conflicts, property issues
8. **Legal Analysis:** Procedural patterns, appeals, use of evidence

## Contributors

- **Extractor:** Claude (AI assistant)
- **Validation:** Schema-based JSON validation
- **Data Model:** Designed based on trial_schema.json

## Notes

- The extraction schema captures both quantitative data (counts, dates, demographics) and qualitative data (quotes, contexts, descriptions)
- All French quotes are preserved alongside English translations
- Relationships are coded with direction (directed/undirected) for network analysis
- Hearsay chains are tracked to assess evidence quality
- Material culture and spatial references enable historical context analysis

---

**Last Updated:** December 15, 2024
**Extraction Rate:** ~1-2 trials per hour with AI assistance
**Estimated Time to Completion:** 184-368 hours of extraction work
