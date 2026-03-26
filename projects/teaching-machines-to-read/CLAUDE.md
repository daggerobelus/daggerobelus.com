# Early Modern Recipe Books Research Project

Research and transcription of early modern English recipe books, with a focus on gendered knowledge production, domestic medicine, and the construction of the recipe book genre.

## Project Structure

```
recipes/
├── ingest/                      # Source materials
│   ├── archive/                 # Manuscript images (photographed or downloaded)
│   │   └── test/                # Test materials ONLY — never mix with the real corpus
│   └── references/              # Folger paleography guide, secondary sources
├── extracted/                   # Processed data
│   ├── transcriptions/          # Semi-diplomatic transcriptions (per-manuscript)
│   ├── derived/                 # Aggregated/computed datasets
│   │   └── vocab/               # Curated vocabulary reference (~19K words from 40 sources)
│   └── schema/                  # JSON schema for structured recipe data
├── outputs/                     # Analysis results (intermediate, not web-ready)
└── public/                      # Web assets
    ├── dashboard/               # Interactive visualizations
    ├── figures/                  # Generated visualizations
    └── data/                    # JSON/CSV for web consumption
```

### Important: Test vs. Corpus Data

All test transcriptions, baseline comparisons, and experimental materials go in `ingest/archive/test/`. Each test should have its own subfolder (e.g., `test/jane-jackson-ms-373/`). **Never place test materials directly in `ingest/archive/`** — that folder is reserved for the real manuscript corpus. This keeps test runs clearly separated so they don't get mixed into the actual project data.

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

### Accuracy Evaluation

**CER (Character Error Rate)** is the standard metric for evaluating transcription accuracy. This is the field standard for HTR/OCR evaluation.

```
CER = (Substitutions + Insertions + Deletions) / Total Reference Characters
```

CER is computed using Levenshtein edit distance at the character level between the reference and hypothesis transcriptions. All accuracy reporting for this project should use CER. Word-level accuracy may be reported alongside CER for readability but is not the primary metric.

Benchmarks:
- < 1% CER = very good
- < 5% CER = usable for most research purposes
- Transkribus Egerton model (best existing for English secretary hand) ≈ 3% CER

Qualitative error analysis (modernization bias, capitalization ambiguity, etc.) is reported separately as value judgments about where the inaccuracy lies, not as alternative accuracy metrics.

### Blind Evaluation Protocol

Transcription and evaluation are performed by **separate agents** with no shared context, to prevent the transcription from being influenced by the reference material.

- **Transcription agent:** Receives only the manuscript image and the paleography guide (`ingest/references/paleography-guide.md`). Has **no access** to the FromThePage reference transcription or any other ground truth. Produces a transcription based solely on what it can read in the image.

- **Evaluation agent:** Receives the transcription produced by Agent 1 and the FromThePage reference transcription. Computes CER, categorizes errors, and writes the comparison report. Does **not** see the original manuscript image.

This separation ensures the transcription is a genuine blind reading of the manuscript, not influenced by prior knowledge of what the "correct" answer should be. It also makes the evaluation more defensible as a research methodology — analogous to blinding in experimental design.

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

**Full manuscript test (Lady Sedley MS534, 42 pages, 80,623 characters):**
- **Overall CER: 0.45%** (recipe text only: 0.41%) — NOTE: this was a non-blind test (agent had access to reference text). See blind evaluation results below for honest accuracy assessment.
- Hand legibility is the strongest predictor of CER (clear hands < 0.1%, compact hands up to ~4%)
- Core methodological risk: modernization bias — the AI silently corrects scribal errors toward modern spellings
- Full results: `ingest/archive/test/sedley-ms534-full/full-manuscript-summary.txt`

**Initial 5-page baseline (5 manuscripts, 2,312 words):**
- Average word accuracy ~98.7% — NOTE: non-blind test, likely inflated
- Results: `ingest/archive/test/test-results-summary.md`

**Blind evaluation (5 manuscripts, 6 runs):**
- Run 1 (basic blind): CER ranged from ~11% (Henslow) to ~96% (Jane Jackson — hallucinated)
- Run 2 (updated guide with anti-hallucination rules): No significant improvement — instruction changes alone don't move the needle
- **Run 3 (alphabet-first method, Henslow only): 6.12% CER — ~50% reduction vs. Runs 1-2**
- **Run 4 (alphabet-first, all 5 manuscripts, formalized instructions): Henslow 4.96% (crossed <5% usable threshold), Brumwich 9.30% (from ~96% hallucinated)**
- Run 5 (stronger instructions + review agent): No meaningful improvement — confirmed again that instruction changes alone don't help. Reverted to Run 4 instructions.
- **Run 6 (alphabet-first + vocabulary verification): Henslow 3.80% (best result, approaching Transkribus ~3% benchmark), Bulkeley 16.21% (best for this MS)**

Current best results:

| Manuscript | Best CER | Best Run | Status |
|---|---|---|---|
| Henslow MS688 | **3.80%** | Run 6 | Near Transkribus benchmark, usable for research |
| Sedley MS534 | **15.13%** | Run 4 | Above usable threshold, needs work |
| Bulkeley MS169 | **16.21%** | Run 6 | Above usable threshold, needs work |
| Brumwich MS160 | **9.30%** | Run 4 | Above usable threshold, image resolution limited |
| Jane Jackson MS373 | **46.85%** | Run 5 | Water damage, needs human transcription |

- Full run-by-run details: `ingest/archive/test/blind-evaluation/blind-test-summary.md`
- Test instructions: kept on Desktop at `~/Desktop/blind-test-alphabet/instructions.md` (isolated from project to prevent agent contamination)

### Alphabet-First Transcription Method

The most promising approach discovered during blind testing. Based on how human paleographers are trained: study the hand first, then transcribe.

**Three-agent workflow:**
1. **Alphabet Builder:** Studies the manuscript image and creates a letter-by-letter reference chart for this specific scribe's hand. Identifies clear examples of each letterform, confusion risks, and variant forms. Does NOT transcribe.
2. **Transcriber:** Uses the hand-specific alphabet + the general paleography guide to transcribe the page. Cross-references each letterform against the alphabet rather than guessing words from context.
3. **Evaluator:** Compares transcription against FromThePage reference. Computes CER. Never sees the original image.

This approach addresses the core problem: without the alphabet step, the AI reads top-down (what word makes sense here?) instead of bottom-up (what letterforms do I see?). Top-down reading causes hallucination and modernization bias.

**Vocabulary Verification (Step 2b):**
After the initial transcription, the agent checks each unfamiliar or uncertain word against a vocabulary reference of ~19,000 words attested in early modern recipe books. The vocab list is a verification tool, not a prediction tool — it confirms readings but does not generate them. Clear letterforms always override the vocab list. This step improved Henslow from 4.96% to 3.80% CER and Bulkeley from 18.70% to 16.21%.

**Key Lessons from Blind Testing:**
1. Non-blind testing produces dramatically inflated results (0.45% non-blind vs. ~16% blind on Sedley)
2. Instruction changes alone don't improve accuracy — confirmed twice (Runs 1→2 and 4→5). Only structural process changes matter.
3. The alphabet-first method is the single biggest improvement
4. Vocabulary verification helps on legible manuscripts but can't fix image resolution limits
5. Honest gaps (`[...]`) are better than plausible fiction — the shift from fabricated text to gap markers is a fundamental improvement in reliability

### Vocabulary Reference

A curated list of ~19,000 words attested in early modern recipe books, built from 40 sources totaling 1.68 million words:
- **35 FromThePage transcriptions** — crowd-sourced transcriptions of Folger/Wellcome recipe books via IIIF API
- **3 EMROC triple-keyed transcriptions** — highest quality ground truth
- **2 printed herbals** — Gerard 1597 and Culpeper 1652 from Internet Archive OCR

Files:
- **Vocab reference** (for AI use): `extracted/derived/vocab/vocab-reference.txt`
- **Full frequency list**: `extracted/derived/vocab/word-frequency-complete.csv`
- **Categorized vocabulary**: `extracted/derived/vocab/vocabulary-categorized.md`
- **Processing summary**: `extracted/derived/vocab/processing-summary.md`
- **Build instructions**: `ingest/references/vocab-list-instructions.md`
- **Build script**: `extracted/derived/vocab/build-vocab.py`

The vocab list filters to words attested in 2+ manuscripts to reduce noise. It includes non-English sources (Italian, French, German) because recipe books of this period frequently use Latin and continental terms.

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
Step 2a: BUILD HAND-SPECIFIC ALPHABET (Agent 1)
Study the manuscript image, create letter-by-letter reference chart
with confusion risk ranking. Does NOT transcribe yet.
         ↓
Step 2b: BLIND TRANSCRIPTION (Agent 1)
Transcribe using the alphabet chart + paleography guide.
Read bottom-up: pen strokes → letterforms → words.
         ↓
Step 2c: VOCABULARY VERIFICATION (Agent 1)
Check readings against vocab reference (~19K attested words).
Vocab confirms readings but never overrides clear letterforms.
         ↓
Step 3: BLIND EVALUATION (Agent 2 — separate context)
Compare transcription against FromThePage reference
Compute CER, categorize errors, write comparison report
Agent 2 never sees the original manuscript image
         ↓
Step 4: HUMAN REVIEW
Sarah reviews flagged sections and evaluation report
(paleographic expertise is essential here)
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

1. **Expand testing to more manuscript pages**: Current results are based on 1 page per manuscript. Need to test across multiple pages to confirm the methodology holds.
2. **Test with higher-resolution images**: Brumwich's small hand might be readable at higher resolution. Check if better images are available from Wellcome Collection.
3. **Explore multi-pass transcription**: Multiple independent reads of the same page, compared for consistency. Especially promising for manuscripts in the 10-20% CER range.
4. **Fine-tune TrOCR**: The long-term goal remains an open-source model trained on the FromThePage paired data. The vocab list and transcription pipeline developed here will feed into that work.
5. **Set up GPU access**: Create Kaggle account and apply for Google Colab student access for TrOCR fine-tuning.
6. **Apply for CUNY HPCC account**: Free computing resources for the fine-tuning work.
7. **Apply for Provost's Digital Innovation Grant**: Next cycle, to fund cloud computing or other project needs.
