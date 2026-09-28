#!/usr/bin/env bash
# Wait for T2 full V5 completion, then score T3 INV families (V1b+V5 + T6-B zoo).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
V5="${ROOT}/results/raw/t2_full/v5_ragas_nli.jsonl"
TARGET=533
echo "t3 score queue: waiting for V5 ${TARGET} lines $(date -Is)"
while true; do
  n=0
  [[ -f "${V5}" ]] && n=$(wc -l < "${V5}")
  if [[ "${n}" -ge "${TARGET}" ]]; then
    echo "T2 V5 complete (${n}); starting T3 scoring $(date -Is)"
    break
  fi
  sleep 60
done
bash "${ROOT}/jobs/run_t3_t2_score_openrouter.sh"
bash "${ROOT}/jobs/run_t3_t6b_score_openrouter.sh"
echo "t3 scoring queue done $(date -Is)"
