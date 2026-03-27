# Run 12: Error Analysis Transfer — Reverse Direction

## Overview

Run 10 showed that an error protocol built from Henslow mistakes improved Sedley results (13.65% CER, down from ~17%). This experiment tests whether the transfer works in the **reverse direction**: build an error protocol from Sedley mistakes, then test on Henslow.

**Question:** Does error analysis transfer both ways, or only from easier → harder manuscripts?

Stanovich's compensatory model (1980) predicts the protocol should help *less* on more legible manuscripts, because there's less need to compensate for poor decoding. If it helps equally in both directions, that's interesting — it suggests the error patterns are truly general, not difficulty-dependent.

## Baselines

- **Henslow best CER:** 3.80% (Run 6, alphabet-first + vocab)
- **Henslow self-taught CER:** 5.17–7.17% (Run 9, depending on training pages)
- **Sedley best CER:** 13.65% (Run 10, with Henslow-derived error protocol)

## Design

### Phase 1: Transcribe Sedley (5 agents, blind)

Five agents independently transcribe Sedley MS534 page 13 using the self-taught guide (5-page version from Run 9) and the standard paleography guide. No error protocol, no vocab list.

Each agent works in a separate isolated folder.

### Phase 2: Error Analysis

A separate agent compares all 5 Sedley transcriptions against the FromThePage reference. Produces a detailed error analysis following the same format as Run 10:
- **Section A:** Systematic errors (4-5 agents made the same mistake)
- **Section B:** Common errors (2-3 agents)
- **Section C:** Stochastic errors (1 agent only)
- **Section D:** What agents got right that was hard
- **Section E:** Pattern analysis

### Phase 3: Build Error Protocol

A separate agent reads the error analysis and writes a revised transcription protocol, modeled on Run 10's `revised-protocol.txt`. The protocol should:
- Address the specific error patterns found in Sedley transcriptions
- Include letterform warnings, vocabulary, and a verification checklist
- Be written to help with early modern manuscripts *generally*, not just Sedley

### Phase 4: Transcribe Henslow with Sedley-derived Protocol (5 agents, blind)

Five agents transcribe Henslow MS688 page 12 using:
- The self-taught guide (5-page version)
- The paleography guide
- The Sedley-derived error protocol (from Phase 3)

Each agent works in a separate isolated folder.

### Phase 5: Evaluation

Separate evaluation agents compute CER for each Henslow transcription against the FromThePage reference.

## What We Compare

| Condition | Manuscript | Expected CER |
|---|---|---|
| Baseline (Run 9, 5-page self-taught) | Henslow | 5.17–7.17% |
| With Sedley-derived error protocol | Henslow | ? |
| Run 10 (with Henslow-derived protocol) | Sedley | 13.65% |

**If the Sedley protocol helps on Henslow:** Error patterns are general paleographic problems. Transfer is bidirectional.

**If it doesn't help (or helps less):** Transfer may be asymmetric — error analysis helps more on harder manuscripts where there's more room to improve.

## Agent Isolation — CRITICAL

Each agent runs in a **completely isolated folder** containing ONLY its authorized materials. No shared output directories. No access to other agents' work, reference transcriptions, or evaluation results.

### Folder Structure

```
run-12-error-transfer-reverse/
├── instructions-error-transfer-reverse.md
├── phase1-sedley-transcription/
│   ├── agent-1/
│   │   ├── materials/
│   │   │   ├── sedley-ms534-page13.jpg
│   │   │   ├── paleography-guide.md
│   │   │   └── self-taught-guide.txt
│   │   └── output/
│   ├── agent-2/ ... agent-5/
├── phase2-error-analysis/
│   ├── materials/
│   │   ├── sedley-reference.txt
│   │   └── transcriptions/        # Copies of Phase 1 outputs
│   └── output/
│       └── error-analysis.txt
├── phase3-build-protocol/
│   ├── materials/
│   │   └── error-analysis.txt      # Copy from Phase 2
│   └── output/
│       └── error-protocol.txt
├── phase4-henslow-transcription/
│   ├── agent-1/
│   │   ├── materials/
│   │   │   ├── henslow-ms688-page12.jpg
│   │   │   ├── paleography-guide.md
│   │   │   ├── self-taught-guide.txt
│   │   │   └── error-protocol.txt
│   │   └── output/
│   ├── agent-2/ ... agent-5/
├── phase5-evaluation/
│   ├── materials/
│   │   ├── henslow-reference.txt
│   │   └── transcriptions/        # Copies of Phase 4 outputs
│   └── output/
└── results.txt
```

---

## Phase 1 Instructions: Transcribe Sedley (Transcription Agent)

You are given a manuscript page to transcribe and two reference guides.

**Your materials:**
- `materials/sedley-ms534-page13.jpg` (the manuscript page)
- `materials/paleography-guide.md` (Folger paleography guide)
- `materials/self-taught-guide.txt` (self-taught guide from studying 5 paired examples)

**You do NOT have:** Any error protocol, vocabulary list, reference transcription, or access to other agents' work.

**Your task:** Transcribe the manuscript page using the two guides.

**Transcription rules:**
- Transcribe exactly what you see — preserve original spelling, punctuation, capitalization, and line breaks
- If you cannot read a word or passage, mark it `[...]` — do NOT guess or make up text
- If you are uncertain about a reading, mark it `[word?]`
- Note any abbreviations you expand

**Save your transcription as:** `output/sedley-ms534-transcription.txt`

---

## Phase 2 Instructions: Error Analysis (Analysis Agent)

You are given 5 independent transcriptions of the same manuscript page, plus the correct reference transcription.

**Your materials:**
- `materials/sedley-reference.txt` (the correct transcription)
- `materials/transcriptions/agent-1.txt` through `agent-5.txt`

**Your task:** Compare all 5 transcriptions against the reference and produce a detailed error analysis.

Organize your analysis into:
- **Section A: Systematic errors** — mistakes made by 4-5 agents. These reveal fundamental gaps.
- **Section B: Common errors** — mistakes made by 2-3 agents.
- **Section C: Stochastic errors** — mistakes made by only 1 agent.
- **Section D: What agents got right that was hard** — difficult readings that agents handled well.
- **Section E: Pattern analysis** — what categories of error dominate? What's the root cause?

For each error, quote the reference reading, quote each agent's reading, and explain what went wrong (letterform confusion? normalization? vocabulary gap? hallucination?).

**Save your analysis as:** `output/error-analysis.txt`

---

## Phase 3 Instructions: Build Error Protocol (Protocol Agent)

You are given a detailed error analysis of 5 agents' attempts to transcribe an early modern manuscript.

**Your materials:**
- `materials/error-analysis.txt`

**Your task:** Write a revised transcription protocol that addresses the specific error patterns found in the analysis. This protocol will be given to new agents who will transcribe a *different* manuscript from the same era.

Your protocol should include:
1. **Critical mindset rules** — the most important behavioral changes
2. **Specific letterform warnings** — documented confusions with examples
3. **Vocabulary** — herbal, medical, and recipe terms that caused problems
4. **Scribe habit detection** — what to look for before transcribing
5. **Post-transcription verification checklist**
6. **Decision framework for ambiguous letterforms**

Write the protocol to address *general* early modern paleography problems, not Sedley-specific issues. The goal is to help on any similar manuscript.

**Save your protocol as:** `output/error-protocol.txt`

---

## Phase 4 Instructions: Transcribe Henslow with Error Protocol (Transcription Agent)

You are given a manuscript page to transcribe, two reference guides, and an error protocol built from analyzing mistakes on a different manuscript.

**Your materials:**
- `materials/henslow-ms688-page12.jpg` (the manuscript page)
- `materials/paleography-guide.md` (Folger paleography guide)
- `materials/self-taught-guide.txt` (self-taught guide)
- `materials/error-protocol.txt` (error protocol built from Sedley mistakes)

**Read the error protocol carefully before you begin transcribing.** It contains specific warnings about letterform confusions, vocabulary, and common mistakes that other agents made on a different manuscript from the same era.

**You do NOT have:** Any vocabulary list, reference transcription, or access to other agents' work.

**Transcription rules:**
- Transcribe exactly what you see — preserve original spelling, punctuation, capitalization, and line breaks
- If you cannot read a word or passage, mark it `[...]` — do NOT guess or make up text
- If you are uncertain about a reading, mark it `[word?]`
- Use the post-transcription verification checklist from the error protocol before saving

**Save your transcription as:** `output/henslow-ms688-transcription.txt`
