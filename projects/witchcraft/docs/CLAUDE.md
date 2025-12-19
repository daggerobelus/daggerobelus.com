# Witchcraft Trials Research Project

This project contains data and analysis tools for studying the Lorraine witch trials, one of Europe's richest witch trial archives. The research focuses on extracting and analyzing data from historical trial records.

## Project Structure

### `/Archive_Complete/`
Contains 156 digitized witch trial PDFs from the Lorraine archive. Files are named `w001.pdf` through `w347.pdf` (with some gaps and variants like `w022A.pdf`, `w022B.pdf`). Each PDF represents an individual trial record.

### `/figures/`
Generated visualizations from data analysis:
- `accusation_network.png` - Network graph of accusations between individuals
- `outcomes_distribution.png` - Distribution of trial outcomes
- `reputation_analysis.png` - Analysis of reputation mentions
- `term_correlations.png` - Correlations between legal terms
- `term_frequencies.png` - Frequency of key terms across trials
- `witness_analysis.png` - Witness-related statistics

#### `/figures/non_death_analysis/`
Analysis specifically examining cases that did not result in death sentences:
- `all_cases_term_counts.csv` - Term frequencies per trial
- `all_cases_term_summary.csv` - Aggregated term statistics
- `non_death_cases_detailed.csv` - Details on non-death outcomes
- `term_comparison_by_outcome.csv` - Term usage by outcome type
- `statistical_tests.csv` - Statistical analysis results
- `why_they_survived.md` - Research findings on survival factors

### `/social network data/`
Social network analysis pipeline and outputs.

#### `/social network data/modules/`
Python analysis modules (run in sequence):
1. `01_entity_extraction.py` - Extract named entities from PDFs
2. `02_entity_resolution.py` - Resolve/deduplicate entities
3. `03_relationship_extraction.py` - Extract relationships between entities
4. `04_network_construction.py` - Build network graphs
5. `05_centrality_analysis.py` - Calculate network centrality metrics
6. `06_role_analysis.py` - Analyze roles (accuser, accused, witness)
7. `07_logistic_regression.py` - Predictive modeling
8. `08_ergm_analysis.py` - Exponential random graph models
9. `09_robustness_checks.py` - Validation and sensitivity analysis
10. `10_temporal_analysis.py` - Time-based patterns
11. `11_contagion_modeling.py` - Accusation spread modeling
12. `12_visualizations.py` - Generate network visualizations

#### `/social network data/output/`
Analysis outputs organized by type:
- `entities/` - Extracted entities (people, places)
- `edges/` - Relationship data
- `networks/` - Network graph files
- `metrics/` - Centrality and other metrics
- `roles/` - Role classification data
- `models/` - Statistical model outputs
- `robustness/` - Validation results
- `temporal/` - Time-series data
- `contagion/` - Contagion model outputs
- `figures/` - Network visualizations
- `THESIS_FINDINGS_SUMMARY.md` - Key research findings
- `GLOSSARY_OF_TERMS.md` - Terminology definitions

## Key Files

### `extract_trial_terms.py`
Python script to extract term counts from trial PDFs. Counts occurrences of key legal/procedural terms (reputation, witness, torture, confession, etc.) in both English and French. Outputs CSV files for visualization.

**Usage:** `python extract_trial_terms.py`

**Requirements:** `pip install PyPDF2 pandas`

### `witchcraft_dashboard.html`
Interactive D3.js visualization dashboard for exploring the trial data.

### `witchcraft_data.js`
JavaScript data file containing processed trial information for the dashboard.

### `MAIN_INDEX.pdf`
Master index of all trials in the archive.

### Research Paper
`Unlocking New Scholarship from Europe's Richest Witch Trial Archive_ The Lorraine Database Research Agenda.pdf` - Academic paper describing the research agenda and methodology.

## Key Terms Tracked

The analysis tracks these term categories (with French equivalents):
- **reputation** - reputation, reputed, reputée
- **suspected** - suspected, suspect, soupçon
- **accused** - accused, accusé, accusée
- **witness** - witness, témoin
- **quarrel** - quarrel, querelle, dispute
- **threat** - threat, menace
- **confess** - confess, confession, aveu
- **sabbat** - sabbat, sabbath
- **torture** - torture, rack, question, tourment
- **death** - died, death, mort, exécuté
- **released** - released, renvoyé, libéré
- **banished** - banished, banni, exile

## Trial Outcomes

Most trials resulted in death sentences. Known non-death outcomes include:
- **Released** - w014, w034, w141, w142, w193, w198, w246, w279, w280
- **Banished** - w064, w065, w090, w118, w132, w215, w235, w325, w344
- **Unknown** - Various trials with unclear outcomes

## Bug Fixes

### Node Type Classification (Fixed Dec 2024)

**Problem:** The network visualization in `witchcraft_dashboard.html` showed nearly all nodes as "unknown" type instead of properly classifying them as "accused" or "witness".

**Root Cause:** In `04_network_construction.py`, the `build_node_index()` function assigned `entity_type: 'unknown'` to all nodes found in edges but not in the canonical entities file, without inferring their role from context.

**Fix Applied:**
1. `04_network_construction.py` - Updated to infer entity types from:
   - Node IDs containing "witch" (case insensitive) -> accused
   - Targets of TESTIFIED_AGAINST edges -> accused
   - Sources of TESTIFIED_AGAINST edges -> witness

2. `fix_node_types.py` - One-time script to repair `witchcraft_data.js`

**Result:** Network visualization now correctly shows:
- 52 Accused (red) - people with "witch" in their ID or targets of testimony
- 60 Witnesses (blue) - people who testified or appeared as co-witnesses
- 18 Family + Witness (cyan) - people who are both family members AND testified
- 13 Family (purple) - people only in kinship relationships (spouses, widows, children)
- 7 Unknown (gray) - people with no edges in the current data subset

**Trial Information:** Tooltips now display which trials each person is connected to (e.g., "Trials: w003, w051, w248"). Trial IDs are extracted from accused node names and propagated to witnesses and family members through edge relationships.
