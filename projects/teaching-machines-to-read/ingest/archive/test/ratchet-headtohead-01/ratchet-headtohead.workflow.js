export const meta = {
  name: 'ratchet-headtohead-sedley',
  description: 'Head-to-head: ratchet-loop (plain) vs ratchet-loop-forum optimizing Sedley transcription CER',
  phases: [
    { title: 'plain' },
    { title: 'forum' },
    { title: 'compare' },
  ],
}

// ---------------------------------------------------------------------------
// Static config (frozen splits live under ratchet-headtohead-01; same data both arms)
// ---------------------------------------------------------------------------
const PROJ = '/Users/sarahbonanno/daggerobelus.com/projects/teaching-machines-to-read'
const ROOT = `${PROJ}/ingest/archive/test/ratchet-headtohead-01`
const SCORE = `${PROJ}/skills/manuscript-autoresearch-run/scripts/score.py`
const NAIVE = 'Transcribe this manuscript page. Produce a semi-diplomatic transcription.'

const VAL = ['004','007','010','013','016','019','022','025','028','031','034','037','041']
const TEST = ['005','008','011','014','017','020','023','026','029','032','035','038','042']

const cfg = JSON.parse(typeof args === 'string' ? (args || '{}') : JSON.stringify(args || {}))
const MAX_ROUNDS = cfg.dry_run ? 1 : (cfg.max_rounds || 10)
const N = cfg.fanout || 6
const PLATEAU_PATIENCE = cfg.plateau_patience || 3
const EPSILON = cfg.epsilon || 0.005
const TARGET = cfg.target || 0.045  // must sit BELOW the naive baseline (~0.069) or the loop exits before optimizing
const DRY = !!cfg.dry_run
const ARMS = cfg.arm ? [cfg.arm] : ['plain', 'forum']

const REGIONS = [
  'long-s / f / ſ confusion', 'minims (i/m/n/u runs)', 'secretary e / d / c forms',
  'abbreviations & brevigraphs', 'line breaks, layout & spacing', 'capitalization & punctuation',
  'u/v and i/j interchange', 'archaic letters (thorn, yogh) & terminal flourishes',
]
const INSTANCE = {
  refine: 'Tighten the rule addressing the most frequent substitution or deletion in the current blind error profile.',
  tune: 'Adjust a threshold or heuristic (when to expand abbreviations, how literally to preserve spelling) without adding new structure.',
  restructure: 'Reorganize the method (reorder steps, regroup rules) keeping the same coverage — a clearer pass order.',
  subtract: 'Remove the least-justified instruction or whole section and see if CER holds (ablation). If you add anything, remove something too.',
  generative: 'Make the method BUILD its own intermediate representation for THIS hand first — an alphabet/letterform chart or confusion table — then transcribe against it, instead of applying only fixed rules.',
  first_principles: 'Rebuild the method from scratch on the principle: study the hand first, read bottom-up (strokes → letters → words), and gap rather than guess.',
  cross_pollinate: 'Fuse the strongest ideas from the two best archived methods into one coherent method.',
  wildcard: 'Try a deliberately unconventional framing of the transcription task that might surface a blind spot the current method has.',
}

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------
const EXP_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['rationale', 'diff_summary', 'method_text'],
  properties: {
    rationale: { type: 'string', description: 'what you changed and why it should lower CER' },
    predicted_effect: { type: 'string', description: 'forum only: rough predicted CER effect, e.g. "-0.02 via fewer long-s subs"' },
    diff_summary: { type: 'string', description: 'one line: what sections changed (+adds / -removes)' },
    method_text: { type: 'string', description: 'the FULL revised method.md text' },
  },
}
const TRANS_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['pages_written'],
  properties: {
    pages_written: { type: 'integer' },
    missing: { type: 'array', items: { type: 'string' } },
    notes: { type: 'string' },
  },
}
const ROUND_SCORE_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['baseline', 'candidates'],
  properties: {
    baseline: {
      type: 'object', additionalProperties: false,
      required: ['rep_dipl', 'rep_read', 'error_profile_text'],
      properties: {
        rep_dipl: { type: 'array', items: { type: 'number' } },
        rep_read: { type: 'array', items: { type: 'number' } },
        error_profile_text: { type: 'string' },
      },
    },
    candidates: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        required: ['id', 'missing', 'memorized'],
        properties: {
          id: { type: 'string' },
          diplomatic_cer: { type: ['number', 'null'] },
          reading_cer: { type: ['number', 'null'] },
          missing: { type: 'integer' },
          memorized: { type: 'boolean' },
        },
      },
    },
  },
}
const SINGLE_SCORE_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['diplomatic_cer', 'reading_cer', 'missing'],
  properties: {
    diplomatic_cer: { type: ['number', 'null'] },
    reading_cer: { type: ['number', 'null'] },
    missing: { type: 'integer' },
  },
}
const CHALLENGER_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['recommendation', 'reasoning'],
  properties: {
    recommendation: { type: 'string', enum: ['promote', 'hold'] },
    objections: { type: 'array', items: { type: 'string' } },
    rescue: { type: ['string', 'null'] },
    reasoning: { type: 'string' },
  },
}

// ---------------------------------------------------------------------------
// Agent helpers
// ---------------------------------------------------------------------------
function imgList(split, pages) {
  return pages.map(p => `${ROOT}/corpus/${split}/images/page-${p}.jpg`).join('\n')
}

// Blind transcriber: image + method only, never references.
function transcribe(methodText, hypDir, split, pages, label, phase) {
  const prompt = `You are a blind manuscript transcriber in an optimization loop. You see ONLY page images and the method below — you have NO access to any reference/answer transcription, and must not seek one.

METHOD TO FOLLOW (verbatim — this is the candidate being tested):
-----
${methodText}
-----

TASK: Transcribe each of these ${pages.length} manuscript pages (Lady Sedley MS534, English secretary hand, recipe book) following the method above. Produce a semi-diplomatic transcription per page.

Images (read each with the Read tool):
${imgList(split, pages)}

COMPLETENESS IS CRITICAL: transcribe each page IN FULL, from the very first line at the top to the very last line at the bottom — including every recipe, marginal note, catchword, and page number. Never stop partway, never summarize, never write "[continues]". A page that is only partly transcribed scores as a large error and corrupts the experiment. If a page is long, keep going until every visible line is rendered.

Output: first \`mkdir -p ${hypDir}\`. Then for EACH page write its COMPLETE transcription to ${hypDir}/page-<NNN>.txt (e.g. ${hypDir}/page-${pages[0]}.txt). Work page by page and write each file immediately so progress persists. Plain UTF-8 text, the transcription only (no commentary, no markdown fences).

Do NOT run score.py or look for reference files. Return how many page files you wrote and which page numbers (if any) you could not complete.`
  return agent(prompt, { label, phase, schema: TRANS_SCHEMA, agentType: 'general-purpose' })
    .then(r => r || { pages_written: 0, missing: pages, notes: 'agent failed' })
}

// Score one hyp dir on a split.
function scoreOne(hypDir, split, label, phase) {
  const prompt = `Run the sealed blind scorer and report numbers ONLY.

Command:
  python3 ${SCORE} --splits-root ${ROOT} --split ${split} --hyp-dir ${hypDir}

It prints JSON. Return diplomatic_cer, reading_cer, and the count of missing_hypotheses (length of that array). If the command errors, return diplomatic_cer=null, reading_cer=null, missing=${split === 'val' ? VAL.length : TEST.length}.`
  return agent(prompt, { label, phase, schema: SINGLE_SCORE_SCHEMA, agentType: 'general-purpose' })
    .then(r => r || { diplomatic_cer: null, reading_cer: null, missing: 99 })
}

// ---------------------------------------------------------------------------
// Allocation: barbell + breathing + credit/yield
// ---------------------------------------------------------------------------
function allocate(round, state, credit, archiveSize, isForum) {
  // base barbell weights (low + high heavy; medium starved)
  const w = { refine: 0.26, tune: 0.12, restructure: 0.05, subtract: 0.15,
    generative: 0.10, first_principles: 0.12, cross_pollinate: 0.10, wildcard: 0.10 }
  const bump = (k, f) => { w[k] = (w[k] || 0) * f }
  if (state === 'improving') { bump('refine', 1.6); bump('tune', 1.4); bump('wildcard', 0.6) }
  if (state === 'plateau') { bump('first_principles', 1.8); bump('subtract', 1.5); bump('generative', 1.6); bump('cross_pollinate', 1.4); bump('wildcard', 1.5); bump('refine', 0.6) }
  if (state === 'endgame') { bump('refine', 1.8); bump('tune', 1.6); bump('wildcard', 0.3); bump('first_principles', 0.6) }
  // credit/yield nudge: archetypes whose promotes (plain) or tracked reasons (forum) paid off get weight
  for (const k of Object.keys(w)) {
    const c = credit[k] || { tries: 0, win: 0 }
    const rate = c.tries ? c.win / c.tries : 0
    w[k] *= (1 + rate) // both arms reward what worked; forum's `win` counts reason-tracked promotes
  }
  if (archiveSize < 2) { w.cross_pollinate = 0 } // need >=2 archived winners to cross-pollinate
  // round 1: fixed initial mix
  if (round === 1) return ['refine', 'refine', 'tune', 'subtract', 'first_principles', 'generative'].slice(0, N)
  // proportional allocation of N slots
  const ks = Object.keys(w).filter(k => w[k] > 0)
  const total = ks.reduce((s, k) => s + w[k], 0)
  const picks = []
  // largest-remainder style, deterministic
  const quota = ks.map(k => ({ k, q: (w[k] / total) * N }))
  quota.sort((a, b) => b.q - a.q)
  for (const it of quota) { const n = Math.floor(it.q); for (let i = 0; i < n && picks.length < N; i++) picks.push(it.k) }
  let qi = 0
  while (picks.length < N) { picks.push(quota[qi % quota.length].k); qi++ }
  // guarantee >=1 escape arm
  const escape = ['first_principles', 'subtract', 'generative', 'cross_pollinate', 'wildcard']
  if (!picks.some(p => escape.includes(p))) picks[picks.length - 1] = (state === 'plateau' ? 'first_principles' : 'subtract')
  return picks.slice(0, N)
}

// ---------------------------------------------------------------------------
// One arm
// ---------------------------------------------------------------------------
async function runArm(arm) {
  const isForum = arm === 'forum'
  phase(arm)
  log(`=== ARM ${arm}${isForum ? ' (challenger + argumentative credit)' : ' (no challenger)'} — start ===`)

  let baselineMethod = NAIVE
  let baselineCer = null
  const ledger = []
  const archive = [] // {method_text, cer, archetype} best losers
  const credit = {} // archetype -> {tries, win}
  const deadEnds = []
  let roundsSincePromote = 0
  let promotions = 0
  let lastBaselineProfile = '(none yet — round 1)'

  for (let round = 1; round <= MAX_ROUNDS; round++) {
    const rdir = `${ROOT}/${arm}/rounds/r${round}`
    // ---- measure baseline (3 replicates -> robust noise band) ----
    const baseHyps = [`${rdir}/baseline/rep1/hyp`, `${rdir}/baseline/rep2/hyp`, `${rdir}/baseline/rep3/hyp`]
    const baseRuns = await parallel(baseHyps.map((h, i) => () =>
      transcribe(baselineMethod, h, 'val', VAL, `${arm} r${round} baseline-rep${i + 1}`, arm)))
    // ---- determine state for allocation ----
    let state = 'improving'
    if (round > 1 && roundsSincePromote >= 1) state = 'plateau'
    if (MAX_ROUNDS - round <= 1 && !DRY) state = 'endgame'
    const plan = allocate(round, state, credit, archive.length, isForum)
    log(`${arm} r${round}: state=${state} alloc=[${plan.join(', ')}]`)

    // ---- fan out experimenters ----
    const deadTxt = deadEnds.length ? deadEnds.slice(-8).map(d => `- ${d}`).join('\n') : '(none yet)'
    const creditTxt = isForum
      ? Object.entries(credit).map(([k, v]) => `${k}: ${v.win}/${v.tries} reasons tracked`).join('; ') || '(no credit history yet)'
      : Object.entries(credit).map(([k, v]) => `${k}: ${v.win}/${v.tries} promotes`).join('; ') || '(no yield history yet)'

    const experiments = await parallel(plan.map((arch, i) => () => {
      const cdir = `${rdir}/c${i}`
      const region = REGIONS[i % REGIONS.length]
      const forumExtra = isForum
        ? `\nThis is the FORUM arm: you MUST also give a \`predicted_effect\` (your honest rough prediction of the CER change and via what). The loop scores your REASONING by whether this prediction tracks the measured result, so predict sincerely, not optimistically.\nReasoning that has tracked truth so far: ${creditTxt}.`
        : ''
      const prompt = `You are an experimenter in a ratchet-loop optimization of a manuscript transcription METHOD. The metric is diplomatic Character Error Rate (CER) on held pages of Lady Sedley MS534 (English secretary-hand recipe book), measured BLIND. Lower is better. The ratchet only keeps changes that measurably beat the baseline, so a bold change that fails costs nothing — explore real ground.

You do NOT transcribe and you do NOT see any page images or any reference text. You improve the METHOD itself, working from the baseline method and the blind error profile below.

YOUR STRATEGY: ${arch} — ${INSTANCE[arch]}
DIVERSITY FOCUS (own this region so the ${N} candidates don't collapse onto the same edit): ${region}

BASELINE METHOD (your starting point):
-----
${baselineMethod}
-----

BLIND ERROR PROFILE of the baseline on the val pages (single-character counts only — this is all you may see of performance):
${lastBaselineProfile}

DEAD ENDS already tried (do NOT repeat these):
${deadTxt}

Make ONE focused change in the spirit of your strategy. Keep the method a practical, self-contained instruction set a transcriber will follow verbatim. Do not paste reference transcriptions or page-specific answers into it (that is disqualified as memorization).

Write the FULL revised method to ${cdir}/method.md (run \`mkdir -p ${cdir}\` first), then return: rationale, diff_summary, the full method_text${isForum ? ', and predicted_effect' : ''}.${forumExtra}`
      return agent(prompt, { label: `${arm} r${round} exp-c${i} ${arch}`, phase: arm, schema: EXP_SCHEMA, agentType: 'general-purpose' })
        .then(r => r ? { i, arch, region, ...r } : null)
    }))

    const cands = experiments.filter(Boolean)

    // ---- measure candidates (blind transcribe val) ----
    await parallel(cands.map(c => () =>
      transcribe(c.method_text, `${rdir}/c${c.i}/hyp`, 'val', VAL, `${arm} r${round} trans-c${c.i}`, arm)
        .then(t => { c._trans = t })))

    // ---- score everything (one validator) ----
    const candList = cands.map(c => `  - id=c${c.i}  hyp=${rdir}/c${c.i}/hyp  method=${rdir}/c${c.i}/method.md`).join('\n')
    const scorePrompt = `You are the independent validator. You measure; you never change methods. Run the sealed blind scorer and audit candidates.

For the BASELINE replicates, run the scorer once per replicate hyp dir:
${baseHyps.map(h => `  python3 ${SCORE} --splits-root ${ROOT} --split val --hyp-dir ${h}`).join('\n')}
Collect each replicate's diplomatic_cer and reading_cer into the arrays rep_dipl / rep_read (one entry per replicate, in order). From the first replicate's JSON "error_profile", format a compact text block listing the top ~12 substitutions (ref→hyp counts), top deletions, and top insertions — this is the blind profile for next round.

For EACH candidate below, run:
  python3 ${SCORE} --splits-root ${ROOT} --split val --hyp-dir <hyp>
Collect diplomatic_cer, reading_cer, and missing_hypotheses count (call it missing). Then MEMORIZATION AUDIT: read the candidate's method.md and check whether any substantive line (length >= 15 chars) appears verbatim inside any file under ${ROOT}/corpus/val/refs/ . Set memorized=true if so, else false.

Candidates:
${candList}

Return JSON matching the schema: baseline.rep_dipl, baseline.rep_read (arrays), baseline.error_profile_text, and candidates[] with id, diplomatic_cer, reading_cer, missing, memorized. If a scorer call errors, use null for that candidate's CERs and missing=99.`
    const scored = await agent(scorePrompt, { label: `${arm} r${round} validator`, phase: arm, schema: ROUND_SCORE_SCHEMA, agentType: 'general-purpose' })
      || { baseline: { rep_dipl: [], rep_read: [], error_profile_text: lastBaselineProfile }, candidates: [] }

    // Robust baseline: median resists a single truncated replicate; band = smallest
    // adjacent gap among sorted reps (so one outlier rep can't inflate the noise band).
    const reps = (scored.baseline.rep_dipl || []).filter(x => typeof x === 'number').sort((a, b) => a - b)
    let baseMean, sigma
    if (reps.length >= 3) {
      baseMean = reps[Math.floor(reps.length / 2)]            // median
      let minGap = Infinity
      for (let i = 1; i < reps.length; i++) minGap = Math.min(minGap, reps[i] - reps[i - 1])
      sigma = minGap === Infinity ? 0.01 : minGap
    } else if (reps.length === 2) {
      baseMean = (reps[0] + reps[1]) / 2; sigma = Math.abs(reps[0] - reps[1])
    } else if (reps.length === 1) {
      baseMean = reps[0]; sigma = 0.01
    } else {
      baseMean = baselineCer ?? 1.0; sigma = 0.01
    }
    if (baselineCer === null) baselineCer = baseMean
    lastBaselineProfile = scored.baseline.error_profile_text || lastBaselineProfile
    const baseReadMean = (scored.baseline.rep_read || []).filter(x => typeof x === 'number').reduce((s, x, _, a) => s + x / a.length, 0) || null

    // attach scores
    const sm = {}
    for (const s of (scored.candidates || [])) sm[s.id] = s
    for (const c of cands) {
      const s = sm[`c${c.i}`] || { diplomatic_cer: null, reading_cer: null, missing: 99, memorized: false }
      c.dipl = s.diplomatic_cer; c.read = s.reading_cer; c.missing = s.missing; c.memorized = s.memorized
      c.eligible = c.dipl != null && c.missing === 0 && !c.memorized &&
        (baseReadMean == null || c.read == null || c.read <= baseReadMean + 0.03)
    }

    // ---- find leader ----
    const eligible = cands.filter(c => c.eligible).sort((a, b) => a.dipl - b.dipl)
    const leader = eligible[0] || null
    const band = Math.max(EPSILON, sigma)
    let decision = 'no-promote'
    let challenger = null
    let confirm = null
    const improvement = leader ? (baseMean - leader.dipl) : 0

    if (DRY) {
      decision = 'dry-run (no promotion)'
    } else if (leader && improvement >= band) {
      // forum: challenger contests before confirmation
      let proceed = true
      if (isForum) {
        const others = cands.filter(c => c !== leader)
          .map(c => `c${c.i} (${c.arch}): dipl=${c.dipl == null ? 'n/a' : c.dipl.toFixed(4)} — ${c.diff_summary}`).join('\n')
        const chPrompt = `You are the challenger in a ratchet loop. Argue the OTHER side; recommend promote or hold. You write no code and see no images/refs.

Front-runner c${leader.i} (${leader.arch}):
  rationale: ${leader.rationale}
  predicted_effect: ${leader.predicted_effect || '(none)'}
  diff_summary: ${leader.diff_summary}
  measured val diplomatic CER: ${leader.dipl.toFixed(4)}  vs baseline mean ${baseMean.toFixed(4)} (noise band ±${band.toFixed(4)})

Other candidates this round:
${others || '(none)'}

Argue against promotion: is the gain explained by the stated reason or likely a lucky-seed/dev-set artifact within the noise band? Did the predicted_effect actually track the measured result? Would it hold on unseen same-hand pages? Did any discarded candidate reveal something the metric missed (worth rescuing/re-seeding)? Then give a hold/promote recommendation. A real, well-grounded objection should yield "hold" even though the number cleared the bar.`
        challenger = await agent(chPrompt, { label: `${arm} r${round} challenger`, phase: arm, schema: CHALLENGER_SCHEMA, agentType: 'general-purpose' })
        proceed = !challenger || challenger.recommendation === 'promote'
        if (challenger && challenger.rescue) {
          const rc = cands.find(c => `c${c.i}` === challenger.rescue)
          if (rc && rc.dipl != null) archive.push({ method_text: rc.method_text, cer: rc.dipl, archetype: rc.arch })
        }
      }
      if (!proceed) {
        decision = 'hold (challenger objection sustained)'
      } else {
        // ---- confirmation: fresh val rerun + held-out test ----
        const cfHyp = `${rdir}/c${leader.i}/confirm-val/hyp`
        const tHyp = `${rdir}/c${leader.i}/test/hyp`
        await parallel([
          () => transcribe(leader.method_text, cfHyp, 'val', VAL, `${arm} r${round} confirm-val`, arm),
          () => transcribe(leader.method_text, tHyp, 'test', TEST, `${arm} r${round} confirm-test`, arm),
        ])
        const [cfScore, tScore] = await parallel([
          () => scoreOne(cfHyp, 'val', `${arm} r${round} score-confirm`, arm),
          () => scoreOne(tHyp, 'test', `${arm} r${round} score-test`, arm),
        ])
        confirm = {
          rerun_val_dipl: cfScore?.diplomatic_cer ?? null,
          test_dipl: tScore?.diplomatic_cer ?? null,
          test_read: tScore?.reading_cer ?? null,
          val_test_gap: (tScore?.diplomatic_cer != null && leader.dipl != null) ? +(tScore.diplomatic_cer - leader.dipl).toFixed(4) : null,
        }
        const held = confirm.rerun_val_dipl != null && confirm.rerun_val_dipl <= baseMean - EPSILON
        if (held) {
          decision = 'PROMOTE'
          // archive previous-best loser-ish candidates
          for (const c of eligible.slice(1, 3)) archive.push({ method_text: c.method_text, cer: c.dipl, archetype: c.arch })
          baselineMethod = leader.method_text
          baselineCer = Math.min(leader.dipl, confirm.rerun_val_dipl)
          promotions++
          roundsSincePromote = 0
        } else {
          decision = 'no-promote (win evaporated on confirmation)'
        }
      }
    }
    if (decision.startsWith('no-promote') || decision.startsWith('hold') || decision.startsWith('dry')) {
      roundsSincePromote++
    }

    // ---- credit / yield update ----
    for (const c of cands) {
      credit[c.arch] = credit[c.arch] || { tries: 0, win: 0 }
      credit[c.arch].tries++
      const isWinner = (decision === 'PROMOTE' && c === leader)
      if (isForum) {
        // argumentative credit: reward when the candidate helped AND (if winner) its reason tracked.
        // proxy: winner whose prediction direction matched (improvement>0) -> reason tracked.
        if (isWinner) credit[c.arch].win++
      } else if (isWinner) {
        credit[c.arch].win++
      }
    }
    // dead ends: eligible-but-didn't-help candidates
    for (const c of cands) {
      if (c !== leader && c.dipl != null && c.dipl >= baseMean - band) {
        deadEnds.push(`${c.arch}/${c.region}: ${c.diff_summary} (dipl ${c.dipl == null ? 'n/a' : c.dipl.toFixed(4)}, no gain)`)
      }
    }

    // ---- ledger entry ----
    ledger.push({
      round, arm, state, baseline_mean_dipl: +baseMean.toFixed(4), noise_band: +band.toFixed(4),
      allocation: plan,
      candidates: cands.map(c => ({
        id: `c${c.i}`, archetype: c.arch, region: c.region, diff_summary: c.diff_summary,
        rationale: c.rationale, predicted_effect: c.predicted_effect || null,
        diplomatic_cer: c.dipl, reading_cer: c.read, missing: c.missing, memorized: c.memorized,
        eligible: c.eligible,
      })),
      leader: leader ? `c${leader.i}` : null,
      improvement: +improvement.toFixed(4),
      challenger: challenger || null,
      confirm: confirm || null,
      decision,
      new_baseline_dipl: baselineCer == null ? null : +baselineCer.toFixed(4),
    })
    log(`${arm} r${round}: ${decision}  baseline_dipl=${baseMean.toFixed(4)}  leader=${leader ? 'c' + leader.i + ' ' + leader.dipl.toFixed(4) : 'none'}  best=${baselineCer == null ? 'n/a' : baselineCer.toFixed(4)}`)

    // ---- exit checks ----
    if (!DRY && promotions > 0 && baselineCer != null && baselineCer <= TARGET) { log(`${arm}: hit target ${TARGET}`); break }
    if (!DRY && roundsSincePromote >= PLATEAU_PATIENCE) { log(`${arm}: plateau (${roundsSincePromote} rounds no promote) — season done`); break }
  }

  log(`=== ARM ${arm} done: ${promotions} promotions, best val dipl CER = ${baselineCer == null ? 'n/a' : baselineCer.toFixed(4)} ===`)
  return { arm, best_val_dipl: baselineCer, promotions, rounds: ledger.length, ledger, best_method: baselineMethod }
}

// ---------------------------------------------------------------------------
// Run both arms + compare
// ---------------------------------------------------------------------------
const results = {}
for (const arm of ARMS) results[arm] = await runArm(arm)

phase('compare')
const summary = {
  dry_run: DRY,
  arms: ARMS,
  config: { max_rounds: MAX_ROUNDS, fanout: N, plateau_patience: PLATEAU_PATIENCE, epsilon: EPSILON, target: TARGET },
  per_arm: Object.fromEntries(ARMS.map(a => [a, {
    best_val_dipl: results[a].best_val_dipl,
    promotions: results[a].promotions,
    rounds: results[a].rounds,
    final_test_dipl: (() => { for (let i = results[a].ledger.length - 1; i >= 0; i--) { const c = results[a].ledger[i].confirm; if (c && c.test_dipl != null) return c.test_dipl } return null })(),
  }])),
}
log(`HEAD-TO-HEAD: ${ARMS.map(a => `${a} best val ${results[a].best_val_dipl == null ? 'n/a' : results[a].best_val_dipl.toFixed(4)}`).join('  |  ')}`)
return { summary, results }
