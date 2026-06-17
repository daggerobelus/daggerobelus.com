You record one iteration's outcome into the run's ledger.

Inputs:
- run dir: {{RUN_DIR}}
- iteration number: {{ITER}}
- decision: {{DECISION}}   (either "keep" or "revert")
- change description: {{CHANGE_DESCRIPTION}}
- val diplomatic CER: {{DIPL_CER}}
- val reading CER: {{READ_CER}}
- ledger module: {{LEDGER_PY}}  (importable; run python3 from {{SCRIPTS_DIR}})

Do BOTH steps with one `python3` invocation importing the ledger module:
1. If decision is "keep": snapshot the current method —
   snapshot_path = ledger.snapshot_method({{RUN_DIR}}, {{ITER}}, "{{RUN_DIR}}/method.md")
   Then append a row with kept=True and that snapshot_path.
   If decision is "revert": copy the best method back over method.md using
   shutil.copyfile(ledger.best_method_path({{RUN_DIR}}), "{{RUN_DIR}}/method.md")
   (only if best_method_path is not None), then append a row with kept=False and snapshot_path="".
2. Append via ledger.append_result({{RUN_DIR}}, {{ITER}}, "{{CHANGE_DESCRIPTION}}",
   {{DIPL_CER}}, {{READ_CER}}, <kept bool>, <snapshot_path or "">).

Return JSON: {"recorded": true, "kept": <bool>, "snapshot_path": "<path or empty>"}
