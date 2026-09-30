#!/usr/bin/env bash
# Lane B: calibrate bespoke on 200 rows → gate ≥97% vs node30 → then packs.
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
unset MEDVERIF_BESPOKE_LIMIT
source "${ROOT}/jobs/lib/hf_env.sh"
medverif_hf_env

echo "bespoke dtype policy: bf16 (see v2b_bespoke VERSION/precision metadata)"

score_bespoke() {
  local pack="$1"
  local inst="$2"
  local out="${ROOT}/results/raw/lane_b/${pack}/v2b_bespoke.jsonl"
  if [[ ! -f "${inst}" ]]; then
    echo "skip ${pack}: no instances"
    return 0
  fi
  python3 src/score_jsonl.py --verifier v2b_bespoke --instances "${inst}" --out "${out}"
}

CAL_OUT="${ROOT}/results/raw/lane_b/calibration_200/v2b_bespoke.jsonl"
PACK_N="$(wc -l < "${ROOT}/data/lane_b/calibration_200.jsonl")"
if [[ ! -f "${CAL_OUT}" ]] || [[ "$(wc -l < "${CAL_OUT}")" -lt "${PACK_N}" ]]; then
  echo "=== calibration_200 bespoke === $(date -Is)"
  score_bespoke calibration_200 "${ROOT}/data/lane_b/calibration_200.jsonl"
fi

if ! python3 scripts/lane_b_bespoke_calibration_gate.py; then
  echo "FATAL: bespoke calibration gate failed (<97% or not bf16) — packs not scored"
  exit 2
fi

score_bespoke main_e1_evid "${ROOT}/data/lane_b/main_e1_evid.jsonl"
score_bespoke t17_downdose "${ROOT}/data/v3/t17_downdose.jsonl"
score_bespoke t14_pending "${ROOT}/data/v3/instances_t14_pending_node30.jsonl"
score_bespoke m1_main_inv_e1_c0 "${ROOT}/data/lane_b/m1_main_inv_e1_c0.jsonl"
score_bespoke m1_t7_e1_unit "${ROOT}/data/lane_b/m1_t7_e1_unit.jsonl"
score_bespoke e2_unit "${ROOT}/data/e2/instances_e2_unit_t7.jsonl"

echo "lane B bespoke done $(date -Is)"
