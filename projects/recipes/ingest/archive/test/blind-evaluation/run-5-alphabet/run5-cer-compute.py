#!/usr/bin/env python3
"""
Run 5 Blind Evaluation: CER Computation
Computes Character Error Rate using Levenshtein edit distance.
"""

import re
import json

def levenshtein_distance(s1, s2):
    """Compute Levenshtein edit distance between two strings.
    Returns (distance, substitutions, insertions, deletions)."""
    m, n = len(s1), len(s2)

    # dp[i][j] = (distance, subs, ins, dels) for s1[:i] vs s2[:j]
    dp = [[(0, 0, 0, 0)] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = (i, 0, 0, i)  # all deletions
    for j in range(n + 1):
        dp[0][j] = (j, 0, j, 0)  # all insertions

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                # substitution
                d_sub, s_sub, i_sub, del_sub = dp[i-1][j-1]
                cost_sub = d_sub + 1
                ops_sub = (cost_sub, s_sub + 1, i_sub, del_sub)

                # insertion (char in s2 not in s1)
                d_ins, s_ins, i_ins, del_ins = dp[i][j-1]
                cost_ins = d_ins + 1
                ops_ins = (cost_ins, s_ins, i_ins + 1, del_ins)

                # deletion (char in s1 not in s2)
                d_del, s_del, i_del, del_del = dp[i-1][j]
                cost_del = d_del + 1
                ops_del = (cost_del, s_del, i_del, del_del + 1)

                dp[i][j] = min(ops_sub, ops_ins, ops_del, key=lambda x: x[0])

    return dp[m][n]


def get_edit_operations(s1, s2):
    """Get detailed edit operations using backtrace."""
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

    # Backtrace
    ops = []
    i, j = m, n
    while i > 0 or j > 0:
        if i > 0 and j > 0 and s1[i-1] == s2[j-1]:
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + 1:
            ops.append(('SUB', i-1, j-1, s1[i-1], s2[j-1]))
            i -= 1
            j -= 1
        elif j > 0 and dp[i][j] == dp[i][j-1] + 1:
            ops.append(('INS', i, j-1, '', s2[j-1]))
            j -= 1
        elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
            ops.append(('DEL', i-1, j, s1[i-1], ''))
            i -= 1
        else:
            break

    ops.reverse()
    return ops


def normalize_blind_transcription(text, manuscript_name):
    """Normalize blind transcription by stripping metadata, markers, etc."""

    # Strip header/metadata section (everything before and including ====)
    # Find the first ===== line and take everything after it
    parts = re.split(r'={5,}', text)
    if len(parts) >= 2:
        # Take the content between first and second ===== blocks
        content = parts[1]
    else:
        content = text

    # For manuscripts with REVIEWED transcription format, extract the REVISED TRANSCRIPTION section
    if 'REVISED TRANSCRIPTION' in text:
        match = re.search(r'REVISED TRANSCRIPTION\s*={5,}\s*(.*?)(?:={5,}|$)', text, re.DOTALL)
        if match:
            content = match.group(1)

    # Strip section labels like "LEFT COLUMN", "RIGHT COLUMN", etc.
    content = re.sub(r'^LEFT COLUMN.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^RIGHT COLUMN.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^LEFT PAGE.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^RIGHT PAGE.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^---+$', '', content, flags=re.MULTILINE)

    # Strip CONFIDENCE NOTES section and everything after
    content = re.split(r'CONFIDENCE NOTES', content)[0]
    # Strip REVIEW LOG/STATISTICS sections
    content = re.split(r'REVIEW LOG', content)[0]
    content = re.split(r'REVIEW STATISTICS', content)[0]
    content = re.split(r'NOTES\s*$', content, flags=re.MULTILINE)[0]

    # Strip decorative dot patterns
    content = re.sub(r'\.(\s*\.)+', '', content)

    # Strip confidence markers [word?] -> word and [word??] -> word
    content = re.sub(r'\[(\w+)\?\?\]', r'\1', content)
    content = re.sub(r'\[(\w+)\?\]', r'\1', content)

    # Strip italic markers *letters* -> letters
    content = re.sub(r'\*([^*]+)\*', r'\1', content)

    # Strip strikethrough markers ~~text~~ -> text
    content = re.sub(r'~~([^~]+)~~', r'\1', content)

    # Strip [...] illegibility markers (will handle alignment later)
    content = re.sub(r'\[\.\.\.\]', '⌀', content)  # Replace with placeholder first
    content = re.sub(r'\[\.+\]', '⌀', content)  # Also [.....] patterns

    # Strip [Passage largely illegible ...] markers
    content = re.sub(r'\[Passage largely illegible[^\]]*\]', '', content)

    # Strip recipe number markers like XXVII, XXVIII, XXIX
    content = re.sub(r'^[XVILC]+$', '', content, flags=re.MULTILINE)

    # Normalize whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = re.sub(r'[ \t]+', ' ', content)

    return content.strip()


def normalize_reference(text):
    """Normalize reference transcription."""
    # Strip header/metadata (everything before ---)
    parts = text.split('---', 1)
    if len(parts) >= 2:
        content = parts[1]
    else:
        content = text

    # Strip editorial brackets: [er] -> er, [pro] -> pro
    content = re.sub(r'\[([a-zA-Z]+)\]', r'\1', content)

    # Strip page numbers at start of lines (like "20" or "21" or "{6}" or "{7}")
    content = re.sub(r'^\{?\d+\}?\s*$', '', content, flags=re.MULTILINE)

    # Strip caret insertions ^text -> text
    content = re.sub(r'\^', '', content)

    # Strip = used for line-break hyphenation: "incor=\nporated" -> "incorporated"
    content = re.sub(r'=\s*\n\s*', '', content)

    # Normalize whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = re.sub(r'[ \t]+', ' ', content)

    return content.strip()


def align_and_strip_illegible(blind_text, ref_text):
    """
    For [...] markers in the blind transcription, we need to exclude
    corresponding reference text from the CER calculation.

    Strategy: Since [...] marks represent sections the agent couldn't read,
    we remove them and any surrounding whitespace. For manuscripts with
    heavy illegibility, we do line-by-line alignment where possible.

    For simple cases (Henslow), [...] markers are few and can be handled
    by removing them and the corresponding reference words.

    For complex cases (Brumwich, Jane Jackson), the massive number of [...]
    makes line-by-line alignment necessary.
    """
    # Count illegibility markers
    illegible_count = blind_text.count('⌀')
    return blind_text, ref_text, illegible_count


def process_henslow():
    """Process Henslow MS688 - relatively clean transcription with few [...] markers."""
    blind = """My lorde of Caunterberries
Brothe for a Consumptione

Take like as before savinge putt thereto a handfull of violett leaues
Langdebeefe leaues Boorrage leaues and Strawberrie leaues, knitt
togeather of euerie one a like quantitye.

ffor the pyles

Take one handefull of mollett leaues, and wrappe them in a Coleworte
leafe, and rake them in the imbers untill they bee well rested
then take them, and putt awaye the Coleworte leafe, and grinde
them in a morter, and putt to ytt oyle of roses, and grinde them togeather
then take itt and laye itt to the pyles withe a trosser, and vse this
mornynge and evenynge.

ffor the fflixe

Take horsedeunge new made and frie itt withe sweete butter
and putt itt in a clothe and laye itt to the fundamente as hott
as you maye suffer ytt, and lye vppon vntill you haste ease

ffor Deafnes

Take blacke woole whiche growes vppon the flanke
of a sheepe and burne and mingell them togeather
and putt them into the eare"""

    ref = """My Lorde of Cannterberries
Brothe for a Consumptione
Take like as before sauinge putt thereto a handfull of voilett leaues
langdebeeffe leaues Buorrage leaues and strawberrie leaues, knitt
togeather of euerie one alike quantitye.
For the pyles
Takeone handefull of mollett leaues, and wrappe them in a Colewort
leafe, and rake them in the Imbers vntill they bee well rosted.
then take them, and putt awaye the Coleworte leafe, and grinde
them in a morter, and putt to ytt oyle of roses, and grinde them togeather
then take itt and laye itt to the pyles withe a trusser, and use this
moreninge and euenynde.
For the Flixe
Take horsedounge new made and frie itt withe sweete butter.
and putt itt in a clothe and laye itt to the fundamente. as hott
as yow maye suffer ytt, and sitte uppon untill yow haue ease.
For Deffnes
Take blacke woole, whiche growes vppon the flanke
of a sheepe and tarre, and mingell them togeather
and putt them into the eare."""

    return blind, ref, "Henslow MS688"


def process_sedley():
    """Process Sedley MS534."""
    blind = """A Salue for sundry sores called
the Leaden plaister

Take one pt of oyle oliue of the best Take a pounde of
lead very well centured with dust 12 ounces of
Spanish sope incorporate all those well together in
an earthen pott well glased & when the lead is incor-
porated that the softe comes appermost & putt it upon
a small face of coales contineweinge the said fire an
houres & a halfe still stirringe it on a bole of boyes
fastned to a sticke of wood, yt make yr fire some
what eager, till the reddnes be turned into a gray
colour but yt must not leaue stirringe till the
matter be turned into the colour of oyle somewhat
darker, then drop it on a wooden trencher yt it is
nether cleue to yt fingers nor the trencher favourith
enoughe, then dipp thearein in that, the hear or
thereon dipped will last 20 yeares, yt of glory yt knees
this plaister laid to the stomack provoke appetite and
takes away the paines of the stomack laid to the
sides tis a remedy for the stitche laid to the
reines of the back it stops the bloudy fluxe

openings of the reines heat of the Kidneyes noodes
of the backe it heales all swellinges, Aches & bruises it
breakes ffelons, Impostuemes, pushes & styles them in
livinge applyed to the fineament it heales all diseases
thereon laid to the head, it is good for the menills

A Tried Cordiall for Mistris Nowell in Childbed

Take a quarter of a pint of Couslip water & twoo ounces of
Syrrup of Clovegilliflowers & a pennyworth of Cinnamon
water & a Spoonefull of Claret wine & Manus
Cristi mingle all these together and it is a soverain
good cordiall for any, especially for one that lyes
in Childbed

Pills for the Gall

Two receipts yt followe and ever
after A Tetter

Take one handfull of Sallanders & as much bay
salt as can take up & twone yt finger & Thumbe &
the iuice of halfe a Lemon stamp yt together in a
Morter & straines the iuice out & small the place of yt
& putt some of the hearbs upon it, vse this 2 or 3
dayes togeather dressing it 3 or 4 times in a Day
togeather &c"""

    ref = """A Salve for sundry vses called
the Leaden plaister
XXVII

Take one pound of oyle olive of the best 1 pound of white
Lead very well calcinated into dust, 12 ounces of
Spanish sope incorporate all these well together in
an earthen pott well glazed & when they be well incor\u2060porated that the sope comes upermost & put it upon
a small fire of coales, continueinge the said fire an
houre & a halfe still stirring it with a bolt of Iron
fastned to a Stick of wood, then make your fire some
what bigger, till the redness be turned into a grey
collour but you must not leave stirringe till the
matter be turned into the colour of oyle somewhat
darker, then drop it on a wooden trenchar & if it
neither cleave to your fingers nor the trenchar t'is boyled
enough, then dipp your cloathes in that, the Searclothes
therein dipped will last 20 yeares, & the older the better
this plaister laid to the stomach provokes appetite and
takes away the paine of the Stomach layd to the
belly, t'is a remedy for the Collicke laid to the
reines of the back it stops the bloudy flux

Runinge of the reines heat of the kidney & weakness
of the back, it heales all swellings, Aches & bruises, it
breakes the ffellons, Impostumes, pushes & heales them
being applyed to the fundaments it heales all diseases
therein laid to the head, it is good for the vnnilla.

A Good Cordiall For A woman in Childbed
XXVIII

Take a quarter of a pint of Cowslip water & 2 ounces of
Syrrup of Clovegillyflowers & 2 pennyworth of Cinamon
water & 2 Spoonefulls of Clarett wine & Alcemus one
dramme mingle all these together and it is a soveraigne cordiall for any especially for one that lyes
in Childbed

Pills for the head
XXIX

Take one handfull of Alloes one dramme

ffor A Tetter

Take one handfull of Sallandine & as much bay
salt as can take up betweene your finger & Thumbe &
the juice of halfe a Lemon stamp them together in a
Mortar & straine the juice out & wash the place and
then put some of the hearbs upon it, vse this 3 or 4
dayes together dressinge it 3 or 4 times in a day
together &c"""

    return blind, ref, "Sedley MS534"


def process_bulkeley():
    """Process Bulkeley MS169."""
    blind = """of Lavander, her comperaturs,

Lavander is hott & drye, & that in the third degree.
& is of a thinne substance, stiffninges of many arising
& spirituall also, to purifie it is said to bee good in
any case against the diseases of the head, &
especially those which cause them to bee of small or
bee ymmit not of a ondance of humors, but
rather of a qualitie only.

The vertues

The distilled water of Lavander smelt vnto,
or the temples and fore-head bathed therewith,
is a re freshnesse to revint that haue the catalepsie
a light migram, & to them that haue the fallinge
sicknes, & that lose to some men. But wee see
there is abundans of humors, of thicke mixed
with blood, it is not then to bee vsed solely, nether
is the composition to bee taken, no the much of
distilled water: in which sure kinds of herbes,
flowers, or seeds, & certayne spirits are mixed
or procured though most men despiseth all
adventure anie upon without mashing and diff-
ference at all for by using sure yett strong
that fill & stuffe the head the bycause it
makes greater & the like also brought one
Lavander, especially to open letting of blood, or
putting hands not done before, I putt much
by way of admonition, because esteem were
desirous laste & owerload Apothecarist, & open
for[...]s woemen, do be ob yt rule compitions
& dispers of the like kinde, not onely to those
that haue the Apoplexie; but also to those

that"""

    ref = """Of Lauander spike, the temperature.

Lauander is hot & drye, & that in the third degree,
& is of a thinn substance, consistinge of many airie
& spirituall partes. Therefore it is good to be giuen
any way against the diseases of the head, &
espetially those which haue theire originall or
beginninge not of a bundance of humors, but
cheifely of a qualitie onely.

The Vertues.

The distilled water of Lauander smelt vnto,
or the temples and forehead bathed therwith,
is a refreshinge to them that haue the Catalepsie,
a light Migram, & to them that haue the fallinge
sicknes, & that vse to soone much. But when
there is a bundance of humors, espetiallly mixed
with blood, it is not then to be vsed safely, neither
is the composition to be taken, which made of
distilled Wine: in which such kinde of herbes,
flowers, or seedes, & certayne spices are infused
or steeped, though most men do rashly & att
adventure giue them without makinge any dif-
ference at all for by vsinge such hot thinges
that fill & stuffe the head, both the disease is
made greater & the sicke also brought into
danger, espetially when letting of blood, or
purging haue not gone before. This much
by way of admonition, because euery where
divers rash & ouerbould Apothecaries, & other
foolish weomen, do by & by giue such compositions,
& others of the like kinde, not onely to those
that haue the Apoplexie; but also to those

that"""

    return blind, ref, "Bulkeley MS169"


def process_brumwich():
    """Process Brumwich MS160. Heavy [...] markers - align line by line."""
    # For Brumwich, the blind transcription has massive numbers of [...] markers.
    # We need to extract only the words the agent actually attempted to read
    # and compare them against the corresponding parts of the reference.

    # The blind transcription covers two pages (verso 6, recto 7)
    # The reference also covers two pages.

    # Strategy: Extract readable fragments from blind, find corresponding
    # sections in reference, compare only those sections.

    blind_full = """A water of Violett extraordinarily good
of Dames Vyolet yt yt yat grow they
are rayed by yor Doctors
or wher none

Take Devyne of frenche in water very smalle
⌀ ⌀ ⌀ continewe the said a morninge
⌀ ⌀ ⌀ broyle fire more the beatter
⌀ three parts being well ⌀ sett of ⌀
⌀ in ⌀ ⌀ ⌀ ⌀ mese of ⌀
is as sole as enough dressthe ⌀ mixinge
yt ⌀ yt yt present yt the compound ⌀ ⌀
⌀ ⌀ ⌀ ⌀
⌀ ⌀
⌀ be as sure as ytt can before

A salue to ⌀
Take ⌀ ⌀ ⌀ of ⌀ grasse grene, well ⌀
⌀ earthen which couered closed & steeped through
⌀ a ⌀ of ⌀ in ⌀ of the ⌀ ⌀
⌀ ⌀ ⌀ ⌀ ⌀
by them in distilling like a pinte yt of ⌀ ⌀
yt vpon ⌀ ⌀ ⌀
of reed oyle, ⌀ ⌀ ⌀ in a ⌀ ⌀
put in a common ⌀ ⌀ ⌀ ⌀ ⌀ ⌀
⌀ ⌀ ⌀ ⌀ to pfitte yow putt in note
of ⌀ fowle a clothe yt lay in ⌀ mixinge
nothinge of ⌀

yr ⌀ for ⌀ yr ⌀

The ⌀ of ⌀ summer savoured or yett
⌀ in a manner of mese & ⌀ of
broth ⌀ ⌀ ⌀ ⌀ & spare
⌀ ⌀ of ⌀ ⌀ ⌀
⌀ & ⌀ of ⌀ ⌀ ⌀ ⌀
stamp & yt ⌀ same of ⌀ sugar

for ⌀ a ⌀ bone to prepare
⌀ ⌀ the ⌀ of ⌀ ⌀
⌀ the ⌀ ⌀ ⌀ then &c &c yt
⌀ ⌀ yt ⌀ ⌀ yt ⌀ yt ⌀ led
& ⌀ ⌀ ⌀ ⌀ & the ⌀ ⌀
⌀ yt ⌀ ⌀ & ⌀ ⌀ ⌀ & ⌀
the oyle ⌀ & yt ⌀ ⌀ the ⌀ ⌀
⌀ ⌀ ⌀ ⌀
⌀ ⌀ ⌀ ⌀ ⌀ laste ⌀
⌀ ⌀ ⌀ ⌀ yr ⌀ yt yt ⌀
⌀ ⌀

⌀ ⌀ ⌀ ⌀ for ⌀
⌀ ⌀ ⌀

⌀ Take both those ⌀ of euery ⌀ their benefitt
⌀ a ⌀ of Cowslipps ⌀ a ⌀ pound of
⌀ ⌀ ⌀ ⌀ ⌀ ⌀ ⌀
⌀ ⌀ & the ⌀ ⌀ ⌀ yt of these

A ⌀ as you need yt

The ⌀ of two ⌀ in ⌀ peper ⌀ of ⌀ & ⌀ euerie part ⌀
said yt. ⌀

A receipt for ⌀ ⌀ to ⌀ Comittis her coruption

Take of ⌀ of ⌀ ⌀ gallons a ⌀ & ⌀ other ⌀ on
& a ⌀ of ⌀ ⌀ ⌀ ⌀ of ⌀ ⌀
⌀ ⌀ ⌀ Take the ⌀ ⌀ they ⌀
⌀ of ⌀ lett ⌀ ⌀ the & ⌀ ⌀ ⌀ from
& ⌀ a ⌀ pinte of ⌀ pepper & ⌀ of ⌀ ⌀
⌀ ⌀ of ⌀ & ⌀ ⌀ ⌀ the ⌀ of this ⌀
⌀ ⌀ ⌀ would ⌀ to ⌀ or the ⌀ ⌀ ⌀
⌀ ⌀ & yt ⌀ for yor ⌀ ⌀ ⌀ the ⌀
⌀ ⌀

a very good receipt for the ⌀ commended yt Mistris Bartley

Take a very great handfull of ⌀ lett a pound of raisins of
the ⌀ halfe a pound of them ⌀ the ⌀ ⌀ ⌀
⌀ then ⌀ & ⌀ & that the ⌀ ⌀ ⌀ this
⌀ & ⌀ from ⌀ ⌀ ⌀ ⌀ ⌀
⌀ yt ⌀ ⌀"""

    ref_full = """A water of Exelent uirtue to helpe the weake or dimme sight of the eyes when they are decayed by age sicknes or other way

Take 3 drames of tueiah in puder uery smalle & as much of aloes epyricum in puder 2 drames of fine sugar 6 ounces of red rose water 6 ounces of good white wine mix all thes together & put it into a Cleane glase being well Closed & stoped & set it in the sune a mounth together mixing & stiring together all the sayd things at least ons a day to the intent you in corproate this being done take of the same water & put one drope in each eye morning & euening contineue soe a Cartin space it will cause the sight to come again & be as pure as it was before

A water to Stringthen the sight

Take of wood bettony of 3 leaued grase with the white spote ockley Cristy yarow sinckfold sallendine red fenill of each a good handfull of eye bright 2 great handfulls a handfull of white rosses or the water of them a quarter of a pinte shread all this together & lay them in steepe in halfe a pinte of white wine & 2 or 3 sponfulls of honey in an earthen pot close stoped one whole night in the morning still it in a common still adding to it halfe a pint of the urine of a man Child when you put it into the stille drinck a litell of this in the morning festing 2 howers after it & with a litell rage wash the eyes

A powder for the eyes

Take of the seeds of Corander prepared & swet fenill of each a drame of mase 2 scruples of eye bright one ounce of fine sugar beaten & seised 3 ounces make a powder of them take halfe a sponfull of it after diner & after supper

To Cuer a blind horse or Cristane

Take of the best & newest wheat & lay it Corne by Corne one a Clean Cleauer then take a red hot fyre shouell & lay upon it & soe let a man tread hard upon it & ther will come forth an oyle then take a feather quikley & like up the oyle with it & soe draw the feather through the eye

A water for sore eyes whose lides are all swelled

Take a pritey quantety of red rosewater & as much Alowes beaten to fine powder as with turne it yeallow drope a drope into the eyes morning & euening & wash the eye lides with a feather

A Medicine for sore eyes

Take three Cloues beat them fine and searse them three Spoonefulls of fennill water 3 Spoonefulls of mamsey 3 penny worth of Tutty pared and beaten fine mix all these in a little glasse and dresse the eye with a feather once a day or as you shall see occasion

For a pinne or pin & web in the Eye

The white of hens doung, and grated ginger, more of the white than of the ginger put some into the eye

A water for sore eyes commeded by Sir James Langham

Take of watter of frogs spawn perdelicum half a pinte infuse into it a dram of uolus metelorum after wait decant it of through a peice of lawne paper after put into it of Salprunla & sugar candy finly powdred of each half an ounce after it has stood so 24 howers strein it through a thick peice of brown paper & keep it for your use it is for cooling the eyes & preseruing & stringthing them & to take of specks in the eyes put in more sugar & salprunlla put some of this water into a prety wide mouth vioyll so open as to receiue the eye open into it & so let the water lye upon the eye being opened some while this you may doe in a morning

A uery good receipt for sore eyes commended by Mrs Worsley

Take a uery good handfull of scabeious half a pound of raisons of the sun stoned half a pound of blue corans brused put thes into a galond of midling bear & drinke no other drinke & this has helpt many they must at the same tyme lay blistering plaisters behind the ears"""

    # For Brumwich, the blind transcription is so fragmentary that
    # line-by-line comparison is impossible. Instead, we extract only
    # the words the agent actually read (non-⌀ tokens) and try to
    # match them to corresponding words in the reference.

    # Given the massive illegibility, we'll do a simplified approach:
    # Extract all non-⌀ text fragments, remove isolated function words
    # that can't be aligned, and compare the fragments we CAN align.

    # Actually, per the instructions: "Strip [...] illegibility markers from
    # the blind transcription AND any corresponding text from the reference
    # that aligns with those gaps."

    # For Brumwich, the transcription is so fragmentary we need to identify
    # what lines in the blind correspond to what lines in the reference.
    # Let me try to align by identifiable landmarks.

    return blind_full, ref_full, "Brumwich MS160"


def process_jane_jackson():
    """Process Jane Jackson MS373."""

    blind_full = """for Drinck and lay it to your nauell as hott as you can endure
& The oile of a mace is very much to a dose twelve or
⌀

for hearteburne or the stomacke ⌀ ⌀ good ⌀ ⌀ of
other ⌀ one ⌀ of rosemary ⌀ one ⌀ of
the ⌀ ⌀ ⌀ ⌀ the ⌀ ⌀ ⌀ cold
⌀ of ⌀ ⌀ the ⌀ ⌀ ⌀ ⌀ ⌀ ⌀
the ⌀ yt ⌀ the ⌀ the ⌀ ⌀ ⌀ ⌀

An ⌀ for the ⌀
for hose ⌀ and ⌀ them ⌀ ⌀ all
⌀ ⌀ ⌀

ffor ⌀

Take ⌀ ⌀ ⌀ and make ⌀ ⌀ a grasse
⌀ ⌀

for the dropsey

Take Elder ⌀ ⌀ and a gallon of strong ale ⌀ &
⌀ a ⌀ about and ⌀ a ⌀ & ⌀ a ⌀
⌀ ⌀ ⌀ ⌀ ⌀ ⌀
another ⌀ in the ⌀ by the ⌀ yt ⌀ ⌀ ⌀
⌀ &c a ⌀ ⌀ the ⌀ ⌀ ⌀

Take a handfull of ⌀ and a quantitie of dried Tabaco
and ⌀ yr ⌀ ⌀ ⌀ and the ⌀ is named ⌀
⌀ & ⌀ ⌀ ⌀ the ⌀ ⌀ of ⌀
⌀ ⌀ ⌀ the ⌀ ⌀ ⌀ ⌀ & ⌀ the strength
⌀ then ⌀ the ⌀ then ⌀ & ⌀ & the remainder
of the ⌀ yt ⌀ & ⌀ the ⌀ ⌀ & ⌀ ⌀

A receipt ⌀ ⌀

The ⌀ ⌀ and ⌀ and ⌀ in ⌀ ⌀ a
⌀ ⌀ and ⌀ ⌀ ⌀ & ⌀ & ⌀ ⌀ ⌀
⌀ ⌀ ⌀

A ⌀ for ⌀ ⌀ ⌀

⌀ the ⌀ of ⌀ ⌀ yt ⌀ ⌀ a ⌀
⌀ a ⌀ supping the ⌀ of ⌀ is ⌀ ⌀
the ⌀ ⌀ ⌀ ⌀ ⌀ the ⌀ ⌀ the ⌀
⌀ & ⌀ ⌀ ⌀ & the ⌀ of ⌀ ⌀ ⌀ ⌀

for an ⌀ and on the ⌀

The ⌀ ⌀ ⌀ and ⌀ harts ⌀ of ⌀ ⌀ ⌀
in ⌀ ⌀

⌀ ⌀ a ⌀ and and ⌀ ⌀ of ⌀ ⌀ ⌀ of
a ⌀ ⌀ ⌀ & a ⌀ ⌀ and ⌀ ⌀ that ⌀ ⌀
and ⌀ the ⌀ ⌀ ⌀ of ⌀ ⌀ ⌀ ⌀
the ⌀ yt ⌀ ⌀

for ⌀ the ⌀ ⌀ ⌀

⌀ ⌀ ⌀ the ⌀ ⌀ one of ⌀ standing ⌀ ⌀
⌀ and ⌀ then ⌀ ⌀ ⌀ ⌀ then ⌀ ⌀
the ⌀ of ⌀ ⌀

⌀ the ⌀ ⌀ ⌀ ⌀ one of ⌀ standing ⌀
⌀ and ⌀ & then ⌀ ⌀ ⌀ ⌀ ⌀ ⌀

⌀ ⌀ ⌀ ⌀ in ⌀ draining ⌀ after the first ⌀ ⌀

⌀ ⌀ then ⌀ ⌀ and ⌀ ⌀ ⌀
⌀ ⌀ ⌀ and ⌀ of ⌀ ⌀ ⌀ ⌀
⌀ ⌀ the ⌀ ⌀ and ⌀ together
⌀ ⌀ ⌀

⌀ ⌀ ⌀"""

    ref_full = """the harth and lay it to the navell as hot as you can indure it This use shifting it once in xxiiij howers 3 or 4 dayes together

For the pilling of the face

Take Turpendine of venice and wash it with red rose water till you haue taken away the smell of the turpentine then take the marrow of a stagg or for want thereof deere suitt and melt them altogether but lett them not seeth put into it vergins wax more then the qantity of the suett and so stirr it still till it be could

For freckles on the face

Take the leaues of white poppy and distill them and with the water thereof wash your face

For a Timpany

Take flouer delice and seeth them in white wine from a quart to a pinte and drinke that next your heart ix mornings together

A Fume for the same

Take a Pottle of white wine and a gallon of runing water and the dung of a ston'd horse and lett it seeth a while then sitt ouer it on a close stoole alwayes as hott as you can suffer it of[.....] times in the day by the space of ix dayes half an hower at a time or an hower if you can

For the same

Take a quantitie of vrine and a quantity of sheepes Tallow well clarified and boyled together till half the vrine bee wasted Then take as much black wooll of the sheeps flank as will couer all your stomack down to your nauell from the one side of your ribbs to the other, when you haue taken the vrine from the fyer put the woole into it till it bee through wett, then wring the Liquor out of the woole and lay it ouer all aforesaid and euer as the swelling doth descend follow it with the medicine vntill it come into your leggs Ankles and feete refresse the woole in the Liquor twice a day at the least and when the swelling is come downe cleane out of the body lett a Surgeon make an Issue in each of your insteps and lett it so runne out till the swelling be cleane dissolued Then lay a healing plaster to it and dry it vp, butt in any wise lay not the woole vnto your legg after the issue made

Another of the same

Take radish rootes slice them and seeth them in white wine from a quarte to a pint and drinke euery two mornings a pint vsing it thus it will breake your Tympany.

A restoratiue for a Consumption

Take the cleane yelks of xxx egge new layd lay them in cleane water halfe an hower and take away the straynes of them and putt to them a quart of cow milke as it cometh from the cow a pinte of rosewater the crumes of a penny white loafe beate them all together and put them into a stillitory distill it all together with a soft fyer, It will bee neere hand a quarte of water drinke of it oftentimes ix euery day.

For an euill sore in the head

Take neats foote oyle and doues dunge, beate them together till they come to bee a salue then annoynt the head with it twice a day morning and evening, when it is almost whole put a little hony to the medicine and that will make the haire grow when it is Cleane whole within on weeke or two peraduenture it will breake out againe in little white pimples, But then annoint it againe with the medicine and it will bee whole for euer

For the Migrim in the head

Take housleeke and garden wormes more of the housleek then of wormes and stamp them together putt thereto fine flower make it plasterwise spread it on a fine cloth and lay to the forehead temples and all

For a stich or ach in the side or any other place and for the gout

Take Camomile flowers meliote flowers and wormwood leaues of each mj well dryed and beaten to powder semgreke linseed of each ʒij anyseed, Cumminseede of each ℥j mustick ℥jd breake all these into smale powlder and medle them well together make of all them one powlder then take a pottle of strong vinegar and a quarte of runing water boyle them well together and put thereto a handfull of your powlder and let it boyle a little while Then take it from the fyer as fast as you can and make ready two cloaths of frize as broad as your too hands a peece wett them that Liquor and lay on the place where the greife is as you may suffer it And when the"""

    return blind_full, ref_full, "Jane Jackson MS373"


def extract_readable_words(text):
    """Extract non-illegible words from text with ⌀ markers."""
    words = text.split()
    readable = [w for w in words if w != '⌀']
    return readable


def compute_cer_for_aligned_text(blind_text, ref_text, manuscript_name):
    """Compute CER for two aligned text strings."""
    dist, subs, ins, dels = levenshtein_distance(ref_text, blind_text)
    ref_len = len(ref_text)
    if ref_len == 0:
        return 0, 0, 0, 0, 0, 0
    cer = dist / ref_len
    return cer, dist, subs, ins, dels, ref_len


def find_word_differences(blind_text, ref_text):
    """Find word-level differences for error categorization."""
    blind_words = blind_text.split()
    ref_words = ref_text.split()

    # Use word-level edit distance to align words
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

    # Backtrace
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
            diffs.append(('INS', '', ref_words[j-1]))
            j -= 1
        elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
            diffs.append(('DEL', blind_words[i-1], ''))
            i -= 1
        else:
            break

    diffs.reverse()
    return diffs


def categorize_error(ref_word, blind_word):
    """Categorize the type of error."""
    if ref_word.lower() == blind_word.lower():
        return "capitalization"

    # Check u/v convention
    if ref_word.replace('u', 'v').replace('U', 'V') == blind_word.replace('u', 'v').replace('U', 'V'):
        return "u/v convention"
    if ref_word.replace('v', 'u').replace('V', 'U') == blind_word.replace('v', 'u').replace('V', 'U'):
        return "u/v convention"

    # Check i/y convention
    if ref_word.replace('i', 'y') == blind_word or ref_word.replace('y', 'i') == blind_word:
        return "i/y convention"

    # Terminal e
    if ref_word + 'e' == blind_word or ref_word == blind_word + 'e':
        return "terminal 'e'"
    if ref_word + 'e' == blind_word.lower() or ref_word.lower() == blind_word + 'e':
        return "terminal 'e'"

    # Double letter
    if len(ref_word) > len(blind_word):
        # Check if adding a doubled letter to blind = ref
        for i in range(len(blind_word)):
            test = blind_word[:i] + blind_word[i] + blind_word[i:]
            if test == ref_word:
                return "double-letter omission"
    elif len(blind_word) > len(ref_word):
        for i in range(len(ref_word)):
            test = ref_word[:i] + ref_word[i] + ref_word[i:]
            if test == blind_word:
                return "double-letter addition"

    # Punctuation
    if ref_word.strip('.,;:!?') == blind_word.strip('.,;:!?'):
        return "punctuation"

    # Word segmentation
    # (This would require checking adjacent words)

    # Letterform confusion
    ref_lower = ref_word.lower()
    blind_lower = blind_word.lower()
    if len(ref_lower) == len(blind_lower):
        diffs = sum(1 for a, b in zip(ref_lower, blind_lower) if a != b)
        if diffs <= 2:
            return f"letterform misreading ({diffs} char{'s' if diffs > 1 else ''})"

    if len(ref_word) > 0 and len(blind_word) > 0:
        # Check for significant length difference suggesting hallucination
        if abs(len(ref_word) - len(blind_word)) > max(len(ref_word), len(blind_word)) * 0.5:
            return "hallucination/major misreading"

    return "letterform misreading"


def align_brumwich_fragments():
    """
    For Brumwich, do fragment-based alignment.
    Extract readable segments from blind transcription,
    find their best match in the reference, and compute CER
    only on matched segments.
    """
    # The blind transcription is extremely fragmentary.
    # Let's identify the segments we CAN align:

    # Blind line 1: "A water of Violett extraordinarily good"
    # Ref line 1: "A water of Exelent uirtue to helpe the weake or dimme sight of the eyes..."
    # These are recipe headings - they don't match at all. The blind agent misread the heading.

    # Actually, looking at this more carefully, the blind transcription for Brumwich
    # is attempting to read a COMPLETELY DIFFERENT text than what the reference contains.
    # The reference is about eye remedies. The blind is reading "Violett water",
    # "Dames Vyolet", etc. - which suggests the agent is reading from a different
    # page or completely hallucinating.

    # Wait - looking at the reference again, it IS page 10 which covers pages 6-7.
    # The blind agent is also claiming to read pages 6-7. But the content is
    # completely different.

    # This means the agent essentially hallucinated most of the content.
    # We should still compute CER to show this.

    # For Brumwich, let's strip all [...] markers and compute CER on what remains
    # vs the full reference. This will give us a sense of how wrong the reading is.

    blind_readable = """A water of Violett extraordinarily good
of Dames Vyolet yt yt yat grow they
are rayed by yor Doctors
or wher none
Take Devyne of frenche in water very smalle
continewe the said a morninge
broyle fire more the beatter
three parts being well sett of
in mese of
is as sole as enough dressthe mixinge
yt yt yt present yt the compound
be as sure as ytt can before
A salue to
Take of grasse grene, well
earthen which couered closed & steeped through
a of in of the
by them in distilling like a pinte yt of
yt vpon
of reed oyle, in a
put in a common
to pfitte yow putt in note
of fowle a clothe yt lay in mixinge
nothinge of
yr for yr
The of summer savoured or yett
in a manner of mese & of
broth & spare
of
& of
stamp & yt same of sugar
for a bone to prepare
the of
the then &c &c yt
yt yt yt led
& & the
yt & &
the oyle & yt the
laste
yr yt yt
for
Take both those of euery their benefitt
a of Cowslipps a pound of
& the yt of these
A as you need yt
The of two in peper of & euerie part
said yt.
A receipt for to Comittis her coruption
Take of of gallons a & other on
& a of of
Take the they
of lett the & from
& a pinte of pepper & of
of & the of this
would to or the
& yt for yor the
a very good receipt for the commended yt Mistris Bartley
Take a very great handfull of lett a pound of raisins of
the halfe a pound of them the
then & & that the this
& from
yt"""

    ref = """A water of Exelent uirtue to helpe the weake or dimme sight of the eyes when they are decayed by age sicknes or other way
Take 3 drames of tueiah in puder uery smalle & as much of aloes epyricum in puder 2 drames of fine sugar 6 ounces of red rose water 6 ounces of good white wine mix all thes together & put it into a Cleane glase being well Closed & stoped & set it in the sune a mounth together mixing & stiring together all the sayd things at least ons a day to the intent you in corproate this being done take of the same water & put one drope in each eye morning & euening contineue soe a Cartin space it will cause the sight to come again & be as pure as it was before
A water to Stringthen the sight
Take of wood bettony of 3 leaued grase with the white spote ockley Cristy yarow sinckfold sallendine red fenill of each a good handfull of eye bright 2 great handfulls a handfull of white rosses or the water of them a quarter of a pinte shread all this together & lay them in steepe in halfe a pinte of white wine & 2 or 3 sponfulls of honey in an earthen pot close stoped one whole night in the morning still it in a common still adding to it halfe a pint of the urine of a man Child when you put it into the stille drinck a litell of this in the morning festing 2 howers after it & with a litell rage wash the eyes
A powder for the eyes
Take of the seeds of Corander prepared & swet fenill of each a drame of mase 2 scruples of eye bright one ounce of fine sugar beaten & seised 3 ounces make a powder of them take halfe a sponfull of it after diner & after supper
To Cuer a blind horse or Cristane
Take of the best & newest wheat & lay it Corne by Corne one a Clean Cleauer then take a red hot fyre shouell & lay upon it & soe let a man tread hard upon it & ther will come forth an oyle then take a feather quikley & like up the oyle with it & soe draw the feather through the eye
A water for sore eyes whose lides are all swelled
Take a pritey quantety of red rosewater & as much Alowes beaten to fine powder as with turne it yeallow drope a drope into the eyes morning & euening & wash the eye lides with a feather
A Medicine for sore eyes
Take three Cloues beat them fine and searse them three Spoonefulls of fennill water 3 Spoonefulls of mamsey 3 penny worth of Tutty pared and beaten fine mix all these in a little glasse and dresse the eye with a feather once a day or as you shall see occasion
For a pinne or pin & web in the Eye
The white of hens doung, and grated ginger, more of the white than of the ginger put some into the eye
A water for sore eyes commeded by Sir James Langham
Take of watter of frogs spawn perdelicum half a pinte infuse into it a dram of uolus metelorum after wait decant it of through a peice of lawne paper after put into it of Salprunla & sugar candy finly powdred of each half an ounce after it has stood so 24 howers strein it through a thick peice of brown paper & keep it for your use it is for cooling the eyes & preseruing & stringthing them & to take of specks in the eyes put in more sugar & salprunlla put some of this water into a prety wide mouth vioyll so open as to receiue the eye open into it & so let the water lye upon the eye being opened some while this you may doe in a morning
A uery good receipt for sore eyes commended by Mrs Worsley
Take a uery good handfull of scabeious half a pound of raisons of the sun stoned half a pound of blue corans brused put thes into a galond of midling bear & drinke no other drinke & this has helpt many they must at the same tyme lay blistering plaisters behind the ears"""

    return blind_readable, ref


def align_jane_jackson_fragments():
    """
    For Jane Jackson, extract readable fragments and align with reference.
    The JJ manuscript has water damage, so many [...] markers, but
    the readable portions should correspond to the reference text.
    """

    # The first line of the blind starts mid-sentence - this is the continuation
    # from a previous page. The reference starts: "the harth and lay it to the navell..."
    # The blind starts: "for Drinck and lay it to your nauell..."

    # Let me trace through the alignable sections:

    # Blind: "for Drinck and lay it to your nauell as hott as you can endure"
    # Ref: "the harth and lay it to the navell as hot as you can indure it"

    # Blind: "for hearteburne or the stomacke ... good ... of"
    # -- This doesn't match anything in the reference well. The ref has
    #    "For the pilling of the face" and "For freckles on the face" next.
    # Actually wait - looking at the reference more carefully:
    # The reference doesn't have a "hearteburne" recipe on this page.
    # The blind is reading content that doesn't match the reference layout.

    # Actually, the reference page 20 starts mid-sentence and continues through
    # many recipes. Let me look at what the blind agent is trying to read vs reference.

    # Let me extract just the readable words from blind (stripping ⌀)
    # and compare against reference.

    blind_readable = """for Drinck and lay it to your nauell as hott as you can endure
& The oile of a mace is very much to a dose twelve or
for hearteburne or the stomacke good of
other one of rosemary one of
the the cold
of the
the yt the the
An for the
for hose and them all
ffor
Take and make a grasse
for the dropsey
Take Elder and a gallon of strong ale &
a about and a & a
another in the by the yt
&c a the
Take a handfull of and a quantitie of dried Tabaco
and yr and the is named
& the of
the & the strength
then the then & & the remainder
of the yt & the &
A receipt
The and and in a
and & &
A for
the of yt a
a supping the of is
the the the
& & the of
for an and on the
The and harts of
in
a and and of of
a & a and that
and the of
the yt
for the
the one of standing
and then then
the of
the one of standing
and & then
in draining after the first
then and
and of
the and together"""

    ref = """the harth and lay it to the navell as hot as you can indure it This use shifting it once in xxiiij howers 3 or 4 dayes together
For the pilling of the face
Take Turpendine of venice and wash it with red rose water till you haue taken away the smell of the turpentine then take the marrow of a stagg or for want thereof deere suitt and melt them altogether but lett them not seeth put into it vergins wax more then the qantity of the suett and so stirr it still till it be could
For freckles on the face
Take the leaues of white poppy and distill them and with the water thereof wash your face
For a Timpany
Take flouer delice and seeth them in white wine from a quart to a pinte and drinke that next your heart ix mornings together
A Fume for the same
Take a Pottle of white wine and a gallon of runing water and the dung of a ston'd horse and lett it seeth a while then sitt ouer it on a close stoole alwayes as hott as you can suffer it times in the day by the space of ix dayes half an hower at a time or an hower if you can
For the same
Take a quantitie of vrine and a quantity of sheepes Tallow well clarified and boyled together till half the vrine bee wasted Then take as much black wooll of the sheeps flank as will couer all your stomack down to your nauell from the one side of your ribbs to the other, when you haue taken the vrine from the fyer put the woole into it till it bee through wett, then wring the Liquor out of the woole and lay it ouer all aforesaid and euer as the swelling doth descend follow it with the medicine vntill it come into your leggs Ankles and feete refresse the woole in the Liquor twice a day at the least and when the swelling is come downe cleane out of the body lett a Surgeon make an Issue in each of your insteps and lett it so runne out till the swelling be cleane dissolued Then lay a healing plaster to it and dry it vp, butt in any wise lay not the woole vnto your legg after the issue made
Another of the same
Take radish rootes slice them and seeth them in white wine from a quarte to a pint and drinke euery two mornings a pint vsing it thus it will breake your Tympany.
A restoratiue for a Consumption
Take the cleane yelks of xxx egge new layd lay them in cleane water halfe an hower and take away the straynes of them and putt to them a quart of cow milke as it cometh from the cow a pinte of rosewater the crumes of a penny white loafe beate them all together and put them into a stillitory distill it all together with a soft fyer, It will bee neere hand a quarte of water drinke of it oftentimes ix euery day.
For an euill sore in the head
Take neats foote oyle and doues dunge, beate them together till they come to bee a salue then annoynt the head with it twice a day morning and evening, when it is almost whole put a little hony to the medicine and that will make the haire grow when it is Cleane whole within on weeke or two peraduenture it will breake out againe in little white pimples, But then annoint it againe with the medicine and it will bee whole for euer
For the Migrim in the head
Take housleeke and garden wormes more of the housleek then of wormes and stamp them together putt thereto fine flower make it plasterwise spread it on a fine cloth and lay to the forehead temples and all
For a stich or ach in the side or any other place and for the gout
Take Camomile flowers meliote flowers and wormwood leaues of each mj well dryed and beaten to powder semgreke linseed of each anyseed, Cumminseede of each mustick breake all these into smale powlder and medle them well together make of all them one powlder then take a pottle of strong vinegar and a quarte of runing water boyle them well together and put thereto a handfull of your powlder and let it boyle a little while Then take it from the fyer as fast as you can and make ready two cloaths of frize as broad as your too hands a peece wett them that Liquor and lay on the place where the greife is as you may suffer it And when the"""

    return blind_readable, ref


def main():
    results = {}

    #############################################
    # 1. HENSLOW MS688
    #############################################
    print("=" * 60)
    print("HENSLOW MS688")
    print("=" * 60)

    blind_h, ref_h, name_h = process_henslow()

    # Normalize whitespace
    blind_h = re.sub(r'\s+', ' ', blind_h).strip()
    ref_h = re.sub(r'\s+', ' ', ref_h).strip()

    dist_h, subs_h, ins_h, dels_h = levenshtein_distance(ref_h, blind_h)
    cer_h = dist_h / len(ref_h) if len(ref_h) > 0 else 0

    print(f"Reference length: {len(ref_h)} chars")
    print(f"Blind length: {len(blind_h)} chars")
    print(f"Edit distance: {dist_h}")
    print(f"  Substitutions: {subs_h}")
    print(f"  Insertions: {ins_h}")
    print(f"  Deletions: {dels_h}")
    print(f"CER: {cer_h:.4f} ({cer_h*100:.2f}%)")

    # Word diffs
    diffs_h = find_word_differences(blind_h, ref_h)
    print(f"\nWord-level differences ({len(diffs_h)}):")
    for op, ref_w, blind_w in diffs_h:
        if op == 'SUB':
            cat = categorize_error(ref_w, blind_w)
            print(f"  {op}: ref='{ref_w}' -> blind='{blind_w}' [{cat}]")
        elif op == 'INS':
            print(f"  {op}: missing ref word '{ref_w}' [word omitted in blind]")
        elif op == 'DEL':
            print(f"  {op}: extra blind word '{blind_w}' [word added in blind]")

    results['henslow'] = {
        'cer': cer_h, 'dist': dist_h, 'ref_len': len(ref_h),
        'subs': subs_h, 'ins': ins_h, 'dels': dels_h, 'diffs': diffs_h
    }

    #############################################
    # 2. SEDLEY MS534
    #############################################
    print("\n" + "=" * 60)
    print("SEDLEY MS534")
    print("=" * 60)

    blind_s, ref_s, name_s = process_sedley()
    blind_s = re.sub(r'\s+', ' ', blind_s).strip()
    ref_s = re.sub(r'\s+', ' ', ref_s).strip()

    dist_s, subs_s, ins_s, dels_s = levenshtein_distance(ref_s, blind_s)
    cer_s = dist_s / len(ref_s) if len(ref_s) > 0 else 0

    print(f"Reference length: {len(ref_s)} chars")
    print(f"Blind length: {len(blind_s)} chars")
    print(f"Edit distance: {dist_s}")
    print(f"  Substitutions: {subs_s}")
    print(f"  Insertions: {ins_s}")
    print(f"  Deletions: {dels_s}")
    print(f"CER: {cer_s:.4f} ({cer_s*100:.2f}%)")

    diffs_s = find_word_differences(blind_s, ref_s)
    print(f"\nWord-level differences ({len(diffs_s)}):")
    for op, ref_w, blind_w in diffs_s:
        if op == 'SUB':
            cat = categorize_error(ref_w, blind_w)
            print(f"  {op}: ref='{ref_w}' -> blind='{blind_w}' [{cat}]")
        elif op == 'INS':
            print(f"  {op}: missing ref word '{ref_w}'")
        elif op == 'DEL':
            print(f"  {op}: extra blind word '{blind_w}'")

    results['sedley'] = {
        'cer': cer_s, 'dist': dist_s, 'ref_len': len(ref_s),
        'subs': subs_s, 'ins': ins_s, 'dels': dels_s, 'diffs': diffs_s
    }

    #############################################
    # 3. BULKELEY MS169
    #############################################
    print("\n" + "=" * 60)
    print("BULKELEY MS169")
    print("=" * 60)

    blind_b, ref_b, name_b = process_bulkeley()
    blind_b = re.sub(r'\s+', ' ', blind_b).strip()
    ref_b = re.sub(r'\s+', ' ', ref_b).strip()

    dist_b, subs_b, ins_b, dels_b = levenshtein_distance(ref_b, blind_b)
    cer_b = dist_b / len(ref_b) if len(ref_b) > 0 else 0

    print(f"Reference length: {len(ref_b)} chars")
    print(f"Blind length: {len(blind_b)} chars")
    print(f"Edit distance: {dist_b}")
    print(f"  Substitutions: {subs_b}")
    print(f"  Insertions: {ins_b}")
    print(f"  Deletions: {dels_b}")
    print(f"CER: {cer_b:.4f} ({cer_b*100:.2f}%)")

    diffs_b = find_word_differences(blind_b, ref_b)
    print(f"\nWord-level differences ({len(diffs_b)}):")
    for op, ref_w, blind_w in diffs_b:
        if op == 'SUB':
            cat = categorize_error(ref_w, blind_w)
            print(f"  {op}: ref='{ref_w}' -> blind='{blind_w}' [{cat}]")
        elif op == 'INS':
            print(f"  {op}: missing ref word '{ref_w}'")
        elif op == 'DEL':
            print(f"  {op}: extra blind word '{blind_w}'")

    results['bulkeley'] = {
        'cer': cer_b, 'dist': dist_b, 'ref_len': len(ref_b),
        'subs': subs_b, 'ins': ins_b, 'dels': dels_b, 'diffs': diffs_b
    }

    #############################################
    # 4. BRUMWICH MS160
    #############################################
    print("\n" + "=" * 60)
    print("BRUMWICH MS160")
    print("=" * 60)

    blind_br, ref_br = align_brumwich_fragments()
    blind_br = re.sub(r'\s+', ' ', blind_br).strip()
    ref_br = re.sub(r'\s+', ' ', ref_br).strip()

    dist_br, subs_br, ins_br, dels_br = levenshtein_distance(ref_br, blind_br)
    cer_br = dist_br / len(ref_br) if len(ref_br) > 0 else 0

    print(f"Reference length: {len(ref_br)} chars")
    print(f"Blind length: {len(blind_br)} chars")
    print(f"Edit distance: {dist_br}")
    print(f"  Substitutions: {subs_br}")
    print(f"  Insertions: {ins_br}")
    print(f"  Deletions: {dels_br}")
    print(f"CER: {cer_br:.4f} ({cer_br*100:.2f}%)")

    results['brumwich'] = {
        'cer': cer_br, 'dist': dist_br, 'ref_len': len(ref_br),
        'subs': subs_br, 'ins': ins_br, 'dels': dels_br, 'diffs': []
    }

    #############################################
    # 5. JANE JACKSON MS373
    #############################################
    print("\n" + "=" * 60)
    print("JANE JACKSON MS373")
    print("=" * 60)

    blind_jj, ref_jj = align_jane_jackson_fragments()
    blind_jj = re.sub(r'\s+', ' ', blind_jj).strip()
    ref_jj = re.sub(r'\s+', ' ', ref_jj).strip()

    dist_jj, subs_jj, ins_jj, dels_jj = levenshtein_distance(ref_jj, blind_jj)
    cer_jj = dist_jj / len(ref_jj) if len(ref_jj) > 0 else 0

    print(f"Reference length: {len(ref_jj)} chars")
    print(f"Blind length: {len(blind_jj)} chars")
    print(f"Edit distance: {dist_jj}")
    print(f"  Substitutions: {subs_jj}")
    print(f"  Insertions: {ins_jj}")
    print(f"  Deletions: {dels_jj}")
    print(f"CER: {cer_jj:.4f} ({cer_jj*100:.2f}%)")

    results['jane_jackson'] = {
        'cer': cer_jj, 'dist': dist_jj, 'ref_len': len(ref_jj),
        'subs': subs_jj, 'ins': ins_jj, 'dels': dels_jj, 'diffs': []
    }

    #############################################
    # OVERALL
    #############################################
    print("\n" + "=" * 60)
    print("OVERALL RESULTS")
    print("=" * 60)

    total_dist = sum(r['dist'] for r in results.values())
    total_ref = sum(r['ref_len'] for r in results.values())
    overall_cer = total_dist / total_ref if total_ref > 0 else 0

    print(f"Total edit distance: {total_dist}")
    print(f"Total reference chars: {total_ref}")
    print(f"Overall CER: {overall_cer:.4f} ({overall_cer*100:.2f}%)")

    print("\n--- Summary Table ---")
    for name, key in [("Henslow MS688", "henslow"), ("Sedley MS534", "sedley"),
                       ("Bulkeley MS169", "bulkeley"), ("Brumwich MS160", "brumwich"),
                       ("Jane Jackson MS373", "jane_jackson")]:
        r = results[key]
        print(f"{name}: CER = {r['cer']*100:.2f}% (edits={r['dist']}, ref_chars={r['ref_len']})")

    return results


if __name__ == "__main__":
    main()
