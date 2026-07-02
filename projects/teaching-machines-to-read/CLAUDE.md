# Teaching Machines to Read

A digital humanities research project investigating what AI agents' learning processes reveal about the cognitive demands of reading early modern handwriting. By teaching AI to read secretary hand manuscripts — and observing where it fails, what interventions help, and how its learning mirrors human students — this project uses AI as a lens for understanding paleographic pedagogy itself.

## Research Direction

The process of teaching AI agents to read early modern handwriting closely mirrors how human students learn paleography. The same pedagogical interventions that work in the classroom — studying examples, building alphabets, error analysis, reflection, taking your own notes — produce analogous effects on AI performance. This project investigates what those parallels reveal about the cognitive demands of paleographic reading itself.

The transcription pipeline (Claude vision + paleography guide + blind evaluation) is the experimental apparatus, not the end goal. The research contribution is what the experiments reveal about how reading works.

Key findings:
- **Agents learn from examples like students do.** Studying paired manuscript images + correct transcriptions, agents independently discover the same core rules taught in paleography courses (u/v interchange, long-s, minim confusion, secretary d).
- **There's a learning curve with a sweet spot.** Too few examples (1 page) produces poor results; too many (10 pages) causes information overload. 5 pages is optimal — enough to generalize, not enough to overwhelm.
- **Taking your own notes beats reading someone else's.** Agents that study examples and write their own guide in the same session produce more consistent results than agents reading a guide written by a different agent (0.84 vs 2.11 spread). This mirrors the "generation effect" in cognitive science.
- **Reflection improves consistency, not accuracy.** Asking agents to plan before transcribing produces the most reliable results (tightest spread) but doesn't improve the best-case outcome. Consistency and accuracy are separate problems requiring different interventions.
- **Error analysis generalizes across manuscripts.** Studying an agent's specific mistakes on one manuscript and writing targeted warnings improves performance on a different, unseen manuscript. The lessons transfer because the error patterns (normalization bias, long-s/l confusion, vocabulary gaps) are general early modern paleography problems.
- **Post-hoc revision doesn't work.** Giving agents better tools after they've transcribed doesn't help — they rubber-stamp their own work. Changes must affect the first reading, not come after. (Confirmed twice: Runs 5 and 9.)
- **Agents cheat when they can.** Shared output folders, access to reference transcriptions, or proximity to other agents' work silently inflates results. Strict isolation is essential for honest evaluation.

These findings draw on Sarah's 6+ years of experience teaching writing to college and graduate students, and her expertise in early modern literature. The project is a humanities investigation — using AI experiments as a method — not a data science project about the humanities.

## Project Structure

```
teaching-machines-to-read/
├── ingest/                      # Source materials
│   ├── archive/                 # Manuscript images (photographed or downloaded)
│   │   └── test/                # Test materials and blind evaluation runs
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
- Transkribus Egerton model (trained on 2,500+ pages of one hand) ≈ 3% CER
- Transkribus Titan general model (no hand-specific training) ≈ 5–8% CER

Qualitative error analysis (modernization bias, capitalization ambiguity, etc.) is reported separately as value judgments about where the inaccuracy lies, not as alternative accuracy metrics.

### Blind Evaluation Protocol

Transcription and evaluation are performed by **separate agents** with no shared context, to prevent the transcription from being influenced by the reference material.

- **Transcription agent:** Receives only the manuscript image and the paleography guide (`ingest/references/paleography-guide.md`). Has **no access** to the FromThePage reference transcription or any other ground truth. Produces a transcription based solely on what it can read in the image.

- **Evaluation agent:** Receives the transcription produced by Agent 1 and the FromThePage reference transcription. Computes CER, categorizes errors, and writes the comparison report. Does **not** see the original manuscript image.

This separation ensures the transcription is a genuine blind reading of the manuscript, not influenced by prior knowledge of what the "correct" answer should be. It also makes the evaluation more defensible as a research methodology — analogous to blinding in experimental design.

**Test folder isolation:** All blind test runs MUST be set up on the Desktop (`~/Desktop/`), NOT inside the project directory. Agents browse their environment — if test folders are inside the project, agents can navigate to reference transcriptions, previous run results, or other agents' work. This is a contamination risk that invalidates results for scholarly use.

Each agent MUST run in a completely clean, isolated folder containing ONLY the materials that agent is authorized to access. Never place multiple agents' outputs in the same folder. Create a fresh folder per agent, and verify it contains nothing extra before launching. This was learned the hard way: accumulating outputs in a shared folder silently inflated CER results by 1-2 percentage points in Run 9.

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

**Blind evaluation (5 manuscripts, Runs 1–13** — per-run folders under `ingest/archive/test/blind-evaluation/`; narrative log for Runs 1–8 in `blind-test-summary.md`**):**
- Run 1 (basic blind): CER ranged from ~11% (Henslow) to ~96% (Jane Jackson — hallucinated)
- Run 2 (updated guide with anti-hallucination rules): No significant improvement — instruction changes alone don't move the needle
- **Run 3 (alphabet-first method, Henslow only): 6.12% CER — ~50% reduction vs. Runs 1-2**
- **Run 4 (alphabet-first, all 5 manuscripts, formalized instructions): Henslow 4.96% (crossed <5% usable threshold), Brumwich 9.30% (from ~96% hallucinated)**
- Run 5 (stronger instructions + review agent): No meaningful improvement — confirmed again that instruction changes alone don't help. Reverted to Run 4 instructions.
- **Run 6 (alphabet-first + vocabulary verification): Henslow 3.80% (best result, matching Transkribus with zero training data), Bulkeley 16.21% (best for this MS)**
- Run 7 (Folger visual alphabet charts): no improvement on any manuscript — more reference material doesn't automatically help.
- Run 8 (triple-pass consensus, EMROC-style): no improvement — multi-pass consensus can't fix an image-legibility bottleneck (catastrophic on the illegible hands).
- Run 9 (self-taught guide) & Run 10 (error-analysis protocol): Sedley reached **13.65%** via a Henslow-derived error protocol; post-hoc revision confirmed useless again (Run 9).
- Runs 11–13: the four follow-up experiments (generation effect, error-transfer, cumulative protocol) — see "Follow-Up Experiments" below.

*(All CERs above are pre-cleaning — see the correction note under "Current best results.")*

Current best results:

> **⚠️ Status (updated 2026-07): the table below is the HISTORICAL blind-testing record (Runs 1–10, through early 2026); its absolute numbers are superseded. Two corrections apply:**
> 1. **Reference-cleaning correction (2026-06):** every pre-2026-06-16 CER is inflated ~2.5–3 pp by un-cleaned reference markup (standalone page/recipe numbers, FromThePage `(n)` counters, `{page break}` braces, end-of-line hyphenation). Cleaning is now baked into the `manuscript-evaluation` skill (Step 2). Relative findings hold; absolute numbers were always *better* than reported. **A cleaned CER is not on the same scale as these — re-run any historical result through the current pipeline before comparing.** The skill also now reports two metrics: **diplomatic CER** (orthography-strict, primary) and **reading CER** (modernization-tolerant).
> 2. **Newer methods post-date this table** (see "Current Work" under Next Steps). On *cleaned* Sedley, the within-hand longitudinal protocol reaches ~6.8–7% diplomatic; the autoresearch blind optimizer reached **4.60% val diplomatic CER** from a one-line naive seed (run-2, partial — honest test CER still pending).

**Historical record (Runs 1–10, pre-cleaning — do NOT rank cleaned numbers against these):**

| Manuscript | Best CER (pre-cleaning) | Best Run | Status |
|---|---|---|---|
| Henslow MS688 | **3.80%** | Run 6 | Matches Transkribus (zero training data vs. 2,500 pages), usable for research |
| Sedley MS534 | **13.65%** | Run 10 | Improved via error analysis protocol |
| Bulkeley MS169 | **16.21%** | Run 6 | Above usable threshold, needs work |
| Brumwich MS160 | **9.30%** | Run 4 | Above usable threshold, image resolution limited |
| Jane Jackson MS373 | **46.85%** | Run 5 | Water damage, needs human transcription |

- Full run-by-run details: `ingest/archive/test/blind-evaluation/blind-test-summary.md`
- Run 9 (self-taught method) + Run 10 (error analysis protocol): `ingest/archive/test/blind-evaluation/run-9-self-taught/run-9-results.md`
- Test instructions: kept on Desktop, isolated per-agent folders to prevent contamination

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

## Funding & Resources

- **Provost's Digital Innovation Grants (PDIGs)** — Up to $2,000 for GC doctoral students. Favors open-source tools and publicly accessible work. Watch GCDI website for next deadline.
- **GC Digital Initiatives (GCDI)** — Workshops, consultations, Digital Fellows program. https://gcdi.commons.gc.cuny.edu/
- **Early Research Initiative (ERI)** — Internal funding sources: https://www.gc.cuny.edu/fellowships-and-financial-aid/doctoral-student-funding/early-research-initiative/internal-funding-sources
- **NEH Digital Humanities Advancement Grants** — Major funding. Has previously funded OCR/HTR projects. Offered twice yearly. https://www.neh.gov/grants/odh/digital-humanities-advancement-grants

## Next Steps

### Current Work (2026-06 / 2026-07) — the active phase

The project has moved past the Runs 1–10 blind-testing phase into **within-hand learning and automated method-optimization** experiments, all on *cleaned* CER. Three active threads:

1. **Within-hand longitudinal** (`within-hand-longitudinal-design.md`, run `ingest/archive/test/whl-sedley-test-01/`) — a single continuous agent learns one hand over sets of pages with rolling revision. First test on Sedley: ~6.8–7% cleaned diplomatic CER, very tight cross-learner spread, but *no clean learning curve* (Sedley is low-headroom — decoding solves early, residual is vocabulary). Learning-curve hypothesis needs a HARD single-hand manuscript. Driven by the `manuscript-longitudinal-run` skill.
2. **Autoresearch CER optimization** (branch `autoresearch`; spec `docs/superpowers/specs/2026-06-16-autoresearch-cer-optimization-design.md`; skill `skills/manuscript-autoresearch-run/`; corpus `ingest/archive/test/autoresearch-sedley-01/`) — a Karpathy-style ratchet loop where a **blind optimizer** rewrites the transcription method to lower CER, discovering changes from raw error tallies alone (no interpretation handed to it). 2×2 design: start {naive, seed-from-best} × isolation {blind, faithful-control}; single variable = whether the transcriber can see the references. **run-2-naive-blind (partial, 2026-06-17): reached 4.60% val diplomatic CER in 9 iterations from a one-line naive seed** before a session limit halted it; the optimizer independently rediscovered anti-modernization, S/s, u/v, a/e/o, and t/y distinctions. Test CER + the other three cells pending. Full record in that run's `README.md`.
3. **Ratchet head-to-head** (`ingest/archive/test/ratchet-headtohead-01/`, skills `skills/ratchet-loop{,-forum}/`) — a head-to-head of two generalized ratchet-loop optimization skills on Sedley CER: `ratchet-loop` (plain) vs `ratchet-loop-forum`, the latter adding an argumentative **challenger** that can veto a promotion the number alone would pass. Autonomous (no human); the challenger is the single isolated variable. Reuses the frozen `autoresearch-sedley-01` splits by symlink. Infrastructure + a `Workflow` runner built; dry-run showed the naive one-line baseline already transcribes Sedley at ~7% cleaned diplomatic CER (modest headroom) and that occasional page-truncation is the main noise source (since hardened). Paused 2026-07-02 on the credit limit before a clean full run; see its `STATUS.md`.

**Blog post** (below) and the **follow-up experiments** (below) remain planned but are secondary to finishing the optimization runs above.

### Blog Post
Write up the project story so far — what the project set out to do, what it discovered, and where it's going. This frames the research direction before the final experiments.

### Follow-Up Experiments (4 runs, 2 questions) — EXECUTED as Runs 11–13

These were run (early 2026) as blind-evaluation Runs 11–13 (`ingest/archive/test/blind-evaluation/run-1{1,2,3}-*/`). Outcomes so far:
- **Generation effect (Run 11):** confirmed — same-agent guide-writing produces tighter consistency (0.84 vs 2.11 spread); the finding is now in "Research Direction" above.
- **Reverse transfer (Run 12):** a Sedley-derived error protocol did **not** help on the easier Henslow — consistent with Stanovich's compensatory model (less to compensate for on a legible hand).
- **Cumulative protocol (Run 13):** combined Henslow+Sedley protocol tested on unseen Brumwich, with variants 13b/13c/13d; see `run-13-cumulative-protocol/results.txt`.

The original experiment designs (kept for reference):

**Generation Effect — what makes self-generated notes work?**

1. **Convergence test:** Two agents independently study the same manuscript and write their own guides. Do they converge on the same observations (the manuscript teaches) or diverge (learning is idiosyncratic)? In reading theory terms: does the manuscript impose a bottom-up reading (Gough), or does each agent bring its own top-down schema (Goodman)?
2. **Rewrite vs. generate from source:** One agent reads another agent's guide and rewrites it before transcribing. Isolates whether the effect comes from the act of writing or from writing *while looking at the manuscript*. (Cf. Slamecka & Graf 1978 on generation effect; Wong 2023 on deliberate erring — personally engaging with material matters more than observing someone else's work.)

**Error Analysis Transfer — what kind of knowledge transfers?**

3. **Reverse direction:** Build error protocol from Sedley mistakes, test on Henslow. Does transfer only work one way? Stanovich's compensatory model (1980) predicts the protocol should help *less* on more legible manuscripts (less need to compensate for poor decoding). If it helps equally, that's interesting.
4. **Cumulative protocol:** Build error protocol from Henslow, add Sedley's errors, test on a third manuscript. Does paleographic knowledge accumulate, or does more experience just add noise? (Cf. Perkins & Salomon 1988 on high-road transfer.)

### Writing Plan

Lead with the experimental evidence. Layer in secondary sources (reading theory, cognitive science, educational psychology) where they contextualize findings or show what's new — but the results drive the structure, not the bibliography. Literature review compiled March 2026: `~/Desktop/teaching-machines-to-read-literature-review.docx`.

### Future: Recipe Books Project

The recipe book content itself (mapping ingredients, networks, knowledge production — similar to the witchcraft project) will eventually be a separate project under `projects/`. No work started yet.
