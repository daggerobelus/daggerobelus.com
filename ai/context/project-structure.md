# Project Structure

Standard folder structure for projects and their integration with the site.

## Creating a New Project

```bash
# Replace {name} with your project name (e.g., inquisition, plague_records)
mkdir -p projects/{name}/{ingest/{archive,references},extracted/{trials,derived,schema},outputs,public/{figures,data,dashboard}}

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
├── extracted/                 # Structured data from NLP extraction
│   ├── trials/                # Individual record JSONs
│   ├── derived/               # Aggregated/computed CSVs
│   └── schema/                # JSON schema definitions
│
├── outputs/                   # Analysis results (intermediate, not web-ready)
│
├── public/                    # Web-ready outputs (symlinked to site/)
│   ├── figures/               # PNG/SVG visualizations
│   ├── data/                  # JSON/CSV for web consumption
│   └── dashboard/             # Interactive HTML/JS
│
├── CLAUDE.md                  # AI context for this project
│
└── {name}.md                  # Content file for site (symlinked)
```

## Data Flow

```
ingest/  →  [NLP extraction]  →  extracted/
                                     ↓
                              [analysis]
                                     ↓
                                 outputs/
                                     ↓
                              [visualization]
                                     ↓
                                 public/  →  site/
```

## Site Integration

Each project has two symlinks to the site:

1. **Public assets**: `site/public/projects/{name}/` → `projects/{name}/public/`
   - Served at: `https://daggerobelus.com/projects/{name}/`

2. **Content file**: `site/src/content/projects/{name}.md` → `projects/{name}/{name}.md`
   - Used by Astro content collections for page generation

## Content File Schema

Defined in `site/src/content/config.ts`. Frontmatter fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | yes | Project name |
| `description` | string | yes | Short description for SEO/cards |
| `publishDate` | date | yes | When first published |
| `updatedDate` | date | no | Last modified date |
| `image` | string | no | Hero/card image path |
| `imageAlt` | string | no | Image alt text |
| `status` | enum | no | `draft`, `in-progress`, `published` (default) |
| `tags` | string[] | no | For categorization |
| `featured` | boolean | no | Highlight on homepage (default: false) |

Example:

```markdown
---
title: "Project Title"
description: "Brief description for SEO and previews"
publishDate: 2024-12-18
status: in-progress
tags: ["network-analysis", "history"]
featured: true
---

# Project Title

Overview and findings...
```
