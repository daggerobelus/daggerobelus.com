# Fable 5 Transcription Kit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the downloadable Fable 5 manuscript-transcription kit (top-level `tools/` area + "Tools" site section) per `docs/superpowers/specs/2026-07-20-fable-5-transcription-kit-design.md`.

**Architecture:** Kit source of truth at `tools/fable-5-transcription-kit/` (README single-sources the site page and the zip README; validation.json generated from the run 3-ladder results). A shared `tools/build-kit.sh` packages served artifacts into the kit's `public/` folder, symlinked into the Astro site alongside a new `tools` content collection, listing page, tool page, and nav entry.

**Tech Stack:** bash, python3 (stdlib only), Astro content collections (site already uses Astro + Tailwind classes).

## Global Constraints

- **Content policy (repo CLAUDE.md):** all human-read prose published on the site must be authored by Sarah. Agents create structure, scripts, data, and metadata only. NO placeholder or sample prose anywhere that publishes. UI labels must be minimal ("Download", section-less) and are subject to Sarah's edit.
- **Provenance:** nothing Folger-derived ships. The kit prompt derives ONLY from `ingest/archive/test/fable-ladder-2026-07/kits/rung-1-editorial-contract/prompt-template.txt` (Sarah-approved 2026-07-06).
- **Human approval gate:** the chat-adapted prompt text must be approved verbatim by Sarah before its commit (Task 3).
- **README stub ships with `status: draft`** so nothing publishes until Sarah writes the body and flips status.
- The kit is model-specific: no generic "the kit" naming; filenames carry `fable-5`.
- Site work follows existing patterns (`src/pages/projects/[slug].astro`, `Header.astro` navItems, per-item public symlinks). No new dependencies.
- Repo root for all paths below: `/Users/sarahbonanno/daggerobelus.com`.

---

### Task 1: Kit source scaffold + README stub + docs

**Files:**
- Create: `tools/fable-5-transcription-kit/README.md`
- Create: `tools/fable-5-transcription-kit/public/.gitkeep`
- Modify: `CLAUDE.md` (repo root, Structure list)

**Interfaces:**
- Produces: `tools/fable-5-transcription-kit/` folder consumed by every later task; README frontmatter fields `title`, `publishDate`, `status`, `download`, `promptFile` consumed by the site collection (Task 5) and pages (Tasks 6–7).

- [ ] **Step 1: Create the kit folder and README stub (frontmatter only, draft status, empty body for Sarah)**

Write `tools/fable-5-transcription-kit/README.md` with exactly:

```markdown
---
title: "Fable 5 Transcription Kit"
publishDate: 2026-07-20
status: draft
download: fable-5-transcription-kit.zip
promptFile: fable-5-transcription-prompt.txt
---
```

(No body. Sarah authors the body and a `description:` field; the kit cannot build and the page cannot publish until she does.)

- [ ] **Step 2: Create the public output folder placeholder**

```bash
mkdir -p tools/fable-5-transcription-kit/public
touch tools/fable-5-transcription-kit/public/.gitkeep
```

- [ ] **Step 3: Document the tools area in the root CLAUDE.md**

In `CLAUDE.md` (repo root), in the "### Structure" list that currently reads:

```markdown
- `/ai/` - AI context and documentation
- `/projects/` - Individual projects (research, data, analysis pipelines)
- `/site/` - daggerobelus.com (built with Semantic UI web components)
```

add a line so it reads:

```markdown
- `/ai/` - AI context and documentation
- `/projects/` - Individual projects (research, data, analysis pipelines)
- `/tools/` - Downloadable public tool kits (model-specific; spec: docs/superpowers/specs/2026-07-20-fable-5-transcription-kit-design.md)
- `/site/` - daggerobelus.com (built with Semantic UI web components)
```

- [ ] **Step 4: Verify**

```bash
ls tools/fable-5-transcription-kit/ && head -8 tools/fable-5-transcription-kit/README.md
```

Expected: `README.md  public`, and the frontmatter block above.

- [ ] **Step 5: Commit**

```bash
git add tools/ CLAUDE.md
git commit -m "feat(tools): scaffold fable-5 transcription kit source folder"
```

---

### Task 2: validation.json generator

**Files:**
- Create: `tools/fable-5-transcription-kit/generate-validation.py`
- Create (generated): `tools/fable-5-transcription-kit/validation.json`

**Interfaces:**
- Consumes: `projects/teaching-machines-to-read/public/data/runs/run-3-fable-ladder-results.json` (existing; keys `run`, `rungs.rung1_rules`).
- Produces: `tools/fable-5-transcription-kit/validation.json` with top-level keys `kit`, `kit_version`, `model`, `method`, `source_run`, `scoring`, `n_agents_per_manuscript`, `mean_cost_per_page_usd_cached`, `results` (per-manuscript `{agents, strict_mean, lenient_mean}`). Consumed by build-kit.sh (Task 4) and optionally the tool page.

- [ ] **Step 1: Write the generator**

`tools/fable-5-transcription-kit/generate-validation.py`:

```python
#!/usr/bin/env python3
"""Generate validation.json for the Fable 5 transcription kit.

Extracts the rung 1 (editorial contract) cells from the run 3-ladder
results — the condition this kit ships. Data only; no prose fields.
"""
import json
from pathlib import Path

KIT_DIR = Path(__file__).resolve().parent
REPO = KIT_DIR.parents[1]
SRC = (
    REPO
    / "projects/teaching-machines-to-read/public/data/runs/run-3-fable-ladder-results.json"
)

data = json.loads(SRC.read_text())
run = data["run"]
rung1 = data["rungs"]["rung1_rules"]

results = {}
for ms, agents in rung1["cells"].items():
    strict = [a["strict"] for a in agents]
    lenient = [a["lenient"] for a in agents]
    results[ms] = {
        "agents": agents,
        "strict_mean": round(sum(strict) / len(strict), 2),
        "lenient_mean": round(sum(lenient) / len(lenient), 2),
    }

out = {
    "kit": "fable-5-transcription-kit",
    "kit_version": "1.0",
    "model": run["model"],
    "method": "rung-1-editorial-contract",
    "source_run": {"id": run["id"], "name": run["name"], "dates": run["dates"]},
    "scoring": run["scoring"],
    "n_agents_per_manuscript": rung1["n_per_ms"],
    "mean_cost_per_page_usd_cached": rung1["mean_cost_per_page_usd_cached"],
    "results": results,
}

out_path = KIT_DIR / "validation.json"
out_path.write_text(json.dumps(out, indent=1) + "\n")
print(f"Wrote {out_path}")
```

- [ ] **Step 2: Run it**

```bash
python3 tools/fable-5-transcription-kit/generate-validation.py
```

Expected: `Wrote /Users/sarahbonanno/daggerobelus.com/tools/fable-5-transcription-kit/validation.json`

- [ ] **Step 3: Verify values against the source data**

```bash
python3 - <<'EOF'
import json
v = json.load(open("tools/fable-5-transcription-kit/validation.json"))
assert v["model"] == "claude-fable-5"
assert v["n_agents_per_manuscript"] == 3
assert v["results"]["henslow"]["strict_mean"] == 2.18
assert v["results"]["sedley"]["strict_mean"] == 2.72
assert v["results"]["brumwich"]["strict_mean"] == 4.07
assert v["results"]["jane-jackson"]["lenient_mean"] == 2.58
assert len(v["results"]) == 5
print("validation.json OK")
EOF
```

Expected: `validation.json OK`

- [ ] **Step 4: Commit**

```bash
git add tools/fable-5-transcription-kit/generate-validation.py tools/fable-5-transcription-kit/validation.json
git commit -m "feat(tools): generate fable-5 kit validation data from run 3-ladder results"
```

---

### Task 3: Chat-adapted transcription prompt (HUMAN APPROVAL GATE)

**Files:**
- Create: `tools/fable-5-transcription-kit/transcription-prompt.txt`

**Interfaces:**
- Consumes: `projects/teaching-machines-to-read/ingest/archive/test/fable-ladder-2026-07/kits/rung-1-editorial-contract/prompt-template.txt` (read-only source).
- Produces: `transcription-prompt.txt` consumed by build-kit.sh (Task 4) and rendered by the tool page (Task 7).

- [ ] **Step 1: Write the adapted prompt file**

`tools/fable-5-transcription-kit/transcription-prompt.txt` — the Rung 1 contract with ONLY the file-mechanics lines adapted for chat (rules verbatim):

```text
Perform image-to-text analysis on the manuscript image attached to this message.

Reply with only the text content of the image, following these conventions:
- Keep the original spelling, punctuation, capitalization, and line breaks exactly as written — including u/v and i/j usage, and ff for capital F. Do not modernize anything.
- Silently lower superscript letters (w^th → wth).
- Expand abbreviations, supplying the omitted letters according to how the writer spells the word elsewhere on the page, not modern spelling.
- Where a y-shaped character stands for "th" (as in y^e = the, y^t = that), write th.
- Preserve ampersands (& and &c.) as they appear. Show struck-through words with ~~strikethrough~~.
- Where you cannot read something: use [word?] for an uncertain but visible reading, [b....es] with dots for partly visible letters, and [...] where nothing is traceable. Never fill a gap by guessing from context — an honest gap is better than a plausible word.
- Add no headings, notes, descriptions, or commentary of any kind.
```

Changes vs. the original, and the ONLY changes:
- Line 1: `the following image: ${dir}/image.jpg. Save the resulting text to ${dir}/out/text.txt.` → `the manuscript image attached to this message.`
- Line 3: `The file must contain only the text content of the image, following these conventions:` → `Reply with only the text content of the image, following these conventions:`

- [ ] **Step 2: STOP — present the diff to Sarah and wait for her verbatim approval**

Show her:

```bash
diff "projects/teaching-machines-to-read/ingest/archive/test/fable-ladder-2026-07/kits/rung-1-editorial-contract/prompt-template.txt" "tools/fable-5-transcription-kit/transcription-prompt.txt"
```

Do NOT proceed to Step 3 until Sarah approves the adapted wording. If she edits, her wording wins verbatim.

- [ ] **Step 3: Commit (only after approval)**

```bash
git add tools/fable-5-transcription-kit/transcription-prompt.txt
git commit -m "feat(tools): chat-adapted rung-1 transcription prompt (Sarah-approved wording)"
```

---

### Task 4: build-kit.sh

**Files:**
- Create: `tools/build-kit.sh` (mode 755)

**Interfaces:**
- Consumes: a kit folder `tools/<kit>/` containing `README.md` (frontmatter + non-empty body), `transcription-prompt.txt`, `validation.json`.
- Produces: `tools/<kit>/public/<kit>.zip` (README.md with frontmatter stripped + transcription-prompt.txt + validation.json), `tools/<kit>/public/<model>-transcription-prompt.txt`, `tools/<kit>/public/<model>-validation.json`, where `<model>` = `<kit>` minus the `-transcription-kit` suffix.

- [ ] **Step 1: Write the script**

`tools/build-kit.sh`:

```bash
#!/usr/bin/env bash
# Package a kit folder's shippable artifacts into its public/ directory.
# Usage: build-kit.sh <kit-folder-name>   e.g. build-kit.sh fable-5-transcription-kit
set -euo pipefail

KIT="${1:?usage: build-kit.sh <kit-folder-name>}"
TOOLS_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC="$TOOLS_DIR/$KIT"
PUB="$SRC/public"
MODEL="${KIT%-transcription-kit}"

[ -d "$SRC" ] || { echo "ERROR: no kit folder at $SRC" >&2; exit 1; }
for f in README.md transcription-prompt.txt validation.json; do
  [ -s "$SRC/$f" ] || { echo "ERROR: missing or empty $SRC/$f" >&2; exit 1; }
done

strip_frontmatter() {
  awk 'NR==1 && $0=="---" {infm=1; next}
       infm && $0=="---" {infm=0; next}
       !infm {print}' "$1"
}

# A kit must not ship without human-authored instructions.
BODY_NONWS="$(strip_frontmatter "$SRC/README.md" | tr -d '[:space:]')"
[ -n "$BODY_NONWS" ] || {
  echo "ERROR: README.md body is empty — the kit cannot ship without instructions" >&2
  exit 1
}

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

strip_frontmatter "$SRC/README.md" | sed '/./,$!d' > "$STAGE/README.md"
cp "$SRC/transcription-prompt.txt" "$STAGE/transcription-prompt.txt"
cp "$SRC/validation.json" "$STAGE/validation.json"

mkdir -p "$PUB"
rm -f "$PUB/$KIT.zip"
(cd "$STAGE" && zip -q "$PUB/$KIT.zip" README.md transcription-prompt.txt validation.json)
cp "$SRC/transcription-prompt.txt" "$PUB/$MODEL-transcription-prompt.txt"
cp "$SRC/validation.json" "$PUB/$MODEL-validation.json"

echo "Built $PUB/$KIT.zip"
echo "Synced $PUB/$MODEL-transcription-prompt.txt and $PUB/$MODEL-validation.json"
```

```bash
chmod 755 tools/build-kit.sh
```

- [ ] **Step 2: Test the empty-README guard on the real kit (expected failure)**

```bash
tools/build-kit.sh fable-5-transcription-kit; echo "exit=$?"
```

Expected: `ERROR: README.md body is empty — the kit cannot ship without instructions` and `exit=1`. (Sarah hasn't written the body yet — this failure is the guard working.)

- [ ] **Step 3: Test the happy path with a throwaway fixture kit**

```bash
FIX=tools/zz-test-transcription-kit
mkdir -p "$FIX"
printf -- '---\ntitle: "x"\npublishDate: 2026-07-20\n---\nBody line for testing only. Never published.\n' > "$FIX/README.md"
printf 'prompt text\n' > "$FIX/transcription-prompt.txt"
printf '{"kit": "zz-test"}\n' > "$FIX/validation.json"
tools/build-kit.sh zz-test-transcription-kit
unzip -l "$FIX/public/zz-test-transcription-kit.zip"
unzip -p "$FIX/public/zz-test-transcription-kit.zip" README.md
ls "$FIX/public/"
rm -rf "$FIX"
```

Expected: zip lists exactly `README.md  transcription-prompt.txt  validation.json`; the extracted README shows ONLY `Body line for testing only. Never published.` (frontmatter stripped, no leading blank lines); `public/` contains the zip plus `zz-test-transcription-prompt.txt` and `zz-test-validation.json`. Fixture is deleted at the end.

- [ ] **Step 4: Commit**

```bash
git add tools/build-kit.sh
git commit -m "feat(tools): kit build script (zip + standalone artifacts, empty-README guard)"
```

---

### Task 5: Site content collection + symlinks

**Files:**
- Modify: `site/src/content/config.ts`
- Create (symlink): `site/src/content/tools/fable-5-transcription-kit.md`
- Create (symlink): `site/public/tools/fable-5-transcription-kit`

**Interfaces:**
- Consumes: README frontmatter from Task 1.
- Produces: `tools` content collection (schema below) consumed by Tasks 6–7; served path `/tools/fable-5-transcription-kit/<file>` for the public artifacts.

- [ ] **Step 1: Add the tools collection to `site/src/content/config.ts`**

After the `chapters` collection definition, add:

```ts
const tools = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string().optional(),
    publishDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    status: z.enum(['draft', 'published']).default('published'),
    download: z.string().optional(),
    promptFile: z.string().optional(),
  }),
});
```

and change the export line from:

```ts
export const collections = { projects, chapters };
```

to:

```ts
export const collections = { projects, chapters, tools };
```

- [ ] **Step 2: Create the symlinks (mirroring the projects convention)**

```bash
mkdir -p site/src/content/tools site/public/tools
ln -s ../../../../tools/fable-5-transcription-kit/README.md site/src/content/tools/fable-5-transcription-kit.md
ln -s ../../../tools/fable-5-transcription-kit/public site/public/tools/fable-5-transcription-kit
```

- [ ] **Step 3: Verify the symlinks resolve**

```bash
ls -la site/src/content/tools/ site/public/tools/
head -3 site/src/content/tools/fable-5-transcription-kit.md
```

Expected: both symlinks listed with their targets; `head` prints the frontmatter opening (`---`, `title: "Fable 5 Transcription Kit"`).

- [ ] **Step 4: Verify the site still builds with the new collection**

```bash
cd site && npm run build
```

Expected: build succeeds (exit 0). The draft tool generates no listing entry yet.

- [ ] **Step 5: Commit**

```bash
cd /Users/sarahbonanno/daggerobelus.com
git add site/src/content/config.ts site/src/content/tools site/public/tools
git commit -m "feat(site): tools content collection + symlinks for fable-5 kit"
```

---

### Task 6: Tools listing page + nav entry

**Files:**
- Create: `site/src/pages/tools/index.astro`
- Modify: `site/src/components/Header.astro` (navItems array)

**Interfaces:**
- Consumes: `tools` collection (Task 5).
- Produces: `/tools/` route; nav "Tools" entry.

- [ ] **Step 1: Create `site/src/pages/tools/index.astro`**

```astro
---
import { getCollection } from 'astro:content';
import BaseLayout from '../../layouts/BaseLayout.astro';

const tools = (await getCollection('tools'))
  .filter(t => t.data.status !== 'draft')
  .sort((a, b) => b.data.publishDate.valueOf() - a.data.publishDate.valueOf());
---

<BaseLayout title="Tools" description="Tools" compact={true}>
  <section class="max-w-content mx-auto px-6 md:px-10 pt-10 md:pt-14 pb-20">
    <h1 class="max-w-3xl">Tools</h1>
    {/* Intro copy slot — Sarah-authored only; leave empty until she writes it. */}
    <ul class="max-w-3xl list-none p-0">
      {tools.map(tool => (
        <li class="mt-8">
          <a href={`/tools/${tool.slug}/`} class="no-underline">
            <h2>{tool.data.title}</h2>
          </a>
          {tool.data.description && <p>{tool.data.description}</p>}
        </li>
      ))}
    </ul>
  </section>
</BaseLayout>
```

(Check `BaseLayout.astro`'s actual Props during implementation — if `description` is optional, omit it rather than passing filler; if `image` is required anywhere, follow the existing pages' usage. Match `index.astro`/`about.astro` conventions for the section wrapper classes if they differ from the above.)

- [ ] **Step 2: Add the nav entry in `site/src/components/Header.astro`**

Change:

```ts
const navItems: NavItem[] = [
  { href: '/', label: 'Projects', activePrefixes: ['/projects'] },
  { href: '/about/', label: 'About' },
  { href: '/method/', label: 'Methodology' },
];
```

to:

```ts
const navItems: NavItem[] = [
  { href: '/', label: 'Projects', activePrefixes: ['/projects'] },
  { href: '/tools/', label: 'Tools' },
  { href: '/about/', label: 'About' },
  { href: '/method/', label: 'Methodology' },
];
```

- [ ] **Step 3: Build and verify the route**

```bash
cd site && npm run build && ls dist/tools/
```

Expected: build succeeds; `dist/tools/index.html` exists. (Listing body is empty of tools while the kit is a draft — correct.)

- [ ] **Step 4: Commit**

```bash
cd /Users/sarahbonanno/daggerobelus.com
git add site/src/pages/tools/index.astro site/src/components/Header.astro
git commit -m "feat(site): tools listing page and nav entry"
```

---

### Task 7: Tool page

**Files:**
- Create: `site/src/pages/tools/[slug].astro`

**Interfaces:**
- Consumes: `tools` collection; served files under `site/public/tools/<slug>/` (`download` and `promptFile` frontmatter fields name them).
- Produces: `/tools/<slug>/` route rendering Sarah's README as the page body, plus prompt block and download link when the built artifacts exist.

- [ ] **Step 1: Create `site/src/pages/tools/[slug].astro`**

```astro
---
import { getCollection } from 'astro:content';
import fs from 'node:fs';
import path from 'node:path';
import BaseLayout from '../../layouts/BaseLayout.astro';

export async function getStaticPaths() {
  const tools = await getCollection('tools');
  return tools.map(tool => ({ params: { slug: tool.slug }, props: { tool } }));
}

const { tool } = Astro.props;
const { title, description, download, promptFile } = tool.data;
const { Content } = await tool.render();

// Render the copy-paste prompt block only when the built artifact exists.
let promptText: string | null = null;
if (promptFile) {
  const promptPath = path.resolve('public/tools', tool.slug, promptFile);
  if (fs.existsSync(promptPath)) {
    promptText = fs.readFileSync(promptPath, 'utf-8');
  }
}

const zipPath = download ? path.resolve('public/tools', tool.slug, download) : null;
const downloadHref =
  zipPath && fs.existsSync(zipPath) ? `/tools/${tool.slug}/${download}` : null;
---

<BaseLayout title={title} description={description ?? title} compact={true}>
  <article class="max-w-content mx-auto px-6 md:px-10 pt-10 md:pt-14 pb-20">
    <header class="max-w-3xl">
      <h1>{title}</h1>
    </header>

    <div class="max-w-3xl article-prose">
      <Content />
    </div>

    {promptText && (
      <section class="max-w-3xl mt-10">
        <pre class="overflow-x-auto whitespace-pre-wrap"><code>{promptText}</code></pre>
      </section>
    )}

    {downloadHref && (
      <p class="max-w-3xl mt-6">
        <a href={downloadHref} download>Download</a>
      </p>
    )}
  </article>
</BaseLayout>
```

(During implementation, match the article wrapper/prose classes used by `src/pages/projects/[slug].astro` — e.g. if the prose container there uses a specific class like `article-prose` or a component, reuse it verbatim so Jack's styling applies. The `Download` label is deliberate minimal UI copy; Sarah may reword.)

- [ ] **Step 2: Build and verify**

```bash
cd site && npm run build && ls dist/tools/fable-5-transcription-kit/
```

Expected: build succeeds; `dist/tools/fable-5-transcription-kit/index.html` exists (draft pages still build — drafts are only excluded from the listing). No prompt block or download link yet since `public/` artifacts aren't built — the fs.existsSync guards handle that.

- [ ] **Step 3: Verify the page renders the prompt once artifacts exist (dry check via fixture)**

Not applicable until Task 3's prompt is approved and Sarah's README exists — the guards make the page correct in both states. Confirm the guards by checking the built HTML contains the title but no `<pre>`:

```bash
grep -c "<pre" dist/tools/fable-5-transcription-kit/index.html || true
```

Expected: `0`

- [ ] **Step 4: Commit**

```bash
cd /Users/sarahbonanno/daggerobelus.com
git add site/src/pages/tools/\[slug\].astro
git commit -m "feat(site): tool page rendering README, prompt block, and download link"
```

---

### Task 8: Handoff checklist (blocked on Sarah's writing — do not automate)

**Files:** none created by agents.

The ship sequence once Sarah writes:

- [ ] Sarah authors the README body + `description:` frontmatter in `tools/fable-5-transcription-kit/README.md` (this is simultaneously the site page text and the zip README)
- [ ] Sarah flips `status: draft` → `status: published`
- [ ] Sarah approves the prompt diff if Task 3's gate is still open
- [ ] Run `tools/build-kit.sh fable-5-transcription-kit` — must succeed and report the three artifacts
- [ ] `cd site && npm run build` — tool appears in `/tools/` listing; page shows her text, the prompt block, and the download link (`grep -c "<pre" dist/tools/fable-5-transcription-kit/index.html` now returns `1`)
- [ ] Commit `tools/fable-5-transcription-kit/public/` artifacts and any README changes
- [ ] Coordinate with Jack on nav/menu visual treatment (his Semantic UI layer)

## Self-Review Notes

- Spec coverage: structure (T1), validation data (T2), prompt + approval gate (T3), build script + empty-README guard (T4), collection/symlinks (T5), Tools menu + listing (T6), tool page + single-source README rendering (T7), ship gate + Jack coordination (T8). Sample image / eval tooling / GitHub mirror: out of scope per spec — no tasks, correct.
- Content policy: the only prose agents write is agent-facing (CLAUDE.md line, code comments) or minimal UI labels flagged for Sarah; README stub is frontmatter-only; fixture prose is deleted in-task and never published.
- Naming consistency: `fable-5-transcription-kit` slug used identically in Tasks 1, 2, 4, 5, 6, 7; `MODEL` derivation (`fable-5`) matches the spec's served filenames.
