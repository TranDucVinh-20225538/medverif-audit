#!/bin/bash
#SBATCH --job-name=jr2-RD1-gen
#SBATCH --partition=defq
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=06:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/jr2-RD1-gen_%j.out
# (RD1-RD3) questions from the committed FDA labels -> generator answers (API, real-dose cap) -> rule-based extraction + QC sheet.
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal2/jr2_env.sh"
jr2_load_api_env
"${PY}" -u scripts/journal2/rd_questions.py
"${PY}" -u scripts/journal2/rd_generate.py
"${PY}" -u scripts/journal2/rd_extract.py
