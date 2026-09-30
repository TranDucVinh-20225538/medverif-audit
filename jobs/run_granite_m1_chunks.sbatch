#!/bin/bash
#SBATCH --job-name=granite_m1
#SBATCH --partition=defq
#SBATCH --array=0-10
#SBATCH --cpus-per-task=12
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/granite_m1_%A_%a.out
#SBATCH --error=/data2/hpcshared/medverif-audit/jobs/logs/granite_m1_%A_%a.err

# Granite in cpuverif (agreement 60/60 vs raw_node30), CPU-only; one chunk from data/lane_b/granite_chunks per task.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
export HF_HOME="${ROOT}/.cache/huggingface"
export PYTHONUNBUFFERED=1
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
source "${ROOT}/jobs/lib/hf_env.sh"
medverif_hf_env

chunk="$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" data/lane_b/granite_chunks/chunks.txt)"
[[ -n "${chunk}" ]] || { echo "no chunk for task ${SLURM_ARRAY_TASK_ID}"; exit 0; }
out="${ROOT}/results/raw/lane_b/granite_chunks/${chunk%.jsonl}"
mkdir -p "${out}"
cpu_py="$(env -u PYTHONPATH conda run -n cpuverif python -c 'import sys; print(sys.executable)')"
echo "granite chunk ${chunk} start $(date -Is)"
CUDA_VISIBLE_DEVICES="" PYTHONPATH="${ROOT}/src:${ROOT}/analysis:${ROOT}/scripts" MEDVERIF_LANE_B_ENV_PROFILE=cpuverif \
  "${cpu_py}" scripts/t6a_score_instances.py --instances "data/lane_b/granite_chunks/${chunk}" --outdir "${out}" --checker t6a_granite_guardian
wc -l "${out}/t6_granite_guardian.jsonl"
echo "granite chunk ${chunk} done $(date -Is)"
