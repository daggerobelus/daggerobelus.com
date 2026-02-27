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

- **Paleography guide**: `ingest/references/folger-paleography-guide/` — Folger Shakespeare Library handout (11 photos) covering secretary hand alphabet, common abbreviations, and editorial conventions
- **Transcription conventions**: See `ingest/references/paleography-guide.md` for the full encoded guide used by the AI transcription system
- **GPU computing primer**: See `ingest/references/gpu-computing-primer.md` for plain-language explanations of GPU concepts, key terms for grant applications, and sample proposal language
- **Funding guide**: See `ingest/references/funding-guide.md` for a comprehensive list of funding opportunities (income-providing fellowships vs. computing credits/supplies), eligibility details, deadlines, and key contacts
- **Source collection**: Folger Shakespeare Library + Wellcome Collection, accessed via FromThePage and EMMO

### Online Data Sources

- **FromThePage** (https://fromthepage.com/folger/early-modern-recipe-books) — 38 recipe books with paired manuscript images + transcriptions. Collaboration between Folger and Wellcome Collection. Best source for training data because images and transcriptions are already paired.
- **EMMO** (https://emmo.folger.edu/) — Early Modern Manuscripts Online. Side-by-side images and transcriptions. Recipe book transcriptions listed as "coming soon" but has letters and other manuscripts in similar hands.
- **Folgerpedia recipe book list** (https://folgerpedia.folger.edu/Recipe_books_at_the_Folger_Shakespeare_Library) — 130+ recipe books cataloged with call numbers. Many have digital images and transcriptions as PDF/DOCX downloads.
- **EMROC** (Early Modern Recipes Online Collective) — Scholarly collective creating triple-keyed transcriptions of recipe books using the Folger's DROMIO platform. Existing transcriptions could serve as ground truth for model training.

## Transcription Approach

This project uses **semi-diplomatic transcription** following Folger editorial conventions. See `ingest/references/paleography-guide.md` for the complete guide. Key principles:

- Transcription (faithful reproduction) is always performed first
- Translation (modernization) is a separate, optional step — not currently in scope
- Original spelling, punctuation, capitalization, and lineation are preserved
- Abbreviations are expanded with supplied letters in italics
- Confidence levels flag uncertain readings for human review

## Project Values

- **Open source**: All tools, models, and methods developed for this project should be open source and freely available to other scholars. No paid/proprietary HTR platforms (e.g., Transkribus paid tier) as primary dependencies.
- **Open access**: Transcriptions and datasets produced by this project should be openly accessible.
- **Reproducibility**: The pipeline should be documented well enough that other researchers can replicate or adapt it for their own manuscript collections.

## Technical Approach

### Current: Claude Vision Pipeline

The primary transcription pipeline uses Claude's vision capabilities guided by the paleography guide (`ingest/references/paleography-guide.md`). The guide encodes:
- Secretary hand letter forms and their variants
- Common abbreviations and special graphs
- Folger semi-diplomatic editorial conventions
- Confidence flagging system (high/medium/low)
- Recipe-specific vocabulary for contextual reading

Initial baseline test (Jane Jackson MS 373, page 20 from FromThePage): Claude can read clearly-written passages and recipe titles accurately without guidance. Struggles with faded/damaged sections, specific abbreviations, and compact hands. The paleography guide was built to address these gaps but has not yet been tested with a guided transcription.

### Future Goal: Open-Source Fine-Tuned TrOCR Model

The long-term goal is to fine-tune **Microsoft TrOCR** (open-source, MIT license) on paired image + transcription data from the Folger/EMROC collections to build an open-source model specifically for early modern English recipe manuscripts. No such model currently exists — this would fill a gap in the field.

**What TrOCR is**: An encoder-decoder model (vision transformer + language model) that reads an image of a single line of handwriting and outputs text. The base model (`microsoft/trocr-base-handwritten`) is trained on modern handwriting and can be fine-tuned for historical scripts.

**What fine-tuning requires**:
- Paired training data: manuscript line images + their correct transcriptions (available from FromThePage/EMROC)
- Line segmentation: full pages must be split into individual text lines first (Kraken can do this)
- GPU access: a GPU with 16 GB VRAM is sufficient (T4 or P100), using mixed-precision training
- The result would be published on HuggingFace as an open-source model

### HTR Models Evaluated

| Model | Open Source | Languages | Period | Notes |
|-------|-----------|-----------|--------|-------|
| **TrOCR base** (Microsoft) | Yes (MIT) | Modern English | Modern | Foundation model for fine-tuning. Best path for building our own model. |
| **TRIDIS v2** (HuggingFace) | Yes | Latin, French, Spanish, German | 11th–16th c. | Good architecture but not trained on English. Could serve as reference. |
| **Egerton Model** (Transkribus) | No (freemium) | English | 16th–17th c. | Best existing model for English secretary hand (~97% accuracy). Useful as benchmark with free tier (50 pages/month) but not open source. |
| **B2022 English Model** (Transkribus) | No (freemium) | English | 17th–19th c. | Broader date range. Same Transkribus limitation. |
| **Kraken + eScriptorium** | Yes | Any | Any | Fully open-source HTR platform. Could train a custom model. Full model portability. |
| **Kansallisarkisto multicentury** (HuggingFace) | Yes | Finnish/Swedish | 16th–20th c. | Shows TrOCR can be fine-tuned for multi-century historical documents. |
| **Riksarkivet Swedish** (HuggingFace) | Yes | Swedish | 1600–1900 | Date range overlaps. Good reference for pipeline design (HTRflow). |

### Transcription Pipeline Design

```
Step 1: IMAGE INTAKE
Photograph or download manuscript page
         ↓
Step 2: TRANSCRIPTION
Claude (with paleography guide) or fine-tuned TrOCR
produces text transcription
         ↓
Step 3: VERIFICATION
Flag readings by confidence level
(high = clear, medium = probable, low = illegible)
         ↓
Step 4: CORRECTION
Human expert reviews flagged sections
(Sarah's paleography expertise is essential here)
         ↓
Step 5: STRUCTURED DATA
Corrected transcription organized into structured format
(recipe titles, ingredients, instructions, marginal notes)
         ↓
Step 6: ANALYSIS & VISUALIZATION
Data feeds into visualization pipeline
(same approach as witchcraft project)
```

## Computing Resources

### Immediate (Free, No Application)

- **Google Colab** — Free T4 GPU (16 GB VRAM). Students can get free Colab Pro at https://colab.research.google.com/signup (verify via SheerID). Sufficient for TrOCR fine-tuning.
- **Kaggle Notebooks** — 30 free GPU hours/week (P100, 16 GB VRAM). No application needed, just create an account at kaggle.com.

### CUNY Resources

- **CUNY High Performance Computing Center (HPCC)** — Supercomputing cluster at College of Staten Island. Every CUNY grad student is entitled to an account. Apply at https://hpcreg1.csi.cuny.edu/forms/application.php. Contact: hpchelp@csi.cuny.edu. Ask about current GPU inventory (older K20m GPUs may have been upgraded).
- **Provost's Digital Innovation Grants (PDIGs)** — Up to $2,000 for GC doctoral students. Favors open-source tools and publicly accessible work. Could fund cloud GPU time. Watch GCDI website for next deadline.
- **GC Digital Initiatives (GCDI)** — Workshops, consultations, Digital Fellows program. Good for networking and finding others with similar computing needs. https://gcdi.commons.gc.cuny.edu/
- **Early Research Initiative (ERI)** — Internal funding sources page lists multiple awards: https://www.gc.cuny.edu/fellowships-and-financial-aid/doctoral-student-funding/early-research-initiative/internal-funding-sources

### Cloud Credits (Application Required)

- **Google Cloud Research Credits** — $1,000/year, rolling applications, 4-6 week decisions. https://edu.google.com/intl/ALL_us/programs/credits/research/
- **AWS Cloud Credit for Research** — Up to $5,000, needs research proposal. https://aws.amazon.com/government-education/research-and-technical-computing/cloud-credit-for-research/
- **Microsoft Azure for Students** — $100 in credits, no credit card. https://azure.microsoft.com/en-us/free/students

### Larger Grants

- **NSF ACCESS (Explore tier)** — Free national supercomputing (A100s, H100s). Grad students can apply as PI with advisor letter. Humanities research explicitly supported. https://access-ci.org/
- **NVIDIA Academic Grants** — Up to 30,000 H100 GPU hours. Deadline: June 30. https://academicgrants.nvidia.com/
- **Lambda Labs Research Grant** — Up to $5,000 in cloud credits. Rolling applications. https://lambdalabs.com/research
- **NEH Digital Humanities Advancement Grants** — Major funding. Has previously funded OCR/HTR projects. Offered twice yearly. https://www.neh.gov/grants/odh/digital-humanities-advancement-grants

## Next Steps

1. **Test the paleography guide**: Run a guided transcription of a FromThePage manuscript page (Jane Jackson MS 373) with the paleography guide loaded, and compare against the human transcription to measure accuracy improvement over the unguided baseline.
2. **Set up GPU access**: Create Kaggle account and apply for Google Colab student access.
3. **Explore training data**: Download paired image + transcription data from FromThePage to assess viability for TrOCR fine-tuning.
4. **Apply for CUNY HPCC account**: Free computing resources for the fine-tuning work.
5. **Apply for Provost's Digital Innovation Grant**: Next cycle, to fund cloud computing or other project needs.
