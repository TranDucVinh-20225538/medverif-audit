#!/usr/bin/env bash
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
SESSION=t3_score_queue
if tmux has-session -t "${SESSION}" 2>/dev/null; then
  echo "tmux ${SESSION} already running"
  exit 0
fi
tmux new-session -d -s "${SESSION}" "bash ${ROOT}/jobs/run_t3_score_when_t2_done.sh"
echo "started tmux ${SESSION}"
