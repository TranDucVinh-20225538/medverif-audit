#!/bin/bash
#SBATCH --job-name=t15_ood
#SBATCH --partition=defq
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/t15_ood-%j.out
#SBATCH --error=/data2/hpcshared/medverif-audit/jobs/logs/t15_ood-%j.err

# T15 OOD: base + ft MiniCheck-RoBERTa on T24b and T18 Wikipedia OOD pack, CPU only.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
export HF_HOME="${ROOT}/.cache/huggingface"
export PYTHONUNBUFFERED=1
export PYTHONPATH="${ROOT}/.cache/src/MiniCheck:${ROOT}/src:${ROOT}/analysis"
export MEDVERIF_ROOT="${ROOT}"
export MEDVERIF_MINICHECK_BATCH=8
export CUDA_VISIBLE_DEVICES=""
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
source "${ROOT}/jobs/lib/hf_env.sh"
medverif_hf_env
python3 -u scripts/t15_eval.py --packs t24b,t18_ood --pack-leg both --packs-only --report "${ROOT}/jobs/logs/t15_ood_status.md"
wc -l results/raw/t15/{base,ft}_{t24b,t18_ood}.jsonl
