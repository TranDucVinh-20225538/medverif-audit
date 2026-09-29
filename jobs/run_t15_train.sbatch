#!/bin/bash
#SBATCH --job-name=t15-train
#SBATCH --partition=defq
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --cpus-per-task=4
#SBATCH --time=06:00:00
#SBATCH --exclude=node001,node004
#SBATCH --signal=B:TERM@120
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/t15-%x-%j.out

set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
source "${ROOT}/jobs/lib/flock.sh"
source "${ROOT}/jobs/lib/gpu_graceful.sh"
source "${ROOT}/jobs/lib/gpu_node_precheck.sh"

medverif_acquire_lock t15_train

export MEDVERIF_REQ_MEM_GB=64
medverif_gpu_node_precheck

export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export HF_HUB_DISABLE_TELEMETRY=1
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
export PYTHONPATH="${ROOT}/src"

source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
source "${ROOT}/jobs/lib/job_elapsed.sh"
medverif_job_elapsed_begin --pack "data/t15/train.jsonl" --verifier "t15_train" --machine "hpc"

gpu_graceful_init
echo "T15 train start $(date -Is)"
gpu_run python3 -u scripts/t15_train.py
echo "T15 eval start $(date -Is)"
gpu_run python3 -u scripts/t15_eval.py
echo "T15 done $(date -Is)"
medverif_job_elapsed_end --rows 0
