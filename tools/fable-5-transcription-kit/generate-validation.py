#!/usr/bin/env python3
"""Generate validation.json for the Fable 5 transcription kit.

Extracts the rung 1 (editorial contract) cells from the run 3-ladder
results — the condition this kit ships. Data only; no prose fields.
"""
import json
from pathlib import Path

KIT_DIR = Path(__file__).resolve().parent
REPO = KIT_DIR.parents[1]
SRC = (
    REPO
    / "projects/teaching-machines-to-read/public/data/runs/run-3-fable-ladder-results.json"
)

data = json.loads(SRC.read_text())
run = data["run"]
rung1 = data["rungs"]["rung1_rules"]

results = {}
for ms, agents in rung1["cells"].items():
    strict = [a["strict"] for a in agents]
    lenient = [a["lenient"] for a in agents]
    results[ms] = {
        "agents": agents,
        "strict_mean": round(sum(strict) / len(strict), 2),
        "lenient_mean": round(sum(lenient) / len(lenient), 2),
    }

out = {
    "kit": "fable-5-transcription-kit",
    "kit_version": "1.0",
    "model": run["model"],
    "method": "rung-1-editorial-contract",
    "source_run": {"id": run["id"], "name": run["name"], "dates": run["dates"]},
    "scoring": run["scoring"],
    "n_agents_per_manuscript": rung1["n_per_ms"],
    "mean_cost_per_page_usd_cached": rung1["mean_cost_per_page_usd_cached"],
    "results": results,
}

out_path = KIT_DIR / "validation.json"
out_path.write_text(json.dumps(out, indent=1) + "\n")
print(f"Wrote {out_path}")
