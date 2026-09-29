#!/usr/bin/env bash
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
SESSION=t4_eco
if tmux has-session -t "${SESSION}" 2>/dev/null; then
  echo "tmux ${SESSION} already running"
  exit 0
fi
if [[ -s "${ROOT}/data/t4/eco_answers.jsonl" ]]; then
  JOB="${ROOT}/jobs/run_t4_eco_postonly.sh"
else
  JOB="${ROOT}/jobs/run_t4_eco_answer_only.sh"
fi
tmux new-session -d -s "${SESSION}" "bash ${JOB}"
echo "started tmux ${SESSION}"
