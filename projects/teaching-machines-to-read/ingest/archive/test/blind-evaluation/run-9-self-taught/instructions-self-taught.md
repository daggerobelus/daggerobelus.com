# Blind Transcription Test — Self-Taught Method

## Overview

This experiment tests whether an AI agent can learn to read early modern English handwriting by studying paired examples (manuscript images + their correct transcriptions), without any external guides or reference materials.

There are two phases, performed by **separate agents** with no shared context beyond the output of Phase 1.

---

## Phase 1: Learn the Hand (Learning Agent)

You are given three manuscript pages from early modern English recipe books (1500s–1600s), each paired with its correct human-made transcription. These are from three different scribes — each has a distinct handwriting style.

**Your materials** (in `training-materials/`):
- `brumwich-ms160.jpg` + `brumwich-ms160-transcription.txt`
- `bulkeley-ms169.jpg` + `bulkeley-ms169-transcription.txt`
- `sedley-ms534.jpg` + `sedley-ms534-transcription.txt`

**You do NOT have:**
- Any paleography guide or handwriting manual
- Any alphabet chart or letterform reference
- Any vocabulary list
- Any prior knowledge of how to read this kind of handwriting

**Your task:** Study the three image–transcription pairs and figure out everything you can about how to read this kind of handwriting. Then write a comprehensive guide that would allow someone (or another agent) to transcribe a new, unseen manuscript page in a similar hand.

**Your guide should cover whatever you think is important.** You are discovering the rules, not following them. Some things you might address (but you are not limited to these):

- How individual letters are formed — what does each letter of the alphabet look like?
- Which letters look similar to each other and could easily be confused?
- Common abbreviations, shorthand, or symbols
- Spelling conventions that differ from modern English
- How words are spaced, connected, or separated
- How lines and pages are organized
- Patterns in capitalization, punctuation, or formatting
- Anything else you notice that would help someone read a new page

**Work across all three manuscripts.** Note where the three scribes are similar (general conventions of the period) versus where they differ (individual quirks). The goal is to learn generalizable rules for reading early modern English handwriting, not rules specific to one scribe.

**Be specific and give examples.** For every rule or observation, point to specific words or passages in the training materials that illustrate it. Quote the transcription and describe what the handwriting looks like.

**Save your guide as:** `output/self-taught-guide.txt`

---

## Phase 2: Blind Transcription (Transcription Agent)

You are given a manuscript page you have never seen before:

- `test-materials/henslow-ms688.jpg`

You also have a guide written by another agent who studied three other manuscript pages from the same era:

- `output/self-taught-guide.txt`

**You do NOT have:**
- Any external paleography guide or handwriting manual
- Any vocabulary list
- Any reference transcription
- Access to the training images or their transcriptions

**Your task:** Using only the self-taught guide and the manuscript image, produce a transcription of the Henslow page.

**Transcription rules:**
- Transcribe exactly what you see — preserve original spelling, punctuation, capitalization, and line breaks
- If you cannot read a word or passage, mark it `[...]` — do NOT guess or make up text
- If you are uncertain about a reading, mark it `[word?]`
- Note any abbreviations you expand

**Save your transcription as:** `output/henslow-ms688-transcription.txt`

Also save a brief set of notes about your experience — what was easy, what was hard, where the guide helped, where it fell short:

**Save your notes as:** `output/henslow-ms688-notes.txt`

---

## Phase 3: Evaluation (Evaluation Agent)

A separate evaluation agent will compare the Phase 2 transcription against the FromThePage reference transcription and compute the Character Error Rate (CER). The evaluation agent never sees the manuscript image or the self-taught guide.

---

## Important: Agent Isolation

- The **Learning Agent** (Phase 1) sees only the training materials. It never sees the Henslow test page or any reference transcription for Henslow.
- The **Transcription Agent** (Phase 2) sees only the Henslow image and the self-taught guide. It never sees the training materials, any reference transcription, or any external guide.
- The **Evaluation Agent** (Phase 3) sees only the transcription output and the reference. It never sees the image or the guide.

This three-way separation ensures the transcription is a genuine blind reading.
