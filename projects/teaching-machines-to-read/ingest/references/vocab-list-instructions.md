# Build a Curated Vocabulary List from Early Modern Recipe Book Transcriptions

## What This Is

You are helping a PhD student (Sarah) who is working on early modern English recipe books. She has an AI transcription pipeline that reads handwritten manuscript pages, but the AI struggles with unfamiliar vocabulary -- it substitutes modern words instead of reading the actual letterforms on the page. For example, it reads "evening" instead of "euenynde," or "violet" instead of "voilett."

To fix this, you are going to build a vocabulary reference from 38 recipe books that have already been transcribed by human volunteers on FromThePage (a public crowdsourcing platform). The idea is simple: if hundreds of pages of real early modern recipe text contain the word "euenynde" or "sallendine" or "calcinated," then when the transcription AI encounters those letterforms, it can check its reading against this list of words that actually appear in the genre.

This is a **verification tool, not a prediction tool**. The transcription AI should still read letterforms first. The vocabulary list just helps it confirm that what it read is a real word that appears in early modern recipes, rather than silently swapping in a modern equivalent.

## What You Need to Know Before Starting

- **Sarah is new to programming.** Any code you write should be clearly commented, explaining what each section does and why. Prefer simple, readable code over clever tricks.
- **This is an open-source project.** Use only free tools. Python is available on the machine. Do not use any paid APIs or services.
- **Preserve original spellings exactly.** The whole point of this list is to capture how words were actually written in early modern manuscripts. Never modernize, normalize, or "correct" spellings. "Syrrup" stays "syrrup." "Putt" stays "putt." "Oyle" stays "oyle."
- **Provenance matters.** Track which manuscripts each word appears in. A word that shows up in 15 different manuscripts is much more reliable than one that appears in only 1 (which could be a transcription error or an idiosyncrasy of that particular scribe).
- **FromThePage is public.** No login is required to view or download transcriptions.
- **Be respectful of the server.** Add a short delay (1-2 seconds) between requests when downloading. Do not hammer the site with rapid-fire requests.

## Where to Save Everything

Save all output files to: `/Users/sarahbonanno/daggerobelus.com/projects/recipes/extracted/derived/vocab/`

Create this folder if it does not exist.

## Step 1: Access the FromThePage Collection via IIIF API

FromThePage exposes transcription text through IIIF (International Image Interoperability Framework) API endpoints. You do not need to scrape HTML pages -- there are clean API endpoints that return the text directly.

**Collection endpoint** (lists all 38 manuscripts with their IDs):
```
https://fromthepage.com/iiif/collection/early-modern-recipe-books
```

This returns JSON. Each entry in the `manifests` array has:
- `@id` -- a manifest URL like `https://fromthepage.com/iiif/55048/manifest`
- `label` -- the manuscript title
- `service.pctComplete` -- transcription completion percentage (100.0 means fully transcribed)

The number in the manifest URL (e.g., `55048`) is the **work ID**. You will use this to download plaintext.

**Plaintext export for an entire manuscript** (one request per manuscript, returns all pages):
```
https://fromthepage.com/iiif/{work_id}/export/plaintext/verbatim
```

For example:
```
https://fromthepage.com/iiif/55048/export/plaintext/verbatim
```
returns the full plaintext transcription of the Lady Sedley manuscript (MS534).

This "verbatim" export preserves original spellings and formatting. This is the endpoint you want.

### Here are all 38 manuscripts and their work IDs

You can extract these from the collection endpoint, but here they are for reference:

| Work ID | Manuscript Title |
|---------|-----------------|
| 32086913 | College of Physicians of Philadelphia: Robert Pryor Richardson notes (10a-198) |
| 32056035 | English recipe book, 17th century and later MS 8575 |
| 32034068 | London Metropolitan Archives: Recipe Book (CLC/270/MS00558) |
| 32048812 | Medici, Antonio De' |
| 32151602 | MS 222: Croy, Anne de, Princesse de Chimay |
| 32110958 | MS 244: Dineley/Dyneley (or Dingley/Dyngley), Henry (& others) |
| 32142178 | MS 373: Jane Jackson |
| 52011 | MS 7113: Wellcome Collection: Fanshawe, Lady Ann (1625-1680) |
| 32176418 | MS 9198: Lady Caroline Eliza East's recipe book |
| 32139603 | MS.5853 Recipe Collection, 19th Century |
| 32053094 | MS.9317 |
| 32175110 | Royal College of Physicians: Mistress Honore Henslow (MS688) |
| 32086974 | Royal College of Physicians: Medical receipts (MS504) |
| 32028396 | Royal College of Physicians: Medical receipts and prescriptions, 17th century |
| 55048 | Royal College of Physicians: The Lady Sedley (MS534) |
| 55051 | Sample transcription: Lady Ayscough |
| 32043671 | Thomas Fisher Rare Book Library: Medical recipe book (MSS 03340) |
| 25005964 | University of Guelph: Recipe and Remedy Book (XM1 MS A117045) |
| 25006107 | University of Guelph: Recipe and Remedy Book (XM1 MS A117046) |
| 54701 | Wellcome Collection: Ayscough, Lady (MS1026) |
| 25002909 | Wellcome Collection: Brumwich, Anne (& others) (MS160) |
| 32038497 | Wellcome Collection: Bulkeley, Elizabeth (MS.169) |
| 32038498 | Wellcome Collection: Catchmay, Lady Frances (MS.184a) |
| 32026529 | Wellcome Collection: Coley Family (MS1711) |
| 25002906 | Wellcome Collection: Cookery-books: 18th cent. (MS1810) |
| 32032489 | Wellcome Collection: English culinary and medical recipe book, 18th century (MS8468) |
| 50147 | Wellcome Collection: English Recipe Book, 18th century (MS6956) |
| 32042533 | Wellcome Collection: English Recipe Book, early 18th century (MS.7746) |
| 50144 | Wellcome Collection: Ex tribus [regnis] arcana (MS2315) |
| 32038499 | Wellcome Collection: Hughes, Sarah (MS.363) |
| 25002908 | Wellcome Collection: John and Joan Gibson (MS311) |
| 32006262 | Wellcome Collection: Grace Carteret, 1st Countess Granville |
| 32030454 | Wellcome Collection: Mary Hawker's recipe book (MS9304) |
| 32054009 | Wellcome Collection: Miller, Mrs. Mary (MS.3547) |
| 50146 | Wellcome Collection: Ostfrisisches rares Medicinbuch (German) |
| 32086958 | Wellcome Collection: Receipt-Book, 17th-18th century (MS.4054) |
| 25010759 | Wellcome Collection: Saint John, Johanna (MS4338) |
| 25002907 | Wellcome Collection: The Regiment of Healthe (MS674) |

### Your approach

1. Fetch the collection JSON from the collection endpoint to get the current list of manuscripts and their completion status.
2. For each manuscript that is fully or substantially transcribed (check `pctComplete` or `pctTranscribed`), download the plaintext verbatim export.
3. Add a 1-2 second delay between downloads to be respectful of the server.
4. Save each manuscript's raw text to a subfolder (`vocab/raw-text/`) so you have the source material.
5. If any downloads fail, log the failure and move on. Even 5-10 manuscripts would be a useful start.

**Important note about the collection:** Some of these manuscripts are not English (the Medici manuscript is Italian; the Ostfrisisches Medicinbuch is German; the Croy manuscript is French). You should still download them -- the foreign-language terms are genuinely part of the recipe vocabulary (many English recipes include Latin and French terms). But note which manuscripts are primarily in a non-English language in your summary.

## Step 1b: Additional Vocabulary Sources (After FromThePage)

After processing the FromThePage transcriptions, incorporate vocabulary from these additional sources. These are lower priority than FromThePage (start there first), but will fill important gaps — especially for specialized botanical, medical, and pharmaceutical terminology.

### Printed Herbals

Early modern herbals are essentially dictionaries of the plant names and medical terms that appear in recipe manuscripts. Two are especially relevant:

- **John Gerard, *The Herball or Generall Historie of Plantes* (1597)** — Available on the Internet Archive (search for "Gerard Herball 1597"). Contains hundreds of plant names with Latin equivalents and medicinal uses. Many recipe book ingredients come directly from Gerard's vocabulary.
- **Nicholas Culpeper, *The English Physitian* (1652)** — Also on the Internet Archive. More accessible than Gerard, with English-language descriptions of plant properties and medical applications.

For these texts: download the full text (Internet Archive often has plain text or OCR versions), tokenize, and add to the frequency list. Tag these words with their source (e.g., "Gerard-1597" or "Culpeper-1652") so they are distinguishable from the manuscript transcription vocabulary. Words that appear in both the herbals AND the FromThePage transcriptions are especially high-confidence.

### EMROC (Early Modern Recipes Online Collective)

EMROC (https://emroc.hypotheses.org/) produces **triple-keyed transcriptions** of recipe books — meaning three people independently transcribe each page and discrepancies are resolved. This makes their transcriptions more reliable than the crowd-sourced FromThePage versions.

EMROC works through the Folger's DROMIO platform. Their transcriptions may be available through:
- The EMROC website directly
- The Folger's digital collections
- Published scholarly editions based on EMROC transcriptions

Explore what's accessible and incorporate any available transcription text. EMROC vocabulary is especially valuable because of the triple-keying quality control — if a word appears in an EMROC transcription, it's very likely to be a correct reading.

### How to handle multiple sources

When building the final vocabulary files, track the source type for each word:
- `FTP` = FromThePage transcription
- `HERBAL` = printed herbal (Gerard, Culpeper, etc.)
- `EMROC` = EMROC triple-keyed transcription

A word attested across multiple source types is more reliable than one from a single source. Include a `source_types` column in the CSV files.

## Step 2: Clean and Tokenize the Text

Once you have the raw transcription text from each manuscript:

1. **Remove metadata lines.** The plaintext exports may begin with catalog numbers, library stamps, and bookplate descriptions. These are not recipe text. Look for patterns like shelf marks, accession numbers, and "Wellcome Historical Medical Library" headers. Strip these out before tokenizing. Be conservative -- if you are not sure whether something is metadata or recipe text, keep it.

2. **Tokenize into individual words.** Split on whitespace. A "word" here is any whitespace-delimited token.

3. **Handle punctuation carefully.** Strip leading and trailing punctuation from each token (periods, commas, colons, semicolons, parentheses) but preserve internal punctuation. For example:
   - `"syrrup."` becomes `"syrrup"` (strip trailing period)
   - `"t'is"` stays `"t'is"` (internal apostrophe is part of the word)
   - `"h^eales"` stays `"h^eales"` (the caret marks a manuscript feature)
   - `"[seised]"` becomes `"seised"` (strip editorial brackets)
   - `"ounces,"` becomes `"ounces"` (strip trailing comma)

4. **Preserve case as-is for the raw frequency list.** "Take" and "take" should be counted separately in the raw list. But also create a case-insensitive version for the categorized vocabulary (where "Take" and "take" are merged).

5. **Track provenance.** For every word, record which manuscript(s) it appears in and how many times it appears in each.

## Step 3: Build the Frequency List

Create a complete word frequency list that includes:

- The word exactly as it appears (original spelling and case)
- Total count across all manuscripts
- Number of manuscripts the word appears in
- List of which manuscripts it appears in (use short identifiers, e.g., "Sedley-MS534", "Henslow-MS688")

Sort the list by total frequency (most common first).

Save this as: `vocab/word-frequency-complete.csv`

Format:
```
word,total_count,manuscript_count,manuscripts
the,12847,35,"Sedley-MS534|Henslow-MS688|Brumwich-MS160|..."
and,9823,35,"Sedley-MS534|Henslow-MS688|Brumwich-MS160|..."
of,8912,35,"Sedley-MS534|Henslow-MS688|Brumwich-MS160|..."
Take,4521,34,"Sedley-MS534|Henslow-MS688|..."
...
```

Also create a case-insensitive version: `vocab/word-frequency-case-insensitive.csv`

In this version, merge "Take", "take", "TAKE" into a single entry. Show the most common capitalization as the canonical form, and note all variant capitalizations.

## Step 4: Categorize the Vocabulary

This is the most valuable part. Go through the frequency list and organize words into topical categories. You do not need to categorize every single word -- focus on words that are specific to early modern recipe books and would be unfamiliar to a modern reader or AI.

Skip extremely common English words (the, and, of, to, a, in, etc.) unless they have unusual early modern spellings (e.g., "ye" for "the", "y^e" for "the").

### Categories to create:

**1. Ingredients: Plants and Herbs**
Words like: sallendine (celandine), rosemary, fennill (fennel), wormewood (wormwood), buglosse (bugloss), synamome (cinnamon), comferie (comfrey), angellica, borage, hysope, etc.

**2. Ingredients: Animal Products**
Words like: harts horne (hartshorn), snailes, neats foote (neat's foot), doues dunge (dove's dung), ambergreece (ambergris), sperma ceti (spermaceti), etc.

**3. Ingredients: Minerals and Chemicals**
Words like: vitriol, brimstone, allum (alum), saltpeter, ceruse (white lead), tutty, litharge, etc.

**4. Medical and Ailment Terms**
Words like: ague, dropsie (dropsy), consumptione (consumption), collicke (colic), pyles (piles), impostume (abscess), tympany, surfeit, flux, pleurisie, etc.

**5. Body Parts (with early modern spellings)**
Words like: stomacke (stomach), fundamente (fundament), reines (reins/kidneys), maw, splene (spleen), etc.

**6. Preparation and Process Verbs**
Words like: distill, calcinate, seeth (seethe/boil), stampe (stamp/pound), straine, clarifie, infuse, decoct, incorporat, etc.

**7. Measurement Terms**
Words like: dramme (dram), scruple, ounce, pennyworth, handfull, spoonfull, pottle, gallon, quarter, gill, etc.

**8. Equipment and Vessels**
Words like: mortar, limbeck (alembic), stillitory (distillery), pipkin, posnet, crucible, bolthead, retort, etc.

**9. Common Early Modern Spelling Variants**
Words that are recognizable modern English words but spelled differently. This is especially important for the transcription AI. Examples:
- oyle (oil), syrrup (syrup), juyce (juice), plaister (plaster)
- phisicke (physic), chirurgery (surgery), receite/receipt (recipe)
- putt (put), itt (it), hearbe (herb), sope (soap)
- euery (every), vpon (upon), vnto (unto), haue (have)
- togeather (together), cordiall (cordial), soueraigne (sovereign)

**10. Latin and French Terms**
Words or phrases from Latin or French that appear in English recipe texts:
- probatum est (it has been proved), aqua vitae, sal ammoniac
- ana (of each, equal parts), recipe (take), quantum sufficit

**11. Abbreviated Forms and Contractions**
Common abbreviations found in the transcriptions:
- t'is (it is), y^e (the), w^th (with), w^ch (which)
- & (and), &c (etc.)

### Format for categorized vocabulary

Save as: `vocab/vocabulary-categorized.md`

For each category, list words alphabetically with:
- The word as it appears in the transcriptions (original spelling)
- Modern English equivalent (if applicable)
- Total frequency across the corpus
- Number of manuscripts it appears in
- A brief note if helpful (e.g., "always appears as recipe title opening")

Example format:
```
## Ingredients: Plants and Herbs

| Word | Modern Form | Count | MSS | Notes |
|------|-------------|-------|-----|-------|
| angellica | angelica | 47 | 12 | |
| borage | borage | 89 | 18 | also spelled "borrage", "buorrage" |
| buglosse | bugloss | 23 | 8 | |
| comferie | comfrey | 31 | 11 | also "comfrey", "comferie" |
| fennill | fennel | 52 | 15 | also "fenell", "fennil" |
| rosemary | rosemary | 134 | 28 | spelling stable across manuscripts |
| sallendine | celandine | 19 | 7 | also "sallandine", "celandine" |
| wormewood | wormwood | 67 | 19 | also "wormwood", "wormewoode" |
```

When a word has multiple spelling variants across the manuscripts, group them together and list all variant forms. This is extremely useful for the transcription AI -- if it sees letterforms that could spell "sallendine" or "sallandine" or "celandine," all three are real attested forms.

## Step 5: Create a Summary Report

Save as: `vocab/processing-summary.md`

Include:
- Date processed
- Total number of manuscripts attempted and successfully downloaded
- For each manuscript: title, work ID, whether download succeeded, approximate word count, primary language (English, Latin, French, German, Italian, etc.)
- Total words processed across all manuscripts
- Total unique word forms found
- Total unique word forms (case-insensitive)
- Any manuscripts that failed to download and why
- Any issues or anomalies noticed in the data
- Notes on which manuscripts seem most useful for the vocabulary list (e.g., which ones have the richest recipe-specific vocabulary, which ones are mostly in a non-English language)

## Step 6: Create a Flat Vocabulary File for AI Consumption

In addition to the human-readable files above, create a simple flat text file that can be easily fed to the transcription AI as a reference.

Save as: `vocab/vocab-reference.txt`

This file should contain one word per line, sorted alphabetically, including only words that are:
- Specific to early modern recipe vocabulary (not common modern English words like "the", "and", "of")
- Attested in at least 2 manuscripts (to filter out possible transcription errors)

At the top of the file, include a header comment explaining what it is:
```
# Early Modern Recipe Vocabulary Reference
# Built from [N] transcribed recipe books on FromThePage
# (Folger/Wellcome Collection: Early Modern Recipe Books)
#
# This list contains words that appear in human-transcribed
# early modern recipe books, preserving original spellings.
# Use this to verify transcription readings -- if the word
# you read appears on this list, it is a real attested form.
#
# Words are included only if they appear in 2+ manuscripts.
# Total unique forms: [N]
# Source manuscripts: [N]
# Generated: [date]
```

## Technical Notes

### Python setup

The code should use only Python standard library modules if possible. If you need external packages, the most likely useful ones are:
- `requests` -- for downloading from URLs (should already be installed; if not, install with `pip3 install requests`)
- `csv` -- standard library, for writing CSV files
- `json` -- standard library, for parsing IIIF API responses
- `collections` -- standard library, for Counter and defaultdict
- `re` -- standard library, for regular expressions
- `time` -- standard library, for adding delays between requests
- `os` -- standard library, for creating directories

Do not use `pandas`, `nltk`, `spacy`, or other heavy libraries unless there is a very good reason. Simple Python is preferred.

### Handling HTML in transcription text

The IIIF annotation lists return text in HTML format. The plaintext verbatim export should return plain text, but if you encounter HTML tags in the downloaded text, strip them. Python's `html` standard library module or a simple regex like `re.sub(r'<[^>]+>', '', text)` will work.

### Handling editorial markup

FromThePage transcriptions may include editorial markup:
- `[text]` -- square brackets indicate editorial uncertainty or supplied text
- `^` -- caret marks interlineal insertions
- `{text}` -- curly braces may indicate page numbers or marginalia
- `[...]` -- indicates illegible text

For the vocabulary list, strip the brackets but keep the text inside them (since that is the transcriber's best reading). Strip `{page numbers}` entirely since those are not recipe vocabulary. Preserve carets within words like `h^eales` since those are part of the diplomatic transcription convention.

### What counts as a "word" for categorization

Use your knowledge to categorize words. You are an AI with broad knowledge of early modern English, historical medicine, botany, and cooking terminology. Apply that knowledge to sort words into categories. When you are unsure whether a word is an ingredient vs. a preparation term, make your best judgment and note the ambiguity.

Not every word needs to be categorized. Focus on words that would be useful for a transcription AI to know about -- primarily recipe-specific vocabulary that differs from modern English. Common function words, prepositions, and conjunctions can be skipped in the categorized list (though they should still appear in the complete frequency list).

## Final Output Checklist

When you are done, the `vocab/` folder should contain:

```
vocab/
  raw-text/                           # Downloaded transcription text, one file per manuscript
    sedley-ms534.txt
    henslow-ms688.txt
    brumwich-ms160.txt
    ...
  word-frequency-complete.csv         # Every word form, sorted by frequency
  word-frequency-case-insensitive.csv # Case-insensitive version
  vocabulary-categorized.md           # Words organized by topic (the most useful file)
  vocab-reference.txt                 # Flat list for AI consumption
  processing-summary.md               # What was processed, statistics, notes
  build-vocab.py                      # The Python script you wrote (so Sarah can re-run it)
```

Save the Python script you write as `vocab/build-vocab.py` so Sarah can re-run it later if new manuscripts are added. Include clear comments throughout explaining what each section does.

## A Note on What This Is For

The vocabulary list you are building will be used as part of a **blind transcription pipeline**. Here is how it fits:

1. A transcription AI looks at a manuscript image and reads the letterforms
2. It produces a candidate reading of each word
3. It checks that reading against the vocabulary list: "Is this a word that actually appears in early modern recipe books?"
4. If the word is on the list, it has higher confidence in its reading
5. If the word is NOT on the list, it does not automatically reject the reading -- the manuscript might contain a word not in the reference set. But it should flag that reading for closer attention.

The vocabulary list is **evidence from the corpus**, not a dictionary. It tells the AI: "Here are the words that real human transcribers have actually read in these manuscripts." This helps prevent the most common error mode, which is silently substituting a familiar modern word for an unfamiliar early modern one.
