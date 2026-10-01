#!/bin/bash
#SBATCH --job-name=jr2-RD4-judges
#SBATCH --partition=defq
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=08:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/jr2-RD4-judges_%j.out
# (RD4) the two pinned LLM judges (Llama-3.3-70B RAGAS-NLI, Mistral-Small-24B MedScore) on the real-dose instances (API).
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal2/jr2_env.sh"
jr2_load_api_env
"${PY}" -u scripts/journal2/rd_score.py --part judges
