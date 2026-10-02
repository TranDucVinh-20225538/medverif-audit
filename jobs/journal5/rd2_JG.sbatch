#!/bin/bash
#SBATCH --job-name=rd2-JG
#SBATCH --partition=defq
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=128G
#SBATCH --time=10:00:00
#SBATCH --array=0-6,8-9%2
#SBATCH --exclude=node001,node004
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/rd2-JG_%A_%a.out
# (RD2-4b) chain-3 local open LLM judges (scripts/journal3/j3_judge_score.py unchanged: RAGAS-NLI paper prompt, strict parser,
# vLLM greedy) on RD2 via scripts/journal5/rd2_j3_score.py.  Array index = j3_models.JUDGES position:
#   0 qwen25_7b 1 llama31_8b 2 medgemma_4b 3 qwen25_0p5b 4 qwen25_1p5b 5 qwen25_3b 6 qwen25_14b 8 medgemma_27b 9 baichuan_m2_32b
# -> results/journal5/rd2/judges/<slug>__rd2.jsonl (resumable).  Markers: results/journal5/rd2/markers_j3/.
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal5/rd2_env.sh"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
case "${SLURM_ARRAY_TASK_ID}" in 8|9) export MEDVERIF_J3_GPU_UTIL="${MEDVERIF_J3_GPU_UTIL:-0.95}" ;; esac
export MEDVERIF_J3_TP="${MEDVERIF_J3_TP:-1}"
nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv 2>/dev/null || true
"${PY}" -u scripts/journal5/rd2_j3_score.py --what judge --array-index "${SLURM_ARRAY_TASK_ID}" --backend vllm
