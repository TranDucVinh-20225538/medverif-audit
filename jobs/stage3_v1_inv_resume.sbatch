#!/bin/bash
#SBATCH --job-name=medverif-v1-inv
#SBATCH --partition=defq
#SBATCH --exclude=node001,node002
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --cpus-per-task=8
#SBATCH --time=04:00:00
#SBATCH --signal=B:TERM@120
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/%x-%j.out

set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export VLLM_CACHE_ROOT="${ROOT}/.cache/vllm"
export HF_HUB_DISABLE_TELEMETRY=1
export TOKENIZERS_PARALLELISM=false
export PYTHONPATH="${ROOT}/src"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
source "${ROOT}/jobs/lib/gpu_graceful.sh"
source "${ROOT}/jobs/lib/stage_vllm_cache.sh"
gpu_graceful_init
export MEDVERIF_ROOT="${ROOT}"
stage_hf_snapshot "mistralai/Mistral-Small-24B-Instruct-2501" "9527884be6e5616bdd54de542f9ae13384489724"

gpu_run python src/score_jsonl.py --verifier v1_medscore --instances data/v3/instances_main.jsonl --out results/raw/v1_medscore.jsonl
gpu_run python src/score_jsonl.py --verifier v1_medscore --instances data/v3/instances_threshold.jsonl --out results/raw_threshold/v1_medscore.jsonl
python src/reparse_v1_study.py --in-place results/raw/v1_medscore.jsonl results/raw_threshold/v1_medscore.jsonl
echo "v1 inv resume done $(date -Is)"
sbatch --dependency=afterok:"${SLURM_JOB_ID}" "${ROOT}/jobs/stage4.sbatch"
