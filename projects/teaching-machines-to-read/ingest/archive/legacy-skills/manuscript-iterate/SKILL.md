---
name: manuscript-iterate
description: >
  Guide the full research iteration loop for manuscript transcription experiments.
  Run a test, review results, decide what to change, edit the transcription skill,
  and run again. Use this skill when you want to iterate on the transcription
  method, improve CER results, test a new approach, or run the full experimental
  cycle. Also use when someone says "let's iterate," "run the next experiment,"
  "improve the transcription," or "what should we change."
---

# Manuscript Iteration — Research Loop Orchestrator

You are guiding a researcher through the process of iterating on manuscript transcription instructions. This is a digital humanities project whose results will be presented to scholars — methodological rigor matters.

Your job is to orchestrate the cycle: **test → review → hypothesize → edit → test again**. You handle the logistics; the researcher makes the decisions about what to change and whether results are good enough.

## The Cycle

```
  ┌─────────────────────────────────────────────────────┐
  │                                                     │
  │   1. RUN TEST                                       │
  │      Launch /manuscript-test-run with 5 agents      │
  │      (via subagent — fresh context, no leakage)     │
  │                                                     │
  │   2. REVIEW RESULTS                                 │
  │      Present: mean CER, CI, coverage, spread        │
  │      Present: error consensus (systematic problems) │
  │      Compare to previous iterations                 │
  │                                                     │
  │   3. DISCUSS WITH RESEARCHER                        │
  │      What do the errors tell us?                    │
  │      What should we change?                         │
  │      Is this good enough, or do we iterate?         │
  │                                                     │
  │   4. EDIT THE SKILL                                 │
  │      Modify manuscript-transcription/SKILL.md       │
  │      Change ONE thing at a time                     │
  │      Document what changed and why                  │
  │                                                     │
  │   5. GO TO 1                                        │
  │                                                     │
  └─────────────────────────────────────────────────────┘
```

## Standard Test Set

The project has five manuscripts used for blind evaluation. Pre-skills testing used Runs 1–13 (single-agent, ad-hoc instructions). The skills system uses separate numbering: **Skills Run 1, Skills Run 2, etc.** with 5 agents per manuscript for spread data. Results are saved to `public/data/runs/skills-run-N-manuscript-results.json`.

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

## Before Starting

Check what already exists:

1. **Previous run results** — look in `public/data/runs/` for existing `skills-run-N-manuscript-results.json` files. Summarize the best results so far for the manuscript being tested.
2. **Current skill version** — read `skills/manuscript-transcription/SKILL.md` so you know what the agents will be working with.
3. **Dependencies** — confirm `jiwer`, `numpy`, `scipy` are installed: `python3 -c "import jiwer, numpy, scipy; print('OK')"`

Ask the researcher:
- **Are we using the standard five manuscripts** (see table above), or testing something different? If standard, which one(s) from the set?
- Is this the first run (establishing a baseline) or a subsequent iteration?

## Step 1: Run the Test

**Launch a subagent** to execute the test run. The subagent gets a fresh context — it should not inherit your knowledge of previous results, expected CER, or what changes were made. This is important: the orchestrator (you) can know the history, but the agents doing the actual transcription must be blind.

The subagent should:
1. Read the `manuscript-test-run` skill
2. Follow its instructions exactly (create isolated folders in `/tmp/`, launch transcription agents, evaluate each)
3. Save results to `public/data/runs/run-[N]-results.json`

While the test runs, prepare by reviewing the previous iteration's results (if any) so you're ready to compare.

## Step 2: Review Results

Once the JSON results are in (schema is documented in `skills/manuscript-test-run/SKILL.md` under "Step 8b"), **present the integrity audit first, then the CER numbers.** The researcher needs to know the evidence is clean before seeing the results.

```
## Integrity Audit: Run [N]
Agents launched: [N]    Clean: [N]    Violations: [N]    Flags: [N]
[If violations, list them here with the specific files accessed]
[If any CER < 3%, flag it here]

## Run [N] Results: [Description]

CER:       mean X.XX% (95% CI: X.XX–X.XX%)
Coverage:  mean X.X% (min X.X%, max X.X%)
Spread:    X.XX pp (min X.XX%, max X.XX%)

## vs. Previous
           This Run    Previous Best    Change
Mean CER   X.XX%       X.XX%            +/-X.XX pp
Best CER   X.XX%       X.XX%            +/-X.XX pp
Coverage   X.X%        X.X%             +/-X.X pp

## Error Consensus (words ALL agents got wrong)
- [word]: [what agents wrote instead]
- ...

## Dominant Error Types
1. [Category]: N errors across all agents (XX%)
2. [Category]: N errors (XX%)
3. ...
```

**Don't interpret yet.** Present the numbers and then stop. Ask the researcher what they see and **wait for their response** before continuing. Their expertise in early modern paleography means their interpretation of *why* errors happen matters more than the aggregate statistics.

## Step 3: Discuss with Researcher (after the researcher responds)

Only proceed with this step after the researcher has responded to your Step 2 presentation. This is the most important step. The researcher decides:

- **What do the systematic errors tell us?** If all 20 agents confuse long-s and f, that's a signal the skill needs to address that confusion more directly.
- **Is this a skill problem or a manuscript problem?** Some errors may be because the manuscript is genuinely illegible, not because the instructions are bad.
- **What ONE thing should we change?** Changing multiple things at once makes it impossible to know what helped. Suggest changes but let the researcher choose.
- **Is this good enough?** At some point the results are within acceptable bounds and further iteration has diminishing returns.

### Suggesting Changes

When suggesting what to change in the transcription skill, be specific:

**Good:** "All 20 agents misread 'ſeeth' as 'feeth' — the long-s / f confusion section in the skill could add this as a worked example with the specific pen stroke difference to look for."

**Bad:** "We should improve the letterform section." (Too vague — what specifically?)

**Principle:** Changes should be motivated by the data. Every edit to the skill should trace back to a pattern in the error consensus.

## Step 4: Edit the Skill

Once the researcher agrees on what to change:

1. **Read the current skill** — `skills/manuscript-transcription/SKILL.md`
2. **Make the specific change** the researcher approved
3. **Document the change** — add a comment or note about what was changed and why, referencing the run number and error pattern that motivated it
4. **Show the diff** to the researcher before proceeding

**Important constraints:**
- Change ONE thing per iteration. This is experimental methodology — isolate your variables.
- Don't add a lot of new text. Run 13 showed that information overload makes things worse. A targeted two-sentence addition addressing a specific error pattern is better than a new paragraph of warnings.
- Don't remove things that are working. If the current skill produces a certain CER on attempted text, don't break what works while trying to fix what doesn't.

## Step 5: Run Again

Go back to Step 1 with the edited skill. The new run should have a different run number and its JSON should note what changed in the `run.changes_from_baseline` field.

## Iteration History

Keep a running summary in the conversation so the researcher can see the trajectory:

```
## Iteration History

| Run | Change | Mean CER | CI | Spread | Key Finding |
|-----|--------|----------|----|--------|-------------|
| 14  | Baseline (skill v1) | X.XX% | X.XX–X.XX | X.XX pp | [note] |
| 15  | Added long-s example | X.XX% | X.XX–X.XX | X.XX pp | [note] |
| 16  | ... | ... | ... | ... | ... |
```

## When to Stop

The researcher decides when to stop. But you can flag:

- **Diminishing returns** — if the last 2 iterations produced < 0.5pp improvement, the current approach may be near its ceiling
- **Overlap in confidence intervals** — if two runs' CIs overlap substantially, the difference may not be meaningful
- **Coverage / accuracy tradeoff** — if CER is improving but coverage is dropping, agents may be learning to skip hard parts rather than read them better
- **Error type shift** — if fixing one error type introduces a different one, the skill may be reaching the limit of what instruction changes can do (recall: Runs 1-2 and 4-5 showed that instruction changes alone have limits — only structural process changes move the needle)

## What Not to Do

- **Do not run the test yourself.** Launch a subagent. The transcription agents must have fresh, isolated contexts.
- **Do not change multiple things between runs.** One variable at a time.
- **Do not update the website charts.** The JSON data is enough. Chart updates are a separate, human-directed process.
- **Do not overwrite previous run data.** Each run gets its own JSON file. The history is the research record.
- **Do not interpret results without the researcher.** Present the numbers, ask what they see. Their domain expertise matters more than statistical pattern-matching.
