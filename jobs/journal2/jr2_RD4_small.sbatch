#!/bin/bash
#SBATCH --job-name=jr2-RD4-small
#SBATCH --partition=defq
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/jr2-RD4-small_%j.out
# (RD4) five small checkers on the real-dose instances in the paper's cpuverif env (CPU).
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal2/jr2_env.sh"
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16} MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export MEDVERIF_RD_SMALL_PY="$(jr2_cpuverif_py)" MEDVERIF_SCORE_ENV_TAG=hpc_cpuverif
"${PY}" -u scripts/journal2/rd_score.py --part small
