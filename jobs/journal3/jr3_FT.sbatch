#!/bin/bash
#SBATCH --job-name=jr3-FT
#SBATCH --partition=defq
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=10:00:00
#SBATCH --array=0-7%3
#SBATCH --exclude=node001,node004
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/jr3-FT_%A_%a.out
# (J3-FT) chain-1 fine-tuned checkers + same-path bases on RD (1451), held-out UNF (raw/v1/v2) and RD-UNF pairs
# (raw/v1/v2).  Tasks (j3_models.FT): 0 minicheck_ft5_r1, 1 alignscore_large_r1, 2 minicheck_ft5_base,
# 3 alignscore_large_base, 4 minicheck_ft5_r0.5, 5 minicheck_ft5_r2, 6 alignscore_large_r0.5, 7 alignscore_large_r2.
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal3/jr3_env.sh"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1   # compute nodes: cached weights only (as chain 1 C3)
EVAL_PY="${PY}"
case "${SLURM_ARRAY_TASK_ID}" in 1|3|6|7) IS_AS=1 ;; *) IS_AS=0 ;; esac
if [[ ${IS_AS} -eq 1 ]] && ! "${PY}" -c "import pytorch_lightning, alignscore" 2>/dev/null; then
  EVAL_PY="$(jr3_cpuverif_py)"
  export CUDA_VISIBLE_DEVICES=""
  echo "AlignScore: pytorch_lightning/alignscore missing in vllm env -> cpuverif CPU fallback (${EVAL_PY})"
fi
nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv 2>/dev/null || true
"${EVAL_PY}" -u scripts/journal3/j3_ft_score.py --array-index "${SLURM_ARRAY_TASK_ID}"
