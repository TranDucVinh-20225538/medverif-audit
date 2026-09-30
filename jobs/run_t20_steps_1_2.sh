#!/usr/bin/env bash
# T20 steps 1–2: drug list + openFDA label cache (CPU/API, no OR scoring).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock t20_build

cd "${ROOT}"
export PYTHONPATH="${ROOT}/src"
LOG="${ROOT}/jobs/logs/t20_steps12_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "t20 steps 1-2 start $(date -Is)"
python3 scripts/t20_build_drug_list.py
python3 scripts/t20_fetch_openfda_labels.py
echo "t20 steps 1-2 done $(date -Is)"
