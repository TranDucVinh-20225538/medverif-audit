#!/bin/bash
#SBATCH --job-name=jr-C1-data
#SBATCH --partition=defq
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/jr-C1-data_%j.out
# (C1) ANLI mixing ratios {0.5,1,2} over the T15 dose pairs.
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal/jr_env.sh"
"${PY}" -u scripts/journal/jr_ft_data.py
