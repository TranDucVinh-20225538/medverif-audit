#!/bin/bash
#SBATCH --job-name=m1_amend5
#SBATCH --partition=defq
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=03:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/m1_amend5_%j.out
#SBATCH --error=/data2/hpcshared/medverif-audit/jobs/logs/m1_amend5_%j.err

# Amendment 5: rescore the 46 off-spec US_up after-M1 rows (spec text; MEDVERIF_M1=0) with every M1-strong checker.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
export HF_HOME="${ROOT}/.cache/huggingface"
export PYTHONUNBUFFERED=1
export MEDVERIF_M1=0
export NLTK_DATA="${ROOT}/.cache/nltk"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
source "${ROOT}/jobs/lib/hf_env.sh"
medverif_hf_env

INST="${ROOT}/data/lane_b/m1_t7_e1_unit_amend5.jsonl"
OUT="${ROOT}/results/raw/lane_b/m1_t7_e1_unit_amend5"
mkdir -p "${OUT}"
SRC_PATH="${ROOT}/.cache/src/MiniCheck:${ROOT}/src:${ROOT}/analysis:${ROOT}/scripts:${ROOT}/.cache/src/AlignScore/src"
echo "m1 amend5 start $(date -Is) job=${SLURM_JOB_ID}"

cpu_py="$(env -u PYTHONPATH conda run -n cpuverif python -c 'import sys; print(sys.executable)')"
legacy_py="$(env -u PYTHONPATH conda run -n cpuverif_legacy python -c 'import sys; print(sys.executable)')"

for cid in t6a_minicheck_roberta t6a_minicheck_deberta t6a_alignscore_base t6a_granite_guardian; do
  echo "=== ${cid} $(date -Is)"
  PYTHONPATH="${SRC_PATH}" MEDVERIF_LANE_B_ENV_PROFILE=cpuverif \
    "${cpu_py}" scripts/t6a_score_instances.py --instances "${INST}" --outdir "${OUT}" --checker "${cid}"
done

echo "=== t6a_summac_zs $(date -Is)"
PYTHONPATH="${ROOT}/src:${ROOT}/analysis:${ROOT}/scripts" MEDVERIF_LANE_B_ENV_PROFILE=legacy MEDVERIF_LEGACY_GPU=1 \
  "${legacy_py}" scripts/t6a_score_instances.py --instances "${INST}" --outdir "${OUT}" --checker t6a_summac_zs

for vid in v2a_minicheck v3_alignscore; do
  echo "=== ${vid} $(date -Is)"
  PYTHONPATH="${SRC_PATH}" MEDVERIF_LANE_B_ENV_PROFILE=cpuverif \
    "${cpu_py}" src/score_jsonl.py --verifier "${vid}" --instances "${INST}" --out "${OUT}/${vid}.jsonl"
done

echo "=== v2b_bespoke $(date -Is)"
conda activate vllm
PYTHONPATH="${ROOT}/src:${ROOT}/.cache/src/MiniCheck" MEDVERIF_GPU_GLOBAL_SCORE_LOCK=1 \
  python3 src/score_jsonl.py --verifier v2b_bespoke --instances "${INST}" --out "${OUT}/v2b_bespoke.jsonl"

wc -l "${OUT}"/*.jsonl
echo "m1 amend5 done $(date -Is)"
