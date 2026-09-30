#!/bin/bash
#SBATCH --job-name=summac_evid
#SBATCH --partition=defq
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/summac_evid_%j.out
#SBATCH --error=/data2/hpcshared/medverif-audit/jobs/logs/summac_evid_%j.err

# SummaC-ZS on main E1-evid (NS_x10 EVID for M1-strong); other checkers already in this folder.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
export HF_HOME="${ROOT}/.cache/huggingface"
export PYTHONUNBUFFERED=1
export NLTK_DATA="${ROOT}/.cache/nltk"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
source "${ROOT}/jobs/lib/hf_env.sh"
medverif_hf_env

INST="${ROOT}/data/lane_b/main_e1_evid.jsonl"
OUT="${ROOT}/results/raw/lane_b/main_e1_evid"
legacy_py="$(env -u PYTHONPATH conda run -n cpuverif_legacy python -c 'import sys; print(sys.executable)')"
echo "summac evid start $(date -Is) job=${SLURM_JOB_ID}"
PYTHONPATH="${ROOT}/src:${ROOT}/analysis:${ROOT}/scripts" MEDVERIF_LANE_B_ENV_PROFILE=legacy MEDVERIF_LEGACY_GPU=1 \
  "${legacy_py}" scripts/t6a_score_instances.py --instances "${INST}" --outdir "${OUT}" --checker t6a_summac_zs
wc -l "${OUT}"/t6_summac_zs.jsonl
echo "summac evid done $(date -Is)"
