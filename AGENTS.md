# Agents

Project instructions for AI agents working on this codebase.

## Startup

On startup, check the current git user:
```bash
git config user.email
```

Then follow the user-specific instructions below.

---

## User: Jack Lukic

**Matches:** `user.email` is `jacklukic@gmail.com`

**Background:** Principal engineer and author of Semantic UI. Deep technical expertise across the full stack. Currently developing a new version of Semantic UI using web components, which will be used to implement components in the `/site/` folder.

**Domain knowledge:** Strong technical background. Relies on collaborators for subject matter expertise in humanities and research domains.

### Instructions for Jack

- Skip basic technical explanations—assume familiarity with advanced patterns, architectures, and tooling
- When discussing the historical/literary subject matter, provide context and explain domain-specific terminology
- For `/site/` work: Jack is implementing components using his new web components-based Semantic UI
- Be direct and concise; prefer code over lengthy explanations
- Can discuss tradeoffs at an architectural level

---

## User: Sarah Bonanno

**Matches:** `user.email` is `sarahbonanno@gmail.com`

**Background:** PhD student in English at the CUNY Graduate Center, specializing in early modern literature. Deep expertise in the historical and literary subject matter of this project.

**Domain knowledge:** Expert in early modern literature and humanities research methodology. New to programming—just learned git last week. No prior coding experience.

### Instructions for Sarah

- Explain technical concepts clearly and avoid jargon without definition
- Provide step-by-step guidance for git operations and command-line tasks
- When suggesting code changes, explain what the code does and why
- Leverage her expertise—ask for guidance on subject matter interpretation, historical context, and research methodology
- Be patient with technical questions; offer to explain further if something is unclear
- For git: remind about `git status` before commits, explain what commands will do before running them
- Prefer simple, readable code over clever optimizations

---

## Project Overview

**daggerobelus.com** is a personal site featuring in-depth explorations of interesting topics, powered by NLP, data analysis, and interactive visualizations.

### Structure

- `/ai/` - AI context and documentation
- `/projects/` - Individual projects (research, data, analysis pipelines)
- `/site/` - daggerobelus.com (built with Semantic UI web components)

### Technical Approach

Projects may incorporate:
- NLP entity extraction and relationship mapping
- Network analysis and graph visualizations
- Statistical modeling and predictive analysis
- Interactive data explorations

## General Guidelines

- Each project in `/projects/` is self-contained with its own data and analysis
- See `/ai/context/project-structure.md` for project folder conventions and site integration
