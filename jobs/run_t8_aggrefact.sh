#!/usr/bin/env bash
# T8 audit only (HF cache + quantity stats). Synthetic INV/E1 scoring removed — deprecated.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock t8_aggrefact

cd "${ROOT}"
export PYTHONPATH="${ROOT}/src"

LOG="${ROOT}/jobs/logs/t8_aggrefact_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "t8 audit-only start $(date -Is)"

if [[ ! -f "${ROOT}/data/t8/aggrefact/dev.jsonl" ]]; then
  set -a && source ~/kkk/openrouter.env && set +a
  python3 scripts/t8_download_aggrefact.py
fi

python3 scripts/t8_aggrefact_analysis.py --splits dev,test
echo "t8 audit-only done — synthetic sample deprecated; T8b: jobs/run_t8b_aggrefact.sh (after mismatch QC)"
