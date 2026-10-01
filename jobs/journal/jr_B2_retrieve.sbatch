#!/bin/bash
#SBATCH --job-name=jr-B2-retr
#SBATCH --partition=defq
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=06:00:00
#SBATCH --exclude=node001,node004
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/jr-B2-retr_%j.out
# (B2) BM25 + MedCPT dense retrieval over MedRAG textbooks (embeddings cached, resumable).
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal/jr_env.sh"
nvidia-smi -L || true
"${PY}" -u scripts/journal/jr_rag_retrieve.py --dense "${JR_DENSE:-medcpt}" --topk 3
