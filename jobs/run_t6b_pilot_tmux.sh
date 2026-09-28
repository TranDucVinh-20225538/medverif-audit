#!/usr/bin/env bash
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
SESSION=t6b_pilot
if tmux has-session -t "${SESSION}" 2>/dev/null; then
  echo "tmux ${SESSION} already running"
  exit 0
fi
tmux new-session -d -s "${SESSION}" \
  "bash ${ROOT}/jobs/lib/openrouter_retry.sh ${ROOT}/jobs/run_t6b_pilot_openrouter.sh"
echo "started tmux ${SESSION}"
