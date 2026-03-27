# Manuscript Transcription Skills

A set of Claude Code skills for running blind evaluation experiments on early modern manuscript transcription. These skills are the experimental apparatus for the Teaching Machines to Read project — they automate the setup, execution, measurement, and iteration of transcription experiments while maintaining methodological rigor.

## Quick Start

```
# In a fresh Claude Code session:
/manuscript-iterate
```

Then tell it which manuscript to test and it will guide you through the process.

## The Skills

### `/manuscript-transcription` — The Instructions Being Tested

The transcription method itself. This is what you're iterating on — the instructions that tell an agent how to read a manuscript page. Currently implements the **alphabet-first method** (build a hand-specific alphabet, then transcribe, then verify against the vocabulary reference).

**When to edit this:** When you want to test a different approach, add a new step, or refine the instructions based on error patterns from a previous run.

**Location:** `skills/manuscript-transcription/SKILL.md`

### `/manuscript-evaluation` — The Ruler

Blind CER grading. An evaluation agent compares a transcription against a reference transcription — it never sees the manuscript image. CER is computed by a deterministic Python script (`jiwer`), not by the agent. The agent's job is qualitative: categorize what kind of errors occurred and why.

**When to edit this:** Rarely. The measurement method should stay constant while you iterate on the transcription instructions. Only change this if you're adding a new metric or fixing a bug in the evaluation process.

**Location:** `skills/manuscript-evaluation/SKILL.md`
**Scripts:** `skills/manuscript-evaluation/scripts/`

### `/manuscript-test-run` — The Experiment

Sets up isolated agent folders, launches 20 transcription agents in parallel, evaluates each blindly, and saves structured JSON results. This is the experimental protocol — it enforces isolation, prevents contamination, and records everything.

**When to edit this:** If you need to change the experimental setup (different number of agents, different folder structure, different output format).

**Location:** `skills/manuscript-test-run/SKILL.md`

### `/manuscript-iterate` — The Research Loop

The meta-orchestrator. Guides you through the full cycle: run a test → review results → decide what to change → edit the skill → run again. Launches fresh subagents for each test run to prevent context contamination. Keeps you in the loop for decisions while handling the orchestration.

**When to use:** When you want to iterate on the transcription method. This is your main entry point.

**Location:** `skills/manuscript-iterate/SKILL.md`

## How to Run an Experiment

### First time setup

1. **Install dependencies** (one time only):
   ```bash
   pip3 install -r skills/manuscript-evaluation/scripts/requirements.txt
   ```

2. **Verify the scripts work:**
   ```bash
   python3 skills/manuscript-evaluation/scripts/compute_cer.py --help
   ```

### Running a test

1. **Open a fresh Claude Code session.** Don't reuse a session that was editing the skills — start clean.

2. **Invoke the test runner or the iteration loop:**
   ```
   /manuscript-test-run
   ```
   or
   ```
   /manuscript-iterate
   ```

3. **Tell it what to test:**
   > Run a blind evaluation on Henslow MS688 page 12.
   > Image: ingest/archive/test/[path to image]
   > Reference: ingest/archive/test/[path to reference transcription]
   > 20 agents.

4. **Verify isolation** before agents launch. Ask to see the contents of a few agent folders. Each should contain ONLY the manuscript image, paleography guide, and vocab reference — nothing else.

5. **Wait for results.** With 20 agents, this takes a while. The skill runs agents in batches if needed.

6. **Review the JSON output** in `public/data/runs/run-[N]-results.json`. Key numbers:
   - Mean CER and 95% confidence interval
   - Coverage (did agents attempt the whole page?)
   - Spread (tight = reliable, wide = inconsistent)
   - Error consensus (words ALL agents got wrong = systematic problems)

### Iterating

After reviewing results:

1. Look at the **error consensus** — which words did every agent misread?
2. Look at the **dominant error categories** — letterform confusion? modernization? hallucination?
3. Edit `skills/manuscript-transcription/SKILL.md` to address the systematic problems
4. Run another test and compare

**The principle:** change one thing at a time, measure, compare. Same as any experiment.

## Where Results Go

```
public/data/runs/
├── run-14-results.json     # Each run gets its own file
├── run-15-results.json     # Never modifies existing files
└── run-16-results.json     # Compatible with site chart schema
```

These JSON files are raw data. They are NOT automatically displayed on the website. Updating the site charts is a separate, human-directed process — the data just needs to be there when you're ready.

## What You Need for a Test

For each manuscript you want to test, you need:

1. **A manuscript image** (JPG) — the page to transcribe
2. **A reference transcription** (TXT) — ground truth from FromThePage or EMROC
3. The **paleography guide** — already in the repo at `ingest/references/paleography-guide.md`
4. The **vocabulary reference** — already at `extracted/derived/vocab/vocab-reference.txt`

## Contamination Rules

These exist because agents cheat when given the opportunity (confirmed in Runs 5 and 9):

- **Test runs happen in `/tmp/`**, not inside the project directory
- **Each agent gets its own folder** with only its authorized materials
- **No agent sees the reference transcription** — that's only for the evaluator
- **No agent sees other agents' work** — shared folders inflate results
- **Evaluator agents never see the manuscript image** — text-against-text only

If any of these rules are violated, the run is contaminated and the results should be discarded.

## File Overview

```
skills/
├── README.md                          # This file
├── manuscript-transcription/
│   └── SKILL.md                       # The reading method (what you iterate on)
├── manuscript-evaluation/
│   ├── SKILL.md                       # Blind CER grading protocol
│   └── scripts/
│       ├── compute_cer.py             # Deterministic CER via jiwer
│       ├── compute_stats.py           # Statistical summaries via scipy
│       ├── requirements.txt           # Python dependencies
│       └── README.md                  # Script documentation
├── manuscript-test-run/
│   └── SKILL.md                       # Experiment orchestrator
└── manuscript-iterate/
    └── SKILL.md                       # Research iteration loop
```
