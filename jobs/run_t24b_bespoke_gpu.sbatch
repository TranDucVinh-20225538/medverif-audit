#!/bin/bash
#SBATCH --job-name=t24b_bespoke
#SBATCH --partition=defq
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/t24b_bespoke_%j.out

set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
export HF_HOME="${ROOT}/.cache/huggingface"
export PYTHONPATH="${ROOT}/src:${ROOT}/.cache/src/MiniCheck"
export MEDVERIF_BESPOKE_BATCH=8
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
source "${ROOT}/jobs/lib/hf_env.sh"
medverif_hf_env
python3 src/score_jsonl.py --verifier v2b_bespoke \
  --instances "${ROOT}/data/t24/instances_t24b.jsonl" \
  --out "${ROOT}/results/raw/t24b/v2b_bespoke.jsonl"
python3 scripts/t24b_report.py
echo "t24b bespoke done $(date -Is)"
