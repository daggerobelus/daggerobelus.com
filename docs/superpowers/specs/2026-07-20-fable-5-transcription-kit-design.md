# Fable 5 Transcription Kit — Design

**Date:** 2026-07-20
**Project:** teaching-machines-to-read
**Status:** Approved design, pre-implementation

## Goal

A downloadable kit that lets non-technical scholars transcribe early modern
secretary-hand manuscript pages using Claude via claude.ai — no command line,
no repo. The kit packages the validated Rung 1 editorial-contract method from
the July 2026 Fable 5 scaffolding ladder (run 3-ladder).

## Audience and usage model

Historians / grad students with a Claude account. Usage: open claude.ai,
upload a manuscript page image, paste the kit prompt, receive a
semi-diplomatic transcription in the chat. No CER evaluation step (users have
no reference transcriptions); no scripts.

## Kit identity: model-specific by design

This kit is **the Claude Fable 5 kit**. It is not a model-neutral method with
per-model validation. Future kits for other models may have entirely
different steps, because different models have different capabilities. Nothing
in the folder layout, filenames, or page structure should imply future kits
share this kit's shape. New models get new kits; there is no shared method
contract across kits.

## Content: Rung 1 editorial contract only

- The kit prompt is the Rung 1 editorial-rules contract
  (`ingest/archive/test/fable-ladder-2026-07/kits/rung-1-editorial-contract/prompt-template.txt`),
  approved by Sarah 2026-07-06 and validated at 2.2–4.1% strict CER across
  all five test manuscripts.
- **Excluded:** the Folger-derived paleography guide (provenance — classroom
  material, cannot ship; see the run's PROVENANCE.md). Sarah's own
  public-sourced replacement guide may join a future kit version.
- **Excluded:** the vocab reference (ladder data: helped Henslow, hurt
  Sedley/Bulkeley, ~3x cost; also awkward to use in a chat workflow).

## Authorship policy (repo content policy applies)

- **Sarah writes all human-read prose:** the kit README (which is also the
  site-facing kit text — see single-sourcing below) and any narrative on the
  project page. Agents scaffold structure only, never draft this text — not
  even placeholder text.
- **Agent builds:** folder structure, build script, symlink/site wiring, and
  `validation.json` (machine-readable data extracted from
  `public/data/runs/run-3-fable-ladder-results.json` — numbers, not prose).
- **Hybrid — the prompt file:** `transcription-prompt.txt` is read by Claude,
  not by humans. Its text is Sarah's approved Rung 1 contract; the agent makes
  only the mechanical chat adaptation (below), and Sarah approves the adapted
  wording verbatim before anything ships.

## Prompt chat adaptation

The experimental prompt assumes a file-based agent (`${dir}/image.jpg`, save
to `${dir}/out/text.txt`). The kit version changes only the mechanics:

- Input: the image the user has uploaded to the chat (no file paths).
- Output: the transcription as the reply, nothing else.
- All editorial rules (spelling/lineation preservation, superscripts,
  abbreviation expansion, thorn, ampersands, strikethrough, uncertainty
  markers `[word?]` / `[b....es]` / `[...]`, no-guessing rule, no commentary)
  carry over verbatim.

Changes are presented to Sarah as a diff against the original for approval.

## Structure

```
projects/teaching-machines-to-read/
├── kit/                          # source of truth (not served)
│   ├── fable-5/
│   │   ├── README.md             # Sarah's prose; single source for zip README
│   │   │                         #   AND the site kit text
│   │   ├── transcription-prompt.txt
│   │   └── validation.json       # generated from run-3 ladder results
│   └── build-kit.sh              # packages a named kit → public/kit/
└── public/
    └── kit/                      # served via existing symlink convention at
        │                         #   daggerobelus.com/projects/teaching-machines-to-read/kit/
        ├── tmtr-fable-5-kit.zip  # README + prompt + validation.json
        ├── fable-5-transcription-prompt.txt   # standalone copy-paste version
        └── fable-5-validation.json            # for the page to render numbers
```

`build-kit.sh` takes the kit folder name (`fable-5`) so future kits reuse it;
it is the only shared machinery across kits. Rerunning it re-syncs zip and
standalone files from source. It should fail loudly if README.md is missing
or empty rather than shipping a kit without instructions.

## validation.json (generated)

Keyed by what it documents: model (`claude-fable-5`), run id (3-ladder),
dates, method (rung1 editorial contract), and per-manuscript per-agent strict
and lenient CER plus means, and cost-per-page figures — extracted from
`public/data/runs/run-3-fable-ladder-results.json` (rung1 cells only, plus
the scoring definitions line). No interpretation, no prose fields beyond
labels.

## Site integration

- Kit section on the project page (`site/src/content/projects/teaching-machines-to-read.mdx`),
  presenting kits as a list of one: "Transcription kit for Claude Fable 5."
- The section renders Sarah's `kit/fable-5/README.md` (single source). MDX can
  import/include it; exact mechanism (import vs. symlink vs. build-script
  copy into `public/kit/`) decided at implementation based on the Astro
  setup — whatever preserves single-source editing.
- Copy-paste prompt block + zip download link + optionally rendered
  validation numbers.
- Component/visual treatment is Jack's layer (Semantic UI web components);
  keep the MDX clean and structural.

## Facts Sarah's README should have available (her call how/whether to use)

- Validation numbers are from Claude Fable 5, July 2026; users on claude.ai
  may be running a different model, and results will differ.
- Strict vs. lenient CER meaning; what 2–4% CER looks like in practice.
- Image-quality guidance exists as a finding (resolution limits were the
  bottleneck on Brumwich/Jane Jackson historically).

## Versioning

- Within this kit: v1 now; v1.x for prompt revisions. Version + date stamped
  in README (Sarah's text) and validation.json (generated).
- New models: new kit folders with whatever steps suit them.

## Out of scope for v1

- Sample manuscript image in the zip (licensing check on Folger/FromThePage
  images not done; revisit if Sarah wants one).
- CER evaluation tooling for users.
- Claude Code skill / technical tier.
- GitHub mirror (possible later; site is the front door).
- Sarah's public-sourced paleography guide (future kit version).

## Success criteria

- A scholar can go from the kit page to a transcription in one claude.ai
  session with no tooling.
- Everything human-read on the page and in the zip is Sarah's writing.
- `build-kit.sh fable-5` reproduces the served artifacts from source exactly.
- Nothing Folger-derived ships.
