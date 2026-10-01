#!/bin/bash
#SBATCH --job-name=jr-A-thresh
#SBATCH --partition=defq
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=03:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/jr-A-thresh_%j.out
# (A) threshold robustness + 10k-resample bootstrap CIs for all card cells. CPU only.
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal/jr_env.sh"
"${PY}" -u scripts/journal/jr_threshold_robustness.py --boot "${JR_BOOT:-10000}" --grid 400
