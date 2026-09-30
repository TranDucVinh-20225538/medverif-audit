#!/usr/bin/env bash
# Lane B: Bespoke-MiniCheck-7B on packs (skip main_ext / T18 until PI review).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
LOG="${ROOT}/jobs/logs/lane_b_bespoke_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "lane B bespoke GPU start $(date -Is)"

source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
export PYTHONPATH="${ROOT}/src:${ROOT}/.cache/src/MiniCheck"
export MEDVERIF_GPU_GLOBAL_SCORE_LOCK=1
export HF_HOME="${ROOT}/.cache/huggingface"
source "${ROOT}/jobs/lib/hf_env.sh"
medverif_hf_env

score_bespoke() {
  local pack="$1"
  local inst="$2"
  local out="${ROOT}/results/raw/lane_b/${pack}/v2b_bespoke.jsonl"
  if [[ ! -f "${inst}" ]]; then
    echo "skip ${pack}: no instances"
    return 0
  fi
  python3 src/score_jsonl.py --verifier v2b_bespoke --instances "${inst}" --out "${out}" --limit "${MEDVERIF_BESPOKE_LIMIT:-0}"
}

LIMIT="${MEDVERIF_BESPOKE_LIMIT:-0}"
score_bespoke main_e1_evid "${ROOT}/data/lane_b/main_e1_evid.jsonl"
score_bespoke t17_downdose "${ROOT}/data/v3/t17_downdose.jsonl"
score_bespoke t14_pending "${ROOT}/data/v3/instances_t14_pending_node30.jsonl"
score_bespoke m1_main_inv_e1_c0 "${ROOT}/data/lane_b/m1_main_inv_e1_c0.jsonl"
score_bespoke m1_t7_e1_unit "${ROOT}/data/lane_b/m1_t7_e1_unit.jsonl"
score_bespoke e2_unit "${ROOT}/data/e2/instances_e2_unit_t7.jsonl"

echo "lane B bespoke done $(date -Is)"
