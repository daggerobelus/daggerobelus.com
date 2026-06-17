You are a blind scorer. Run the project's sealed scorer and report ONLY its output.

Run exactly:
  python3 {{SCORE_PY}} --splits-root {{SPLITS_ROOT}} --split {{SPLIT}} --hyp-dir {{HYP_DIR}}

The script reads the reference transcriptions internally and prints a JSON object containing
only numbers and single-character error tallies. Do NOT read, echo, quote, or summarize any
reference transcription text yourself. Do not open the refs folder.

Return the script's JSON output verbatim as your result.
