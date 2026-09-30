#!/usr/bin/env bash
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
if squeue -u "${USER}" -h -o "%j" 2>/dev/null | rg -q "^t17-or-score$"; then
  echo "t17-or-score already in queue"
  exit 0
fi
mkdir -p "${ROOT}/jobs/locks"
exec 9>"${ROOT}/jobs/locks/t17_hpc_score.lock"
if ! flock -n 9; then
  echo "t17_hpc_score lock held; already running"
  exit 0
fi
flock -u 9
bash "${ROOT}/scripts/t17_prefetch_tokenizers.sh"
nohup bash "${ROOT}/jobs/run_t17_score_hpc.sh" >/tmp/t17_hpc_score.log 2>&1 &
echo "t17 scoring pid=$! log=/tmp/t17_hpc_score.log and jobs/logs/t17_hpc_*.log"
