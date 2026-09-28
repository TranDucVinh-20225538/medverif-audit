#!/usr/bin/env bash
# T4 resume: finish all answerers (148×3), then classify → qc/eco_sample.csv → score all verifiers.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock t4_eco

cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_API_LEDGER=1
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-3}"
export MEDVERIF_T4_BUDGET_USD="${MEDVERIF_T4_BUDGET_USD:-5}"

LOG="${ROOT}/jobs/logs/t4_eco_resume_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "t4 eco resume start $(date -Is) inflight=${MEDVERIF_OR_MAX_INFLIGHT} budget=${MEDVERIF_T4_BUDGET_USD}"

python3 scripts/openrouter_budget.py || exit 2
if [[ ! -f data/t4/eco_tasks.jsonl ]]; then
  python3 scripts/t4_build_eco_tasks.py
fi

python3 scripts/t4_eco_answer.py

bash "${ROOT}/jobs/lib/t4_eco_postanswer.sh"

echo "t4 eco resume done $(date -Is)"
