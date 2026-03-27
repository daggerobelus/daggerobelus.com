# Run 11: Generation Effect — Convergence Test

## Overview

This experiment tests two things:

1. **Convergence:** When multiple agents independently study the same manuscript and write their own paleography guides, do they converge on the same observations — or does each agent learn something different?

2. **Generation effect:** Does the act of writing the guide yourself improve your transcription, compared to using a guide someone else wrote?

## Design

- **5 learning agents** each independently study 5 paired Henslow MS688 pages (manuscript image + correct transcription). Each writes their own paleography guide. Each then transcribes Sedley MS534 page 13 using their own guide.
- **25 transcription agents** (5 per guide) each receive one guide written by a different learning agent and use it to transcribe Sedley MS534 page 13.
- **Evaluation agents** compare each transcription against the FromThePage reference and compute CER.

## What We Measure

- **Convergence:** Compare the 5 independently-written guides. What features do they all identify? Where do they diverge?
- **Generation effect (same-agent):** CER for the 5 learning agents who wrote their own guide and then transcribed with it.
- **No generation (different-agent):** CER for the 25 agents who used someone else's guide.
- **Baseline comparison:** Run 10 Sedley results (13.65% best, 13.89% median with error protocol).

---

## Phase 1: Learn the Hand and Write a Guide (Learning Agent)

You are given five pages from an early modern English recipe book (Henslow MS688, 1601), each paired with its correct human-made transcription. All five pages are from the same scribe.

**Your materials** (in `training-materials/`):
- `henslow-ms688-page08.jpg` + `henslow-ms688-page08-transcription.txt`
- `henslow-ms688-page10.jpg` + `henslow-ms688-page10-transcription.txt`
- `henslow-ms688-page14.jpg` + `henslow-ms688-page14-transcription.txt`
- `henslow-ms688-page16.jpg` + `henslow-ms688-page16-transcription.txt`
- `henslow-ms688-page20.jpg` + `henslow-ms688-page20-transcription.txt`

**You do NOT have:**
- Any paleography guide or handwriting manual
- Any alphabet chart or letterform reference
- Any vocabulary list
- Any prior knowledge of how to read this kind of handwriting

**Your task:** Study the five image–transcription pairs and figure out everything you can about how to read this kind of handwriting. Then write a comprehensive guide that would allow someone (or another agent) to transcribe a new, unseen manuscript page in a similar hand.

**Your guide should cover whatever you think is important.** You are discovering the rules, not following them. Some things you might address (but you are not limited to these):

- How individual letters are formed — what does each letter of the alphabet look like?
- Which letters look similar to each other and could easily be confused?
- Common abbreviations, shorthand, or symbols
- Spelling conventions that differ from modern English
- How words are spaced, connected, or separated
- How lines and pages are organized
- Patterns in capitalization, punctuation, or formatting
- Anything else you notice that would help someone read a new page

**Work across all five pages.** The goal is to learn generalizable rules for reading this scribe's hand, not rules specific to one page.

**Be specific and give examples.** For every rule or observation, point to specific words or passages in the training materials that illustrate it. Quote the transcription and describe what the handwriting looks like.

**Save your guide as:** `output/self-taught-guide.txt`

---

## Phase 2a: Transcribe with Your Own Guide (Same Learning Agent)

Now you will transcribe a page from a **different** manuscript you have never seen before. This is not the same scribe as the training materials — it is a different person's handwriting from the same era.

**Your materials:**
- `test-materials/sedley-ms534-page13.jpg` (the manuscript page to transcribe)
- Your own guide from Phase 1 (`output/self-taught-guide.txt`)

**You do NOT have:**
- Any external paleography guide or handwriting manual
- Any vocabulary list
- Any reference transcription
- Access to the training images or their transcriptions (do not look back at them)

**Your task:** Using only your self-taught guide and the manuscript image, produce a transcription of the Sedley page.

**Transcription rules:**
- Transcribe exactly what you see — preserve original spelling, punctuation, capitalization, and line breaks
- If you cannot read a word or passage, mark it `[...]` — do NOT guess or make up text
- If you are uncertain about a reading, mark it `[word?]`
- Note any abbreviations you expand

**Save your transcription as:** `output/sedley-ms534-transcription.txt`

---

## Phase 2b: Transcribe with Someone Else's Guide (Transcription Agent)

You are given a manuscript page you have never seen before and a guide written by another agent who studied a different manuscript from the same era.

**Your materials:**
- `test-materials/sedley-ms534-page13.jpg` (the manuscript page to transcribe)
- A guide written by another agent (`guide/self-taught-guide.txt`)

**You do NOT have:**
- Any external paleography guide or handwriting manual
- Any vocabulary list
- Any reference transcription
- Access to the training images or their transcriptions

**Your task:** Using only the guide and the manuscript image, produce a transcription of the Sedley page.

**Transcription rules:**
- Transcribe exactly what you see — preserve original spelling, punctuation, capitalization, and line breaks
- If you cannot read a word or passage, mark it `[...]` — do NOT guess or make up text
- If you are uncertain about a reading, mark it `[word?]`
- Note any abbreviations you expand

**Save your transcription as:** `output/sedley-ms534-transcription.txt`

---

## Phase 3: Evaluation (Evaluation Agent)

A separate evaluation agent compares each transcription against the FromThePage reference transcription and computes the Character Error Rate (CER).

**Materials:**
- The transcription to evaluate
- `evaluation-materials/sedley-ms534-page13-reference.txt`

The evaluation agent never sees the manuscript image, the training materials, or any guide.

---

## Agent Isolation — CRITICAL

Each agent runs in a **completely isolated folder** containing ONLY its authorized materials. No shared output directories. No access to other agents' work.

**Learning agents** see: training materials only. They write a guide and a transcription in their own output folder. They never see the Sedley reference, other agents' guides, or other agents' transcriptions.

**Transcription agents** see: the Sedley image and ONE guide (not written by them). They never see the training materials, the Sedley reference, other agents' work, or the guide author's transcription.

**Evaluation agents** see: one transcription and the Sedley reference. They never see the image, the guide, or the training materials.

This three-way separation ensures every transcription is a genuine blind reading.

### Folder Structure for Each Agent

```
learning-agent-N/
├── training-materials/          # COPY of Henslow images + transcriptions
│   ├── henslow-ms688-page08.jpg
│   ├── henslow-ms688-page08-transcription.txt
│   ├── ... (all 5 pages)
├── test-materials/              # COPY of Sedley image only
│   └── sedley-ms534-page13.jpg
└── output/                      # Agent writes here
    ├── self-taught-guide.txt
    └── sedley-ms534-transcription.txt

transcription-agent-N/
├── guide/                       # Contains ONE guide from a learning agent
│   └── self-taught-guide.txt
├── test-materials/              # COPY of Sedley image only
│   └── sedley-ms534-page13.jpg
└── output/                      # Agent writes here
    └── sedley-ms534-transcription.txt
```
