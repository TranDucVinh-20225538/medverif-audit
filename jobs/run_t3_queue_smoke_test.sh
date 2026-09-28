#!/usr/bin/env bash
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_OR_MAX_INFLIGHT=1
# Match T2 full / fixed T3 T2 job (override env DeepInfra for V1).
export MEDVERIF_V1B_PROVIDER="${MEDVERIF_V1B_PROVIDER:-OpenAI}"
export MEDVERIF_V5_PROVIDER="${MEDVERIF_V5_PROVIDER:-Anthropic}"
exec python3 scripts/t3_queue_smoke_test.py
