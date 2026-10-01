#!/usr/bin/env bash
# E2 PASS for all 9 LLM judges; scores missing E2 rows (hard cap $3). Login node; CPU only.
# Usage: bash jobs/run_e2_remaining_judges.sh [--dry-run] [--budget-usd 3]
set -euo pipefail
ROOT="${MEDVERIF_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "${ROOT}"
if [[ -f .env ]]; then set -a && source .env && set +a; elif [[ -f ~/kkk/openrouter.env ]]; then set -a && source ~/kkk/openrouter.env && set +a; fi
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_API_LEDGER=1
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-2}"
PY="${MEDVERIF_PYTHON:-python3}"
mkdir -p jobs/logs
LOG="jobs/logs/e2_remaining_judges_$(date +%Y%m%dT%H%M).log"
"${PY}" scripts/e2_remaining_judges.py "$@" 2>&1 | tee -a "${LOG}"
exit "${PIPESTATUS[0]}"
