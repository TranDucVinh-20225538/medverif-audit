#!/usr/bin/env bash
# T4 ecological: 3 answerer LLMs + verifier scoring, budget ≤$5.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock t4_eco

cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_API_LEDGER=1
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-2}"
export MEDVERIF_T4_BUDGET_USD="${MEDVERIF_T4_BUDGET_USD:-5}"
export MEDVERIF_T4_MAX_TASKS="${MEDVERIF_T4_MAX_TASKS:-0}"

LOG="${ROOT}/jobs/logs/t4_eco_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "t4 eco start $(date -Is) budget=${MEDVERIF_T4_BUDGET_USD}"

python3 scripts/openrouter_budget.py || exit 2
python3 scripts/t4_build_eco_tasks.py
python3 scripts/t4_eco_answer.py
python3 scripts/t4_eco_classify.py --in data/t4/eco_answers.jsonl --out data/t4/eco_classified.jsonl
python3 scripts/t4_eco_qc.py
python3 scripts/t4_build_eco_instances.py

INST="${ROOT}/data/t4/instances_eco_verify.jsonl"
RAW="${ROOT}/results/raw/t4_eco"
mkdir -p "${RAW}"

# Cheap verifiers first; stop when t4 budget exhausted.
for v in v1c_medscore v6_ragas_nli v1b_medscore v5_ragas_nli v4_ragas_nli v1_medscore; do
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
  echo "scoring ${v} ..."
  python3 src/score_jsonl.py --verifier "${v}" --instances "${INST}" --out "${RAW}/${v}.jsonl" || true
done

python3 scripts/openrouter_account_credits.py
echo "t4 eco done $(date -Is)"
