#!/usr/bin/env bash
# V4 provenance: re-score all packs → *.llama.jsonl (budget ≤ $3).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_M1=0
export MEDVERIF_OR_MIN_CREDIT=1.0
export MEDVERIF_API_LEDGER=1

LOG="${ROOT}/jobs/logs/v4_llama_rescore_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "v4 llama rescore start $(date -Is)"

python3 scripts/v4_llama_rescore.py --prepare-only
python3 scripts/v4_llama_rescore.py --budget-usd 3.0

set +e
source ~/kkk/openrouter.env 2>/dev/null || true
python3 scripts/openrouter_generation_recovery.py
set -e
python3 scripts/v4_legacy_agreement_report.py
python3 scripts/rebuild_v4_tables.py
echo "v4 llama rescore done $(date -Is)"
