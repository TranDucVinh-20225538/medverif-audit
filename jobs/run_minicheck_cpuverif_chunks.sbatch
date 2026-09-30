#!/bin/bash
#SBATCH --job-name=mc_cpuverif
#SBATCH --partition=defq
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=02:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/mc_cpuverif_%A_%a.out
#SBATCH --error=/data2/hpcshared/medverif-audit/jobs/logs/mc_cpuverif_%A_%a.err

# Reference-env (cpuverif) rescoring of paper MiniCheck score files: one "<checker> <chunk>" line from tasks.txt per task.
# Submit with: sbatch --array=0-$(( $(wc -l < data/minicheck_cpuverif_chunks/tasks.txt) - 1 )) jobs/run_minicheck_cpuverif_chunks.sbatch
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
export HF_HOME="${ROOT}/.cache/huggingface"
export PYTHONUNBUFFERED=1
export CUDA_VISIBLE_DEVICES=""
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK}"
export MEDVERIF_M1=0
export NLTK_DATA="${ROOT}/.cache/nltk"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
source "${ROOT}/jobs/lib/hf_env.sh"
medverif_hf_env

TASKS="${MC_TASKS:-data/minicheck_cpuverif_chunks/tasks.txt}"
read -r cid name conda_env < <(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" "${TASKS}")
conda_env="${conda_env:-cpuverif}"
profile=cpuverif
[[ "${conda_env}" == "cpuverif_legacy" ]] && profile=legacy
inst="${ROOT}/data/minicheck_cpuverif_chunks/${name}.jsonl"
outdir="${ROOT}/results/raw/minicheck_cpuverif/chunks"
mkdir -p "${outdir}"
cpu_py="$(env -u PYTHONPATH conda run -n "${conda_env}" python -c 'import sys; print(sys.executable)')"
export PYTHONPATH="${ROOT}/.cache/src/MiniCheck:${ROOT}/src:${ROOT}/analysis:${ROOT}/scripts:${ROOT}/.cache/src/AlignScore/src"
export MEDVERIF_LANE_B_ENV_PROFILE="${profile}"
echo "minicheck ${conda_env} ${cid} ${name} start $(date -Is)"
if [[ "${cid}" == "v2a_minicheck" || "${cid}" == "v3_alignscore" ]]; then
  # score_jsonl locks per (verifier, first dir under results/raw); a unique top-level file lets chunks run in parallel.
  tmp_out="${ROOT}/results/raw/minicheck_cpuverif__${name}.jsonl"
  rm -f "${outdir}/${name}.jsonl" "${tmp_out}"
  "${cpu_py}" src/score_jsonl.py --verifier "${cid}" --instances "${inst}" --out "${tmp_out}"
  mv "${tmp_out}" "${outdir}/${name}.jsonl"
else
  tmp="${outdir}/${name}.d"
  rm -rf "${tmp}"
  "${cpu_py}" scripts/t6a_score_instances.py --instances "${inst}" --outdir "${tmp}" --checker "${cid}" --force
  mv "${tmp}"/*.jsonl "${outdir}/${name}.jsonl"
  rm -rf "${tmp}"
fi
wc -l "${outdir}/${name}.jsonl"
echo "done $(date -Is)"
