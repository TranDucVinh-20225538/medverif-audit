#!/usr/bin/env bash
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
SESSION=v1_full
if tmux has-session -t "${SESSION}" 2>/dev/null; then
  echo "tmux session ${SESSION} already running"
  exit 0
fi
tmux new-session -d -s "${SESSION}" "bash ${ROOT}/jobs/lib/openrouter_retry.sh ${ROOT}/jobs/run_v1_openrouter_full.sh"
echo "started tmux ${SESSION}"
