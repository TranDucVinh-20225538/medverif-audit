#!/usr/bin/env bash
# Re-score M1-affected rows only (V1+V4 OR → raw_m1).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock t1_m1_or

cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_M1=0
export MEDVERIF_API_LEDGER=1
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-3}"

INST="${ROOT}/data/v3/instances_m1_rescore_affected.jsonl"
OUT="${ROOT}/results/raw_m1"
LOG="${ROOT}/jobs/logs/t1_m1_rescore_affected_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "m1 affected rescore start $(date -Is) n=$(wc -l < "${INST}")"

python3 scripts/build_m1_rescore_affected.py
for v in v1_medscore v4_ragas_nli; do
  python3 scripts/openrouter_budget.py || exit 2
  python3 src/score_jsonl.py --verifier "${v}" --instances "${INST}" --out "${OUT}/${v}.jsonl"
done
python3 scripts/m1_before_after_report.py
echo "m1 affected rescore done $(date -Is)"
