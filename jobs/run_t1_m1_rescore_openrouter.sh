#!/usr/bin/env bash
# T1 priority: re-score V1 + V4 on cpu_early with MEDVERIF_M1=1 → results/raw_m1/
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock t1_m1_or

cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_M1=1
export MEDVERIF_GPU_GLOBAL_SCORE_LOCK=0
export MEDVERIF_API_LEDGER=1
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-2}"
export MEDVERIF_OR_MIN_CREDIT="${MEDVERIF_OR_MIN_CREDIT:-2}"

INST="${ROOT}/data/v3/instances_cpu_early.jsonl"
OUT="${ROOT}/results/raw_m1"
mkdir -p "${OUT}"
LOG="${ROOT}/jobs/logs/t1_m1_or_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "t1 m1 rescore start $(date -Is) MEDVERIF_M1=1"

for v in v1_medscore v4_ragas_nli; do
  python3 scripts/openrouter_budget.py || exit 2
  python3 src/score_jsonl.py --verifier "${v}" --instances "${INST}" --out "${OUT}/${v}.jsonl"
done
python3 scripts/t1_cost_validity_report.py
echo "t1 m1 rescore done $(date -Is)"
