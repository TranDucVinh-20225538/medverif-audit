#!/usr/bin/env bash
# T15 eval only (checkpoint from notes/t15_config.json); no retrain.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
export PYTHONPATH="${ROOT}/src"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate cpuverif
LOG="${ROOT}/jobs/logs/t15_eval_only_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "T15 eval-only start $(date -Is)"
python3 -u scripts/t15_eval.py
echo "T15 eval-only done $(date -Is)"
