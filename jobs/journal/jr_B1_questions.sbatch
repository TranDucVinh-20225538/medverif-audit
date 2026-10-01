#!/bin/bash
#SBATCH --job-name=jr-B1-quest
#SBATCH --partition=defq
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/jr-B1-quest_%j.out
# (B1) dose-sentence pool from MedRAG textbooks (disjoint) + LLM-written questions (API, cap-checked).
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal/jr_env.sh"
jr_load_api_env
"${PY}" -u scripts/journal/jr_rag_questions.py --n "${JR_N_QUESTIONS:-200}"
