# Historical Corpus Project Template

This is the standard folder structure for historical corpus data analysis projects.

## Creating a New Project

```bash
# Replace {name} with your project name (e.g., inquisition, plague_records)
mkdir -p projects/{name}/{ingest/{archive,references},extracted/{trials,derived,schema},pipeline/{extraction,analysis,viz},outputs/{entities,edges,networks,metrics,models,temporal,robustness},public/{figures,data,dashboard},docs}

# Create symlinks to site
ln -s ../../../projects/{name}/public site/public/projects/{name}
ln -s ../../../../projects/{name}/{name}.md site/src/content/projects/{name}.md
```

## Folder Structure

```
projects/{name}/
│
├── ingest/                    # Raw source materials (read-only after import)
│   ├── archive/               # Primary source documents (PDFs, images)
│   └── references/            # Secondary sources, indexes, research papers
│
├── extracted/                 # Structured data from NLP/extraction
│   ├── trials/                # Individual record JSONs
│   ├── derived/               # Aggregated/computed CSVs
│   └── schema/                # JSON schema definitions
│
├── pipeline/                  # All processing code
│   ├── extraction/            # Source → JSON scripts
│   ├── analysis/              # Analysis modules
│   └── viz/                   # Visualization scripts
│
├── outputs/                   # Intermediate analysis results
│   ├── entities/              # Canonical entities, mappings
│   ├── edges/                 # Relationship edge lists
│   ├── networks/              # GraphML/graph files
│   ├── metrics/               # Centrality, statistics
│   ├── models/                # Regression, statistical models
│   ├── temporal/              # Time-series analysis
│   └── robustness/            # Validation results
│
├── public/                    # Web-ready outputs (symlinked to site/)
│   ├── figures/               # PNG/SVG visualizations
│   ├── data/                  # JSON/CSV for web consumption
│   └── dashboard/             # Interactive HTML/JS
│
├── docs/                      # Project documentation
│   ├── README.md              # Project overview, data provenance
│   └── ...                    # Additional documentation
│
└── {name}.md                  # Content file for site (symlinked)
```

## Data Flow

```
ingest/          →  pipeline/extraction/  →  extracted/
                                               ↓
                    pipeline/analysis/    ←───┘
                           ↓
                       outputs/
                           ↓
                    pipeline/viz/         →  public/  →  site/
```

## Site Integration

Each project has two symlinks to the site:

1. **Public assets**: `site/public/projects/{name}/` → `projects/{name}/public/`
   - Served at: `https://daggerobelus.com/projects/{name}/`

2. **Content file**: `site/src/content/projects/{name}.md` → `projects/{name}/{name}.md`
   - Used by Astro content collections for page generation

## Content File Template

```markdown
---
title: "Project Title"
description: "Brief description for SEO and previews"
date: YYYY-MM-DD
---

# Project Title

Overview of the project...

## Data Overview

- **N** source documents
- **N** extracted records
- ...

## Analysis Pipeline

1. Step one
2. Step two
...

## Key Findings

Summary or link to dashboard.
```
