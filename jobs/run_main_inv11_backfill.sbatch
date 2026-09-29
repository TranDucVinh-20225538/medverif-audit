#!/bin/bash
#SBATCH --job-name=inv11-m1
#SBATCH --partition=defq
#SBATCH --gres=gpu:1
#SBATCH --mem=48G
#SBATCH --cpus-per-task=8
#SBATCH --time=04:00:00
#SBATCH --nodelist=node002
#SBATCH --signal=B:TERM@120
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/inv11-%x-%j.out

set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
source "${ROOT}/jobs/lib/flock.sh"
source "${ROOT}/jobs/lib/gpu_graceful.sh"
source "${ROOT}/jobs/lib/gpu_node_precheck.sh"

medverif_acquire_lock main_inv11_backfill
export MEDVERIF_REQ_MEM_GB=48
medverif_gpu_node_precheck

export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export PYTHONPATH="${ROOT}/src:${ROOT}/analysis"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
source /data2/shared/apps/conda/etc/profile.d/conda.sh

gpu_graceful_init
python3 scripts/build_audit_gap_instance_packs.py

INST="${ROOT}/data/v3/instances_main_inv11_m1_gap.jsonl"
RAW="${ROOT}/results/raw"

conda activate cpuverif
gpu_run python3 src/score_jsonl.py --verifier v2a_minicheck --instances "${INST}" --out "${RAW}/v2a_minicheck.jsonl"
gpu_run python3 src/score_jsonl.py --verifier v3_alignscore --instances "${INST}" --out "${RAW}/v3_alignscore.jsonl"

conda activate vllm
set -a && source ~/kkk/openrouter.env && set +a
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_GPU_GLOBAL_SCORE_LOCK=0
gpu_run python3 src/score_jsonl.py --verifier v1_medscore --instances "${INST}" --out "${RAW}/v1_medscore.jsonl"

echo "inv11 GPU backfill done $(date -Is)"
