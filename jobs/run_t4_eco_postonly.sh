#!/usr/bin/env bash
# T4 post-answer only (no openrouter_retry): classify → QC → instances → OR verifiers.
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

LOG="${ROOT}/jobs/logs/t4_eco_postonly_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "t4 eco postonly start $(date -Is)"
bash "${ROOT}/jobs/lib/t4_eco_postanswer.sh"
echo "t4 eco postonly done $(date -Is)"
