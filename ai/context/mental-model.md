# Mental Model: daggerobelus.com

## Site Identity

**Name Origin:** "Daggerobelus" references typographical symbols—the dagger (†) and obelus (÷)—marks traditionally used by scribes and editors to annotate texts, flag questionable passages, or indicate critical apparatus. This connects to the site's focus on textual analysis and digital humanities work on historical documents.

**Purpose:** Academic work showcase, primarily supporting coursework in English/Digital Humanities.

**Audience:** Academic peers—historians, digital humanities scholars, researchers.

---

## Owner Context

- **Field:** English / Digital Humanities
- **Approach:** Computational methods applied to historical texts and archives
- **Current focus:** Course projects with potential to expand

---

## Active Projects

### Witchcraft (Lorraine Witch Trials)

**Source:** 368 digitized trial records from the Lorraine region (16th-17th century France)—one of Europe's richest witch trial archives.

**Status:** Course project, 157 trials extracted (42.7% complete)

**Research Questions:**
1. **Social network dynamics** — How did accusations spread through communities? Who were the "super-witnesses" and brokers?
2. **Gender and power** — Who was accused and why? What patterns emerge in targeting?
3. **Legal/procedural history** — How did trials function? What determined outcomes (death vs. survival)?

**Methods:**
- NLP extraction from PDFs to structured JSON
- Entity resolution and relationship mapping
- Social network analysis (centrality, clustering, temporal evolution)
- Statistical modeling (logistic regression, ERGM)
- Contagion/cascade modeling

**Key Outputs:**
- Network graphs (GraphML)
- Interactive dashboard
- Publication-ready figures
- Derived datasets (CSV)

---

## Site Architecture

```
daggerobelus.com/
├── site/                 # Astro frontend
│   ├── public/projects/  # Symlinked project assets
│   └── src/content/      # Symlinked content files
├── projects/             # Data analysis projects
│   ├── TEMPLATE.md       # Reusable structure for new corpora
│   └── witchcraft/       # Active project
└── ai/                   # AI collaboration context
    ├── context/          # Mental models, project understanding
    ├── plans/            # Implementation plans
    └── research/         # Background research, notes
```

---

## Design Principles

1. **Reproducibility** — Clear separation of raw data → processing → outputs
2. **Modularity** — Each corpus follows the same template structure
3. **Integration** — Public outputs symlinked to site for seamless publishing
4. **Documentation** — Each project self-documents its provenance and methods

---

## Future Directions

- Additional historical corpora (TBD)
- Expanding extraction coverage (remaining 211 trials)
- Refining network analysis methods
- Building out site with project pages and visualizations

---

## Working Style Notes

- Prefers plain folder names over numbered prefixes
- Values clean, reproducible data pipelines
- Academic audience = careful sourcing and methodology
- Comfortable with Python, data analysis tools
- New to some git/dev workflows (learning as we go)
