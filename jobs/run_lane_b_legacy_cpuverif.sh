#!/usr/bin/env bash
# Legacy Lane B: calibrate + score packs for SummaC/HHEM/Granite (cpuverif_legacy only).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock lane_b_legacy_cpuverif

cd "${ROOT}"
LOG="${ROOT}/jobs/logs/lane_b_legacy_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "lane B legacy start $(date -Is)"

source /data2/shared/apps/conda/etc/profile.d/conda.sh
bash "${ROOT}/scripts/setup_cpuverif_legacy.sh"

export PYTHONPATH="${ROOT}/src:${ROOT}/analysis:${ROOT}/scripts"
export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export MEDVERIF_SCORE_FLUSH_EVERY=20

python3 scripts/lane_b_recalibrate_legacy.py

score_legacy_pack() {
  local pack="$1"
  local inst="$2"
  echo "=== lane_b legacy pack=${pack} === $(date -Is)"
  python3 scripts/lane_b_score_pack.py --legacy-only --pack "${pack}" --instances "${inst}"
}

score_legacy_pack main_e1_evid "${ROOT}/data/lane_b/main_e1_evid.jsonl"
score_legacy_pack t17_downdose "${ROOT}/data/v3/t17_downdose.jsonl"
score_legacy_pack t14_pending "${ROOT}/data/v3/instances_t14_pending_node30.jsonl"
export MEDVERIF_M1=1
score_legacy_pack m1_t7_e1_unit "${ROOT}/data/lane_b/m1_t7_e1_unit.jsonl"
score_legacy_pack m1_main_inv_e1_c0 "${ROOT}/data/lane_b/m1_main_inv_e1_c0.jsonl"
score_legacy_pack e2_unit "${ROOT}/data/e2/instances_e2_unit_t7.jsonl" || true

echo "lane B legacy done $(date -Is)"
