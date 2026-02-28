# Project Plan: An Open-Source Model for Historical Recipe Book Transcription

## Core Principles

- **Open source** — all code, models, and documentation publicly available
- **Free to use** — no API costs or commercial dependencies
- **Reproducible** — any scholar can download, run, and build on this work
- **Benchmarked** — tested against commercial models to establish accuracy baselines

## Phase 1: Benchmarking with Claude

Test Claude's ability to interpret historical handwriting using a paleography guide as a reference. The goal is not to build on Claude, but to establish a performance ceiling — how accurate is a state-of-the-art commercial model at this task? This phase identifies what the hard problems are (specific letter forms, abbreviations, damage, etc.) and where AI struggles with manuscript images. These findings directly inform Phase 2.

## Phase 2: Building an Open-Source Model for Recipe Books

Using insights from Phase 1, fine-tune an open-source model specifically for historical recipe book transcription. This includes manuscript image parsing, recipe categorization, and structured formatting. Because the model is open and free, any scholar can use and adapt it — for recipe books or potentially other types of historical manuscripts.

## Phase 3: Pipeline Development

Build a reproducible, open-source pipeline around the model. A scholar with no ML background should be able to feed in manuscript images and get structured, transcribed output. All code hosted on GitHub with clear documentation.
