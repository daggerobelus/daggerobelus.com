export const meta = {
  name: 'autoresearch-run',
  description: 'Drive one autoresearch CER-optimization run (ratchet loop + final test eval)',
  phases: [{ title: 'Optimize' }, { title: 'Final test eval' }],
}

// Fill the per-iteration placeholders the runner left in the prompt text.
function fill(t, map) {
  let out = t
  for (const k of Object.keys(map)) out = out.split('{{' + k + '}}').join(String(map[k]))
  return out
}

const A = args
let best = Infinity
let bestIter = 0
let noImprove = 0
let lastProfile = '{}'   // blind error profile JSON handed to the next propose agent

phase('Optimize')
let iter = 0
for (iter = 1; iter <= A.max_iters; iter++) {
  // 1. PROPOSE — fresh blind agent edits method.md (one call per iteration)
  const proposed = await agent(
    fill(A.prompts.propose, { RESULTS_PATH: A.run_dir + '/results.tsv', PROFILE_JSON: lastProfile }),
    { label: `propose:${iter}`, phase: 'Optimize', schema: {
      type: 'object', required: ['change_description'],
      properties: { change_description: { type: 'string' } } } }) || { change_description: '(no change)' }

  // 2. TRANSCRIBE — fresh agent, val materials (refs present only in faithful arm)
  await agent(A.prompts.transcribe, { label: `transcribe:${iter}`, phase: 'Optimize',
    schema: { type: 'object', properties: { pages_done: { type: 'number' } } } })

  // 3. SCORE — fresh blind scorer; returns score.py JSON only
  const score = await agent(A.prompts.score, { label: `score:${iter}`, phase: 'Optimize',
    schema: { type: 'object', required: ['diplomatic_cer', 'reading_cer'],
      properties: { diplomatic_cer: { type: 'number' }, reading_cer: { type: 'number' },
        error_profile: { type: 'object' } } } })
  if (!score) { log(`iter ${iter}: scorer failed; reverting`); continue }
  lastProfile = JSON.stringify(score.error_profile || {})

  // 4. RATCHET — deterministic
  const improved = score.diplomatic_cer < best
  const decision = improved ? 'keep' : 'revert'
  if (improved) { best = score.diplomatic_cer; bestIter = iter; noImprove = 0 }
  else { noImprove++ }

  await agent(fill(A.prompts.record, {
    ITER: iter, DECISION: decision, CHANGE_DESCRIPTION: proposed.change_description,
    DIPL_CER: score.diplomatic_cer, READ_CER: score.reading_cer,
  }), { label: `record:${iter}`, phase: 'Optimize', schema: {
    type: 'object', properties: { recorded: { type: 'boolean' }, kept: { type: 'boolean' } } } })

  log(`iter ${iter}: dipl ${score.diplomatic_cer.toFixed(4)} (best ${best.toFixed(4)} @ ${bestIter}), ${decision}, noImprove ${noImprove}`)
  if (noImprove >= A.patience) { log(`stopping: ${A.patience} non-improving iterations`); break }
}

// FINAL — restore best method, transcribe+score the locked TEST split once
phase('Final test eval')
const testHyp = A.run_dir + '/final-test-eval'
const testTranscribe = A.prompts.transcribe
  .split(A.materials_dir).join(A.run_dir + '/test-materials')
  .split(A.hyp_dir).join(testHyp)
const testScore = A.prompts.score.split('--split ' + 'val').join('--split ' + 'test').split(A.hyp_dir).join(testHyp)

await agent(testTranscribe, { label: 'transcribe:test', phase: 'Final test eval',
  schema: { type: 'object', properties: { pages_done: { type: 'number' } } } })
const testRes = await agent(testScore, { label: 'score:test', phase: 'Final test eval',
  schema: { type: 'object', required: ['diplomatic_cer', 'reading_cer'],
    properties: { diplomatic_cer: { type: 'number' }, reading_cer: { type: 'number' } } } }) || {}

return {
  iterations: iter - 1 < 0 ? 0 : Math.min(iter, A.max_iters),
  best_val_diplomatic_cer: best === Infinity ? null : best,
  best_iter: bestIter,
  test_diplomatic_cer: testRes.diplomatic_cer ?? null,
  test_reading_cer: testRes.reading_cer ?? null,
}
