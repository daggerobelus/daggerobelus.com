# Mental Model: daggerobelus.com

## Site Identity

**Name Origin:** "Daggerobelus" references typographical symbols—the dagger (†) and obelus (÷)—marks traditionally used by scribes and editors to annotate texts, flag questionable passages, or indicate critical apparatus.

**What it is:** A personal site featuring in-depth explorations of interesting topics, powered by NLP, data analysis, and interactive visualizations.

---

## Repository Structure

```
/
├── site/                 # daggerobelus.com (Astro + Semantic UI web components)
│   ├── public/projects/  # Symlinked project assets
│   └── src/content/      # Symlinked content files
├── projects/             # Individual projects (research, data, analysis)
│   └── witchcraft/       # Lorraine witch trials analysis
└── ai/                   # AI collaboration context
    ├── context/          # Mental models, project understanding
    ├── plans/            # Implementation plans
    └── research/         # Background research, notes
```

---

## Projects

Each project in `/projects/` is self-contained with its own data, analysis pipelines, and outputs.

### witchcraft
Analysis of the Lorraine witch trials archive—social network dynamics, trial outcomes, and historical patterns. See `/projects/witchcraft/docs/CLAUDE.md` for details.

---

## Design Principles

1. **Reproducibility** — Clear separation of raw data → processing → outputs
2. **Modularity** — Each project follows a consistent structure
3. **Integration** — Public outputs symlinked to site for seamless publishing
4. **Documentation** — Each project self-documents its provenance and methods

---

## Technical Approach

Projects may incorporate:
- NLP entity extraction and relationship mapping
- Network analysis and graph visualizations
- Statistical modeling and predictive analysis
- Interactive data explorations
