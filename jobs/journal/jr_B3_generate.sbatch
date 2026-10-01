#!/bin/bash
#SBATCH --job-name=jr-B3-gen
#SBATCH --partition=defq
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=06:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/jr-B3-gen_%j.out
# (B3) 2 generators (API) -> edit pack + human-check CSV (CPU) -> LLM judges (API). Shared $5 cap.
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal/jr_env.sh"
jr_load_api_env
"${PY}" -u scripts/journal/jr_rag_generate.py
"${PY}" -u scripts/journal/jr_rag_instances.py
"${PY}" -u scripts/journal/jr_rag_score.py --part judges
