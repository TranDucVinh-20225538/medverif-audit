#!/usr/bin/env bash
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
SESSION=m1_analysis
if tmux has-session -t "${SESSION}" 2>/dev/null; then
  echo "tmux ${SESSION} already running"
  exit 0
fi
tmux new-session -d -s "${SESSION}" "bash ${ROOT}/jobs/run_m1_analysis.sh"
echo "started tmux ${SESSION}"
