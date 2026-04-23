# Skill: Write prompts for the blended archival-editorial illustration style

## Goal

Write image prompts that reliably produce illustrations matching the
daggerobelus.com house style:

* **A blended aesthetic** combining:
  * a contemporary early-modern scholarly archive
  * a soft illustrated apartment-study interior
* **Editorial, literary, refined** rather than cinematic, glossy, or
  cartoonish
* **Soft watercolor-and-ink rendering** with tactile paper presence
* **Restrained, desaturated palette** with carefully controlled accents

The output of this skill should be a prompt that feels deliberate,
visual, and compositionally aware.

---

## Core principles (non-negotiable)

Before reading on, these are load-bearing rules that override style
considerations if they ever conflict:

1. **Real source material beats AI-generated historical text.** If a
   project depicts a specific manuscript, map, or artifact, the author
   must pass a reference scan (Henslowe diary, period recipe book,
   period map, botanical plate) to the generating agent and instruct
   it to integrate or reproduce that artifact faithfully. Synthetic
   "old handwriting" or invented period typography reads as fake at
   any zoom and undermines scholarly credibility. If no scan is
   available, change the subject — don't let the model hallucinate
   paleography.
2. **Upper-left title-safe zone.** Every hero image sits beside a
   headline on desktop. The upper-left quadrant is reserved as calm
   negative space (lavender stars are fine, focal elements are not).
   Never compose a focal element there.
3. **Aspect ratio and pixel dimensions matter.** Hero images render at
   exactly **4:3, 1600×1200 or larger**. About-page portraits render at
   4:5 portrait, 1200×1500 or larger. Producing an 800px-wide image
   forces a re-generation.
4. **At least one gold moment AND one blue moment per image** (see
   "Color discipline" below — the two accents carry distinct narrative
   jobs and the palette needs both to breathe).

---

## Core style identity

Every prompt should preserve this merged visual identity:

### Archive layer

Use cues from:

* early-modern manuscripts
* paleography and marginal annotation
* botanical specimen sheets
* cartographic fragments
* archival documents laid on paper
* engraved linework and aquatint-like shading
* subtle foxing, ink bleed, paper grain, laid-paper texture

This layer should suggest scholarship, history, paper, and intellectual
craft.

### Soft illustrated interior layer

Use cues from:

* a beautiful personal workspace or apartment study
* gentle watercolor washes
* thin hand-drawn ink outlines
* warm, intimate domestic objects
* airy negative space
* subtle whimsical celestial motifs (see "Lavender stars" below)
* soft pastel accents integrated into an editorial composition

This layer should suggest warmth, humanity, and approachability.

### Combined effect

The final image should feel:

* scholarly
* intimate
* literary
* humane
* quiet
* page-friendly
* suitable for an academic/editorial website

It should **not** feel like:

* fantasy art
* shiny concept art
* a children's cartoon
* photorealism
* slick corporate illustration
* overly busy collage

---

## Required visual language

When writing prompts, strongly bias toward the following phrases and
ideas:

### Rendering

Prefer language like:

* delicate ink linework
* lightly engraved line quality
* watercolor washes
* loose aquatint-style shading
* soft paper grain
* aged-paper texture
* subtle foxing
* faded ink bleed
* hand-drawn editorial illustration
* tactile surface
* softly feathered edges
* deckled paper border

Avoid language like:

* ultra-detailed 3D
* cinematic lighting
* hyperreal
* glossy
* dramatic rim light
* vibrant neon palette
* hard cel shading

### Color discipline

Prompts should usually specify this palette logic:

**Base palette:**

* ivory paper background `#F6F2EC`
* deep ink-black `#1E1A17`
* archive-gray `#6E685F`
* pale secondary gray `#BFB7AB`
* muted gold `#B19557` used sparingly

**Pastel accent family:**

* research blue `#5EA3D6`
* pale lavender `#C8B8D8`
* dusty periwinkle
* soft sage
* blush peach
* muted rose-beige

**Semantic split between the two primary accents** (important):

* **Muted gold (`#B19557`) is the material register** — it lives *on*
  the historical object: wax seals, gilt initial capitals, brass
  instrument highlights, gilt tooling, ornamental borders.
* **Research blue (`#5EA3D6`) is the analytical register** — it lives
  *over* the object, made by someone studying it: dashed annotation
  lines, circled place names, a researcher's ink underline,
  diagrammatic arrows, marginal pointing lines.
* **Use at least one of each per image.** If you find yourself building
  an image with only gold or only blue, reconsider — the palette needs
  to breathe. Never substitute one for the other's role.

**Rules:**

* all colors should be soft, dusty, and desaturated
* accent colors should be sparse and intentional
* no neon
* no harsh saturation
* no strong modern UI colors unless explicitly requested

### Lavender stars (atmospheric layer)

Scattered small lavender (`#C8B8D8`) four-pointed or six-pointed stars
and tiny sparkles in the empty regions of the image — especially the
upper-left title-safe zone. They are **never** a focal element; they
are an atmospheric wash that reads as the researcher's dreaming-
over-sources register. Aim for ~8–20 stars, varied in size. Think of
them as visible silence.

### Lighting

Prefer:

* even, diffused lighting
* soft daylight
* gentle ambient light
* calm, low-contrast modeling

Avoid:

* dramatic shadows
* spotlighting
* lens flare
* intense contrast

---

## Composition rules

Prompts should guide layout, not just subject matter.

### Preferred composition

Mention some of the following when relevant:

* clear focal hierarchy
* elegant negative space
* clean editorial composition
* **upper-left quadrant held open for title treatment** (hero images)
* right-of-center or centered subject when useful
* supporting objects arranged with restraint
* ample breathing room for page layout
* a composition that reads clearly at webpage scale

### Edge treatment

For page integration, prompts should often include:

* soft feathered paper edges
* deckled border
* lightly faded outer margin
* illustration dissolving gently into the page

### Background behavior

Backgrounds should:

* support the main subject
* remain light and breathable
* avoid clutter
* allow a page title or copy to sit nearby if needed

---

## Subject handling rules

### If the image includes a person

The prompt should:

* preserve recognizable facial structure if a reference image exists
* describe expression as warm, thoughtful, approachable, or attentive
* keep pose natural and editorial rather than theatrical
* integrate them into the environment through desk work, reading,
  writing, arranging papers, or quiet study

Do not over-style the person into:

* fashion illustration
* caricature
* fantasy character art
* glossy portrait photography imitation

### If the image is a still life

The prompt should:

* organize objects on a desk, table, shelf, or paper field
* keep the arrangement meaningful and not overly crowded
* emphasize tactile materials: paper, books, ceramics, wood, linen,
  glass, brass

### If the image references research

Use historical or scholarly props selectively:

* manuscript fragments (from a real source scan — see Core principle 1)
* paleography notes
* annotation cards
* botanical sheets
* map fragments (from a real source scan if naming specific places)
* wax seals
* notebooks
* pens
* marginal notes

Only include historical artifacts if they support the concept. Do not
automatically add every archival object.

---

## Object vocabulary

These objects fit the style especially well:

**Domestic / personal workspace:**

* books
* stacked notebooks
* open journal
* fountain pen or pencil
* ceramic mug
* pen cup
* desk lamp
* flowers in a glass vase
* leafy houseplants
* framed print
* shelf of books
* wooden table

**Archival / research layer:**

* manuscript page (source-scan based)
* letterform study card
* annotation lines in research blue
* botanical specimen sheet
* partial historical map
* wax seal
* magnifying lens
* note cards
* paper labels

Use only the subset that actually serves the image.

---

## Tone words to prioritize

**Good tone words:**

* refined
* literary
* archival
* intimate
* scholarly
* humane
* quiet
* contemplative
* warm
* tactile
* poetic
* editorial
* restrained

**Words to use carefully or avoid:**

* epic
* cinematic
* magical realism
* maximalist
* whimsical (allowed, but use lightly)
* fantasy
* ornate everywhere
* surreal

"Dreamlike" is acceptable only if balanced by restraint.

---

## Prompt construction pattern

Use this structure when writing prompts:

1. **State the subject clearly**
2. **Name the blended style explicitly**
3. **Describe rendering technique**
4. **Define palette and color rules (including gold/blue semantic split)**
5. **Describe environment and objects**
6. **Set composition and negative space (including upper-left title zone)**
7. **Set lighting and mood**
8. **Add exclusions / constraints**
9. **Specify aspect ratio and pixel dimensions**

---

## Prompt template

Use this template as a base:

```text
Create a stylized editorial illustration of [SUBJECT / SCENE].

Blend two aesthetics into one coherent image:
1. a contemporary early-modern scholarly archive
2. a soft illustrated apartment-study interior

Use delicate ink linework with a lightly engraved quality, softened by
watercolor washes, loose aquatint-style shading, subtle paper grain,
faint foxing, and aged-paper texture. The image should feel tactile,
literary, and refined rather than glossy or cinematic.

Base the image on an ivory paper ground (#F6F2EC) with deep ink-black
(#1E1A17) for primary linework, archive-gray (#6E685F and #BFB7AB) for
secondary forms. Use muted gold (#B19557) sparingly for the MATERIAL
register — wax seals, gilt capitals, brass highlights, ornamental
period detail. Use research blue (#5EA3D6) for the ANALYTICAL register
— the scholar's pen marking the archive: dashed lines, circled names,
stamps, marginal annotation. Include AT LEAST ONE gold moment and ONE
blue moment, doing distinct jobs. Interweave sparse additional
desaturated accents in pale lavender, dusty periwinkle, soft sage, and
blush peach. Keep all colors soft, dusty, and restrained. No neon.

Scatter 8 to 20 small lavender (#C8B8D8) four- or six-pointed stars
and tiny sparkles in the negative space — especially the upper-left —
as an atmospheric wash. Lavender is never a focal accent.

Depict [SUBJECT] in [SETTING], emphasizing [ACTION / THEME]. Include
[OBJECTS TO INCLUDE] only where they reinforce the concept. Keep the
environment elegant, breathable, and page-friendly, with generous
negative space and a clear editorial focal hierarchy. Hold the
upper-left quadrant open as calm space for a title overlay. Main
subject right-of-center.

Lighting should be even, diffused, and gentle. The mood should be
warm, contemplative, scholarly, intimate, and quietly inviting.

Add a soft feathered or deckled edge treatment so the illustration
blends naturally into a page background.

Avoid [OBJECTS / EFFECTS TO EXCLUDE]. No dramatic shadows, no glossy
rendering, no photorealism, no visual clutter, no invented period
handwriting.

[ASPECT RATIO / PIXEL DIMENSIONS — hero: 4:3, 1600×1200+ / about
portrait: 4:5, 1200×1500+]
```

---

## Specialized variants

### 1. About-page portrait

Emphasize:

* likeness
* warmth
* personal workspace
* books, notebook, mug, plants, lamp
* fewer overt historical props unless needed

Useful phrasing:

* half-body or three-quarter portrait
* seated at a desk
* writing or reading
* approachable, thoughtful, friendly
* polished but personal

**Aspect ratio:** 4:5 portrait, 1200×1500+.

### 2. Research hero image

Emphasize:

* symbolic still life or research setup
* title-safe negative space (upper-left)
* one or two strong thematic artifacts (source-scan based if possible)
* stronger editorial abstraction

Useful phrasing:

* right-of-center composition
* upper-left negative space held open for title
* layered papers and fragments
* restrained implication rather than spectacle

**Aspect ratio:** 4:3 landscape, 1600×1200+.

### 3. Archival still life

Emphasize:

* tactile paper objects
* layout clarity
* object relationships
* minimal human presence or no human presence

Useful phrasing:

* flat lay or desk arrangement
* layered papers
* carefully spaced supporting objects
* scholarly quiet

---

## Integrating real source material

When a reference scan is available (strongly preferred for any project
that depicts a specific manuscript, map, or artifact):

1. Upload the scan to the generating agent as a **source image**, not
   a style reference.
2. In the prompt, instruct the agent explicitly: "Reproduce the
   handwriting and textual content of the provided source scan
   faithfully. Do not invent period typography or handwriting."
3. Call out exactly which elements are source-derived vs. illustrated
   (e.g. "the manuscript page at center-right is the provided source;
   the surrounding botanical specimen and wax seal are illustrated to
   match the medium").

If the model produces invented period text that you cannot read as
real language of the period, reject the output and regenerate with
stronger source-faithfulness instructions.

---

## Style guardrails

The AI writing the prompt should check for these failure modes before
finalizing:

### Too historical

If the image starts to feel like a museum display or historical
reenactment, add:

* personal workspace cues
* domestic warmth
* editorial simplification
* softer composition

### Too cute or childish

If the image starts to feel like a children's book, add:

* literary refinement
* restraint
* editorial sophistication
* subtler motifs
* more disciplined palette language

### Too modern

If the image starts to feel like a generic lifestyle illustration,
add:

* manuscript / archive / paper texture cues
* paleography or document references
* engraved line quality
* muted gold and archival neutrals

### Too cluttered

If there are too many props, remove half of them. Prioritize one focal
subject and two to five supporting elements.

### Monochromatic palette

If the generated image has gold accents but no blue (or vice versa),
regenerate with stronger language about the two-accent semantic split.
Both must appear.

### Fake handwriting

If any visible text on a manuscript, map, or annotation card is not
clearly the provided source scan AND looks invented, reject and
regenerate with source-faithfulness instructions.

---

## Review checklist

Before accepting a generated image, confirm:

* [ ] Paper ground is ivory (optionally parchment-warm under the
  primary artifact); no pastel shifts into pink, tan, or butter-yellow
* [ ] Upper-left quadrant clear for title overlay (hero images only)
* [ ] At least one gold moment AND one blue moment, doing distinct
  jobs (material vs. analytical). Neither dominates.
* [ ] Lavender stars present in negative space as atmospheric wash —
  visible but never focal
* [ ] No AI-generated fake handwriting or invented period typography
  (either source-derived or not shown legibly)
* [ ] No modern objects (except permitted wooden/articulated
  mannequin hand as a discreet machine stand-in), no crowd scenes,
  no dramatic violence
* [ ] Even, diffused daylight; no cinematic shadow play
* [ ] Edge treatment is feathered or deckled, not hard-edged
* [ ] Image reads as a chapter of the same illuminated journal as the
  other shipped heroes — if placed beside them on the site, no image
  looks out of register

---

## Existing images (worked examples)

### About-page portrait — Sarah Bonanno
`/site/public/about/sarah.png`

Seated at a desk in a warm apartment workspace, writing in an open
notebook. Books stacked at left, ceramic mug, pen cup, desk lamp,
flowers in a glass vase, houseplants, arched window with lavender
stars in the sky. Warm thoughtful expression, three-quarter pose. No
overt historical props — the scholarly register comes from the books
and journal, not from manuscript fragments. 4:5 portrait.

### Teaching Machines to Read
`/projects/teaching-machines-to-read/public/images/hero.png`

An open early-modern recipe manuscript at center-right (from a real
source scan). A wooden articulated mannequin hand emerges from the
left edge, fingertips reaching toward the manuscript page — the
"machines" of the title rendered as a scholar's anatomical study
rather than a robot. Beneath: fragments of a letterform-variant
chart, a partial alphabet, a branching-tree diagram, a small CER
result chart, checklists with ✓ ✓ ✗ marks. **Gold moment
(material):** brass magnifying glass at lower-left with warm gilt on
its rim; gilt highlight on the manuscript binding. **Blue moment
(analytical):** Research-blue dashed line connecting a handwritten
word on the manuscript to a small transcription glyph in the right
margin. **Lavender stars** scatter through the upper-left quadrant.
4:3 landscape.

### The Healer's Trap
`/projects/witchcraft/public/images/hero.png`

A torn cartographic fragment of the Duchy of Lorraine at center-right
(from a real period map scan), showing river networks and named
prévôtés. Below and overlapping: a single herbalist's specimen
(yarrow or vervain) rendered in archive-gray with botanical-plate
precision, Latin binomial in italic serif. Small stone mortar and
pestle at lower-right. **Gold moment (material):** a small gilded
cross beside the village of Saint-Mihiel, as a period map detail.
**Blue moment (analytical):** a research-blue wax seal silhouette
(cross-impressed) stamped into the upper-right margin — the
researcher's mark on the artifact. **Lavender stars** scatter across
the upper-left and left-side negative space. No figures, no crowds,
no stake, no fire — violence implied by the circled village and the
cross, craft shown by the pressed plant. 4:3 landscape.

---

## Final rule

A good prompt in this style should always answer these questions
clearly:

* What is the subject?
* What is the emotional tone?
* How much archive vs. how much domestic softness?
* What are the key objects?
* Where is the gold moment? Where is the blue moment?
* What should be left out?
* How should it sit on a webpage, and what aspect ratio?

If those are not clear, rewrite the prompt.
