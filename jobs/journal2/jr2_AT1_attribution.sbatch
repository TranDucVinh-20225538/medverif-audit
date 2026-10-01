#!/bin/bash
#SBATCH --job-name=jr2-AT1-attr
#SBATCH --partition=defq
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --exclude=node001,node004
#SBATCH --signal=B:TERM@120
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/jr2-AT1-attr_%j.out
# (AT1) integrated gradients (128 steps) + attention rollout + occlusion for MiniCheck-RoBERTa, MiniCheck-Flan-T5,
# AlignScore-large on 486 DOSE items (107 bases).  Resumable (attr_<model>.jsonl).  AT2 report runs in jr2_final.
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal2/jr2_env.sh"
export MEDVERIF_REQ_MEM_GB=32
source "${ROOT}/jobs/lib/gpu_node_precheck.sh"; medverif_gpu_node_precheck
"${PY}" -u scripts/journal2/at_attribution.py --device cuda
