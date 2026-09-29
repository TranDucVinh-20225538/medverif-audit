#!/bin/bash
#SBATCH --job-name=medverif-v3b
#SBATCH --partition=defq
#SBATCH --exclude=node001,node002
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --cpus-per-task=8
#SBATCH --time=03:00:00
#SBATCH --signal=B:TERM@120
#SBATCH --open-mode=append
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/%x-%j.out

set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
if [[ -f "${ROOT}/notes/HOLD_medverif_v3" ]]; then
  echo "BLOCKED: notes/HOLD_medverif_v3 present — exit without running" >&2
  exit 0
fi
export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export VLLM_CACHE_ROOT="${ROOT}/.cache/vllm"
export HF_HUB_DISABLE_TELEMETRY=1
export HF_HUB_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
export PYTHONPATH="${ROOT}/src"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
source "${ROOT}/jobs/lib/gpu_graceful.sh"
source "${ROOT}/jobs/lib/stage_vllm_cache.sh"
gpu_graceful_init
export MEDVERIF_ROOT="${ROOT}"
stage_hf_snapshot "microsoft/phi-4" "2db69c1c3e91a05d2c64a3185acfbaf36f744e25"
gpu_run python -u src/label_v3b.py
echo "v3b done $(date -Is)"
INV=$(sbatch --parsable --dependency=afterok:"${SLURM_JOB_ID}" "${ROOT}/jobs/stage3_v1_inv_resume.sbatch")
echo "queued inv v1 resume ${INV}"
