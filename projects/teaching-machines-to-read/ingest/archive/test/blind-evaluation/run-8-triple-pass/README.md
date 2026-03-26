# Run 8: Triple-Pass Consensus Method

## Method

Three independent transcription agents each transcribe all five manuscripts
using the alphabet-first method (Run 4 style — no vocabulary list). A fourth
reconciliation agent then merges the three passes into a consensus reading
using majority rule, and applies vocabulary verification only to the final
consensus.

This mirrors the EMROC triple-keying approach used for the highest-quality
human transcriptions.

## Structure

```
blind-test-run8/
├── README.md
├── pass-instructions.md          ← Shared instructions for all 3 passes
├── pass-1/                       ← Independent transcription agent 1
│   ├── instructions.md
│   ├── manuscripts/              ← Same 5 JPGs
│   └── guide/
│       └── paleography-guide.md  ← NO vocab list
├── pass-2/                       ← Independent transcription agent 2
│   └── (same structure)
├── pass-3/                       ← Independent transcription agent 3
│   └── (same structure)
└── reconciliation/               ← Reconciliation agent
    ├── instructions.md
    └── guide/
        └── vocab-reference.txt   ← Vocab ONLY available here
```

## Execution Order

1. Run pass-1, pass-2, and pass-3 in parallel (completely independent)
2. Copy all transcriptions into reconciliation/
3. Run reconciliation agent
4. Run CER evaluation
```
