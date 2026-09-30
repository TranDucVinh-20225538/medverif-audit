#!/usr/bin/env bash
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
SESSION=t2_pilot
if tmux has-session -t "${SESSION}" 2>/dev/null; then
  echo "tmux session ${SESSION} already running"
  exit 0
fi
tmux new-session -d -s "${SESSION}" "bash ${ROOT}/jobs/lib/openrouter_retry.sh ${ROOT}/jobs/run_t2_pilot_openrouter.sh"
echo "started tmux ${SESSION}"
