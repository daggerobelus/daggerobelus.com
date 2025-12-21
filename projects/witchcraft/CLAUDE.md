# Witchcraft Trials Research Project

Research and analysis of the Lorraine witch trials, one of Europe's richest witch trial archives.

## Project Structure

```
witchcraft/
├── ingest/                   # Source materials
│   ├── archive/              # 156 digitized trial PDFs (w001.pdf - w347.pdf)
│   └── references/           # MAIN_INDEX.pdf, research paper
├── extracted/                # Extracted data
│   ├── trials/               # Per-trial JSON files (w001.json, etc.)
│   ├── derived/              # Derived datasets
│   └── schema/               # JSON schema for validation
├── outputs/                  # Analysis outputs
└── public/                   # Web assets
    ├── dashboard/            # Interactive D3.js dashboard
    └── figures/              # Generated visualizations
```

## Data Workflow

The project uses NLP extraction to structured JSON files in `extracted/trials/`. Each trial has a JSON representation including:

- Trial metadata (dates, location, court, outcome)
- Accused persons with confession details
- Witnesses and their testimony
- Relationships (kinship, social)
- Harms catalog (alleged maleficium)
- Timeline of procedural events
- Historical/economic context

Analysis is performed on these structured JSON files.
