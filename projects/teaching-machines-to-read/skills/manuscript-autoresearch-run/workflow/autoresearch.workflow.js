export const meta = {
  name: 'autoresearch-run',
  description: 'Drive one autoresearch CER-optimization run (ratchet loop + final test eval)',
  phases: [{ title: 'Optimize' }, { title: 'Final test eval' }],
}

// Prompts are passed as FILE PATHS (args stays tiny regardless of prompt size).
// Each agent reads and follows its instruction file; the workflow injects only the
// small per-iteration values, leaving the static placeholders pre-filled by the runner.
const A = typeof args === 'string' ? JSON.parse(args) : args
const followFile = (p) =>
  `Read the instructions in the file at ${p} and follow them exactly. Do only what that file says.`

let best = Infinity
let bestIter = 0
let noImprove = 0
let lastProfile = '{}'   // blind error profile JSON handed to the next propose agent

phase('Optimize')
let iter = 0
for (iter = 1; iter <= A.max_iters; iter++) {
  // 1. PROPOSE — fresh blind agent edits method.md (one call per iteration)
  const proposed = await agent(
    followFile(A.prompts.propose) +
    ` Where that file shows the token {{PROFILE_JSON}}, use this blind error profile JSON instead: ${lastProfile}`,
    { label: `propose:${iter}`, phase: 'Optimize', schema: {
      type: 'object', required: ['change_description'],
      properties: { change_description: { type: 'string' } } } }) || { change_description: '(no change)' }

  // 2. TRANSCRIBE — fresh agent, val materials (refs present only in faithful arm)
  await agent(followFile(A.prompts.transcribe), { label: `transcribe:${iter}`, phase: 'Optimize',
    schema: { type: 'object', properties: { pages_done: { type: 'number' } } } })

  // 3. SCORE — fresh blind scorer; returns score.py JSON only
  const score = await agent(followFile(A.prompts.score), { label: `score:${iter}`, phase: 'Optimize',
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

  await agent(
    followFile(A.prompts.record) +
    ` Substitute in that file: {{ITER}}=${iter}, {{DECISION}}=${decision},` +
    ` {{CHANGE_DESCRIPTION}}=${JSON.stringify(proposed.change_description)},` +
    ` {{DIPL_CER}}=${score.diplomatic_cer}, {{READ_CER}}=${score.reading_cer}.`,
    { label: `record:${iter}`, phase: 'Optimize', schema: {
      type: 'object', properties: { recorded: { type: 'boolean' }, kept: { type: 'boolean' } } } })

  log(`iter ${iter}: dipl ${score.diplomatic_cer.toFixed(4)} (best ${best.toFixed(4)} @ ${bestIter}), ${decision}, noImprove ${noImprove}`)
  if (noImprove >= A.patience) { log(`stopping: ${A.patience} non-improving iterations`); break }
}

// FINAL — transcribe+score the locked TEST split once.
// prompts.transcribe_test / prompts.score_test are pre-filled by the runner for the test split.
phase('Final test eval')
await agent(followFile(A.prompts.transcribe_test), { label: 'transcribe:test', phase: 'Final test eval',
  schema: { type: 'object', properties: { pages_done: { type: 'number' } } } })
const testRes = await agent(followFile(A.prompts.score_test), { label: 'score:test', phase: 'Final test eval',
  schema: { type: 'object', required: ['diplomatic_cer', 'reading_cer'],
    properties: { diplomatic_cer: { type: 'number' }, reading_cer: { type: 'number' } } } }) || {}

return {
  iterations: iter - 1 < 0 ? 0 : Math.min(iter, A.max_iters),
  best_val_diplomatic_cer: best === Infinity ? null : best,
  best_iter: bestIter,
  test_diplomatic_cer: testRes.diplomatic_cer ?? null,
  test_reading_cer: testRes.reading_cer ?? null,
}
