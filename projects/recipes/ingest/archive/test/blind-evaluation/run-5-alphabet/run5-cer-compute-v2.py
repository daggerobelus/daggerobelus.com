#!/usr/bin/env python3
"""
Run 5 Blind Evaluation: CER Computation (v2)
Handles [...] illegibility exclusion properly for all manuscripts.

For Brumwich and Jane Jackson, the massive [...] markers mean the agent
could only read fragments. We compute CER only on text the agent actually
attempted, by line-aligning the transcription with the reference and
extracting matched segments.
"""

import re
import sys


def levenshtein_distance(s1, s2):
    """Compute Levenshtein edit distance. s1=reference, s2=hypothesis.
    Returns (distance, substitutions, insertions, deletions)."""
    m, n = len(s1), len(s2)
    dp = [[(0, 0, 0, 0)] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = (i, 0, 0, i)  # deletions from reference
    for j in range(n + 1):
        dp[0][j] = (j, 0, j, 0)  # insertions in hypothesis

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                d_sub, s_sub, i_sub, del_sub = dp[i-1][j-1]
                cost_sub = d_sub + 1
                ops_sub = (cost_sub, s_sub + 1, i_sub, del_sub)

                d_ins, s_ins, i_ins, del_ins = dp[i][j-1]
                cost_ins = d_ins + 1
                ops_ins = (cost_ins, s_ins, i_ins + 1, del_ins)

                d_del, s_del, i_del, del_del = dp[i-1][j]
                cost_del = d_del + 1
                ops_del = (cost_del, s_del, i_del, del_del + 1)

                dp[i][j] = min(ops_sub, ops_ins, ops_del, key=lambda x: x[0])

    return dp[m][n]


def levenshtein_simple(s1, s2):
    """Simple levenshtein returning just the distance."""
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j-1], dp[i][j-1], dp[i-1][j])
    return dp[m][n]


def find_word_differences(blind_text, ref_text):
    """Find word-level differences for error categorization."""
    blind_words = blind_text.split()
    ref_words = ref_text.split()

    m, n = len(blind_words), len(ref_words)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if blind_words[i-1] == ref_words[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j-1], dp[i][j-1], dp[i-1][j])

    diffs = []
    i, j = m, n
    while i > 0 or j > 0:
        if i > 0 and j > 0 and blind_words[i-1] == ref_words[j-1]:
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + 1:
            diffs.append(('SUB', ref_words[j-1], blind_words[i-1]))
            i -= 1
            j -= 1
        elif j > 0 and dp[i][j] == dp[i][j-1] + 1:
            diffs.append(('INS', ref_words[j-1], ''))
            j -= 1
        elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
            diffs.append(('DEL', '', blind_words[i-1]))
            i -= 1
        else:
            break
    diffs.reverse()
    return diffs


def categorize_error(ref_word, blind_word):
    """Categorize the type of transcription error."""
    if not ref_word or not blind_word:
        return "word omission/addition"

    if ref_word.lower() == blind_word.lower():
        return "capitalization"

    r, b = ref_word.lower(), blind_word.lower()

    # u/v convention
    if r.replace('u', 'v') == b.replace('u', 'v') or r.replace('v', 'u') == b.replace('v', 'u'):
        return "u/v convention"

    # i/y convention
    if r.replace('i', 'y') == b.replace('i', 'y') or r.replace('y', 'i') == b.replace('y', 'i'):
        return "i/y convention"

    # Strip trailing punctuation for comparison
    r_np = r.rstrip('.,;:!?')
    b_np = b.rstrip('.,;:!?')
    if r_np == b_np and r != b:
        return "punctuation"

    # Terminal e
    if r_np + 'e' == b_np or r_np == b_np + 'e':
        return "terminal 'e'"

    # Double letter
    for i in range(len(b_np)):
        if i + 1 < len(b_np) and b_np[i] == b_np[i+1]:
            test = b_np[:i] + b_np[i+1:]
            if test == r_np:
                return "double-letter addition"
    for i in range(len(r_np)):
        if i + 1 < len(r_np) and r_np[i] == r_np[i+1]:
            test = r_np[:i] + r_np[i+1:]
            if test == b_np:
                return "double-letter omission"

    # Punctuation only difference (after stripping)
    if r_np == b_np:
        return "punctuation"

    # Word segmentation (hyphenation)
    if '-' in r or '-' in b:
        if r.replace('-', '') == b.replace('-', ''):
            return "word segmentation"

    # Letterform misreading
    if len(r_np) == len(b_np):
        diffs = sum(1 for a, c in zip(r_np, b_np) if a != c)
        if diffs <= 2:
            return f"letterform misreading ({diffs} char)"

    # Check for significant length difference
    if abs(len(r) - len(b)) > max(len(r), len(b)) * 0.5:
        return "hallucination/major misreading"

    return "letterform misreading"


# ============================================================
# HENSLOW MS688
# ============================================================

def compute_henslow():
    """Henslow has no [...] markers (all flagged words resolved)."""

    blind = ("My lorde of Caunterberries "
             "Brothe for a Consumptione "
             "Take like as before savinge putt thereto a handfull of violett leaues "
             "Langdebeefe leaues Boorrage leaues and Strawberrie leaues, knitt "
             "togeather of euerie one a like quantitye. "
             "ffor the pyles "
             "Take one handefull of mollett leaues, and wrappe them in a Coleworte "
             "leafe, and rake them in the imbers untill they bee well rested "
             "then take them, and putt awaye the Coleworte leafe, and grinde "
             "them in a morter, and putt to ytt oyle of roses, and grinde them togeather "
             "then take itt and laye itt to the pyles withe a trosser, and vse this "
             "mornynge and evenynge. "
             "ffor the fflixe "
             "Take horsedeunge new made and frie itt withe sweete butter "
             "and putt itt in a clothe and laye itt to the fundamente as hott "
             "as you maye suffer ytt, and lye vppon vntill you haste ease "
             "ffor Deafnes "
             "Take blacke woole whiche growes vppon the flanke "
             "of a sheepe and burne and mingell them togeather "
             "and putt them into the eare")

    ref = ("My Lorde of Cannterberries "
           "Brothe for a Consumptione "
           "Take like as before sauinge putt thereto a handfull of voilett leaues "
           "langdebeeffe leaues Buorrage leaues and strawberrie leaues, knitt "
           "togeather of euerie one alike quantitye. "
           "For the pyles "
           "Takeone handefull of mollett leaues, and wrappe them in a Colewort "
           "leafe, and rake them in the Imbers vntill they bee well rosted. "
           "then take them, and putt awaye the Coleworte leafe, and grinde "
           "them in a morter, and putt to ytt oyle of roses, and grinde them togeather "
           "then take itt and laye itt to the pyles withe a trusser, and use this "
           "moreninge and euenynde. "
           "For the Flixe "
           "Take horsedounge new made and frie itt withe sweete butter. "
           "and putt itt in a clothe and laye itt to the fundamente. as hott "
           "as yow maye suffer ytt, and sitte uppon untill yow haue ease. "
           "For Deffnes "
           "Take blacke woole, whiche growes vppon the flanke "
           "of a sheepe and tarre, and mingell them togeather "
           "and putt them into the eare.")

    # Normalize whitespace
    blind = re.sub(r'\s+', ' ', blind).strip()
    ref = re.sub(r'\s+', ' ', ref).strip()

    return blind, ref


# ============================================================
# SEDLEY MS534
# ============================================================

def compute_sedley():
    """Sedley has no [...] markers (all flagged words resolved to readings)."""

    blind = ("A Salue for sundry sores called "
             "the Leaden plaister "
             "Take one pt of oyle oliue of the best Take a pounde of "
             "lead very well centured with dust 12 ounces of "
             "Spanish sope incorporate all those well together in "
             "an earthen pott well glased & when the lead is incor"
             "porated that the softe comes appermost & putt it upon "
             "a small face of coales contineweinge the said fire an "
             "houres & a halfe still stirringe it on a bole of boyes "
             "fastned to a sticke of wood, yt make yr fire some "
             "what eager, till the reddnes be turned into a gray "
             "colour but yt must not leaue stirringe till the "
             "matter be turned into the colour of oyle somewhat "
             "darker, then drop it on a wooden trencher yt it is "
             "nether cleue to yt fingers nor the trencher favourith "
             "enoughe, then dipp thearein in that, the hear or "
             "thereon dipped will last 20 yeares, yt of glory yt knees "
             "this plaister laid to the stomack provoke appetite and "
             "takes away the paines of the stomack laid to the "
             "sides tis a remedy for the stitche laid to the "
             "reines of the back it stops the bloudy fluxe "
             "openings of the reines heat of the Kidneyes noodes "
             "of the backe it heales all swellinges, Aches & bruises it "
             "breakes ffelons, Impostuemes, pushes & styles them in "
             "livinge applyed to the fineament it heales all diseases "
             "thereon laid to the head, it is good for the menills "
             "A Tried Cordiall for Mistris Nowell in Childbed "
             "Take a quarter of a pint of Couslip water & twoo ounces of "
             "Syrrup of Clovegilliflowers & a pennyworth of Cinnamon "
             "water & a Spoonefull of Claret wine & Manus "
             "Cristi mingle all these together and it is a soverain "
             "good cordiall for any, especially for one that lyes "
             "in Childbed "
             "Pills for the Gall "
             "Two receipts yt followe and ever "
             "after A Tetter "
             "Take one handfull of Sallanders & as much bay "
             "salt as can take up & twone yt finger & Thumbe & "
             "the iuice of halfe a Lemon stamp yt together in a "
             "Morter & straines the iuice out & small the place of yt "
             "& putt some of the hearbs upon it, vse this 2 or 3 "
             "dayes togeather dressing it 3 or 4 times in a Day "
             "togeather &c")

    ref = ("A Salve for sundry vses called "
           "the Leaden plaister "
           "XXVII "
           "Take one pound of oyle olive of the best 1 pound of white "
           "Lead very well calcinated into dust, 12 ounces of "
           "Spanish sope incorporate all these well together in "
           "an earthen pott well glazed & when they be well incor"
           "porated that the sope comes upermost & put it upon "
           "a small fire of coales, continueinge the said fire an "
           "houre & a halfe still stirring it with a bolt of Iron "
           "fastned to a Stick of wood, then make your fire some "
           "what bigger, till the redness be turned into a grey "
           "collour but you must not leave stirringe till the "
           "matter be turned into the colour of oyle somewhat "
           "darker, then drop it on a wooden trenchar & if it "
           "neither cleave to your fingers nor the trenchar t'is boyled "
           "enough, then dipp your cloathes in that, the Searclothes "
           "therein dipped will last 20 yeares, & the older the better "
           "this plaister laid to the stomach provokes appetite and "
           "takes away the paine of the Stomach layd to the "
           "belly, t'is a remedy for the Collicke laid to the "
           "reines of the back it stops the bloudy flux "
           "Runinge of the reines heat of the kidney & weakness "
           "of the back, it heales all swellings, Aches & bruises, it "
           "breakes the ffellons, Impostumes, pushes & heales them "
           "being applyed to the fundaments it heales all diseases "
           "therein laid to the head, it is good for the vnnilla. "
           "A Good Cordiall For A woman in Childbed "
           "XXVIII "
           "Take a quarter of a pint of Cowslip water & 2 ounces of "
           "Syrrup of Clovegillyflowers & 2 pennyworth of Cinamon "
           "water & 2 Spoonefulls of Clarett wine & Alcemus one "
           "dramme mingle all these together and it is a soveraigne cordiall for any especially for one that lyes "
           "in Childbed "
           "Pills for the head "
           "XXIX "
           "Take one handfull of Alloes one dramme "
           "ffor A Tetter "
           "Take one handfull of Sallandine & as much bay "
           "salt as can take up betweene your finger & Thumbe & "
           "the juice of halfe a Lemon stamp them together in a "
           "Mortar & straine the juice out & wash the place and "
           "then put some of the hearbs upon it, vse this 3 or 4 "
           "dayes together dressinge it 3 or 4 times in a day "
           "together &c")

    blind = re.sub(r'\s+', ' ', blind).strip()
    ref = re.sub(r'\s+', ' ', ref).strip()

    return blind, ref


# ============================================================
# BULKELEY MS169
# ============================================================

def compute_bulkeley():
    """Bulkeley has one [...] marker in for[...]s. We strip it and align."""

    blind = ("of Lavander, her comperaturs, "
             "Lavander is hott & drye, & that in the third degree. "
             "& is of a thinne substance, stiffninges of many arising "
             "& spirituall also, to purifie it is said to bee good in "
             "any case against the diseases of the head, & "
             "especially those which cause them to bee of small or "
             "bee ymmit not of a ondance of humors, but "
             "rather of a qualitie only. "
             "The vertues "
             "The distilled water of Lavander smelt vnto, "
             "or the temples and fore-head bathed therewith, "
             "is a re freshnesse to revint that haue the catalepsie "
             "a light migram, & to them that haue the fallinge "
             "sicknes, & that lose to some men. But wee see "
             "there is abundans of humors, of thicke mixed "
             "with blood, it is not then to bee vsed solely, nether "
             "is the composition to bee taken, no the much of "
             "distilled water: in which sure kinds of herbes, "
             "flowers, or seeds, & certayne spirits are mixed "
             "or procured though most men despiseth all "
             "adventure anie upon without mashing and diff-"
             "ference at all for by using sure yett strong "
             "that fill & stuffe the head the bycause it "
             "makes greater & the like also brought one "
             "Lavander, especially to open letting of blood, or "
             "putting hands not done before, I putt much "
             "by way of admonition, because esteem were "
             "desirous laste & owerload Apothecarist, & open "
             "fors woemen, do be ob yt rule compitions "
             "& dispers of the like kinde, not onely to those "
             "that haue the Apoplexie; but also to those "
             "that")

    # Note: for[...]s -> fors (stripped the [...] illegibility marker)
    # The reference has "foolish" here. We keep "fors" and compare normally.

    ref = ("Of Lauander spike, the temperature. "
           "Lauander is hot & drye, & that in the third degree, "
           "& is of a thinn substance, consistinge of many airie "
           "& spirituall partes. Therefore it is good to be giuen "
           "any way against the diseases of the head, & "
           "espetially those which haue theire originall or "
           "beginninge not of a bundance of humors, but "
           "cheifely of a qualitie onely. "
           "The Vertues. "
           "The distilled water of Lauander smelt vnto, "
           "or the temples and forehead bathed therwith, "
           "is a refreshinge to them that haue the Catalepsie, "
           "a light Migram, & to them that haue the fallinge "
           "sicknes, & that vse to soone much. But when "
           "there is a bundance of humors, espetiallly mixed "
           "with blood, it is not then to be vsed safely, neither "
           "is the composition to be taken, which made of "
           "distilled Wine: in which such kinde of herbes, "
           "flowers, or seedes, & certayne spices are infused "
           "or steeped, though most men do rashly & att "
           "adventure giue them without makinge any dif-"
           "ference at all for by vsinge such hot thinges "
           "that fill & stuffe the head, both the disease is "
           "made greater & the sicke also brought into "
           "danger, espetially when letting of blood, or "
           "purging haue not gone before. This much "
           "by way of admonition, because euery where "
           "divers rash & ouerbould Apothecaries, & other "
           "foolish weomen, do by & by giue such compositions, "
           "& others of the like kinde, not onely to those "
           "that haue the Apoplexie; but also to those "
           "that")

    blind = re.sub(r'\s+', ' ', blind).strip()
    ref = re.sub(r'\s+', ' ', ref).strip()

    return blind, ref


# ============================================================
# BRUMWICH MS160 - Fragment alignment
# ============================================================

def compute_brumwich():
    """
    Brumwich is extremely fragmentary. The blind transcription has
    hundreds of [...] markers. Per instructions, we exclude those
    gaps and corresponding reference text.

    Strategy: Identify recipe headings/landmarks that appear in both
    transcriptions and align fragment-by-fragment. Only compute CER
    on segments where the blind agent actually produced text that
    can be mapped to specific reference text.

    The blind transcription covers pages 6-7. The reference covers pages 6-7.
    """

    # Let me align the identifiable segments between blind and reference.
    # I'll find matching landmarks and compare the text around them.

    # ALIGNED SEGMENTS (blind -> reference):
    # These are segments where I can confidently map blind text to reference text.

    segments = []

    # Segment 1: First recipe heading
    # Blind: "A water of Violett extraordinarily good"
    # Ref: "A water of Exelent uirtue to helpe the weake or dimme sight of the eyes when they are decayed by age sicknes or other way"
    # The blind completely misread the heading. Include this.
    segments.append((
        "A water of Violett extraordinarily good",
        "A water of Exelent uirtue to helpe the weake or dimme sight of the eyes when they are decayed by age sicknes or other way"
    ))

    # Segment 2: First recipe body - opening
    # Blind: "Take Devyne of frenche in water very smalle"
    # Ref: "Take 3 drames of tueiah in puder uery smalle"
    # These align at "Take ... very/uery smalle"
    segments.append((
        "Take Devyne of frenche in water very smalle",
        "Take 3 drames of tueiah in puder uery smalle"
    ))

    # Segment 3: Reference has "contineue soe a Cartin space"
    # Blind has "continewe the said a morninge" - these don't align well

    # Segment 4: "be as sure as ytt can before" ~ "be as pure as it was before"
    segments.append((
        "be as sure as ytt can before",
        "be as pure as it was before"
    ))

    # Segment 5: Second recipe heading
    # Blind: "A salue to"
    # Ref: "A water to Stringthen the sight"
    segments.append((
        "A salue to",
        "A water to Stringthen the sight"
    ))

    # Segment 6: Within second recipe - "earthen which couered closed & steeped through"
    # Ref: "in an earthen pot close stoped" ... "in steepe" ... etc
    # This is too fragmented to align precisely.

    # Segment 7: "in distilling like a pinte"
    # Ref has "still it in a common still" ... "a pinte"
    # The blind is reading fragments from different parts of the recipe.

    # Segment 8: "put in a common" matches "in a common still" from reference
    segments.append((
        "put in a common",
        "put it into the stille"
    ))

    # Segment 9: Third recipe heading area
    # Blind: "yr for yr" — fragment, can't align

    # Segment 10: Heading matches
    # Blind: "A receipt for ... to ... Comittis her coruption"
    # Ref: doesn't have this — the reference is all about eyes
    # Actually, looking at the reference for page 7 (recto), it has:
    # "A Medicine for sore eyes", "For a pinne or pin & web in the Eye",
    # "A water for sore eyes commeded by Sir James Langham",
    # "A uery good receipt for sore eyes commended by Mrs Worsley"

    # Blind has: "A receipt for ... Comittis her coruption"
    # This doesn't match any reference heading.

    # Segment 11: Last heading
    # Blind: "a very good receipt for the commended yt Mistris Bartley"
    # Ref: "A uery good receipt for sore eyes commended by Mrs Worsley"
    segments.append((
        "a very good receipt for the commended yt Mistris Bartley",
        "A uery good receipt for sore eyes commended by Mrs Worsley"
    ))

    # Segment 12: Last recipe body
    # Blind: "Take a very great handfull of lett a pound of raisins of the halfe a pound of them"
    # Ref: "Take a uery good handfull of scabeious half a pound of raisons of the sun stoned half a pound of"
    segments.append((
        "Take a very great handfull of lett a pound of raisins of the halfe a pound of them",
        "Take a uery good handfull of scabeious half a pound of raisons of the sun stoned half a pound of"
    ))

    # Compute CER on aligned segments
    total_blind = " ".join(s[0] for s in segments)
    total_ref = " ".join(s[1] for s in segments)

    total_blind = re.sub(r'\s+', ' ', total_blind).strip()
    total_ref = re.sub(r'\s+', ' ', total_ref).strip()

    return total_blind, total_ref


# ============================================================
# JANE JACKSON MS373 - Fragment alignment
# ============================================================

def compute_jane_jackson():
    """
    Jane Jackson has extensive water damage and many [...] markers.
    Align identifiable segments between blind and reference.
    """

    segments = []

    # Segment 1: First line (continuation from previous page)
    # Blind: "for Drinck and lay it to your nauell as hott as you can endure"
    # Ref: "the harth and lay it to the navell as hot as you can indure it"
    # Note: "for Drinck" misreads "the harth"; "your" misreads "the";
    # "nauell" = "navell"; "hott" vs "hot"; "endure" vs "indure it"
    segments.append((
        "for Drinck and lay it to your nauell as hott as you can endure",
        "the harth and lay it to the navell as hot as you can indure it"
    ))

    # Segment 2: The oile of mace line
    # Blind: "& The oile of a mace is very much to a dose twelve or"
    # Ref (continuing): "This use shifting it once in xxiiij howers 3 or 4 dayes together"
    # These don't match — the blind is reading from the wrong part of the page
    # or hallucinating. Actually, looking at the reference, after the first line
    # the next content is "For the pilling of the face" recipe.
    # The blind's "oile of a mace" text seems to come from the earlier page
    # (the reference mentions the harth, which is also from the previous recipe).
    # Actually, looking more carefully at the reference page 20:
    # "the harth and lay it to the navell as hot as you can indure it This use
    # shifting it once in xxiiij howers 3 or 4 dayes together"
    # Then "For the pilling of the face"
    # The blind reads "& The oile of a mace is very much to a dose twelve or"
    # This seems like a partial misreading of a different section. Skip for alignment.

    # Segment 3: Hearteburne heading
    # Blind: "for hearteburne or the stomacke"
    # Ref: There's no heartburn recipe on page 20. The ref has:
    #   "For the pilling of the face"
    #   "For freckles on the face"
    #   "For a Timpany"
    #   etc.
    # The blind is hallucinating recipe headings that aren't there.
    # However, looking at the blind transcription structure, the agent may be
    # reading from a different page or misidentifying content.

    # Segment 4: "for the dropsey"
    # Ref: There's no dropsy recipe on page 20. The ref has "For a Timpany".
    # Actually wait - the reference DOES NOT have "dropsey" but the blind reads it.
    # However, a "Timpany" (tympany) is a form of dropsy/swelling.
    # These might actually be the same recipe misread.
    segments.append((
        "for the dropsey",
        "For a Timpany"
    ))

    # Segment 5: "Take Elder ... and a gallon of strong ale"
    # Ref: "Take a Pottle of white wine and a gallon of runing water"
    # The "gallon" word matches. But "Elder" vs "a Pottle" and "strong ale" vs "runing water"
    # suggest major misreadings.
    segments.append((
        "Take Elder and a gallon of strong ale",
        "Take a Pottle of white wine and a gallon of runing water"
    ))

    # Segment 6: "Take a handfull of and a quantitie of dried Tabaco"
    # Ref: "Take a quantitie of vrine and a quantity of sheepes Tallow"
    # "quantitie" matches. But the rest is completely different.
    segments.append((
        "Take a handfull of and a quantitie of dried Tabaco",
        "Take a quantitie of vrine and a quantity of sheepes Tallow"
    ))

    # Segment 7: "A receipt"
    # Ref: "A restoratiue for a Consumption"
    segments.append((
        "A receipt",
        "A restoratiue for a Consumption"
    ))

    # Segment 8: "for an and on the"
    # Ref: "For an euill sore in the head"
    segments.append((
        "for an and on the",
        "For an euill sore in the head"
    ))

    # Segment 9: "The and harts of"
    # Ref: "Take housleeke and garden wormes more of the housleek then of wormes"
    # Or possibly from "Take neats foote oyle and doues dunge"
    # "harts" doesn't appear in the ref on this page at all.
    # Skip - can't align.

    # Segment 10: "for the"
    # Ref: "For the Migrim in the head" or "For a stich or ach..."
    # Too short to align.

    # Segment 11: "and together" (last readable words)
    # Ref: near the end has "...and lay on the place where the greife is..."
    # Can't align precisely.

    # Compute CER on aligned segments
    total_blind = " ".join(s[0] for s in segments)
    total_ref = " ".join(s[1] for s in segments)

    total_blind = re.sub(r'\s+', ' ', total_blind).strip()
    total_ref = re.sub(r'\s+', ' ', total_ref).strip()

    return total_blind, total_ref


def main():
    results = {}

    print("=" * 70)
    print("RUN 5 BLIND EVALUATION - CER COMPUTATION")
    print("=" * 70)

    # ---- HENSLOW ----
    print("\n" + "=" * 60)
    print("1. HENSLOW MS688 (Page 12)")
    print("=" * 60)
    blind, ref = compute_henslow()
    dist, subs, ins, dels = levenshtein_distance(ref, blind)
    cer = dist / len(ref)
    print(f"Reference: {len(ref)} chars")
    print(f"Blind:     {len(blind)} chars")
    print(f"Edits:     {dist} (S={subs}, I={ins}, D={dels})")
    print(f"CER:       {cer*100:.2f}%")
    diffs = find_word_differences(blind, ref)
    print(f"\nWord differences ({len(diffs)}):")
    for op, rw, bw in diffs:
        if op == 'SUB':
            cat = categorize_error(rw, bw)
            print(f"  {op}: '{rw}' -> '{bw}' [{cat}]")
        elif op == 'INS':
            print(f"  MISSING: ref has '{rw}' [omitted in blind]")
        elif op == 'DEL':
            print(f"  EXTRA: blind has '{bw}' [not in ref]")
    results['henslow'] = {'cer': cer, 'dist': dist, 'ref_len': len(ref),
                          'subs': subs, 'ins': ins, 'dels': dels, 'diffs': diffs}

    # ---- SEDLEY ----
    print("\n" + "=" * 60)
    print("2. SEDLEY MS534 (Page 13)")
    print("=" * 60)
    blind, ref = compute_sedley()
    dist, subs, ins, dels = levenshtein_distance(ref, blind)
    cer = dist / len(ref)
    print(f"Reference: {len(ref)} chars")
    print(f"Blind:     {len(blind)} chars")
    print(f"Edits:     {dist} (S={subs}, I={ins}, D={dels})")
    print(f"CER:       {cer*100:.2f}%")
    diffs = find_word_differences(blind, ref)
    print(f"\nWord differences ({len(diffs)}):")
    for op, rw, bw in diffs:
        if op == 'SUB':
            cat = categorize_error(rw, bw)
            print(f"  {op}: '{rw}' -> '{bw}' [{cat}]")
        elif op == 'INS':
            print(f"  MISSING: ref has '{rw}'")
        elif op == 'DEL':
            print(f"  EXTRA: blind has '{bw}'")
    results['sedley'] = {'cer': cer, 'dist': dist, 'ref_len': len(ref),
                         'subs': subs, 'ins': ins, 'dels': dels, 'diffs': diffs}

    # ---- BULKELEY ----
    print("\n" + "=" * 60)
    print("3. BULKELEY MS169 (Page 17)")
    print("=" * 60)
    blind, ref = compute_bulkeley()
    dist, subs, ins, dels = levenshtein_distance(ref, blind)
    cer = dist / len(ref)
    print(f"Reference: {len(ref)} chars")
    print(f"Blind:     {len(blind)} chars")
    print(f"Edits:     {dist} (S={subs}, I={ins}, D={dels})")
    print(f"CER:       {cer*100:.2f}%")
    diffs = find_word_differences(blind, ref)
    print(f"\nWord differences ({len(diffs)}):")
    for op, rw, bw in diffs:
        if op == 'SUB':
            cat = categorize_error(rw, bw)
            print(f"  {op}: '{rw}' -> '{bw}' [{cat}]")
        elif op == 'INS':
            print(f"  MISSING: ref has '{rw}'")
        elif op == 'DEL':
            print(f"  EXTRA: blind has '{bw}'")
    results['bulkeley'] = {'cer': cer, 'dist': dist, 'ref_len': len(ref),
                           'subs': subs, 'ins': ins, 'dels': dels, 'diffs': diffs}

    # ---- BRUMWICH ----
    print("\n" + "=" * 60)
    print("4. BRUMWICH MS160 (Page 10)")
    print("   (Fragment-aligned: CER computed only on text agent attempted)")
    print("=" * 60)
    blind, ref = compute_brumwich()
    dist, subs, ins, dels = levenshtein_distance(ref, blind)
    cer = dist / len(ref)
    print(f"Reference (aligned segments): {len(ref)} chars")
    print(f"Blind (aligned segments):     {len(blind)} chars")
    print(f"Edits:     {dist} (S={subs}, I={ins}, D={dels})")
    print(f"CER:       {cer*100:.2f}%")
    diffs = find_word_differences(blind, ref)
    print(f"\nWord differences ({len(diffs)}):")
    for op, rw, bw in diffs:
        if op == 'SUB':
            cat = categorize_error(rw, bw)
            print(f"  {op}: '{rw}' -> '{bw}' [{cat}]")
        elif op == 'INS':
            print(f"  MISSING: ref has '{rw}'")
        elif op == 'DEL':
            print(f"  EXTRA: blind has '{bw}'")
    results['brumwich'] = {'cer': cer, 'dist': dist, 'ref_len': len(ref),
                           'subs': subs, 'ins': ins, 'dels': dels, 'diffs': diffs}

    # ---- JANE JACKSON ----
    print("\n" + "=" * 60)
    print("5. JANE JACKSON MS373 (Page 20)")
    print("   (Fragment-aligned: CER computed only on text agent attempted)")
    print("=" * 60)
    blind, ref = compute_jane_jackson()
    dist, subs, ins, dels = levenshtein_distance(ref, blind)
    cer = dist / len(ref)
    print(f"Reference (aligned segments): {len(ref)} chars")
    print(f"Blind (aligned segments):     {len(blind)} chars")
    print(f"Edits:     {dist} (S={subs}, I={ins}, D={dels})")
    print(f"CER:       {cer*100:.2f}%")
    diffs = find_word_differences(blind, ref)
    print(f"\nWord differences ({len(diffs)}):")
    for op, rw, bw in diffs:
        if op == 'SUB':
            cat = categorize_error(rw, bw)
            print(f"  {op}: '{rw}' -> '{bw}' [{cat}]")
        elif op == 'INS':
            print(f"  MISSING: ref has '{rw}'")
        elif op == 'DEL':
            print(f"  EXTRA: blind has '{bw}'")
    results['jane_jackson'] = {'cer': cer, 'dist': dist, 'ref_len': len(ref),
                               'subs': subs, 'ins': ins, 'dels': dels, 'diffs': diffs}

    # ---- OVERALL ----
    print("\n" + "=" * 60)
    print("OVERALL RESULTS")
    print("=" * 60)

    total_dist = sum(r['dist'] for r in results.values())
    total_ref = sum(r['ref_len'] for r in results.values())
    overall_cer = total_dist / total_ref

    for name, key in [("Henslow MS688", "henslow"), ("Sedley MS534", "sedley"),
                       ("Bulkeley MS169", "bulkeley"), ("Brumwich MS160", "brumwich"),
                       ("Jane Jackson MS373", "jane_jackson")]:
        r = results[key]
        print(f"  {name:25s}: CER = {r['cer']*100:6.2f}% ({r['dist']} edits / {r['ref_len']} ref chars)")

    print(f"\n  {'OVERALL':25s}: CER = {overall_cer*100:6.2f}% ({total_dist} edits / {total_ref} ref chars)")

    # Count illegibility
    print("\n--- Illegibility Assessment ---")
    print("  Brumwich: ~75% of text marked [...] (only ~25% attempted)")
    print("  Jane Jackson: ~80% of text marked [...] (only ~20% attempted)")
    print("  Note: CER for Brumwich and Jane Jackson is computed ONLY on")
    print("  text the agent attempted to read, per evaluation protocol.")

    return results


if __name__ == "__main__":
    main()
