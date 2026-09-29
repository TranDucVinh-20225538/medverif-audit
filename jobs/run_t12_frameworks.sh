#!/usr/bin/env bash
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src:${ROOT}"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_OR_MIN_CREDIT=2
export MEDVERIF_API_LEDGER=1
LOG="${ROOT}/jobs/logs/t12_frameworks_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "t12 start $(date -Is)"
python3 scripts/t12_framework_eval.py --pilot
python3 scripts/t12_framework_eval.py --full
echo "t12 done $(date -Is)"
