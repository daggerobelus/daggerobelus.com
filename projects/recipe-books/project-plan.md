---
title: Recipe Books — Project Design
date: 2026-04-21
status: draft
project: recipe-books
---

# Recipe Books — Project Design

## Context

A new digital humanities project under `projects/recipe-books/`, separate from Teaching Machines to Read. The project uses **already-transcribed** early modern English recipe books from the FromThePage Folger/Wellcome collaboration as its primary corpus. No new transcription work is required for the first pass; the 35 FromThePage text files are already present locally, pulled as part of the TMTR vocab pipeline.

Structural model: **Teaching Machines to Read**, not **Witchcraft**. The primary output is written scholarship — chapters with embedded figures and quoted close readings — not a public-facing dashboard. Visualizations serve specific arguments inside the prose.

The project is framed as simultaneously a warm-up (getting fluent with the recipe book corpus and its data shape) and a standalone analytical project capable of producing publishable chapters on its own terms. The Folger visit mentioned in the grant proposal is not load-bearing for this project — the grant money was used for the Claude subscription that makes this workflow possible. Folger-acquired material, if/when it happens, is natural expansion, not a blocking dependency.

---

## Section 1 — Research questions

### Primary lens

**Women's gynecological health as the site of both gendered knowledge production and genre obscuring.** The grant proposal gestures at this through examples ("abortions and birth control," "medical or scientific sphere") but doesn't name the throughline. This design makes it explicit.

The gynecological lens unifies Q2 and Q3 and structures the gazetteer, schema, figures, and primary chapter (Ch 4, "The Veiled Uterus").

### The three anchor questions

**Q1. Construction.** *How is the recipe book genre constituted?* What kinds of knowledge actually live inside — culinary, medical, veterinary, cosmetic, devotional? In what proportions? In what order? Where does gynecological content sit within the whole?

**Q2. Gendered production.** *How does the genre instantiate women's knowledge about women's bodies?* Whose books? Whose recipes (attribution patterns)? Whose bodies get treated — and how often is the treated body specifically gendered?

**Q3. Obscuring.** *How is gynecological knowledge specifically labeled, veiled, euphemized, or structurally positioned within recipe books — and what does the rhetorical strategy reveal about what the genre couldn't say plainly?*

### Rule for schema and visualization

A schema field or visualization should serve an answerable research question — either one of the three anchors, or a sub-question/new question that emerged from actual contact with the texts and that is defensible if asked "why is this here?"

**What this rules out:** fields added because "might be useful someday," or visualizations chosen because a charting library makes them easy.

**What this explicitly allows:** questions evolving. Q1/Q2/Q3 getting sharper sub-questions. A Q4 or Q5 emerging if the corpus insists. The three anchors are commitments to granting committees and readers, not a cage. Phase 2 close reading is the explicit place where the research questions sharpen or shift.

---

## Section 2 — Method

Four phases on the recipe corpus. A fifth (comparative) phase is named but deferred.

### Phase 1 — Parse (deterministic)

Rule-based script walks the 35 FromThePage text files and splits each into recipe-level records. Minimal schema only (see §3). No interpretation — just boundaries, verbatim text, and whatever front-matter metadata is cleanly extractable.

Output: `extracted/recipes/{ms_id}.json`, one file per book. ~1000+ recipes, immediately searchable with grep and queryable by script.

Expected scope: half a day to a day of scripting.

### Phase 2 — Explore (close reading, Q1/Q2/Q3 oriented)

Pick 3–4 books spanning the corpus (candidates: one medical-heavy, one culinary-heavy, one with clear female attribution such as Sedley, one miscellaneous). Read them. Use corpus-wide search to chase patterns as they surface.

Close reading is first-class here, not a prep phase. The notes and passages produced during Phase 2 will be quoted in the written chapters. Phase 2 therefore produces two deliverables:

1. **Hypothesis list** that informs the Phase 3 schema
2. **Citable close readings** (annotated passages with interpretive commentary) that will be quoted in Chapters 1–4

Note-taking organized around the three questions, with a fourth running section for new questions the texts raise.

Suggested time-box: **1–2 weeks.** Phase 2 is the phase most prone to becoming the whole project.

### Phase 3 — Rich schema extraction

Schema designed from Phase 2 observations (sketch in §3). Claude extracts rich per-recipe fields across all 35 books. Fields are grouped by which research question they serve; no fields exist that don't serve one.

Output: `extracted/recipes-enriched/{ms_id}.json`

Also produced in parallel: `extracted/gazetteer/gazetteer.json` — the euphemism + marker-ingredient + virginity-discourse reference, seeded in Phase 2 close reading, extended during Phase 3 extraction.

### Phase 4 — Visual output + chapter drafting

Static figures generated from the enriched corpus data. Chapters drafted with figures embedded. Each figure backs a specific written claim.

Figure inventory (candidate, not prescription) and design conventions in §4.

### Phase 5 — Comparative corpus (deferred)

Later phase, out of scope for the first pass. Covered in §5.

### Why this order

Each phase unlocks the next and leaves something usable behind:

- Phase 1 gives searchable corpus (even without Phase 2, you can grep 1000+ recipes)
- Phase 2 gives both the Phase 3 schema and citable close readings for the chapters
- Phase 3 gives queryable structured data for figures
- Phase 4 gives chapters and figures
- Phase 5 extends the argument with genre contrast

---

## Section 3 — Schema preview

**Methodological caveat.** The Phase 1 schema is close to committed because it's tied to what the raw text actually contains. The Phase 3 schema below is a **sketch**, not a commitment — it gets finalized by Phase 2 close reading. It is written out to sanity-check the shape before Phase 1 begins.

### Phase 1 schema (deterministic)

One JSON file per book. Illustrative example (values shaped after the real Sedley text, but `recipe_count` and `source_url` are placeholders until the parser runs):

```json
// extracted/recipes/{ms_id}.json
{
  "ms_id": "sedley-ms534",
  "book": {
    "title": "The Lady Sedley her Receipt Book",
    "date_inscribed": "1686",
    "attributed_compiler": "Lady Sedley",
    "source_url": "https://fromthepage.com/folger/...",
    "recipe_count": 312
  },
  "recipes": [
    {
      "recipe_number": 1,
      "position": 1,
      "raw_title": "A Receipt for the Dropsey.",
      "raw_body": "Take Horehound, Harts tonge, Liverworth...",
      "page_ref": "49"
    }
  ]
}
```

Extracted by rules, not interpretation: recipe boundaries (from `(1)`, `(2)` markers), titles (on-their-own-line headers), page refs (when present), book-level front matter.

### Phase 3 schema (rich, LLM-extracted — sketch)

Illustrative record (recipe is fabricated to show all fields in action — Sedley recipe 17 is not "To bring down the Courses"; this is a composite demonstrating what a gynecological/euphemistic record would look like):

```json
// extracted/recipes-enriched/{ms_id}.json
{
  "ms_id": "sedley-ms534",
  "recipe_number": 17,
  "position": 17,
  "raw_title": "To bring down the Courses.",
  "raw_body": "Take pennyroyall...",

  // Q1 — construction
  "category": "medical",
  "category_confidence": "high",
  "ingredients": [
    {"name": "pennyroyal", "quantity": "a handful", "form": "herb"},
    {"name": "wine",        "quantity": "a pint",    "form": "drink"}
  ],
  "preparation_summary": "Boil pennyroyal in wine, drink hot.",

  // Q2 — gendered production
  "attribution": {
    "type": "anonymous",
    "name": null,
    "gender_inferred": null,
    "relationship": null
  },
  "body_target": {
    "part": "womb",
    "ailment_named": "the courses",
    "gendered_body": true
  },

  // Q3 — obscuring (gynecological lens)
  "gynecological": "yes",
  "gynecological_subtype": ["menstruation"],
  "virginity_discourse": "no",
  "euphemism_level": "euphemistic",
  "marker_ingredients_detected": ["pennyroyal"],

  "neighbors": {
    "previous_title": "For a Cough of the Lungs.",
    "next_title":     "For the Greensickness in Maidens.",
    "previous_gyn_flag": "no",
    "next_gyn_flag":     "yes"
  },

  "analyst_notes": "'The courses' = menses. Pennyroyal canonical English emmenagogue / abortifacient-adjacent. Adjacency to greensickness recipe is itself Q3 evidence — clustering of gynecological material.",
  "uncertainty_flags": []
}
```

Field groups by research question:

- **Q1 (construction):** `category`, `category_confidence`, `ingredients`, `preparation_summary`
- **Q2 (gendered production):** `attribution`, `body_target`
- **Q3 (obscuring):** `gynecological` + `gynecological_subtype`, `virginity_discourse`, `euphemism_level`, `marker_ingredients_detected`, `neighbors`

Enum values:

- `category`: `culinary | medical | cosmetic | veterinary | household | devotional | mixed | other`
- `attribution.type`: `named_person | anonymous | self | print_borrowed`
- `gynecological`, `virginity_discourse`: `yes | possibly | no` (tiered — `possibly` is a meaningful value, not a failure)
- `gynecological_subtype`: `menstruation | contraception | pregnancy | labor | postpartum | lactation | womb | fertility | infertility | greensickness | miscarriage | virginity`
- `euphemism_level`: `plain | euphemistic | heavily_veiled`

**Known fussy area:** structured `ingredients` extraction. Quantities are inconsistent; forms vary; Latin and vernacular names coexist. Phase 2 will tell us how precise we can be.

### The gazetteer

Reference file the Phase 3 extractor consults. Grows during Phase 2 close reading.

```json
// extracted/gazetteer/gazetteer.json
{
  "entries": [
    {
      "term": "the courses",
      "category": "euphemism",
      "maps_to": { "gynecological_subtype": ["menstruation"], "euphemism_level": "euphemistic" },
      "sources": ["Read 2013 (Menstruation and the Female Body)", "Fissell 2004"],
      "notes": "Euphemism for menses. Recipes 'to bring down the courses' frequently function as abortifacients."
    },
    {
      "term": "the mother",
      "category": "euphemism",
      "maps_to": { "gynecological_subtype": ["womb"], "euphemism_level": "heavily_veiled" },
      "sources": ["Crawford 1981", "Fissell 2004"],
      "notes": "Womb/uterus. 'Suffocation of the mother' = hysteria."
    },
    {
      "term": "pennyroyal",
      "category": "marker_ingredient",
      "maps_to": { "flag_types": ["emmenagogue", "abortifacient"] },
      "sources": ["Riddle 1997 (Eve's Herbs)"],
      "notes": "Most common emmenagogue in English recipe books."
    },
    {
      "term": "maidenhead",
      "category": "virginity_marker",
      "maps_to": { "virginity_discourse": "yes", "euphemism_level": "euphemistic" },
      "sources": ["Loughlin 1997", "Gowing 2003"],
      "notes": "Hymen; often metonymic for virginity status."
    }
  ]
}
```

Entry categories: `euphemism | marker_ingredient | virginity_marker | attribution_pattern`.

**The gazetteer is also a scholarly artifact.** Designed to be published openly alongside the project so other recipe-book scholars can use, cite, or extend it.

### What Phase 2 will change

Expected:
- New euphemisms added to the gazetteer (close reading always surfaces more)
- `gynecological_subtype` list may grow or consolidate
- New fields we didn't anticipate (example: a `transmission_verb` field if Phase 2 reveals "given me by" / "taught me by" / "writ in X's book" carry distinct social weight)
- Some fields dropped if Phase 2 shows they can't be reliably extracted or don't serve Q1/Q2/Q3

The Phase 3 schema is a living document until Phase 2 completes; then it freezes before corpus-wide extraction.

---

## Section 4 — Visual output + chapter structure

### Output form

**Chapters + embedded figures + quoted close readings.** Static PNG/SVG figures are the primary artifact. Interactive versions on the website only when interactivity genuinely adds something. No dashboard. One MDX file per chapter.

Each figure exists to back a specific written claim. No orphan figures.

### Chapter structure (tentative, decoupled from phase order)

**Chapter order ≠ phase order.** Phases are the execution plan (bound by dependencies). Chapters are the argument plan (optimized for the reader). Chapter order gets committed to when findings stabilize.

Current best guess:

- **Ch 1 — The Genre** (Q1). What recipe books contain. Organizational logic. Establishes the object of study.
- **Ch 2 — Against the Anatomies** (comparative, from Phase 5). How formal medical/anatomical/midwifery texts handle the same bodies and the same knowledge in plain terms. Establishes what recipe books *aren't* — so the veiling argument in Ch 4 has measurable teeth.
- **Ch 3 — Women's Knowledge** (Q2). Attribution patterns, women-to-women transmission, whose bodies get treated.
- **Ch 4 — The Veiled Uterus** (Q3). How gynecological/reproductive/virginity knowledge is labeled, positioned, and obscured. Central chapter.

Chapters are drafted independently as phase work completes — you don't have to wait for all phases to draft any chapter.

### Candidate figures, by research question

A menu, not a prescription. Chapters pick based on what Phase 3 data actually supports.

**Q1 — Construction**
- Category distribution across the corpus (stacked bar by book; aggregate treemap)
- Book "fingerprint": each book as a horizontal strip showing recipes in order colored by category — shows whether books are thematically grouped or miscellaneous
- Word-length distribution by category
- Temporal shifts in category mix (if dates span enough)

**Q2 — Gendered production**
- Attribution type distribution (named / anonymous / self / print-borrowed)
- Attribution network: recipes transmitted between named women
- Gendered body targets by book
- Frequency of women's-body-specific ailments per book

**Q3 — Obscuring** (central figures for Ch 4)
- **Positional heatmap:** x = position in book (0–100%), y = one row per book, colored by gynecological flag. Shows whether gynecological recipes cluster or scatter.
- **Euphemism ladder:** for gynecological recipes, distribution across plain / euphemistic / heavily veiled
- **Neighbor matrix:** what categories cluster adjacent to gynecological recipes?
- **Marker-ingredient vs. title disclosure:** how often is a recipe gynecological-by-ingredient but not gynecological-by-title? (Direct measure of obscuring.)
- **Virginity discourse map:** where do virginity-coded recipes live? Are they separated from or mingled with contraception/menstruation material?

### Figure design conventions

Follow TMTR conventions:
- Simple bar comparisons preferred over scatter/strip plots
- Descriptive captions, no intro paragraphs
- Generous whitespace; big bold numbers over small text
- 75ch max prose column width in web surfacing
- No orphan figures — each figure has a written claim it backs

---

## Section 5 — Relationship to TMTR + project structure

### Supplier / consumer model

Recipe-books and TMTR are not overlapping projects. They have a clean interface:

```
[Manuscript image]  ──►  TMTR (transcribe)  ──►  [structured transcription]
                                                         │
                                                         ▼
[FromThePage transcription]  ──────────────────►  recipe-books
                                                   (extract → analyze → write)
                                                         │
                                                         ▼
                                                  [chapters + figures]
```

- **TMTR's job:** turn manuscript images into accurate transcriptions. All paleography, alphabet-first method, vocab verification, and blind evaluation lives there.
- **Recipe-books' job:** take transcriptions (from anywhere) and produce structured corpus data, analysis, visualizations, and written chapters.
- **Shared resource:** the ~19K-word vocab reference in TMTR, useful for recipe-term normalization in the Phase 3 extractor. Imported by relative path; not duplicated.
- **Natural expansion path:** when TMTR becomes mature enough to transcribe un-transcribed Folger manuscripts autonomously, those drop into `recipe-books/ingest/transcriptions/` and the downstream pipeline is unaffected. Corpus grows; schema stays; argument deepens.

This separation is what lets recipe-books stand on its own now (FromThePage corpus) while benefiting from TMTR's future maturity without being blocked on it.

### Folder structure

```
projects/recipe-books/
├── project-plan.md              # This design doc
├── CLAUDE.md                    # Project documentation (TMTR-style)
├── ingest/
│   ├── transcriptions/          # Raw text: symlink to TMTR vocab/raw-text for now;
│   │                            # own copies if/when corpus expands
│   └── references/              # Secondary literature, source citations
├── extracted/
│   ├── recipes/                 # Phase 1 output — one JSON per book
│   ├── recipes-enriched/        # Phase 3 output — rich per-recipe JSON
│   ├── gazetteer/               # Euphemism + marker + virginity reference
│   └── schema/                  # JSON schema definitions
├── chapters/                    # One MDX per chapter
│   ├── 01-genre.mdx
│   ├── 02-anatomies.mdx         # drafted after Phase 5
│   ├── 03-womens-knowledge.mdx
│   └── 04-veiled-uterus.mdx
├── figures/                     # Static figures (PNG/SVG), named by chapter
├── outputs/                     # Intermediate analysis results (not web-ready)
├── scripts/                     # Phase 1 parser, Phase 3 extractor, figure gen
└── public/                      # Web-surfaced assets
    ├── data/                    # JSON/CSV for the site
    └── figures/                 # Web-optimized figure versions
```

### Phase 5 corpus placement (named but deferred)

When Phase 5 begins, add:

```
projects/recipe-books/ingest/comparative/
├── sharp-midwives-book-1671.txt
├── raynalde-birth-of-mankind-1545.txt
├── crooke-mikrokosmographia-1615.txt
└── ...
```

…and `extracted/comparative/` for parallel structured data. Schema for the comparative corpus gets designed at that point, from Phase 1–4 findings, not now.

Candidate comparative texts (rough priority order; finalized at Phase 5):

- Jane Sharp, *The Midwives Book* (1671)
- Thomas Raynalde, *The Birth of Mankind* (1545 and later editions)
- Helkiah Crooke, *Mikrokosmographia* (1615)
- Nicholas Culpeper, *Directory for Midwives* (1651)
- John Banister, *The Historie of Man* (1578)
- Ambroise Paré, *Works* (Johnson trans. 1634)
- Levinus Lemnius, *The Secret Miracles of Nature* (1658)
- Gerard, *Herball* (1597) and Culpeper, *The English Physitian* (1652) — already locally available as a "learned vernacular" comparison layer

Sources: EEBO-TCP (free for CUNY students), Internet Archive, Project Gutenberg.

### CLAUDE.md for the project

Borrow TMTR's structure: project overview, research direction, the three questions + primary gynecological lens, data workflow diagram, transcription source map, methodology notes, folder structure recap. Drafted during implementation, not now — it's the last artifact of the scaffolding, not the first.

---

## Next steps

1. **Sarah reviews this design doc** (the step immediately after it is written and committed).
2. **Writing-plans skill produces the Phase 1 implementation plan** — the deterministic parser that turns 35 FromThePage text files into `extracted/recipes/{ms_id}.json`. Small, tightly scoped, ships quickly.
3. **Phase 2 starts** once Phase 1 data is available and searchable. Sarah leads the close reading; I can help with corpus-wide queries.
4. **Phase 3 schema is finalized** after Phase 2 wraps, then extraction runs.
5. **Phase 4 figure generation + chapter drafting** — figures follow the candidate list in §4, chapters follow the tentative structure in §4, both revised as findings shape them.
6. **Phase 5** deferred — scoped as a separate effort once the primary analysis stabilizes.
