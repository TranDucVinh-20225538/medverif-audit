#!/bin/bash
#SBATCH --job-name=jr-B4-besp
#SBATCH --partition=defq
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --exclude=node001,node004
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/jr-B4-besp_%j.out
# (B4) Bespoke-MiniCheck-7B on the RAG pack (vllm env, GPU).
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal/jr_env.sh"
export MEDVERIF_REQ_MEM_GB=48
source "${ROOT}/jobs/lib/gpu_node_precheck.sh"; medverif_gpu_node_precheck
"${PY}" -u scripts/journal/jr_rag_score.py --part bespoke
