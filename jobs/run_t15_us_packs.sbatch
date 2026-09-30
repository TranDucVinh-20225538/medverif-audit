#!/bin/bash
#SBATCH --job-name=t15_us_packs
#SBATCH --partition=defq
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=01:30:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/t15_us_packs-%j.out
#SBATCH --error=/data2/hpcshared/medverif-audit/jobs/logs/t15_us_packs-%j.err

# T15 card US inputs: T7 (unit up) base+ft, T17 (unit down) base; resumes, never archives existing files.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
export HF_HOME="${ROOT}/.cache/huggingface"
export PYTHONUNBUFFERED=1
export PYTHONPATH="${ROOT}/.cache/src/MiniCheck:${ROOT}/src:${ROOT}/analysis"
export MEDVERIF_ROOT="${ROOT}"
export MEDVERIF_MINICHECK_BATCH=16
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
source "${ROOT}/jobs/lib/hf_env.sh"
medverif_hf_env
bash "${ROOT}/jobs/lib/install_minicheck_gpu.sh"
python3 -u scripts/t15_eval.py --packs t7,t17 --pack-leg both --packs-only --report "${ROOT}/jobs/logs/t15_us_packs_status.md"
wc -l results/raw/t15/{base,ft}_{t7,t17}.jsonl
