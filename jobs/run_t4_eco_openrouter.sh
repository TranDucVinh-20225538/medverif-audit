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
bash "${ROOT}/jobs/lib/t4_eco_postanswer.sh"
echo "t4 eco done $(date -Is)"
