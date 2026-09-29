#!/usr/bin/env bash
# T7 M1: V1 + V4 on M1-normalized pack (OpenRouter).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock t7_m1_hpc

cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_M1=0
export MEDVERIF_API_LEDGER=1

python3 scripts/build_t7_m1_pending.py
INST="${ROOT}/data/t7/instances_e1_unit_m1_pending.jsonl"
RAW="${ROOT}/results/raw_m1/t7"
mkdir -p "${RAW}"
LOG="${ROOT}/jobs/logs/t7_m1_hpc_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "t7 m1 hpc start $(date -Is)"

for v in v1_medscore v4_ragas_nli; do
  python3 scripts/openrouter_budget.py || exit 2
  python3 src/score_jsonl.py --verifier "${v}" --instances "${INST}" --out "${RAW}/${v}.jsonl"
done

python3 scripts/t7_m1_mcnemar_report.py
echo "t7 m1 hpc done $(date -Is)"
