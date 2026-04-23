# Illustration Guide — Hero Images

Reference for generating on-brand hero illustrations for daggerobelus.com projects.
Intended audience: human collaborators and AI agents producing prompts for image
generation. When a new project needs a hero image, an agent should be able to
open this doc and produce a prompt that matches the existing visual language
without further direction.

## When to use this

- Every project needs exactly one hero image (landscape, 4:3, 1600×1200+)
- Hero sits beside the title in the homepage featured block and at the top of
  the project detail page
- The goal is a set of images that look like chapters of the same journal, not
  a portfolio of unrelated illustrations

## Core principles

1. **Real source material beats AI-generated historical text.** Always pass a
   reference scan (manuscript page, map fragment, botanical plate, title page)
   to the generating agent and instruct it to integrate or reproduce that
   artifact faithfully. Synthetic "old handwriting" or invented period
   typography reads as fake at any zoom and undermines scholarly credibility.
   If we don't have a scan, change the subject or commission one — don't let
   the model hallucinate paleography.
2. **Restraint and implication, not spectacle.** Violence, drama, and
   atmospheric horror belong in the prose, not the hero image. A single
   circled village and a cross-seal communicate the weight of a witch trial
   more than a crowd scene.
3. **Consistency is the brand.** Every image obeys the same palette, the same
   compositional grammar, and the same rendering technique. If a prompt calls
   for a colour or medium that isn't in the preamble below, either adjust the
   subject or reject the prompt.
4. **Upper-left negative space is reserved.** The title column lands there on
   desktop. Never compose a focal element in the upper-left quadrant.
5. **No modern elements.** Screens, phones, contemporary typography, neon,
   Helvetica, Times New Roman, anything post-1800 in the subject frame.

## Palette (strict)

| Role            | Hex       | Usage                                          |
|-----------------|-----------|------------------------------------------------|
| Ivory Paper     | `#F6F2EC` | Background, paper ground                       |
| Ink Black       | `#1E1A17` | Primary linework, period handwriting           |
| Obelus Gold     | `#B19557` | Single accent only — seals, manicules, rules   |
| Archive Gray    | `#BFB7AB` | Washes, secondary forms                        |
| Slate Gray      | `#6E685F` | Shadow washes, recessive detail                |

No other colors. No saturated blues, reds, greens, purples. Research Blue
(`#5EA3D6`) from the brand palette is **not** used in hero illustrations — it
belongs to data visualizations inside project content.

## Composition rules

- Aspect ratio 4:3, rendered at 1600×1200 or larger
- Main subject sits right-of-center
- Upper-left quadrant held open as calm ivory space (foxing and faint
  marginalia okay, no focal elements)
- Layered-collage logic: a primary artifact (manuscript, map, plate) with
  secondary elements overlapping at the edges — a specimen, a seal, a
  marginal note, a pointing-hand glyph (☞)
- Even archival-photography lighting. No dramatic chiaroscuro, no lens flare,
  no raking light
- Subtle paper texture, foxing, faded ink bleed at edges

## Technique / medium

Detailed engraved linework combined with loose aquatint-style ink washes and
watercolor staining on aged laid paper. Think: the composite frontispieces in
Folio Society editions, the layered-archive approach in Armando Veve's
editorial illustration, the compositional clarity of NYRB Classics covers,
the observational precision of early-modern natural history plates (Redouté,
Ehret).

## Visual references (cite in prompts)

- NYRB Classics covers (David Pearson, Katy Homans)
- Armando Veve — editorial illustrations for *The New Yorker* and *LRB*
- Folio Society frontispieces
- Hans Holbein woodcut detail
- Warburg Institute archival photography
- Codex Seraphinianus layout logic (not content)
- Early-modern natural history plates: Redouté, Ehret, Maria Sibylla Merian

## Prompt structure

Every hero prompt is two blocks, in this order:

```
[SHARED STYLE PREAMBLE — paste verbatim]

Subject: [one paragraph describing the specific artifacts, their
arrangement, and the one accent detail that carries the story]
```

Do not edit the preamble per-prompt. If you're tempted to, adjust the subject
block instead or raise it as a guide revision.

## Shared style preamble

Paste this verbatim at the top of every hero prompt:

```
Editorial illustration in the style of a contemporary early-modern
scholarly archive. Technique: detailed engraved linework combined with
loose aquatint-style ink washes and watercolor staining on aged laid
paper. Layered collage composition — archival documents, marginalia,
botanical and cartographic fragments arranged as if on a scholar's
desk. Restrained palette on an ivory paper background (#F6F2EC): deep
ink-black (#1E1A17) for primary linework, muted archive-gray (#6E685F
and #BFB7AB) for secondary forms, warm muted gold (#B19557) used
sparingly as the only accent color — gilt initial capitals, wax seal,
compass rose, marginal pointing-hand glyph. Absolutely no saturated
modern colors, no neon, no purple, no teal. Even, diffused archival
lighting — no dramatic shadows, no lens flare. Subtle paper texture,
foxing, and faded ink bleed at edges. Visual references: NYRB Classics
covers, Armando Veve's editorial illustrations for the New Yorker and
LRB, Folio Society frontispieces, Hans Holbein woodcut detail, Warburg
Institute archival photographs, Codex Seraphinianus layout logic. 4:3
aspect ratio, 1600×1200, main subject right-of-center, upper-left
quadrant held open as calm negative space.
```

## Integrating real source material

When a reference scan is available (strongly preferred for any project that
depicts a specific manuscript, map, or artifact):

1. Upload the scan to the generating agent as a source image, not a style
   reference
2. In the subject block, instruct the agent explicitly: "Reproduce the
   handwriting and textual content of the provided source scan faithfully.
   Do not invent period typography or handwriting."
3. Call out exactly which elements are source-derived vs. illustrated (e.g.
   "the manuscript page at center-right is the provided source; the
   surrounding botanical specimen and wax seal are illustrated to match
   the medium")

If the model produces invented period text that you cannot read as real
language of the period, reject the output and regenerate with stronger
source-faithfulness instructions.

## Review checklist

Before accepting a generated hero, confirm:

- [ ] Palette obeys the table above (no other colors visible)
- [ ] Upper-left quadrant clear for title overlay
- [ ] Gold used sparingly — one or two accent moments, not throughout
- [ ] No AI-generated fake handwriting or invented period typography
  (either source-derived or not shown legibly)
- [ ] No modern objects, no figures in crowd scenes, no dramatic violence
- [ ] Even lighting; no cinematic shadow play
- [ ] Reads as a chapter of the same journal as the other existing heroes —
  if placed beside them on the homepage, no image looks out of register

## Existing heroes (worked examples)

### Teaching Machines to Read
`/projects/teaching-machines-to-read/public/images/hero.png`

Subject: an open early-modern recipe manuscript at center-right (use a real
scan — e.g. Henslowe or a period recipe book), with a single faint dashed
line connecting one handwritten word on the page to a small gold-inked
transcription glyph in the right margin. Beneath: fragments of a letterform
variant chart (pencil sketch), a partial alphabet in faded brown ink, a
branching-tree diagram of handwriting strokes drawn in scholar's-notebook
style. A small brass magnifying lens at lower-left. A gold pointing-hand
manicule (☞) in the extreme right margin. No modern devices.

### The Healer's Trap
`/projects/witchcraft/public/images/hero.png`

Subject: a torn partial cartographic fragment of the Duchy of Lorraine at
center-right (use a real period map scan) showing river networks, named
prévôtés in period lettering, and faint coordinate grid. One small village
circled in gold ink with a marginal cross beside it. Below and overlapping:
a single herbalist's specimen (yarrow or vervain) rendered in muted
archive-gray with botanical-plate precision, Latin binomial in thin italic
serif. Small stone mortar and pestle at lower-right catching a soft
highlight. A gold wax seal silhouette (cross-impressed) tucked into the
upper-right margin. No figures, no stake, no fire — violence implied by
the circled village and cross, craft shown by the pressed plant.

## Revising this guide

If a new project genuinely needs something this guide forbids (e.g. a color
outside the palette, a composition breaking the upper-left rule), raise it
explicitly rather than silently bending the rules. A single exception ages
into "we don't really have a style anymore" across five projects. Prefer
adjusting the subject to fit the guide.
