#!/usr/bin/env bash
# Poll for T3 INV-family instances; run v1b+v5 when non-empty (once per new row batch).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
LAST_N=0
while true; do
  python3 scripts/t3_build_instances.py >/dev/null
  INST="${ROOT}/data/t3/instances_inv_families.jsonl"
  N=0
  [[ -f "${INST}" ]] && N=$(wc -l < "${INST}")
  if [[ "${N}" -gt 0 && "${N}" -ne "${LAST_N}" ]]; then
    echo "$(date -Is) T3 families n=${N} (was ${LAST_N}) → scoring"
    bash "${ROOT}/jobs/lib/openrouter_retry.sh" "${ROOT}/jobs/run_t3_t2_score_openrouter.sh" || true
    LAST_N="${N}"
  fi
  sleep 300
done
