---
name: manuscript-test-run
description: >
  Run a blind evaluation experiment for manuscript transcription. Sets up isolated
  agent folders, launches N transcription agents in parallel, then evaluates each
  against a reference transcription and saves structured results as JSON. Use this
  skill when you need to test transcription instructions, run a blind evaluation,
  set up an experiment with multiple agents, or measure CER spread across agents.
  Also use when someone says "run a test," "set up a blind test," or "how
  consistent are the results."
---

# Manuscript Test Run — Blind Evaluation Protocol

## Research Context

This is a serious digital humanities research project whose results will be presented to scholars in English literature, paleography, and DH methodology. The experimental protocol must be rigorous enough to withstand peer review.

**What this means for you as the orchestrator:**
- **Use the provided Python scripts** (`compute_cer.py`, `compute_stats.py`) for all quantitative measurement. These use `jiwer` (the field-standard HTR evaluation library) and `scipy.stats`. Do not hand-roll CER calculations, edit distance algorithms, or statistical summaries — use the scripts.
- **Isolation is not a suggestion — it's the experimental design.** A contaminated run is worse than no run. Verify agent folders before launching.
- **Record everything.** The JSON output is the primary research data. Missing fields or approximate values cannot be reconstructed later.
- **Report honestly.** If something went wrong during a run (agent saw files it shouldn't have, a folder wasn't properly isolated, a script errored), document it in the run config. Do not silently discard or re-run.

## Purpose

This skill orchestrates a blind transcription experiment. It creates isolated environments for multiple agents, runs them in parallel with the manuscript-transcription skill, evaluates each result with the manuscript-evaluation skill, and saves structured data that the project website can later ingest.

The purpose is to test how well a set of transcription instructions works — and how consistent the results are across multiple agents. A single CER number doesn't tell you much; you need spread data to know if a method is reliable or if one good result was a fluke.

## Standard Test Set

The project has five manuscripts used for blind evaluation. Pre-skills testing used Runs 1–13 (single-agent, ad-hoc instructions). The skills system uses a separate numbering: **Skills Run 1, Skills Run 2, etc.** Each skills run tests 5 agents per manuscript for spread data.

All test files live under `ingest/archive/test/` in the project directory (`projects/teaching-machines-to-read/`). Results are saved to `public/data/runs/skills-run-N-manuscript-results.json`.

| Manuscript | Image | Reference | Pre-Skills Best | Skills Baseline (Run 1, mean) |
|---|---|---|---|---|
| Henslow MS688 | `henslow-ms688/test-page.jpg` | `henslow-ms688/test-page-reference.txt` | 3.80% (Run 6) | 5.26% (att. 3.30%) |
| Sedley MS534 | `sedley-ms534/test-page.jpg` | `sedley-ms534/test-page-reference.txt` | 13.65% (Run 10) | 16.87% (att. 11.47%) |
| Bulkeley MS169 | `bulkeley-ms169/test-page.jpg` | `bulkeley-ms169/test-page-reference.txt` | 16.21% (Run 6) | 15.65% (att. 12.69%) |
| Brumwich MS160 | `brumwich-ms160/test-page.jpg` | `brumwich-ms160/test-page-reference.txt` | 9.30% (Run 4) | 71.11% (att. 19.75%) |
| Jane Jackson MS373 | `jane-jackson-ms-373/page-20.jpg` | `jane-jackson-ms-373/page-20-reference.txt` | 46.85% (Run 5) | 74.10% (att. 18.61%) |

Shared resources (also in the project directory):
- **Paleography guide:** `ingest/references/paleography-guide.md`
- **Vocabulary reference:** `extracted/derived/vocab/vocab-reference.txt`

When the researcher says "use the standard five" or "run on Henslow," use these paths. If they provide a different manuscript, ask for the image and reference paths.

## Before You Start

**Permissions required:** This skill creates folders, copies files, runs Python scripts, and launches subagents — all via Bash, Read, Write, and Edit. If permissions aren't pre-approved for `/tmp/manuscript-runs/` and the project's `skills/` directory, you'll be blocked immediately. Ask the user to check their Claude settings before starting.

You need:

1. **Which manuscript(s)** — from the standard test set above, or custom paths if testing something new
2. **The number of agents** to run (default: 20 — large batches give high confidence in spread data)
3. **The transcription skill** to test (default: `skills/manuscript-transcription/SKILL.md` in this repo)
4. **The run number** — check existing runs in `public/data/runs/` to determine the next number

Confirm these with the user before setting anything up.

**Model and batch size:** Always use the frontier Opus model for all agents (transcription and evaluation). Default to 20 agents for high statistical confidence. If the system limits concurrent subagents, launch in batches (e.g., 5 at a time × 4 rounds) — the results are the same as long as each agent is isolated. Don't hold back on compute — thoroughness matters more than cost here.

## Step 1: Create the Run Directory

All test runs go in `/tmp/manuscript-runs/`, **not inside the project directory**. This is contamination control — agents are curious and will browse their environment. If the test folder is inside the project, they can find reference transcriptions, previous results, or other agents' work.

```
/tmp/manuscript-runs/run-[N]-[short-description]/
├── agent-1/
│   ├── manuscripts/          # COPY of the manuscript image(s)
│   ├── guide/                # COPY of paleography-guide.md + vocab-reference.txt
│   └── output/               # Agent writes here (alphabet + transcription)
├── agent-2/
│   └── ... (same structure)
├── agent-3/
│   └── ... (same structure)
├── agent-4/
│   └── ... (same structure)
├── agent-5/
│   └── ... (same structure)
├── evaluation/
│   ├── reference/            # The ground truth transcription
│   └── results/              # Evaluation reports go here
└── run-config.txt            # Documents what was tested and why
```

**Critical isolation rules:**

- Each agent folder contains ONLY what that agent is authorized to see: the manuscript image, the paleography guide, and the vocab reference.
- **No reference transcriptions** in any agent folder.
- **No shared output directory.** Each agent writes to its own `output/` folder. Shared folders were proven to contaminate results (Run 9 — CER inflated by 1-2 percentage points).
- **No access to other agents' work.** Each agent must be launched with its own folder as the working directory and must not be told about or given paths to sibling folders.
- The evaluation folder is completely separate. Evaluator agents see only the transcription they're grading and the reference — never the manuscript image.

## Step 2: Write the Run Config

Before launching any agents, create `run-config.txt` documenting:

```
# Run [N]: [Short Description]
Date: [YYYY-MM-DD]
Manuscript: [name, shelfmark, page]
Reference source: [FromThePage / EMROC / other]
Number of agents: [N]
Transcription skill version: [path or description of what changed]

## What We're Testing
[One paragraph: what question is this run trying to answer?]

## Baseline
[Previous best result for this manuscript, if any]

## Changes from Baseline
[What's different about this run's instructions vs. the baseline?]

## Methodology Note
N=[number] independent transcription sessions using [model name], each with a
fresh context and no shared state. This measures intra-method variance — the
reproducibility of the transcription protocol — not variation across different
readers. CER computed deterministically via compute_cer.py using Levenshtein
edit distance. Statistical summary includes mean, 95% CI, median, IQR.
```

This is the experimental record. Future-you needs to know what was tested and why.

## Step 3: Set Up Agent Folders

For each agent, copy (not symlink) the authorized materials into its folder:

1. Copy the manuscript image(s) into `agent-N/manuscripts/`
2. Copy `paleography-guide.md` into `agent-N/guide/`
3. Copy `vocab-reference.txt` into `agent-N/guide/`
4. Create an empty `agent-N/output/` directory

**Verify each folder.** Before launching, list the contents of every agent folder and confirm:
- It contains the manuscript image(s)
- It contains the paleography guide and vocab reference
- It does NOT contain reference transcriptions, other agents' output, or anything else
- The output folder is empty

If anything is wrong, fix it before proceeding. Contamination invalidates the entire run.

## Step 4: Prepare Agent Prompts (Inline Everything)

**Do not ask subagents to read files with tool calls.** Subagents may lack tool permissions, may read files in a different order, or may skip materials. Instead, the orchestrator (you) reads all materials and inlines them directly into each agent's prompt. This ensures every agent starts with exactly the same context — no variance from reading order or tool access.

Before launching, read these files yourself:
1. `skills/manuscript-transcription/SKILL.md` — the full transcription skill
2. `ingest/references/paleography-guide.md` — the full paleography guide

**Do NOT inline the vocab reference** (19K lines). Instead, copy it into each agent's folder and tell the agent the file path. The vocab list is a lookup tool consulted during verification, not something to digest up front. Inlining it would cause information overload.

## Step 5: Launch Transcription Agents

Launch agents in parallel using subagents. Each agent's prompt should contain everything it needs inline — no tool calls required to start working. Structure the prompt like this:

```
You are transcribing an early modern manuscript page. Follow these instructions exactly.

=== TRANSCRIPTION INSTRUCTIONS ===
[Paste the FULL contents of skills/manuscript-transcription/SKILL.md here]

=== PALEOGRAPHY GUIDE ===
[Paste the FULL contents of ingest/references/paleography-guide.md here]

=== YOUR TASK ===
Your working directory is [path to agent-N/].
Your manuscript image is in `manuscripts/`. Read it with the Read tool.
Your vocabulary reference is at `guide/vocab-reference.txt`. Use it during Step 3 (verification).
Save your alphabet to `output/` and your transcription to `output/`.
```

**What NOT to include in the prompt:**
- Any information about other agents
- The reference transcription
- Expected results or previous CER numbers
- Any mention that this is a multi-agent experiment

Each agent should believe it is the only agent doing this task.

**Batch if needed:** If the system limits concurrent subagents, launch in batches (e.g., 5 at a time). The results are the same as long as each agent is isolated.

## Step 6: Evaluate Each Transcription

After all transcription agents finish, launch evaluation agents — one per transcription. Same inlining principle — read the evaluation skill and paste it into each evaluator's prompt:

```
You are evaluating a manuscript transcription. Follow these instructions exactly.

=== EVALUATION INSTRUCTIONS ===
[Paste the FULL contents of skills/manuscript-evaluation/SKILL.md here]

=== YOUR TASK ===
Reference transcription:
[Paste the contents of the reference transcription here]

Hypothesis transcription:
[Paste the contents of agent-N's transcription here]

Run the CER script at: [full path to compute_cer.py]
Save your evaluation report to [path to evaluation/results/agent-N-evaluation.txt]
```

**The evaluator must NOT see:**
- The manuscript image
- The paleography guide
- The agent's alphabet chart
- Any other agent's transcription or evaluation

## Step 7: Integrity Audit (Every Agent, Every Run)

This step is **mandatory** and runs on every agent, not just when results look suspicious. The audit log is the chain of evidence that the run was clean — without it, the results are not publishable.

When each transcription agent completes, capture and record:

### 7a: Agent Metadata

From the subagent completion notification:
- **`duration_ms`** — how long the agent took
- **`total_tokens`** — how much context it consumed

Save to the agent's folder as `output/agent-audit.json`.

### 7b: File Access Log

Review the agent's tool call history (from the subagent output log) and record every file the agent read or accessed. Categorize each access:

| Access | Status |
|---|---|
| Read of file inside `agent-N/manuscripts/` | **Authorized** |
| Read of file inside `agent-N/guide/` | **Authorized** |
| Write to `agent-N/output/` | **Authorized** |
| Read of ANY file outside `agent-N/` | **VIOLATION** |
| Read of any path containing "reference" or "evaluation" | **VIOLATION** |
| Read of another agent's folder | **VIOLATION** |
| Read of any project directory file | **VIOLATION** |
| Any web fetch or URL access | **VIOLATION** |

### 7c: Flags

Check each agent for these red flags:

1. **Unauthorized file access** — any Read/Glob/Grep outside the agent's own folder
2. **Suspiciously fast completion** — if an agent took less than half the time of the median agent, it may have shortcut the alphabet step
3. **No alphabet file** — if `output/` has a transcription but no alphabet, the agent skipped Step 1 (the entire point of the method)
4. **Zero gaps on a hard manuscript** — a transcription with no `[...]` markers on a manuscript rated "hard" or "very hard" suggests the agent fabricated readings instead of marking illegible text
5. **CER below 3%** — the best honest blind result is 3.80%. Below 3% requires explanation.

### 7d: Audit Result

For each agent, record in `agent-audit.json`:

```json
{
  "agent": 1,
  "duration_ms": 45000,
  "total_tokens": 85000,
  "files_accessed": [
    {"path": "agent-1/manuscripts/henslow-ms688-page12.jpg", "status": "authorized"},
    {"path": "agent-1/guide/paleography-guide.md", "status": "authorized"},
    {"path": "agent-1/guide/vocab-reference.txt", "status": "authorized"}
  ],
  "violations": [],
  "flags": [],
  "clean": true
}
```

If ANY agent has a violation, the entire run is **contaminated**. Report it in the run summary and do not include that agent's CER in the aggregate statistics. If multiple agents have violations, discard the run entirely.

If an agent has flags but no violations (e.g., fast completion, no alphabet), note it but don't automatically discard — the researcher decides.

## Step 8: Compile Results and Save Structured Data

After all evaluations complete, compute statistics and produce structured output.

**Use the scripts** for all quantitative work:
- `skills/manuscript-evaluation/scripts/compute_cer.py` — CER for each agent's transcription
- `skills/manuscript-evaluation/scripts/compute_stats.py` — summary statistics from the CER values

If the dependencies aren't installed yet, run `pip install -r skills/manuscript-evaluation/scripts/requirements.txt` first.

Produce two outputs:

### 8a: Human-readable summary

Write `evaluation/results/run-summary.txt`:

```
# Run [N] Results: [Description]

| Agent | CER | Substitutions | Insertions | Deletions |
|-------|-----|---------------|------------|-----------|
| 1     |     |               |            |           |
| ...   |     |               |            |           |

Average CER: X.XX%
Best CER: X.XX%
Worst CER: X.XX%
Spread: X.XX pp (percentage points between best and worst)
Median CER: X.XX%

## Comparison to Baseline
[Previous best for this manuscript]: X.XX%
[This run average]: X.XX%
[This run best]: X.XX%

## Common Error Patterns
[Errors that appeared across multiple agents — systematic problems
with the instructions, not random variation.]

## Observations
[What does the spread tell us? Tight spread = reliable method.
Wide spread = inconsistent.]
```

### 8b: Structured JSON for the website

Write a new file to the project's data directory. **Never modify existing files.** Each run gets its own JSON file:

**Path:** `projects/teaching-machines-to-read/public/data/runs/run-[N]-results.json`

**Principle: Record everything now, decide what to display later.** The current website charts only use a fraction of this data, but future visualizations might need any of it. Capture the full picture so nothing is lost.

**Schema:**

```json
{
  "run": {
    "id": 14,
    "name": "Short descriptive name",
    "date": "2026-03-27",
    "method": "One-sentence description of methodology",
    "category": "structural|instruction|more-input|baseline",
    "question": "What question was this run trying to answer?",
    "changes_from_baseline": "What was different about this run vs. the previous approach"
  },
  "manuscript": {
    "id": "brumwich",
    "page": 10
  },
  "skill_version": "Description of which skill version was used and what changed",
  "agents": [
    {
      "agent": 1,
      "cer": 9.12,
      "attempted_cer": 7.45,
      "coverage": 0.97,
      "reference_characters": 1847,
      "hypothesis_characters": 1823,
      "substitutions": 42,
      "insertions": 8,
      "deletions": 15,
      "errors": {
        "letterformMisreading": 12,
        "doubleLetter": 5,
        "punctuation": 4,
        "capitalization": 3,
        "uvConvention": 2,
        "hallucination": 0
      },
      "error_details": [
        {
          "category": "letterformMisreading",
          "reference": "ſeeth",
          "hypothesis": "feeth",
          "line": 3,
          "note": "long-s read as f"
        }
      ],
      "gap_count": 2,
      "uncertain_count": 5,
      "transcription_text": "Full text of the agent's transcription...",
      "alphabet_observations": {
        "letters_identified": 24,
        "letters_missing": ["x", "z"],
        "top_confusion_risks": ["long-s / f", "c / r", "e / o"],
        "variants_noted": ["two forms of r", "long-s and round-s"]
      },
      "audit": {
        "duration_ms": 45000,
        "total_tokens": 85000,
        "files_accessed": ["agent-1/manuscripts/henslow.jpg", "agent-1/guide/paleography-guide.md", "agent-1/guide/vocab-reference.txt"],
        "violations": [],
        "flags": [],
        "clean": true
      }
    }
  ],
  "summary": {
    "num_agents": 20,
    "cer": {
      "mean": 10.24,
      "median": 10.15,
      "std_dev": 1.43,
      "ci_95_lower": 9.57,
      "ci_95_upper": 10.91,
      "min": 9.12,
      "max": 12.01,
      "iqr_lower": 9.55,
      "iqr_upper": 11.02,
      "spread_pp": 2.89
    },
    "attempted_cer": {
      "mean": 7.45,
      "median": 7.30,
      "std_dev": 0.98,
      "ci_95_lower": 6.80,
      "ci_95_upper": 8.10,
      "min": 6.22,
      "max": 9.01,
      "iqr_lower": 6.85,
      "iqr_upper": 8.02,
      "spread_pp": 2.79
    },
    "coverage": {
      "mean": 0.96,
      "min": 0.89,
      "max": 1.0
    }
  },
  "error_consensus": {
    "all_agents_wrong": ["List of words every agent misread — systematic problems"],
    "most_agents_wrong": ["Words 3+ of 5 agents misread"],
    "one_agent_wrong": ["Words only 1 agent missed — random variation"],
    "common_categories": ["The error types that appeared most across all agents"]
  },
  "baseline_comparison": {
    "previous_best_cer": 9.30,
    "previous_best_run": 4,
    "improved": false
  },
  "reference_text": "Full reference transcription text for this page (enables future diff views)"
}
```

**Field notes for the schema:**

- `run.id` — sequential, matches the run number used in folder names
- `run.category` — use the same categories as `cer-results.json`: "structural" (process changes), "instruction" (wording changes), "more-input" (additional materials), "baseline" (control runs)
- `run.changes_from_baseline` — what specifically changed in the instructions or setup. This is the independent variable.
- `manuscript.id` — use the same IDs as `cer-results.json`: "henslow", "sedley", "bulkeley", "brumwich", "jane-jackson"
- `agents[].errors` — use the same category keys as `error-categories.json`: letterformMisreading, doubleLetter, hallucination, punctuation, capitalization, uvConvention, terminalE, wordSegmentation, lineation, modernizationBias, missingWord, otherSpelling, other
- `agents[].attempted_cer` — CER on confident text only, excluding deletions attributable to `[...]` gaps. Measures: "when the agent says it can read something, how often is it right?" Computed as (Substitutions + Insertions) / (reference_chars - illegible_chars). This is the confidence-calibration metric — compare it against overall CER to see how much of the error is wrong text vs. missing text.
- `agents[].coverage` — fraction of reference characters the agent actually attempted (vs. marking `[...]`). Computed by the CER script. A transcription that's 99% accurate but only covers 40% of the page isn't useful — both numbers matter.
- `agents[].error_details` — every individual error with its line number, the reference text, the agent's text, the category, and a note. This powers future word-diff views and lets you trace exactly where on the page errors cluster.
- `agents[].gap_count` / `uncertain_count` — how many `[...]` gaps and `[word?]` flags the agent used. Honest gaps are a sign of good calibration, not failure.
- `agents[].transcription_text` — the full transcription. Storing this means you can build side-by-side comparisons or word-diff viewers later without going back to the `/tmp/` run folder (which may be cleaned up).
- `agents[].alphabet_observations` — what the agent noticed about the hand during Step 1. Lets you later investigate whether alphabet quality predicts transcription accuracy.
- `agents[].audit` — integrity audit for this agent. `duration_ms` and `total_tokens` from the subagent completion notification. `files_accessed` is every file the agent read. `violations` lists any unauthorized file access (reads outside the agent's folder). `flags` lists soft warnings (fast completion, no alphabet, zero gaps, low CER). `clean` is true only if there are zero violations. **If `clean` is false, this agent's CER should be excluded from aggregate statistics.**
- `summary.cer` — full statistical summary: mean, median, standard deviation, 95% confidence interval (mean ± 1.96 × std_dev / √N), min/max, interquartile range (25th to 75th percentile), and spread. This is what makes the results publishable — "mean CER = 9.82% (95% CI: 8.94–10.70%)" is what a reviewer expects, not just "spread was 3pp."
- `summary.attempted_cer` — same statistical summary but for attempted CER (confident text only). The attempted CER spread measures consistency of the text agents actually commit to — a tighter attempted spread than overall spread means the variance comes from how much text agents skip, not from how well they read.
- `summary.coverage` — mean, min, and max coverage across agents. If any agent has low coverage, it flags that the manuscript may have legitimately illegible sections.
- `error_consensus` — which words ALL agents got wrong (systematic), which only some got wrong (partial), and which only one missed (noise). The most actionable data for improving instructions: if every agent misreads the same word, the skill needs to address that.
- `reference_text` — the full reference transcription. Included so the JSON file is self-contained — you can generate any comparison view from this file alone without needing to look up the reference elsewhere.
- `baseline_comparison.improved` — true only if the average CER is lower than the previous best AND the spread is reasonable (< 6pp). A lucky single agent doesn't count as improvement.

**Create the `runs/` directory if it doesn't exist:** `projects/teaching-machines-to-read/public/data/runs/`

## Boundary: What This Skill Does NOT Do

**This skill does not update the website charts, components, or any existing data files.**

The JSON output in `public/data/runs/` is raw data. It is designed to be compatible with the existing site schema (same field names, same manuscript IDs, same error categories) so it can be ingested later — but the process of updating charts, adding runs to `cer-results.json`, or modifying Astro components is a separate, human-directed step.

Do not:
- Modify `public/data/cer-results.json`
- Modify `public/data/error-categories.json`
- Modify `public/data/nonblind-comparison.json`
- Modify `public/data/hallucination-examples.json`
- Modify any file in `site/src/components/charts/`
- Modify any `.astro` or `.mdx` file

The only file this skill creates in the project directory is the new `run-N-results.json`.

## Integrity Summary

Before presenting ANY CER results to the researcher, first present the integrity audit summary:

```
## Integrity Audit: Run [N]

Agents launched: [N]
Agents clean: [N]
Agents with violations: [N] [list which ones and what they accessed]
Agents with flags: [N] [list which ones and what was flagged]

[If any violations]: ⚠️ CONTAMINATION DETECTED — [N] agent(s) accessed
unauthorized files. Their results are excluded from aggregate statistics.
Affected agents: [list]. Files accessed: [list paths].

[If any CER < 3%]: ⚠️ Agent [N] reported CER of X.XX%, below the 3%
threshold. Best honest blind result in the project is 3.80%. Audit shows
[clean/violations]. [If clean]: Result may be genuine but warrants scrutiny.

[If all clean and no flags]: ✓ All agents passed integrity audit.
```

**Always present this BEFORE the CER results.** The researcher should know the evidence is clean before seeing the numbers. If there are violations, say so plainly — do not bury them after the CER table.

## What Makes a Good Run

- **Tight spread** (< 3 percentage points) means the method is reliable — different agents get similar results, so you can trust the average.
- **Wide spread** (> 6 percentage points) means the method is inconsistent — some agents get lucky and others don't, so the average is less meaningful.
- **Better average than baseline** with tight spread = the instructions improved.
- **Better best than baseline** but wide spread = one agent got lucky, not a real improvement.
- **Common errors across all agents** = systematic problem in the instructions that can be fixed.
- **Errors in only one or two agents** = random variation, probably not worth chasing.

## What Not to Do

- **Do not run tests inside the project directory.** Always use `/tmp/manuscript-runs/`.
- **Do not share output folders between agents.** Each agent gets its own.
- **Do not give agents access to the reference transcription.** That defeats the entire purpose of blind evaluation.
- **Do not tell agents about each other.** They should not know this is a multi-agent experiment.
- **Do not modify agent folders after launching.** If something went wrong, note it in the run config and decide whether the results are valid. Do not retroactively "fix" a contaminated run.
- **Do not run the evaluation yourself.** Use separate evaluation agents with the manuscript-evaluation skill. You orchestrate; they evaluate.
- **Do not update charts or existing data files.** See the boundary section above.
