#!/bin/bash
#SBATCH --job-name=jr-C3-eval
#SBATCH --partition=defq
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --array=0-7%2
#SBATCH --exclude=node001,node004
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/jr-C3-eval_%A_%a.out
# (C3) score base + ft models (tasks 0-3 AlignScore-large base/r0.5/r1/r2, 4-7 MiniCheck-FT5 base/r0.5/r1/r2)
# on card packs, LLM-AggreFact (n=3000), T24b and the journal RAG pack.
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal/jr_env.sh"
EVAL_PY="${PY}"
if [[ "${SLURM_ARRAY_TASK_ID}" -lt 4 ]] && ! "${PY}" -c "import pytorch_lightning, alignscore" 2>/dev/null; then
  # AlignScore library needs pytorch_lightning; fall back to the paper's cpuverif env (CPU, slower)
  EVAL_PY="$(conda run -n "${MEDVERIF_CPUVERIF_CONDA:-cpuverif}" python -c 'import sys; print(sys.executable)')"
  export CUDA_VISIBLE_DEVICES=""
  echo "AlignScore: pytorch_lightning missing in vllm env -> cpuverif CPU fallback (${EVAL_PY})"
fi
"${EVAL_PY}" -u scripts/journal/jr_ft_eval.py --array-index "${SLURM_ARRAY_TASK_ID}"
