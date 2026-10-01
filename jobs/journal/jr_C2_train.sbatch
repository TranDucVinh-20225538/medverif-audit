#!/bin/bash
#SBATCH --job-name=jr-C2-train
#SBATCH --partition=defq
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --array=0-5%2
#SBATCH --exclude=node001,node004
#SBATCH --signal=B:TERM@120
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/jr-C2-train_%A_%a.out
# (C2) fine-tune: tasks 0-2 AlignScore-large r=0.5/1/2, tasks 3-5 MiniCheck-Flan-T5 r=0.5/1/2 (max 2 GPUs at once).
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal/jr_env.sh"
export MEDVERIF_REQ_MEM_GB=64
source "${ROOT}/jobs/lib/gpu_node_precheck.sh"; medverif_gpu_node_precheck
"${PY}" -u scripts/journal/jr_ft_train.py --array-index "${SLURM_ARRAY_TASK_ID}"
