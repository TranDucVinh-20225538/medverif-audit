#!/bin/bash
#SBATCH --job-name=jr-B4-small
#SBATCH --partition=defq
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=16:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/jr-B4-small_%j.out
# (B4) small checkers on the RAG pack in the paper's cpuverif env (CPU).
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal/jr_env.sh"
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16} MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
"${PY}" -u scripts/journal/jr_rag_score.py --part small
