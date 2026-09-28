#!/usr/bin/env bash
# After eco_answers.jsonl is complete: classify → QC sample → instances → verifier scores.
set -euo pipefail
ROOT="${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}"
cd "${ROOT}"
export PYTHONPATH="${ROOT}/src"

python3 - <<'PY'
import json
from pathlib import Path
ROOT = Path("/data2/hpcshared/medverif-audit")
tasks = sum(1 for line in (ROOT / "data/t4/eco_tasks.jsonl").open() if line.strip())
models = len(json.loads((ROOT / "notes/t4_models.json").read_text())["answerers"])
need = tasks * models
n = sum(1 for line in (ROOT / "data/t4/eco_answers.jsonl").open() if line.strip())
if n < need:
    raise SystemExit(f"t4 postanswer: answers {n}/{need} — not ready")
print(f"t4 postanswer: answers {n}/{need} OK")
PY

python3 scripts/t4_eco_classify.py --in data/t4/eco_answers.jsonl --out data/t4/eco_classified.jsonl
python3 scripts/t4_eco_qc.py
python3 scripts/t4_build_eco_instances.py

INST="${ROOT}/data/t4/eco_instances.jsonl"
if [[ ! -f "${INST}" ]]; then
  INST="${ROOT}/data/t4/instances_eco_verify.jsonl"
fi
RAW="${ROOT}/results/raw/t4_eco"
mkdir -p "${RAW}"

export MEDVERIF_V1B_OPENROUTER_MODEL="${MEDVERIF_V1B_OPENROUTER_MODEL:-openai/gpt-4o}"
export MEDVERIF_V1B_PROVIDER="${MEDVERIF_V1B_PROVIDER:-OpenAI}"

# V2/V3 encoders run on node30 only (not HPC login nodes).

OR_VERIFIERS=(
  v1c_medscore
  v6_ragas_nli
  v1b_medscore
  v5_ragas_nli
  v4_ragas_nli
  v1_medscore
)

for v in "${OR_VERIFIERS[@]}"; do
  spent=$(python3 - <<'PY'
import json
from pathlib import Path
p=Path("/data2/hpcshared/medverif-audit/data/t4/eco_answers.jsonl")
s=0.0
if p.is_file():
  for line in p.open():
    if line.strip(): s+=float(json.loads(line).get("api_cost_usd") or 0)
for f in Path("/data2/hpcshared/medverif-audit/results/raw/t4_eco").glob("*.jsonl"):
  for line in f.open():
    if line.strip(): s+=float(json.loads(line).get("api_cost_usd") or 0)
print(s)
PY
)
  python3 - <<PY || exit 0
import os
spent=float("${spent}")
budget=float(os.environ.get("MEDVERIF_T4_BUDGET_USD","5"))
if spent >= budget:
    raise SystemExit(0)
PY
  python3 scripts/openrouter_budget.py || exit 2
  echo "t4 scoring ${v} ..."
  python3 src/score_jsonl.py --verifier "${v}" --instances "${INST}" --out "${RAW}/${v}.jsonl" || true
done

python3 scripts/openrouter_account_credits.py

python3 - <<'PY'
import json
from pathlib import Path
ROOT = Path("/data2/hpcshared/medverif-audit")
manifest = {
    "n_eco_instances": sum(1 for _ in (ROOT / "data/t4/eco_instances.jsonl").open()),
    "qc_sample": "qc/eco_sample.csv",
    "node30_encoders": "run t4_eco_score_encoders.py on node30 only",
    "hpc_verifiers": "results/raw/t4_eco/*.jsonl (OpenRouter)",
}
(ROOT / "notes/t4_eco_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
PY

if [[ "${MEDVERIF_T4_GIT_PUSH:-1}" == "1" ]]; then
  bash "${ROOT}/scripts/t4_eco_git_push.sh" || true
fi
