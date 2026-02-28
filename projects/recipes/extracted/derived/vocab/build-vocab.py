#!/usr/bin/env python3
"""
build-vocab.py
==============
Downloads early modern recipe book transcriptions from FromThePage,
plus printed herbals from the Internet Archive, builds word frequency
lists, and categorizes the vocabulary.

This script is part of a transcription pipeline for early modern
English recipe manuscripts. It creates a vocabulary reference that
helps the transcription AI verify its readings against words that
actually appear in the genre.

Sources:
  - FromThePage (FTP): 38 crowd-sourced manuscript transcriptions
  - EMROC: 3 triple-keyed transcriptions (subset of FromThePage)
  - Herbals (HERBAL): Gerard's Herball (1597), Culpeper's English
    Physitian (1652) from the Internet Archive

Usage:
    python3 build-vocab.py

All output is saved to:
    projects/recipes/extracted/derived/vocab/

For more information, see: vocab-list-instructions.md
"""

# ── Standard library imports (no external packages needed) ──────────────

import json          # For parsing the IIIF API responses (they return JSON)
import csv           # For writing CSV frequency files
import re            # For regular expressions (pattern matching in text)
import time          # For adding polite delays between server requests
import os            # For creating directories and file paths
import sys           # For printing progress updates
import html          # For decoding HTML entities like &amp; → &
import datetime      # For putting today's date in the output files
from collections import Counter, defaultdict   # Handy data structures for counting
from urllib.request import urlopen, Request     # For downloading from URLs
from urllib.error import URLError, HTTPError    # For handling download errors


# ============================================================
# CONFIGURATION
# Change these paths if you want output to go somewhere else.
# ============================================================

# Where all output files will be saved
OUTPUT_DIR = "/Users/sarahbonanno/daggerobelus.com/projects/recipes/extracted/derived/vocab"

# Subfolder for the raw downloaded text from each manuscript
RAW_TEXT_DIR = os.path.join(OUTPUT_DIR, "raw-text")

# The FromThePage API endpoint that lists all 38 recipe manuscripts
COLLECTION_URL = "https://fromthepage.com/iiif/collection/early-modern-recipe-books"

# Template for downloading the full plaintext of one manuscript.
# The {work_id} gets replaced with each manuscript's ID number.
EXPORT_URL_TEMPLATE = "https://fromthepage.com/iiif/{work_id}/export/plaintext/verbatim"

# Wait this many seconds between downloads to be polite to the server
REQUEST_DELAY = 2

# ── Herbal sources from the Internet Archive ────────────────
# These are OCR'd plain text files of two important printed herbals.
# They provide authoritative botanical and medical vocabulary.

HERBAL_SOURCES = [
    {
        "short_id": "Gerard-1597",
        "label": "John Gerard, The Herball or Generall Historie of Plantes (1597)",
        "filename": "herbal-gerard-1597.txt",
        "url": "https://archive.org/download/bim_early-english-books-1475-1640_the-herball-_gerard-john_1597/bim_early-english-books-1475-1640_the-herball-_gerard-john_1597_djvu.txt",
        "source_type": "HERBAL",
        "language": "English",
    },
    {
        "short_id": "Culpeper-1652",
        "label": "Nicholas Culpeper, The English Physitian (1652)",
        "filename": "herbal-culpeper-1652.txt",
        "url": "https://archive.org/download/b30335310/b30335310_djvu.txt",
        "source_type": "HERBAL",
        "language": "English",
    },
]

# ── EMROC manuscripts ──────────────────────────────────────
# These 3 FromThePage manuscripts were part of the EMROC 2021
# transcribathon and have higher-quality triple-keyed transcriptions.
# They are already in the main collection; we just tag them differently.

EMROC_WORK_IDS = {"52011", "55048", "54701"}


# ============================================================
# STOP WORDS
# Common English function words that are NOT specific to recipe
# vocabulary. These get excluded from the flat vocab file (Step 6)
# but still appear in the complete frequency lists.
# ============================================================

STOP_WORDS = {
    # Determiners and articles
    "a", "an", "the", "this", "that", "these", "those",
    # Prepositions
    "in", "on", "at", "to", "for", "of", "with", "by", "from", "as",
    "into", "over", "after", "before", "between", "under", "above",
    "below", "through", "during", "without", "within", "upon", "unto",
    "against", "about", "up", "out", "off", "down",
    # Conjunctions
    "and", "or", "but", "if", "so", "yet", "nor", "for",
    # Pronouns
    "he", "she", "it", "they", "we", "you", "i", "me", "him", "her",
    "us", "them", "my", "his", "its", "our", "your", "their",
    "who", "whom", "which", "what", "whose",
    # Auxiliary and common verbs
    "is", "was", "are", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did",
    "will", "would", "shall", "should", "may", "might", "can", "could",
    "must", "not", "no",
    # Very common adverbs
    "then", "there", "here", "now", "also", "very", "well",
    "when", "where", "how", "why", "still", "even", "too",
    "more", "most", "much", "many", "such", "only", "just",
    "than", "some", "any", "all", "each", "every", "both",
    "other", "same", "own", "few",
    # Common short words
    "one", "two", "three", "four", "five", "six", "new", "old",
    "good", "great", "long", "first", "last",
    # Common verbs (too generic to be recipe-specific)
    "make", "made", "come", "came", "go", "went", "see", "saw",
    "give", "gave", "say", "said", "know", "knew", "think",
    "want", "need", "find", "found", "tell", "told",
    "day", "days", "time", "times", "man", "men", "thing",
    "part", "place",
}


# ============================================================
# VOCABULARY CATEGORIZATION DATA
#
# This is a hand-built dictionary of early modern recipe terms,
# organized by category. Each entry maps a word (in its various
# historical spellings) to a category and modern equivalent.
#
# The script uses this to automatically sort words from the
# frequency list into topical groups. Words not in this
# dictionary end up in an "uncategorized" list for manual review.
# ============================================================

# Each tuple: (category_name, modern_form, spelling1, spelling2, ...)
# You can add more entries here if you notice words the script missed.

_VOCAB_ENTRIES = [

    # ── 1. INGREDIENTS: PLANTS AND HERBS ──────────────────────

    ("Ingredients: Plants and Herbs", "agrimony", "agrimony", "agrimonie"),
    ("Ingredients: Plants and Herbs", "alehoof", "alehoof", "alehofe", "ale-hoof"),
    ("Ingredients: Plants and Herbs", "aloes", "aloes", "aloes"),
    ("Ingredients: Plants and Herbs", "angelica", "angelica", "angellica", "angellicoe"),
    ("Ingredients: Plants and Herbs", "anise", "anise", "annise", "aniseed", "anniseed",
     "anyseede", "annyseede"),
    ("Ingredients: Plants and Herbs", "balm", "balm", "baulme", "bawme", "balme"),
    ("Ingredients: Plants and Herbs", "barley", "barley", "barly", "barlie"),
    ("Ingredients: Plants and Herbs", "basil", "basil", "basill", "bazill"),
    ("Ingredients: Plants and Herbs", "bay", "bay", "bayes", "baye"),
    ("Ingredients: Plants and Herbs", "betony", "betony", "bettony", "bettonie",
     "bettoney"),
    ("Ingredients: Plants and Herbs", "borage", "borage", "borrage", "buorrage",
     "burrage"),
    ("Ingredients: Plants and Herbs", "bugloss", "bugloss", "buglosse", "bugloss"),
    ("Ingredients: Plants and Herbs", "burnet", "burnet", "burnett"),
    ("Ingredients: Plants and Herbs", "camomile", "camomile", "camamile", "chamomile",
     "cammomile", "cammomille", "cammomill"),
    ("Ingredients: Plants and Herbs", "caraway", "caraway", "carraway", "carrawayes",
     "carawayes"),
    ("Ingredients: Plants and Herbs", "cardamom", "cardamom", "cardamome", "cardamum"),
    ("Ingredients: Plants and Herbs", "celandine", "celandine", "sallendine",
     "sallandine", "celidony", "celidonie"),
    ("Ingredients: Plants and Herbs", "centaury", "centaury", "centory", "centaurie",
     "centaurey"),
    ("Ingredients: Plants and Herbs", "chicory", "chicory", "succory", "succorie",
     "chiccory"),
    ("Ingredients: Plants and Herbs", "cinnamon", "cinnamon", "synamome", "cinamon",
     "sinnamon", "cinamone", "cynamon"),
    ("Ingredients: Plants and Herbs", "clove", "clove", "cloues", "cloves", "cloue"),
    ("Ingredients: Plants and Herbs", "coltsfoot", "coltsfoot", "coltsfoote",
     "coltesfoote"),
    ("Ingredients: Plants and Herbs", "comfrey", "comfrey", "comferie", "cumfrie",
     "cumfrey", "comfery"),
    ("Ingredients: Plants and Herbs", "coriander", "coriander", "corriandar",
     "corriander"),
    ("Ingredients: Plants and Herbs", "cowslip", "cowslip", "cowslippe", "couslippe",
     "cowslippes"),
    ("Ingredients: Plants and Herbs", "cumin", "cumin", "cummin", "cummine"),
    ("Ingredients: Plants and Herbs", "daisy", "daisy", "daisie", "daysie"),
    ("Ingredients: Plants and Herbs", "dill", "dill", "dille"),
    ("Ingredients: Plants and Herbs", "dock", "dock", "docke"),
    ("Ingredients: Plants and Herbs", "elder", "elder", "elderflower", "elderflowers",
     "elder-flower"),
    ("Ingredients: Plants and Herbs", "elecampane", "elecampane", "elecampaine",
     "enula"),
    ("Ingredients: Plants and Herbs", "endive", "endive", "endiue", "endiues"),
    ("Ingredients: Plants and Herbs", "eyebright", "eyebright", "eyebrighte"),
    ("Ingredients: Plants and Herbs", "fennel", "fennel", "fennill", "fenell",
     "fenil", "fennell"),
    ("Ingredients: Plants and Herbs", "fenugreek", "fenugreek", "fenigreeke",
     "fenugreke", "fennigreeke"),
    ("Ingredients: Plants and Herbs", "feverfew", "feverfew", "featherfew",
     "fetherfew", "feuerfew"),
    ("Ingredients: Plants and Herbs", "fig", "fig", "figge", "figs", "figges"),
    ("Ingredients: Plants and Herbs", "fumitory", "fumitory", "fumitorie", "fumiterry"),
    ("Ingredients: Plants and Herbs", "galangal", "galangal", "galingale",
     "gallingale"),
    ("Ingredients: Plants and Herbs", "garlic", "garlic", "garlick", "garlicke",
     "garlike"),
    ("Ingredients: Plants and Herbs", "gentian", "gentian", "gentiane"),
    ("Ingredients: Plants and Herbs", "ginger", "ginger", "gingar", "gynger"),
    ("Ingredients: Plants and Herbs", "hart's tongue", "hartstongue",
     "harts tongue", "hartstong"),
    ("Ingredients: Plants and Herbs", "hellebore", "hellebore", "hellibore",
     "ellebore"),
    ("Ingredients: Plants and Herbs", "henbane", "henbane", "henebane"),
    ("Ingredients: Plants and Herbs", "horehound", "horehound", "hoarhound",
     "hoarhounde", "horehounde"),
    ("Ingredients: Plants and Herbs", "horseradish", "horseradish", "horse-radish",
     "horseradishe"),
    ("Ingredients: Plants and Herbs", "hyssop", "hyssop", "hysope", "hyssope",
     "isope", "isop"),
    ("Ingredients: Plants and Herbs", "juniper", "juniper", "iuniper", "juniperus"),
    ("Ingredients: Plants and Herbs", "lavender", "lavender", "lauender",
     "lavander", "lauander"),
    ("Ingredients: Plants and Herbs", "lemon", "lemon", "lemmon", "limon",
     "lemmons", "lemons"),
    ("Ingredients: Plants and Herbs", "lettuce", "lettuce", "lettice", "lettise",
     "lettuse"),
    ("Ingredients: Plants and Herbs", "licorice", "licorice", "liquorice",
     "liquorish", "lickerish", "liccorice", "liquoryce"),
    ("Ingredients: Plants and Herbs", "lily", "lily", "lillie", "lillies", "lilly"),
    ("Ingredients: Plants and Herbs", "liverwort", "liverwort", "liuerwort",
     "lyuerwort"),
    ("Ingredients: Plants and Herbs", "lovage", "lovage", "louage"),
    ("Ingredients: Plants and Herbs", "mace", "mace"),
    ("Ingredients: Plants and Herbs", "maidenhair", "maidenhair", "maiden-hair",
     "maidenhaire", "maidenhayer"),
    ("Ingredients: Plants and Herbs", "mallow", "mallow", "mallowes", "mallows",
     "mallowe"),
    ("Ingredients: Plants and Herbs", "marigold", "marigold", "marigolde",
     "marygolde", "marygold", "marigolds"),
    ("Ingredients: Plants and Herbs", "marjoram", "marjoram", "margerome",
     "marierome", "marjorame", "marjerome"),
    ("Ingredients: Plants and Herbs", "mint", "mint", "minte", "mynt", "mynts"),
    ("Ingredients: Plants and Herbs", "motherwort", "motherwort", "motherworte"),
    ("Ingredients: Plants and Herbs", "mugwort", "mugwort", "mugworte"),
    ("Ingredients: Plants and Herbs", "mullein", "mullein", "mullen", "mullain"),
    ("Ingredients: Plants and Herbs", "mustard", "mustard", "mustarde", "musterd"),
    ("Ingredients: Plants and Herbs", "nettle", "nettle", "nettles", "nettell"),
    ("Ingredients: Plants and Herbs", "nutmeg", "nutmeg", "nutmegg", "nutmeggs",
     "nutmegge"),
    ("Ingredients: Plants and Herbs", "orange", "orange", "orrange", "orenges",
     "oranges"),
    ("Ingredients: Plants and Herbs", "oregano", "oregano", "organie", "origanum"),
    ("Ingredients: Plants and Herbs", "parsley", "parsley", "parsely", "parsly",
     "persly", "persley"),
    ("Ingredients: Plants and Herbs", "pellitory", "pellitory", "pellitorie",
     "pellitore"),
    ("Ingredients: Plants and Herbs", "pennyroyal", "pennyroyal", "pennyroyall",
     "pulioll", "peniryall"),
    ("Ingredients: Plants and Herbs", "pepper", "pepper", "peper", "peppar"),
    ("Ingredients: Plants and Herbs", "pimpernel", "pimpernel", "pimpernell",
     "pimpernelle"),
    ("Ingredients: Plants and Herbs", "plantain", "plantain", "plantaine",
     "plantane", "plantanes"),
    ("Ingredients: Plants and Herbs", "poppy", "poppy", "poppie", "poppey"),
    ("Ingredients: Plants and Herbs", "primrose", "primrose", "primerose",
     "primroses"),
    ("Ingredients: Plants and Herbs", "purslane", "purslane", "purslaine",
     "purselaine"),
    ("Ingredients: Plants and Herbs", "raisin", "raisin", "raisins", "raysins",
     "reasons", "reasins"),
    ("Ingredients: Plants and Herbs", "rhubarb", "rhubarb", "rubarb", "rhubarbe",
     "rewbarbe"),
    ("Ingredients: Plants and Herbs", "rocket", "rocket", "rockett"),
    ("Ingredients: Plants and Herbs", "rose", "rose", "roses"),
    ("Ingredients: Plants and Herbs", "rosemary", "rosemary", "rosemarye",
     "rosemarie"),
    ("Ingredients: Plants and Herbs", "rue", "rue", "rewe"),
    ("Ingredients: Plants and Herbs", "saffron", "saffron", "saffroun",
     "safforne", "safferon"),
    ("Ingredients: Plants and Herbs", "sage", "sage"),
    ("Ingredients: Plants and Herbs", "sanicle", "sanicle", "sanikle"),
    ("Ingredients: Plants and Herbs", "sassafras", "sassafras", "sassaphras",
     "sasafras"),
    ("Ingredients: Plants and Herbs", "savory", "savory", "sauorie", "savorie",
     "sauery"),
    ("Ingredients: Plants and Herbs", "scabious", "scabious", "scabiouse",
     "scabius"),
    ("Ingredients: Plants and Herbs", "sloe", "sloe", "sloes", "sloos"),
    ("Ingredients: Plants and Herbs", "smallage", "smallage", "smalladge"),
    ("Ingredients: Plants and Herbs", "sorrel", "sorrel", "sorell", "sorrell"),
    ("Ingredients: Plants and Herbs", "southernwood", "southernwood",
     "southernwoode"),
    ("Ingredients: Plants and Herbs", "strawberry", "strawberry", "strawberrie",
     "strawberie"),
    ("Ingredients: Plants and Herbs", "tansy", "tansy", "tansie", "tansye",
     "tansey"),
    ("Ingredients: Plants and Herbs", "thyme", "thyme", "thime", "tyme", "time"),
    ("Ingredients: Plants and Herbs", "tormentil", "tormentil", "tormentill"),
    ("Ingredients: Plants and Herbs", "turmeric", "turmeric", "turmericke",
     "turmerike"),
    ("Ingredients: Plants and Herbs", "valerian", "valerian", "valeriane"),
    ("Ingredients: Plants and Herbs", "vervain", "vervain", "veruaine", "vervaine",
     "veruain"),
    ("Ingredients: Plants and Herbs", "violet", "violet", "voilett", "violett",
     "violets", "violettes"),
    ("Ingredients: Plants and Herbs", "walnut", "walnut", "wallnutt", "walnuts",
     "wallnutts"),
    ("Ingredients: Plants and Herbs", "watercress", "watercress", "water-cresses"),
    ("Ingredients: Plants and Herbs", "woodruff", "woodruff", "woodroofe"),
    ("Ingredients: Plants and Herbs", "wormwood", "wormwood", "wormewood",
     "wormewoode", "wormwoode"),
    ("Ingredients: Plants and Herbs", "yarrow", "yarrow", "yarrowe"),

    # ── 2. INGREDIENTS: ANIMAL PRODUCTS ───────────────────────

    ("Ingredients: Animal Products", "ambergris", "ambergris", "ambergreece",
     "ambergrease", "ambergreese"),
    ("Ingredients: Animal Products", "beef", "beef", "beefe", "biefe"),
    ("Ingredients: Animal Products", "butter", "butter", "buttar", "butt"),
    ("Ingredients: Animal Products", "castoreum", "castoreum", "castorium"),
    ("Ingredients: Animal Products", "civet", "civet", "ciuet", "ciuett"),
    ("Ingredients: Animal Products", "cock", "cock", "cocke", "cocks"),
    ("Ingredients: Animal Products", "cream", "cream", "creame", "creme"),
    ("Ingredients: Animal Products", "dove's dung", "doves dung", "doues dunge"),
    ("Ingredients: Animal Products", "egg", "egg", "egge", "eggs", "egges"),
    ("Ingredients: Animal Products", "goose grease", "goose-grease", "goose grease"),
    ("Ingredients: Animal Products", "hartshorn", "hartshorn", "harts-horn",
     "harts horne", "hartshorne"),
    ("Ingredients: Animal Products", "honey", "honey", "hony", "honney", "hunny"),
    ("Ingredients: Animal Products", "isinglass", "isinglass", "isinglasse",
     "isenglasse"),
    ("Ingredients: Animal Products", "lard", "lard", "larde"),
    ("Ingredients: Animal Products", "milk", "milk", "milke", "mylk", "mylke"),
    ("Ingredients: Animal Products", "musk", "musk", "muske", "muusk"),
    ("Ingredients: Animal Products", "mutton", "mutton", "muttone"),
    ("Ingredients: Animal Products", "neat's foot", "neats foot", "neats foote",
     "neates foote"),
    ("Ingredients: Animal Products", "ox", "ox", "oxe"),
    ("Ingredients: Animal Products", "rennet", "rennet", "rennett", "runnet",
     "runnett"),
    ("Ingredients: Animal Products", "snail", "snail", "snaile", "snailes",
     "snails"),
    ("Ingredients: Animal Products", "spermaceti", "spermaceti", "sperma ceti",
     "spermacetti"),
    ("Ingredients: Animal Products", "suet", "suet", "suett", "sewet"),
    ("Ingredients: Animal Products", "tallow", "tallow", "tallowe"),
    ("Ingredients: Animal Products", "veal", "veal", "veale", "veall"),
    ("Ingredients: Animal Products", "wax", "wax", "waxe"),
    ("Ingredients: Animal Products", "whey", "whey", "whay", "wheye"),

    # ── 3. INGREDIENTS: MINERALS AND CHEMICALS ────────────────

    ("Ingredients: Minerals and Chemicals", "alum", "alum", "allum", "allome",
     "alome"),
    ("Ingredients: Minerals and Chemicals", "antimony", "antimony", "antimonie"),
    ("Ingredients: Minerals and Chemicals", "aqua fortis", "aqua fortis",
     "aquafortis"),
    ("Ingredients: Minerals and Chemicals", "arsenic", "arsenic", "arsenick",
     "arsenicke"),
    ("Ingredients: Minerals and Chemicals", "bole armeniac", "bole armeniac",
     "bole armoniack", "bole armoniacke"),
    ("Ingredients: Minerals and Chemicals", "borax", "borax", "borace", "borrax"),
    ("Ingredients: Minerals and Chemicals", "brimstone", "brimstone", "brimston",
     "brymstone"),
    ("Ingredients: Minerals and Chemicals", "camphor", "camphor", "camphire",
     "camphore", "camphyre"),
    ("Ingredients: Minerals and Chemicals", "ceruse", "ceruse", "ceruce"),
    ("Ingredients: Minerals and Chemicals", "chalk", "chalk", "chalke"),
    ("Ingredients: Minerals and Chemicals", "copperas", "copperas", "coperas",
     "copparis"),
    ("Ingredients: Minerals and Chemicals", "corrosive sublimate",
     "corrosive sublimate", "corrasiue sublimate"),
    ("Ingredients: Minerals and Chemicals", "cream of tartar", "cream of tartar",
     "creame of tartar", "creme of tartar"),
    ("Ingredients: Minerals and Chemicals", "litharge", "litharge", "litarge",
     "lytharge"),
    ("Ingredients: Minerals and Chemicals", "mercury", "mercury", "mercurie",
     "quicksilver", "quickesiluer"),
    ("Ingredients: Minerals and Chemicals", "nitre", "nitre", "niter", "nitre",
     "niter"),
    ("Ingredients: Minerals and Chemicals", "oil of vitriol", "oil of vitriol",
     "oyle of vitrioll"),
    ("Ingredients: Minerals and Chemicals", "orpiment", "orpiment", "orpimente"),
    ("Ingredients: Minerals and Chemicals", "pearl", "pearl", "pearle", "perle"),
    ("Ingredients: Minerals and Chemicals", "sal ammoniac", "sal ammoniac",
     "sal armoniack", "sall armoniack"),
    ("Ingredients: Minerals and Chemicals", "saltpeter", "saltpeter", "saltpetre",
     "salt peter", "salt-peter", "salt-petre"),
    ("Ingredients: Minerals and Chemicals", "spirit of wine", "spirit of wine",
     "spiritt of wine", "spirits of wine"),
    ("Ingredients: Minerals and Chemicals", "sugar", "sugar", "suger", "suggar",
     "shugar"),
    ("Ingredients: Minerals and Chemicals", "sulphur", "sulphur", "sulphure",
     "sulfur"),
    ("Ingredients: Minerals and Chemicals", "tartar", "tartar", "tartre"),
    ("Ingredients: Minerals and Chemicals", "treacle", "treacle", "triacle",
     "triakle", "trekle", "treakle"),
    ("Ingredients: Minerals and Chemicals", "tutty", "tutty", "tuttie", "tutia"),
    ("Ingredients: Minerals and Chemicals", "verdigris", "verdigris", "verdigrease",
     "verdigreece", "verdigrece"),
    ("Ingredients: Minerals and Chemicals", "vinegar", "vinegar", "vineger",
     "vinagar", "vinigar"),
    ("Ingredients: Minerals and Chemicals", "vitriol", "vitriol", "vitrioll",
     "vittrioll"),

    # ── 4. MEDICAL AND AILMENT TERMS ──────────────────────────

    ("Medical and Ailment Terms", "ague", "ague", "agew", "agewe"),
    ("Medical and Ailment Terms", "apoplexy", "apoplexy", "apoplexie", "apoplexey"),
    ("Medical and Ailment Terms", "asthma", "asthma", "asma", "asthma"),
    ("Medical and Ailment Terms", "bleeding", "bleeding", "bleading", "bleedinge"),
    ("Medical and Ailment Terms", "bruise", "bruise", "bruise", "bruse"),
    ("Medical and Ailment Terms", "burn", "burn", "burne", "burnes"),
    ("Medical and Ailment Terms", "canker", "canker", "cancor", "cancker"),
    ("Medical and Ailment Terms", "catarrh", "catarrh", "catarr", "catarre"),
    ("Medical and Ailment Terms", "cholera", "cholera", "colera"),
    ("Medical and Ailment Terms", "colic", "colic", "collicke", "collick",
     "cholick", "collique"),
    ("Medical and Ailment Terms", "consumption", "consumption", "consumptione",
     "consumtion"),
    ("Medical and Ailment Terms", "convulsion", "convulsion", "conuulsion",
     "convultions"),
    ("Medical and Ailment Terms", "cough", "cough", "coughe", "couffe"),
    ("Medical and Ailment Terms", "dropsy", "dropsy", "dropsie", "dropsye"),
    ("Medical and Ailment Terms", "dysentery", "dysentery", "disentery",
     "dysenterie"),
    ("Medical and Ailment Terms", "epilepsy", "epilepsy", "epilepsie",
     "falling sickness"),
    ("Medical and Ailment Terms", "erysipelas", "erysipelas", "erisipelas"),
    ("Medical and Ailment Terms", "fever", "fever", "feuer", "feavor",
     "feaver", "feavour"),
    ("Medical and Ailment Terms", "fistula", "fistula", "fistulae"),
    ("Medical and Ailment Terms", "flux", "flux", "fluxe"),
    ("Medical and Ailment Terms", "gout", "gout", "goute", "gowte"),
    ("Medical and Ailment Terms", "gravel", "gravel", "grauell", "gravell"),
    ("Medical and Ailment Terms", "green sickness", "green sickness",
     "greene sicknesse"),
    ("Medical and Ailment Terms", "griping", "griping", "gripeing",
     "gripinge"),
    ("Medical and Ailment Terms", "imposthume", "imposthume", "impostume",
     "impostume", "imposteme"),
    ("Medical and Ailment Terms", "infection", "infection", "infectione"),
    ("Medical and Ailment Terms", "inflammation", "inflammation",
     "inflamation", "inflamacion"),
    ("Medical and Ailment Terms", "jaundice", "jaundice", "jaundies",
     "jaunders", "jandise", "jandies"),
    ("Medical and Ailment Terms", "king's evil", "kings evil",
     "kings euill", "kings euil"),
    ("Medical and Ailment Terms", "leprosy", "leprosy", "leprosie",
     "leprosye"),
    ("Medical and Ailment Terms", "lethargy", "lethargy", "lethargye",
     "lethargie"),
    ("Medical and Ailment Terms", "measles", "measles", "maisles",
     "mesells"),
    ("Medical and Ailment Terms", "melancholy", "melancholy", "melancholly",
     "melancholie"),
    ("Medical and Ailment Terms", "palsy", "palsy", "palsie", "palsye"),
    ("Medical and Ailment Terms", "pestilence", "pestilence", "pestilens",
     "pestilance"),
    ("Medical and Ailment Terms", "piles", "piles", "pyles", "pyles"),
    ("Medical and Ailment Terms", "plague", "plague", "plage"),
    ("Medical and Ailment Terms", "pleurisy", "pleurisy", "pleurisie",
     "plurisie", "plurisy"),
    ("Medical and Ailment Terms", "quinsy", "quinsy", "quinsie", "squinancie"),
    ("Medical and Ailment Terms", "rheum", "rheum", "rheume", "rume"),
    ("Medical and Ailment Terms", "rickets", "rickets", "ricketts",
     "rickitts"),
    ("Medical and Ailment Terms", "sciatica", "sciatica", "siatica",
     "sciattica"),
    ("Medical and Ailment Terms", "scurvy", "scurvy", "scuruie", "scuruy",
     "scuruey"),
    ("Medical and Ailment Terms", "smallpox", "smallpox", "small pox",
     "small-pox", "small pockes"),
    ("Medical and Ailment Terms", "stone", "stone", "stoane"),
    ("Medical and Ailment Terms", "surfeit", "surfeit", "surfeite",
     "surfett", "surfit"),
    ("Medical and Ailment Terms", "swelling", "swelling", "swellinge",
     "swellings"),
    ("Medical and Ailment Terms", "tympany", "tympany", "tympanie",
     "timpany"),
    ("Medical and Ailment Terms", "ulcer", "ulcer", "vlcer", "vlcers",
     "ulcers"),
    ("Medical and Ailment Terms", "vertigo", "vertigo", "vertigoe"),
    ("Medical and Ailment Terms", "worms", "worms", "wormes"),
    ("Medical and Ailment Terms", "wound", "wound", "wounde", "woundes"),

    # ── 5. BODY PARTS ─────────────────────────────────────────

    ("Body Parts", "belly", "belly", "bellie", "bellye"),
    ("Body Parts", "blood", "blood", "bloode", "bloud", "blud"),
    ("Body Parts", "bowels", "bowels", "bowells", "boweles"),
    ("Body Parts", "brain", "brain", "braine", "brayne"),
    ("Body Parts", "breast", "breast", "brest", "breste"),
    ("Body Parts", "ear", "ear", "eare", "eares"),
    ("Body Parts", "eye", "eye", "eie", "eies", "eyes"),
    ("Body Parts", "fundament", "fundament", "fundamente"),
    ("Body Parts", "gums", "gums", "gummes", "gumms"),
    ("Body Parts", "head", "head", "heade"),
    ("Body Parts", "heart", "heart", "harte", "hearte", "hart"),
    ("Body Parts", "kidney", "kidney", "kidneys", "kidnies", "kidnyes"),
    ("Body Parts", "liver", "liver", "liuer", "lyuer"),
    ("Body Parts", "lungs", "lungs", "lungues", "lunges"),
    ("Body Parts", "maw", "maw", "mawe"),
    ("Body Parts", "navel", "navel", "nauell", "navell"),
    ("Body Parts", "reins", "reins", "reines", "reynes"),
    ("Body Parts", "sinew", "sinew", "sinowe", "sinnew", "sinewes"),
    ("Body Parts", "skin", "skin", "skinne", "skinn"),
    ("Body Parts", "spleen", "spleen", "splene", "spleene"),
    ("Body Parts", "stomach", "stomach", "stomacke", "stomack", "stomake"),
    ("Body Parts", "teeth", "teeth", "teethe"),
    ("Body Parts", "throat", "throat", "throte", "throate"),
    ("Body Parts", "tongue", "tongue", "tounge", "tonge"),
    ("Body Parts", "womb", "womb", "wombe"),

    # ── 6. PREPARATION AND PROCESS VERBS ──────────────────────

    ("Preparation and Process Verbs", "anoint", "anoint", "annoynt",
     "annoint", "annointe"),
    ("Preparation and Process Verbs", "apply", "apply", "applye"),
    ("Preparation and Process Verbs", "bake", "bake"),
    ("Preparation and Process Verbs", "boil", "boil", "boile", "boyle",
     "boyll", "byle"),
    ("Preparation and Process Verbs", "bruise", "bruise", "bruse", "bruze"),
    ("Preparation and Process Verbs", "calcinate", "calcinate", "calcine",
     "calcinated"),
    ("Preparation and Process Verbs", "candy", "candy", "candie", "candye"),
    ("Preparation and Process Verbs", "clarify", "clarify", "clarifie",
     "clarifye"),
    ("Preparation and Process Verbs", "cleanse", "cleanse", "clense",
     "clense"),
    ("Preparation and Process Verbs", "decoct", "decoct", "decocte",
     "decoction"),
    ("Preparation and Process Verbs", "digest", "digest", "digeste"),
    ("Preparation and Process Verbs", "dissolve", "dissolve", "dissoule",
     "dissolue", "disolue"),
    ("Preparation and Process Verbs", "distill", "distill", "distil",
     "distille", "distyll"),
    ("Preparation and Process Verbs", "dry", "dry", "drye", "drie"),
    ("Preparation and Process Verbs", "evaporate", "evaporate", "euaporate"),
    ("Preparation and Process Verbs", "ferment", "ferment", "fermente"),
    ("Preparation and Process Verbs", "filter", "filter", "filtre",
     "filtrate"),
    ("Preparation and Process Verbs", "gargle", "gargle", "gargarise"),
    ("Preparation and Process Verbs", "garnish", "garnish", "garnishe"),
    ("Preparation and Process Verbs", "grate", "grate"),
    ("Preparation and Process Verbs", "grind", "grind", "grinde", "grynd"),
    ("Preparation and Process Verbs", "incorporate", "incorporate",
     "incorporat", "incorporate"),
    ("Preparation and Process Verbs", "infuse", "infuse", "infuze"),
    ("Preparation and Process Verbs", "knead", "knead", "kneade"),
    ("Preparation and Process Verbs", "mingle", "mingle", "myngell",
     "myngle"),
    ("Preparation and Process Verbs", "mix", "mix", "mixe"),
    ("Preparation and Process Verbs", "pare", "pare"),
    ("Preparation and Process Verbs", "pickle", "pickle", "pikle"),
    ("Preparation and Process Verbs", "poultice", "poultice", "poultis",
     "pultes", "pultis"),
    ("Preparation and Process Verbs", "pound", "pound", "pounde"),
    ("Preparation and Process Verbs", "preserve", "preserve", "preserue"),
    ("Preparation and Process Verbs", "purge", "purge"),
    ("Preparation and Process Verbs", "scum", "scum", "scumme"),
    ("Preparation and Process Verbs", "seethe", "seethe", "seeth", "seethe"),
    ("Preparation and Process Verbs", "sift", "sift", "sifte", "syft"),
    ("Preparation and Process Verbs", "simmer", "simmer", "simer"),
    ("Preparation and Process Verbs", "slice", "slice", "slyce"),
    ("Preparation and Process Verbs", "stamp", "stamp", "stampe"),
    ("Preparation and Process Verbs", "steep", "steep", "steepe"),
    ("Preparation and Process Verbs", "stir", "stir", "stirr", "stirre",
     "stire"),
    ("Preparation and Process Verbs", "strain", "strain", "straine",
     "strayne", "streyne"),
    ("Preparation and Process Verbs", "take", "take"),
    ("Preparation and Process Verbs", "temper", "temper", "tamper"),

    # ── 7. MEASUREMENT TERMS ──────────────────────────────────

    ("Measurement Terms", "dram", "dram", "dramme", "drame", "drams",
     "drammes"),
    ("Measurement Terms", "drop", "drop", "droppe", "drops", "droppes"),
    ("Measurement Terms", "gallon", "gallon", "gallone", "gallons",
     "gallones"),
    ("Measurement Terms", "gill", "gill", "gille", "gills"),
    ("Measurement Terms", "grain", "grain", "graine", "graines", "grains"),
    ("Measurement Terms", "handful", "handful", "handfull", "handfulle",
     "handfuls", "handfulls"),
    ("Measurement Terms", "ounce", "ounce", "ounces", "ownce", "ownces"),
    ("Measurement Terms", "penny", "penny", "peny", "penie"),
    ("Measurement Terms", "pennyweight", "pennyweight", "pennywaight",
     "peniweight"),
    ("Measurement Terms", "pennyworth", "pennyworth", "pennywoorthe",
     "peniworth"),
    ("Measurement Terms", "pint", "pint", "pinte", "pints", "pintes"),
    ("Measurement Terms", "pottle", "pottle", "pottell", "pottel"),
    ("Measurement Terms", "pound", "pound", "pounde", "pounds", "poundes"),
    ("Measurement Terms", "quart", "quart", "quarte", "quarts", "quartes"),
    ("Measurement Terms", "quarter", "quarter"),
    ("Measurement Terms", "scruple", "scruple", "scrupell", "scruples",
     "scrupells"),
    ("Measurement Terms", "spoonful", "spoonful", "spoonfull", "spoonefulle",
     "spoonfuls", "spoonfulls"),

    # ── 8. EQUIPMENT AND VESSELS ──────────────────────────────

    ("Equipment and Vessels", "alembic", "alembic", "limbeck", "limbecke",
     "lymbeck", "alembick"),
    ("Equipment and Vessels", "bladder", "bladder", "blather", "blader"),
    ("Equipment and Vessels", "bolthead", "bolthead", "bolt-head"),
    ("Equipment and Vessels", "chafing dish", "chafing dish", "chafingdish",
     "chafing-dish", "chafeing dish"),
    ("Equipment and Vessels", "cloth", "cloth", "clothe", "cloath"),
    ("Equipment and Vessels", "crucible", "crucible", "crusible"),
    ("Equipment and Vessels", "distillery", "distillery", "stillitory",
     "stillatorie", "stillatorie"),
    ("Equipment and Vessels", "earthen pot", "earthen pot", "earthen pott",
     "earthen-pot"),
    ("Equipment and Vessels", "furnace", "furnace", "fornace", "fornaise"),
    ("Equipment and Vessels", "gallipot", "gallipot", "gallypot",
     "gally-pot", "gally pot"),
    ("Equipment and Vessels", "kettle", "kettle", "kettell", "ketle"),
    ("Equipment and Vessels", "ladle", "ladle", "ladell"),
    ("Equipment and Vessels", "mortar", "mortar", "morter", "mortor"),
    ("Equipment and Vessels", "oven", "oven", "ouen", "ouen"),
    ("Equipment and Vessels", "pan", "pan", "panne"),
    ("Equipment and Vessels", "pestle", "pestle", "pestell", "pestel"),
    ("Equipment and Vessels", "pipkin", "pipkin", "pipkine", "pypkin"),
    ("Equipment and Vessels", "plaster", "plaster", "plaister", "playster",
     "plaistre"),
    ("Equipment and Vessels", "posnet", "posnet", "posnett", "possnett"),
    ("Equipment and Vessels", "pot", "pot", "pott", "potte"),
    ("Equipment and Vessels", "receiver", "receiver", "receiuer"),
    ("Equipment and Vessels", "retort", "retort", "retorte"),
    ("Equipment and Vessels", "salve", "salve", "salue", "saue"),
    ("Equipment and Vessels", "skillet", "skillet", "skilet", "skellet",
     "skellat"),
    ("Equipment and Vessels", "syringe", "syringe", "syrindge", "seringe"),
    ("Equipment and Vessels", "vessel", "vessel", "vessell", "vesel"),

    # ── 9. COMMON EARLY MODERN SPELLING VARIANTS ──────────────
    # These are normal English words but with distinctive historical
    # spellings that an AI transcriber might not recognize.

    ("Common Early Modern Spelling Variants", "about", "aboute"),
    ("Common Early Modern Spelling Variants", "against", "againste", "agaynst"),
    ("Common Early Modern Spelling Variants", "also", "allso", "alsoe"),
    ("Common Early Modern Spelling Variants", "although", "allthough", "althoughe"),
    ("Common Early Modern Spelling Variants", "always", "alwayes", "allwayes", "alwaies"),
    ("Common Early Modern Spelling Variants", "before", "bfore", "befor"),
    ("Common Early Modern Spelling Variants", "being", "beeing", "beinge"),
    ("Common Early Modern Spelling Variants", "between", "betweene", "betwixt"),
    ("Common Early Modern Spelling Variants", "blood", "bloud", "bloude", "blude"),
    ("Common Early Modern Spelling Variants", "body", "bodie", "bodye"),
    ("Common Early Modern Spelling Variants", "both", "bothe"),
    ("Common Early Modern Spelling Variants", "clean", "cleane"),
    ("Common Early Modern Spelling Variants", "cold", "colde", "coulde"),
    ("Common Early Modern Spelling Variants", "cordial", "cordiall", "cordiell"),
    ("Common Early Modern Spelling Variants", "day", "daye", "daie"),
    ("Common Early Modern Spelling Variants", "do", "doe", "doo"),
    ("Common Early Modern Spelling Variants", "drink", "drinke", "drincke"),
    ("Common Early Modern Spelling Variants", "eat", "eate"),
    ("Common Early Modern Spelling Variants", "enough", "enoughe", "inough",
     "inoughe", "ynough"),
    ("Common Early Modern Spelling Variants", "evening", "euenynde", "euening", "eueninge"),
    ("Common Early Modern Spelling Variants", "every", "euery", "euerie"),
    ("Common Early Modern Spelling Variants", "fair", "faire", "fayre"),
    ("Common Early Modern Spelling Variants", "give", "giue"),
    ("Common Early Modern Spelling Variants", "good", "goode"),
    ("Common Early Modern Spelling Variants", "great", "greate"),
    ("Common Early Modern Spelling Variants", "half", "halfe"),
    ("Common Early Modern Spelling Variants", "have", "haue"),
    ("Common Early Modern Spelling Variants", "heat", "heate"),
    ("Common Early Modern Spelling Variants", "herb", "hearbe", "herbe"),
    ("Common Early Modern Spelling Variants", "hour", "houre", "hower", "howre"),
    ("Common Early Modern Spelling Variants", "it", "itt"),
    ("Common Early Modern Spelling Variants", "juice", "juyce", "iuyce", "iuice"),
    ("Common Early Modern Spelling Variants", "know", "knowe"),
    ("Common Early Modern Spelling Variants", "let", "lett", "lete"),
    ("Common Early Modern Spelling Variants", "little", "litle", "littel", "lytle"),
    ("Common Early Modern Spelling Variants", "long", "longe"),
    ("Common Early Modern Spelling Variants", "manner", "maner"),
    ("Common Early Modern Spelling Variants", "morning", "morninge", "mornynge"),
    ("Common Early Modern Spelling Variants", "much", "mutch", "muche"),
    ("Common Early Modern Spelling Variants", "night", "nighte", "nyght"),
    ("Common Early Modern Spelling Variants", "nothing", "nothinge"),
    ("Common Early Modern Spelling Variants", "oil", "oyle", "oile", "oyl"),
    ("Common Early Modern Spelling Variants", "only", "onely", "onelie"),
    ("Common Early Modern Spelling Variants", "other", "othre"),
    ("Common Early Modern Spelling Variants", "physic", "phisicke", "phisick",
     "physick", "physicke", "physik"),
    ("Common Early Modern Spelling Variants", "powder", "pouder", "poudre", "poulder"),
    ("Common Early Modern Spelling Variants", "put", "putt", "putte"),
    ("Common Early Modern Spelling Variants", "quantity", "quantitie", "quantitye"),
    ("Common Early Modern Spelling Variants", "receipt/recipe", "receite",
     "receit", "receipt", "receipte", "recipe"),
    ("Common Early Modern Spelling Variants", "said", "saide", "sayde"),
    ("Common Early Modern Spelling Variants", "same", "sameinge", "samen"),
    ("Common Early Modern Spelling Variants", "serve", "serue"),
    ("Common Early Modern Spelling Variants", "set", "sett", "sette"),
    ("Common Early Modern Spelling Variants", "soap", "sope", "soape"),
    ("Common Early Modern Spelling Variants", "some", "som"),
    ("Common Early Modern Spelling Variants", "sovereign", "soueraigne",
     "souerayne", "soueraine"),
    ("Common Early Modern Spelling Variants", "sugar", "suger", "suggar", "shugar"),
    ("Common Early Modern Spelling Variants", "surgery", "chirurgery",
     "chirurgerie", "chirurgion"),
    ("Common Early Modern Spelling Variants", "syrup", "syrrup", "sirrup",
     "sirrupe", "syrrupe", "syrupe"),
    ("Common Early Modern Spelling Variants", "the", "ye"),
    ("Common Early Modern Spelling Variants", "then", "thenn"),
    ("Common Early Modern Spelling Variants", "there", "ther"),
    ("Common Early Modern Spelling Variants", "these", "theis", "theise"),
    ("Common Early Modern Spelling Variants", "this", "thiss"),
    ("Common Early Modern Spelling Variants", "together", "togeather",
     "togither", "togeither"),
    ("Common Early Modern Spelling Variants", "upon", "vpon", "vppon"),
    ("Common Early Modern Spelling Variants", "unto", "vnto"),
    ("Common Early Modern Spelling Variants", "use", "vse"),
    ("Common Early Modern Spelling Variants", "very", "verie", "verye"),
    ("Common Early Modern Spelling Variants", "warm", "warme"),
    ("Common Early Modern Spelling Variants", "wash", "washe"),
    ("Common Early Modern Spelling Variants", "water", "watter", "watir", "wattar"),
    ("Common Early Modern Spelling Variants", "well", "welle"),
    ("Common Early Modern Spelling Variants", "when", "whenn"),
    ("Common Early Modern Spelling Variants", "white", "whyte", "whit"),
    ("Common Early Modern Spelling Variants", "whole", "whoale"),
    ("Common Early Modern Spelling Variants", "wine", "wyne", "winn"),
    ("Common Early Modern Spelling Variants", "with", "w^th", "wth"),
    ("Common Early Modern Spelling Variants", "yellow", "yellowe"),

    # ── 10. LATIN AND FRENCH TERMS ────────────────────────────

    ("Latin and French Terms", "ana (of each)", "ana"),
    ("Latin and French Terms", "aqua vitae", "aqua vitae", "aqua-vitae", "aquavitae"),
    ("Latin and French Terms", "conserve", "conserve", "conserue"),
    ("Latin and French Terms", "decoction", "decoction", "decoccion"),
    ("Latin and French Terms", "drachm", "drachm", "drachme"),
    ("Latin and French Terms", "electuary", "electuary", "electuarie", "electuarye"),
    ("Latin and French Terms", "emplastrum", "emplastrum", "emplaistrum"),
    ("Latin and French Terms", "lapis calaminaris", "lapis calaminaris"),
    ("Latin and French Terms", "laudanum", "laudanum", "laudanuim"),
    ("Latin and French Terms", "manus Christi", "manus christi"),
    ("Latin and French Terms", "oleum", "oleum"),
    ("Latin and French Terms", "per se", "per se"),
    ("Latin and French Terms", "pharmacopoeia", "pharmacopoeia", "pharmacopaea"),
    ("Latin and French Terms", "posset", "posset", "possett", "possit", "possett"),
    ("Latin and French Terms", "probatum est", "probatum est", "probatum"),
    ("Latin and French Terms", "quantum sufficit", "quantum sufficit"),
    ("Latin and French Terms", "recipe (take)", "recipe"),
    ("Latin and French Terms", "solutio", "solutio"),
    ("Latin and French Terms", "species", "species"),
    ("Latin and French Terms", "spiritus", "spiritus"),
    ("Latin and French Terms", "tincture", "tincture", "tinctura"),
    ("Latin and French Terms", "unguentum", "unguentum", "unguent", "unguente"),

    # ── 11. ABBREVIATED FORMS AND CONTRACTIONS ────────────────

    ("Abbreviated Forms and Contractions", "the", "y^e", "ye"),
    ("Abbreviated Forms and Contractions", "that", "y^t", "yt"),
    ("Abbreviated Forms and Contractions", "with", "w^th", "wth"),
    ("Abbreviated Forms and Contractions", "which", "w^ch", "wch"),
    ("Abbreviated Forms and Contractions", "it is", "t'is", "tis"),
    ("Abbreviated Forms and Contractions", "and", "&"),
    ("Abbreviated Forms and Contractions", "et cetera", "&c"),
    ("Abbreviated Forms and Contractions", "-tion (suffix)", "tione", "cion", "cione"),
    ("Abbreviated Forms and Contractions", "Mistress", "Mrs", "M^rs"),
]


# ── Build the lookup dictionary from the entries above ──────
VOCAB_LOOKUP = {}
for _entry in _VOCAB_ENTRIES:
    _category = _entry[0]
    _modern = _entry[1]
    for _spelling in _entry[2:]:
        VOCAB_LOOKUP[_spelling.lower()] = (_category, _modern)

# The order categories should appear in the output file
CATEGORY_ORDER = [
    "Ingredients: Plants and Herbs",
    "Ingredients: Animal Products",
    "Ingredients: Minerals and Chemicals",
    "Medical and Ailment Terms",
    "Body Parts",
    "Preparation and Process Verbs",
    "Measurement Terms",
    "Equipment and Vessels",
    "Common Early Modern Spelling Variants",
    "Latin and French Terms",
    "Abbreviated Forms and Contractions",
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def fetch_url(url):
    """
    Download content from a URL and return it as text.
    Returns None if the download fails (and prints an error message).
    """
    try:
        req = Request(url, headers={
            "User-Agent": "RecipeVocabBuilder/1.0 (academic research project)"
        })
        response = urlopen(req, timeout=120)
        data = response.read()
        return data.decode("utf-8")
    except (URLError, HTTPError) as e:
        print(f"  ERROR: Could not download {url}")
        print(f"         Reason: {e}")
        return None
    except Exception as e:
        print(f"  ERROR: Unexpected problem downloading {url}")
        print(f"         Reason: {e}")
        return None


def make_short_id(label, work_id):
    """
    Create a short, readable ID from a manuscript's full title.
    """
    ms_match = re.search(r'\(MS\.?\s*(\w+)\)', label, re.IGNORECASE)
    ms_part = "MS" + ms_match.group(1) if ms_match else ""

    short = label
    for prefix in [
        "Wellcome Collection:", "Royal College of Physicians:",
        "College of Physicians of Philadelphia:",
        "London Metropolitan Archives:", "Thomas Fisher Rare Book Library:",
        "University of Guelph:", "Sample transcription:",
    ]:
        if short.startswith(prefix):
            short = short[len(prefix):]
    short = short.strip()

    skip_words = {
        "the", "a", "an", "lady", "mrs", "mrs.", "mr", "sir", "mistress",
        "recipe", "book", "medical", "receipts", "english", "culinary",
        "receipt-book", "cookery-books", "collection",
    }
    name_word = None
    for word in short.split():
        clean = word.strip(",.()[]:")
        if clean.lower() not in skip_words and len(clean) > 2:
            name_word = clean
            break

    if name_word and ms_part:
        return f"{name_word}-{ms_part}"
    elif name_word:
        return name_word
    elif ms_part:
        return ms_part
    else:
        return f"work-{work_id}"


def make_filename(short_id):
    """Turn a short ID into a safe filename."""
    safe = re.sub(r'[^a-zA-Z0-9\-]', '-', short_id)
    safe = re.sub(r'-+', '-', safe).strip('-')
    return safe.lower() + ".txt"


def clean_text(raw_text):
    """
    Clean raw transcription text by removing HTML, metadata, and
    editorial markup. Returns cleaned text as a string.
    """
    text = re.sub(r'<[^>]+>', '', raw_text)
    text = html.unescape(text)

    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append(line)
            continue
        if re.match(r'^\d+$', stripped):
            continue

        metadata_patterns = [
            r'^Wellcome\s+Historical\s+Medical\s+Library',
            r'^Wellcome\s+Library',
            r'^Royal\s+College\s+of\s+Physicians',
            r'^College\s+of\s+Physicians',
            r'^Folger\s+Shakespeare\s+Library',
            r'^London\s+Metropolitan\s+Archives',
            r'^Thomas\s+Fisher\s+Rare\s+Book',
            r'^University\s+of\s+Guelph',
            r'^Accession\s+(no|number)',
            r'^Shelf\s+mark',
            r'^Call\s+number',
            r'^MS\.?\s*\d+\s*$',
        ]
        is_metadata = False
        for pattern in metadata_patterns:
            if re.match(pattern, stripped, re.IGNORECASE):
                is_metadata = True
                break
        if is_metadata:
            continue
        cleaned_lines.append(line)

    text = '\n'.join(cleaned_lines)
    text = re.sub(r'\{\d+[rv]?\}', '', text)
    text = re.sub(r'\{[^}]*\}', '', text)
    text = re.sub(r'\[\.+\]', '', text)
    text = re.sub(r'\[([^\]]*)\]', r'\1', text)
    return text


def clean_herbal_ocr(raw_text):
    """
    Clean OCR text from Internet Archive djvu.txt files.

    Internet Archive OCR has different artifacts than FromThePage
    transcriptions: broken words across lines, stray characters,
    page headers/footers, and OCR misreadings. This function handles
    the most common issues.
    """
    text = raw_text

    # Strip common Internet Archive boilerplate
    # (often appears at the start/end of djvu.txt files)
    text = re.sub(r'(?i)^.*?internet archive.*?\n', '', text)
    text = re.sub(r'(?i)^.*?digitized by.*?\n', '', text)
    text = re.sub(r'(?i)^.*?generated.*?ocr.*?\n', '', text)

    # Remove page numbers that appear alone on a line
    text = re.sub(r'^\s*\d{1,4}\s*$', '', text, flags=re.MULTILINE)

    # Remove lines that are just repeated characters (OCR artifacts)
    # e.g., "----", "====", "......"
    text = re.sub(r'^[\-=\.~_]{3,}\s*$', '', text, flags=re.MULTILINE)

    # Remove stray single characters on their own line (OCR noise)
    text = re.sub(r'^\s*[^a-zA-Z\d]\s*$', '', text, flags=re.MULTILINE)

    # Decode HTML entities if any
    text = html.unescape(text)

    # Strip any HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    return text


def tokenize(text):
    """
    Split cleaned text into individual word tokens.
    """
    raw_tokens = text.split()
    words = []
    strip_chars = '.,;:!?()[]{}"""\'\'«»~*#=_<>/\\|@+`'

    for token in raw_tokens:
        word = token.strip(strip_chars)
        if not word:
            continue
        words.append(word)
    return words


def detect_primary_language(text):
    """
    Rough language detection based on common function words.
    """
    words = text.lower().split()[:500]
    word_set = set(words)

    scores = {
        "English": len(word_set & {
            "the", "and", "of", "to", "in", "that", "is", "for", "it",
            "with", "was", "his", "her", "but", "they", "have", "from",
            "take", "put", "boil", "water", "let",
        }),
        "German": len(word_set & {
            "der", "die", "das", "und", "ist", "ein", "eine", "nicht",
            "mit", "den", "dem", "sich", "auf", "fur", "von", "zu",
        }),
        "French": len(word_set & {
            "le", "la", "les", "de", "du", "des", "et", "en", "un", "une",
            "est", "que", "qui", "dans", "pour", "avec", "sur", "par",
        }),
        "Italian": len(word_set & {
            "il", "la", "di", "che", "un", "una", "per", "con", "del",
            "della", "sono", "si", "come", "questo", "anche", "piu",
        }),
        "Latin": len(word_set & {
            "et", "in", "est", "ad", "cum", "non", "sed", "ex",
            "per", "quod", "sunt", "qui", "quae", "ut", "ab",
        }),
    }

    best = max(scores, key=scores.get)
    if scores[best] < 3:
        return "English (uncertain)"
    return best


# ============================================================
# MAIN PIPELINE
# ============================================================


def main():
    print("=" * 60)
    print("  Early Modern Recipe Vocabulary Builder")
    print("  (with Herbals + EMROC source tracking)")
    print("=" * 60)
    print()

    # ── Create output directories ──────────────────────────────
    os.makedirs(RAW_TEXT_DIR, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # ──────────────────────────────────────────────────────────
    # STEP 1: Download manuscript transcriptions from FromThePage
    # ──────────────────────────────────────────────────────────

    print("STEP 1: Fetching manuscript collection from FromThePage...")
    print(f"  Collection URL: {COLLECTION_URL}")
    print()

    collection_json = fetch_url(COLLECTION_URL)
    if collection_json is None:
        print("FATAL: Could not download the collection. Check your internet connection.")
        sys.exit(1)

    collection = json.loads(collection_json)
    manifests = collection.get("manifests", [])
    print(f"  Found {len(manifests)} manuscripts in the collection.")
    print()

    # Build manuscript list with source type tagging
    manuscripts = []
    for m in manifests:
        manifest_url = m.get("@id", "")
        work_id_match = re.search(r'/iiif/(\d+)/manifest', manifest_url)
        if not work_id_match:
            continue

        work_id = work_id_match.group(1)
        label = m.get("label", f"Unknown manuscript {work_id}")
        service = m.get("service", {})
        pct_complete = service.get("pctComplete", 0)
        pct_transcribed = service.get("pctTranscribed", 0)
        completion = max(pct_complete, pct_transcribed) if pct_complete or pct_transcribed else 0

        short_id = make_short_id(label, work_id)
        filename = make_filename(short_id)

        # Tag EMROC manuscripts — these have triple-keyed transcriptions
        # and are higher quality than regular FromThePage crowd-sourced ones
        source_type = "EMROC" if work_id in EMROC_WORK_IDS else "FTP"

        manuscripts.append({
            "work_id": work_id,
            "label": label,
            "short_id": short_id,
            "filename": filename,
            "completion": completion,
            "source_type": source_type,
            "downloaded": False,
            "word_count": 0,
            "language": "Unknown",
            "error": None,
        })

    print(f"  Parsed {len(manuscripts)} manuscripts.")
    emroc_count = sum(1 for ms in manuscripts if ms["source_type"] == "EMROC")
    print(f"  ({emroc_count} are EMROC triple-keyed transcriptions)")
    print()

    # ── Download each manuscript's plaintext ───────────────────

    print("  Downloading plaintext transcriptions...")
    print("  (Pausing between downloads to be polite to the server.)")
    print()

    downloaded_count = 0
    failed_count = 0

    for i, ms in enumerate(manuscripts):
        filepath = os.path.join(RAW_TEXT_DIR, ms["filename"])
        progress = f"[{i+1}/{len(manuscripts)}]"

        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            print(f"  {progress} {ms['short_id']} — already downloaded, skipping")
            ms["downloaded"] = True
            downloaded_count += 1
            continue

        url = EXPORT_URL_TEMPLATE.format(work_id=ms["work_id"])
        print(f"  {progress} Downloading {ms['short_id']}...", end=" ", flush=True)

        text = fetch_url(url)

        if text is None:
            print("FAILED")
            ms["error"] = "Download failed"
            failed_count += 1
        elif len(text.strip()) == 0:
            print("EMPTY")
            ms["error"] = "Empty response"
            failed_count += 1
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"OK ({len(text):,} chars)")
            ms["downloaded"] = True
            downloaded_count += 1

        if i < len(manuscripts) - 1:
            time.sleep(REQUEST_DELAY)

    print()
    print(f"  FromThePage: {downloaded_count} succeeded, {failed_count} failed")
    print()

    # ──────────────────────────────────────────────────────────
    # STEP 1b: Download printed herbals from Internet Archive
    # ──────────────────────────────────────────────────────────

    print("STEP 1b: Downloading printed herbals from Internet Archive...")
    print()

    for herbal in HERBAL_SOURCES:
        filepath = os.path.join(RAW_TEXT_DIR, herbal["filename"])

        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            print(f"  {herbal['short_id']} — already downloaded, skipping")
            herbal["downloaded"] = True
            herbal["error"] = None
            continue

        print(f"  Downloading {herbal['short_id']}...", end=" ", flush=True)
        text = fetch_url(herbal["url"])

        if text is None:
            print("FAILED")
            herbal["downloaded"] = False
            herbal["error"] = "Download failed"
        elif len(text.strip()) == 0:
            print("EMPTY")
            herbal["downloaded"] = False
            herbal["error"] = "Empty response"
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"OK ({len(text):,} chars)")
            herbal["downloaded"] = True
            herbal["error"] = None

        time.sleep(REQUEST_DELAY)

    # Add herbals to the manuscripts list so they get processed together
    for herbal in HERBAL_SOURCES:
        manuscripts.append({
            "work_id": herbal["short_id"],
            "label": herbal["label"],
            "short_id": herbal["short_id"],
            "filename": herbal["filename"],
            "completion": 100,
            "source_type": herbal["source_type"],
            "downloaded": herbal.get("downloaded", False),
            "word_count": 0,
            "language": herbal["language"],
            "error": herbal.get("error"),
        })

    print()

    # ──────────────────────────────────────────────────────────
    # STEP 2: Clean and tokenize the text
    # ──────────────────────────────────────────────────────────

    print("STEP 2: Cleaning and tokenizing text...")
    print()

    manuscript_words = {}

    for ms in manuscripts:
        if not ms["downloaded"]:
            continue

        filepath = os.path.join(RAW_TEXT_DIR, ms["filename"])

        with open(filepath, "r", encoding="utf-8") as f:
            raw_text = f.read()

        # Use herbal-specific cleaning for Internet Archive OCR text
        if ms["source_type"] == "HERBAL":
            cleaned = clean_herbal_ocr(raw_text)
        else:
            ms["language"] = detect_primary_language(raw_text)
            cleaned = clean_text(raw_text)

        words = tokenize(cleaned)
        ms["word_count"] = len(words)
        manuscript_words[ms["short_id"]] = words

        tag = f"[{ms['source_type']}]"
        print(f"  {tag:8s} {ms['short_id']}: {len(words):,} words ({ms['language']})")

    total_words = sum(len(w) for w in manuscript_words.values())
    print()
    print(f"  Total words across all sources: {total_words:,}")
    print()

    # ──────────────────────────────────────────────────────────
    # STEP 3: Build frequency lists (with source type tracking)
    # ──────────────────────────────────────────────────────────

    print("STEP 3: Building word frequency lists...")
    print()

    # Build a lookup: short_id → source_type
    source_type_lookup = {ms["short_id"]: ms["source_type"] for ms in manuscripts}

    # Count frequencies (case-sensitive)
    word_total = Counter()
    word_by_ms = defaultdict(Counter)

    for ms_id, words in manuscript_words.items():
        for word in words:
            word_total[word] += 1
            word_by_ms[word][ms_id] += 1

    print(f"  Unique word forms (case-sensitive): {len(word_total):,}")

    # Helper: get source types for a word given its manuscript appearances
    def get_source_types(ms_ids):
        """Return sorted, deduplicated source types for a set of manuscript IDs."""
        types = set()
        for ms_id in ms_ids:
            if ms_id in source_type_lookup:
                types.add(source_type_lookup[ms_id])
        return "|".join(sorted(types))

    # ── Write case-sensitive frequency CSV ──────────────────────

    csv_path = os.path.join(OUTPUT_DIR, "word-frequency-complete.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["word", "total_count", "manuscript_count",
                         "source_types", "manuscripts"])

        for word, count in word_total.most_common():
            ms_ids = word_by_ms[word]
            ms_count = len(ms_ids)
            source_types = get_source_types(ms_ids.keys())
            ms_list = "|".join(sorted(ms_ids.keys()))
            writer.writerow([word, count, ms_count, source_types, ms_list])

    print(f"  Saved: {csv_path}")

    # ── Build case-insensitive frequency data ───────────────────

    ci_total = Counter()
    ci_variants = defaultdict(Counter)
    ci_by_ms = defaultdict(Counter)

    for word, count in word_total.items():
        lower = word.lower()
        ci_total[lower] += count
        ci_variants[lower][word] += count
        for ms_id, ms_count in word_by_ms[word].items():
            ci_by_ms[lower][ms_id] += ms_count

    print(f"  Unique word forms (case-insensitive): {len(ci_total):,}")

    # ── Write case-insensitive frequency CSV ────────────────────

    csv_ci_path = os.path.join(OUTPUT_DIR, "word-frequency-case-insensitive.csv")
    with open(csv_ci_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["word", "total_count", "manuscript_count",
                         "source_types", "manuscripts", "capitalizations"])

        for word, count in ci_total.most_common():
            ms_ids = ci_by_ms[word]
            ms_count = len(ms_ids)
            source_types = get_source_types(ms_ids.keys())
            ms_list = "|".join(sorted(ms_ids.keys()))
            variants = ci_variants[word]
            canonical = variants.most_common(1)[0][0]
            all_forms = ", ".join(f"{v} ({c})" for v, c in variants.most_common())
            writer.writerow([canonical, count, ms_count, source_types,
                             ms_list, all_forms])

    print(f"  Saved: {csv_ci_path}")
    print()

    # ──────────────────────────────────────────────────────────
    # STEP 4: Categorize vocabulary
    # ──────────────────────────────────────────────────────────

    print("STEP 4: Categorizing vocabulary...")
    print()

    category_groups = defaultdict(lambda: defaultdict(lambda: {
        "variants": Counter(),
        "manuscripts": set(),
        "source_types": set(),
    }))

    categorized_count = 0
    uncategorized_interesting = []

    for word, count in ci_total.items():
        if word in VOCAB_LOOKUP:
            category, modern = VOCAB_LOOKUP[word]
            group = category_groups[category][modern]
            for variant, var_count in ci_variants[word].items():
                group["variants"][variant] += var_count
            group["manuscripts"].update(ci_by_ms[word].keys())
            for ms_id in ci_by_ms[word].keys():
                if ms_id in source_type_lookup:
                    group["source_types"].add(source_type_lookup[ms_id])
            categorized_count += 1
        else:
            if (count >= 5
                    and word.lower() not in STOP_WORDS
                    and not word.isdigit()
                    and len(word) > 2):
                ms_count = len(ci_by_ms[word])
                uncategorized_interesting.append((word, count, ms_count))

    uncategorized_interesting.sort(key=lambda x: x[1], reverse=True)

    print(f"  Categorized {categorized_count} word forms into {len(category_groups)} categories")
    print(f"  Found {len(uncategorized_interesting)} uncategorized words (frequency >= 5)")

    # ── Write categorized vocabulary markdown ───────────────────

    cat_path = os.path.join(OUTPUT_DIR, "vocabulary-categorized.md")
    with open(cat_path, "w", encoding="utf-8") as f:
        f.write("# Early Modern Recipe Vocabulary (Categorized)\n\n")
        f.write(f"Generated: {datetime.date.today()}\n\n")
        f.write("This file organizes words from the transcription corpus into ")
        f.write("topical categories.\nWords are grouped by their modern English ")
        f.write("equivalent, with all attested\nspelling variants listed.\n\n")
        f.write("**Source types:** FTP = FromThePage, EMROC = triple-keyed, ")
        f.write("HERBAL = printed herbal\n\n")

        for category in CATEGORY_ORDER:
            if category not in category_groups:
                continue

            f.write(f"## {category}\n\n")
            f.write("| Word | Modern Form | Count | MSS | Sources | Notes |\n")
            f.write("|------|-------------|-------|-----|---------|-------|\n")

            for modern in sorted(category_groups[category].keys()):
                group = category_groups[category][modern]
                variants = group["variants"]
                total = sum(variants.values())
                ms_count = len(group["manuscripts"])

                if total == 0:
                    continue

                primary = variants.most_common(1)[0][0]
                sources = ", ".join(sorted(group["source_types"]))

                other_variants = [v for v, c in variants.most_common() if v != primary]
                notes = ""
                if other_variants:
                    quoted = [f'"{v}"' for v in other_variants[:5]]
                    notes = "also: " + ", ".join(quoted)
                    if len(other_variants) > 5:
                        notes += f" (+{len(other_variants) - 5} more)"

                f.write(f"| {primary} | {modern} | {total} | {ms_count} | {sources} | {notes} |\n")

            f.write("\n")

        # Uncategorized section
        f.write("## Uncategorized (Frequent Words for Review)\n\n")
        f.write("These words appear frequently in the corpus but were not\n")
        f.write("matched to a category. Review and add to categories above\n")
        f.write("as appropriate.\n\n")
        f.write("| Word | Count | MSS |\n")
        f.write("|------|-------|-----|\n")
        for word, count, ms_count in uncategorized_interesting[:200]:
            f.write(f"| {word} | {count} | {ms_count} |\n")
        f.write("\n")

    print(f"  Saved: {cat_path}")
    print()

    # ──────────────────────────────────────────────────────────
    # STEP 5: Write summary report
    # ──────────────────────────────────────────────────────────

    print("STEP 5: Writing summary report...")
    print()

    summary_path = os.path.join(OUTPUT_DIR, "processing-summary.md")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("# Vocabulary Processing Summary\n\n")
        f.write(f"**Date processed:** {datetime.date.today()}\n\n")

        successful = [ms for ms in manuscripts if ms["downloaded"]]
        failed = [ms for ms in manuscripts if not ms["downloaded"]]
        ftp_count = sum(1 for ms in successful if ms["source_type"] == "FTP")
        emroc_count = sum(1 for ms in successful if ms["source_type"] == "EMROC")
        herbal_count = sum(1 for ms in successful if ms["source_type"] == "HERBAL")

        f.write("## Overall Statistics\n\n")
        f.write(f"- **Total sources attempted:** {len(manuscripts)}\n")
        f.write(f"- **Successfully downloaded:** {len(successful)}\n")
        f.write(f"  - FromThePage (FTP): {ftp_count}\n")
        f.write(f"  - EMROC triple-keyed: {emroc_count}\n")
        f.write(f"  - Printed herbals (HERBAL): {herbal_count}\n")
        f.write(f"- **Failed:** {len(failed)}\n")
        f.write(f"- **Total words processed:** {total_words:,}\n")
        f.write(f"- **Unique word forms (case-sensitive):** {len(word_total):,}\n")
        f.write(f"- **Unique word forms (case-insensitive):** {len(ci_total):,}\n")
        f.write(f"- **Words categorized:** {categorized_count}\n")
        f.write(f"- **Uncategorized frequent words:** {len(uncategorized_interesting)}\n")
        f.write("\n")

        f.write("## Source Details\n\n")
        f.write("| # | Short ID | Source | Work ID | Words | Language | Status |\n")
        f.write("|---|----------|--------|---------|-------|----------|--------|\n")

        for i, ms in enumerate(manuscripts):
            status = "OK" if ms["downloaded"] else f"FAILED: {ms['error']}"
            f.write(
                f"| {i+1} | {ms['short_id']} | {ms['source_type']} | "
                f"{ms['work_id']} | {ms['word_count']:,} | "
                f"{ms['language']} | {status} |\n"
            )

        f.write("\n")

        # Non-English manuscripts
        non_english = [
            ms for ms in manuscripts
            if ms["downloaded"] and ms["language"] not in ("English", "Unknown")
        ]
        if non_english:
            f.write("## Non-English Sources\n\n")
            for ms in non_english:
                f.write(f"- **{ms['short_id']}** ({ms['label']}): {ms['language']}\n")
            f.write("\n")

        if failed:
            f.write("## Failed Downloads\n\n")
            for ms in failed:
                f.write(f"- **{ms['label']}** ({ms['work_id']}): {ms['error']}\n")
            f.write("\n")

        f.write("## Source Type Explanation\n\n")
        f.write("- **FTP** (FromThePage): Crowd-sourced transcriptions of ")
        f.write("manuscript recipe books via the FromThePage platform. ")
        f.write("Good coverage but variable quality.\n")
        f.write("- **EMROC** (Early Modern Recipes Online Collective): ")
        f.write("Triple-keyed transcriptions where three people independently ")
        f.write("transcribe each page and discrepancies are resolved. ")
        f.write("Highest quality.\n")
        f.write("- **HERBAL** (Printed Herbals): OCR text from printed books ")
        f.write("(Gerard 1597, Culpeper 1652). These provide authoritative ")
        f.write("botanical and medical vocabulary. Note: OCR quality varies.\n")
        f.write("\n")
        f.write("Words attested across multiple source types are more reliable.\n")
        f.write("\n")

        f.write("## EMROC: Additional Data Available\n\n")
        f.write("The 3 EMROC manuscripts above are those available via FromThePage.\n")
        f.write("Additional EMROC transcriptions may be available through:\n")
        f.write("- **Folger LUNA** (luna.folger.edu) — searchable transcriptions of ~43 collections\n")
        f.write("- **Folger DROMIO** (transcribe.folger.edu) — TEI XML transcriptions\n")
        f.write("- **Contact EMROC** (contactemroc@gmail.com) for bulk data access\n")
        f.write("\n")

        f.write("## Notes\n\n")
        f.write("- FromThePage text downloaded via IIIF API (verbatim plaintext export).\n")
        f.write("- Herbal text downloaded from Internet Archive (djvu.txt OCR export).\n")
        f.write("- Metadata lines, editorial brackets, and page markers stripped.\n")
        f.write("- Original spelling and capitalization preserved exactly.\n")

    print(f"  Saved: {summary_path}")
    print()

    # ──────────────────────────────────────────────────────────
    # STEP 6: Create flat vocabulary file for AI consumption
    # ──────────────────────────────────────────────────────────

    print("STEP 6: Creating flat vocabulary reference file...")
    print()

    vocab_words = set()
    for word, count in ci_total.items():
        ms_count = len(ci_by_ms[word])
        if ms_count < 2:
            continue
        if word.lower() in STOP_WORDS:
            continue
        if word.replace(".", "").replace(",", "").isdigit():
            continue
        if len(word) <= 2 and word not in VOCAB_LOOKUP:
            continue
        vocab_words.add(word)

    sorted_vocab = sorted(vocab_words, key=str.lower)
    ms_downloaded = len([ms for ms in manuscripts if ms["downloaded"]])

    vocab_path = os.path.join(OUTPUT_DIR, "vocab-reference.txt")
    with open(vocab_path, "w", encoding="utf-8") as f:
        f.write("# Early Modern Recipe Vocabulary Reference\n")
        f.write(f"# Built from {ms_downloaded} sources:\n")
        f.write(f"#   - {ftp_count} FromThePage manuscript transcriptions\n")
        f.write(f"#   - {emroc_count} EMROC triple-keyed transcriptions\n")
        f.write(f"#   - {herbal_count} printed herbals (Internet Archive)\n")
        f.write("#\n")
        f.write("# This list contains words that appear in human-transcribed\n")
        f.write("# early modern recipe books and contemporary herbals,\n")
        f.write("# preserving original spellings.\n")
        f.write("#\n")
        f.write("# Use this to verify transcription readings -- if the word\n")
        f.write("# you read appears on this list, it is a real attested form.\n")
        f.write("#\n")
        f.write("# Words are included only if they appear in 2+ sources.\n")
        f.write(f"# Total unique forms: {len(sorted_vocab):,}\n")
        f.write(f"# Total sources: {ms_downloaded}\n")
        f.write(f"# Generated: {datetime.date.today()}\n")
        f.write("#\n\n")

        for word in sorted_vocab:
            f.write(word + "\n")

    print(f"  Saved: {vocab_path}")
    print(f"  Total words in reference: {len(sorted_vocab):,}")
    print()

    # ──────────────────────────────────────────────────────────
    # DONE
    # ──────────────────────────────────────────────────────────

    print("=" * 60)
    print("  DONE! All files saved to:")
    print(f"  {OUTPUT_DIR}")
    print()
    print("  Output files:")
    print(f"    raw-text/                          — {ms_downloaded} source text files")
    print(f"    word-frequency-complete.csv        — {len(word_total):,} word forms")
    print(f"    word-frequency-case-insensitive.csv — {len(ci_total):,} word forms")
    print(f"    vocabulary-categorized.md           — categorized recipe vocabulary")
    print(f"    vocab-reference.txt                — {len(sorted_vocab):,} words for AI use")
    print(f"    processing-summary.md              — processing report")
    print("=" * 60)


# ── Run the script ──────────────────────────────────────────

if __name__ == "__main__":
    main()
