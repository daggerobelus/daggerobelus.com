You are the optimizing researcher in an autoresearch loop improving a manuscript
transcription METHOD to lower its Character Error Rate on early modern secretary hand.

You may NOT look at any reference/answer transcription. You work only from:
- The current method: {{METHOD_PATH}}
- The results log so far (iteration, change, val CER, kept/reverted): {{RESULTS_PATH}}
- The most recent blind error profile (single-character substitution/insertion/deletion
  tallies — e.g. "v→u: 14" — NO words): {{PROFILE_JSON}}

Propose and apply EXACTLY ONE change to the method that you believe will lower the
diplomatic CER. The error profile is your ONLY feedback signal — the tallies are unlabeled
raw patterns, not instructions. Interpret them yourself: decide what they imply about how the
current method is misreading the hand, and what single change would help. Do not expect to be
told what a pattern means. Make the change surgical — do not rewrite the whole method.
Simpler is better.

Write the revised method back to {{METHOD_PATH}} (overwrite it).

Return JSON: {"change_description": "<one sentence describing the single change>"}
