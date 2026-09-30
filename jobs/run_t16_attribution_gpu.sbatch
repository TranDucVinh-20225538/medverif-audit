#!/bin/bash
#SBATCH --job-name=t16_attr_gpu
#SBATCH --partition=defq
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --exclude=node004
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/t16_attribution_gpu-%j.out
#SBATCH --error=/data2/hpcshared/medverif-audit/jobs/logs/t16_attribution_gpu-%j.err

set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
source "${ROOT}/jobs/lib/flock.sh"
source "${ROOT}/jobs/lib/gpu_graceful.sh"
medverif_acquire_lock t16_attribution_gpu

export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export HF_HUB_DISABLE_TELEMETRY=1
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
export PYTHONPATH="${ROOT}/src"
export OMP_NUM_THREADS=2
export MEDVERIF_T16_DEVICE=cuda
export MEDVERIF_REQ_MEM_GB=32

source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
source "${ROOT}/jobs/lib/hf_env.sh"
medverif_hf_env
source "${ROOT}/jobs/lib/gpu_node_precheck.sh"
medverif_gpu_node_precheck
gpu_graceful_init

echo "t16 GPU start $(date -Is)"
python3 -c "import torch; assert torch.cuda.is_available(), 'cpuverif/vllm torch must see CUDA on GPU node'; print('cuda', torch.cuda.get_device_name(0))"
python3 -u scripts/t16_attribution.py
echo "t16 GPU done $(date -Is)"
