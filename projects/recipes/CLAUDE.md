# Early Modern Recipe Books Research Project

Research and transcription of early modern English recipe books, with a focus on gendered knowledge production, domestic medicine, and the construction of the recipe book genre.

## Project Structure

```
recipes/
├── ingest/                      # Source materials
│   ├── archive/                 # Manuscript images (photographed or downloaded)
│   └── references/              # Folger paleography guide, secondary sources
├── extracted/                   # Processed data
│   ├── transcriptions/          # Semi-diplomatic transcriptions (per-manuscript)
│   ├── derived/                 # Aggregated/computed datasets
│   └── schema/                  # JSON schema for structured recipe data
├── outputs/                     # Analysis results (intermediate, not web-ready)
└── public/                      # Web assets
    ├── dashboard/               # Interactive visualizations
    ├── figures/                  # Generated visualizations
    └── data/                    # JSON/CSV for web consumption
```

## Data Workflow

```
ingest/archive/        →  [paleographic transcription]  →  extracted/transcriptions/
(manuscript images)                                              ↓
                                                        [structured extraction]
                                                                 ↓
                                                        extracted/derived/
                                                                 ↓
                                                          [analysis]
                                                                 ↓
                                                            outputs/
                                                                 ↓
                                                        [visualization]
                                                                 ↓
                                                            public/  →  site/
```

## Key References

- **Paleography guide**: `ingest/references/folger-paleography-guide/` — Folger Shakespeare Library handout covering secretary hand alphabet, common abbreviations, and editorial conventions
- **Transcription conventions**: See `ingest/references/paleography-guide.md` for the full encoded guide used by the AI transcription system
- **Source collection**: Folger Shakespeare Library + Wellcome Collection, accessed via FromThePage and EMMO

## Transcription Approach

This project uses **semi-diplomatic transcription** following Folger editorial conventions. See `ingest/references/paleography-guide.md` for the complete guide. Key principles:

- Transcription (faithful reproduction) is always performed first
- Translation (modernization) is a separate, optional step
- Original spelling, punctuation, capitalization, and lineation are preserved
- Abbreviations are expanded with supplied letters in italics
- Confidence levels flag uncertain readings for human review
