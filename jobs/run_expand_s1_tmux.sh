#!/usr/bin/env bash
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
SESSION=expand_s1
if tmux has-session -t "${SESSION}" 2>/dev/null; then
  echo "tmux session ${SESSION} already running"
  exit 0
fi
tmux new-session -d -s "${SESSION}" \
  "bash ${ROOT}/jobs/lib/openrouter_retry.sh ${ROOT}/jobs/run_expand_stage1_openrouter.sh"
echo "started tmux ${SESSION}"
