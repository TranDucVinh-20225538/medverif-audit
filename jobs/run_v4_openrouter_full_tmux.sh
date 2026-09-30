#!/usr/bin/env bash
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
exec bash "${ROOT}/jobs/lib/openrouter_retry.sh" "${ROOT}/jobs/run_v4_openrouter_full.sh"
