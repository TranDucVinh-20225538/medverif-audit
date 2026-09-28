#!/usr/bin/env bash
# Re-run a job script until it exits 0 (for resumable OpenRouter score_jsonl runs).
set -euo pipefail
if (($# < 1)); then
  echo "usage: openrouter_retry.sh /path/to/job.sh [args...]" >&2
  exit 2
fi
JOB=$1
shift
ROOT=${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}
MAX=${MEDVERIF_OPENROUTER_RETRY_MAX:-9999}
SLEEP=${MEDVERIF_OPENROUTER_RETRY_SLEEP_SEC:-90}
n=0
while ((n < MAX)); do
  n=$((n + 1))
  echo "openrouter_retry attempt=${n} job=${JOB} $(date -Is)"
  if bash "${JOB}" "$@"; then
    echo "openrouter_retry success attempt=${n} $(date -Is)"
    exit 0
  fi
  echo "openrouter_retry failed attempt=${n}; sleep ${SLEEP}s $(date -Is)"
  sleep "${SLEEP}"
done
echo "openrouter_retry exhausted max=${MAX}" >&2
exit 1
