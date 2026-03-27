# Run 13: Error Analysis Transfer — Cumulative Protocol

## Overview

Run 10 showed that an error protocol built from Henslow mistakes improved Sedley results. Run 12 showed that a Sedley-derived protocol did NOT help on the easier Henslow manuscript. This experiment tests whether **combining** error analyses from multiple manuscripts produces a stronger protocol that helps on a third, unseen manuscript.

**Question:** Does paleographic knowledge accumulate across manuscripts, or does adding more error data just add noise?

## Baselines

- **Brumwich MS160 best CER:** 9.30% (Run 4, alphabet-first method)
- **Henslow single-manuscript protocol → Sedley:** 13.65% (Run 10)

## Design

### Phase 1: Build Cumulative Protocol

A protocol-building agent receives error analyses from TWO different manuscripts:
- Henslow MS688 error analysis (from Run 10 — 5 agents, 25 systematic errors)
- Sedley MS534 error analysis (from Run 12 — 5 agents, 10 systematic errors)

The agent combines both analyses into a single cumulative protocol, identifying which error patterns appear in BOTH manuscripts (truly general problems) vs. which are manuscript-specific.

### Phase 2: Transcribe Brumwich with Cumulative Protocol (5 agents, blind)

Five agents transcribe Brumwich MS160 page 10 using:
- The self-taught guide (5-page version)
- The paleography guide
- The cumulative error protocol (from Phase 1)

### Phase 3: Evaluation

CER computed against the FromThePage reference for Brumwich.

## What We Compare

| Condition | Manuscript | CER |
|---|---|---|
| Run 4 baseline (alphabet-first, no protocol) | Brumwich | 9.30% |
| Run 13 (cumulative protocol from 2 manuscripts) | Brumwich | ? |

**If the cumulative protocol helps:** Paleographic knowledge accumulates. Studying errors across multiple manuscripts builds general expertise that transfers.

**If it doesn't help (or adds noise):** More data ≠ better. The protocols may become too long or too specific, overwhelming agents with warnings.

## Agent Isolation — CRITICAL

Same isolation rules as all previous runs. Each agent works in its own folder with only its authorized materials.
