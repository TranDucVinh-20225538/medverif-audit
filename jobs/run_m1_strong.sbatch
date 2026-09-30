#!/bin/bash
#SBATCH --job-name=m1_strong
#SBATCH --partition=defq
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/m1_strong_%j.out

set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
export PYTHONPATH="${ROOT}/src:${ROOT}/analysis:${ROOT}/scripts"
PY="${CONDA_PREFIX}/bin/python3"
echo "m1_strong start $(date -Is) job=${SLURM_JOB_ID}"
"${PY}" scripts/m1_strong_score_missing.py
"${PY}" scripts/m1_strong_run.py
echo "m1_strong done $(date -Is)"
