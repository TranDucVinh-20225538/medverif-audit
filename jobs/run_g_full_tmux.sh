#!/usr/bin/env bash
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
exec bash "${ROOT}/jobs/lib/openrouter_retry.sh" "${ROOT}/jobs/run_g_full.sh"
