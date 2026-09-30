#!/usr/bin/env bash
# Score t14_pending + m1_t7_e1_unit (cpuverif trio + V2a/V3; legacy if cal passed).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock lane_b_score_t14_m1

cd "${ROOT}"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate cpuverif
export PYTHONPATH="${ROOT}/src:${ROOT}/analysis:${ROOT}/scripts"
export ALIGNScore_SRC="${ROOT}/.cache/src/AlignScore/src"
export PYTHONPATH="${ALIGNScore_SRC}:${PYTHONPATH}"
export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export MEDVERIF_LANE_B_ENV_PROFILE=cpuverif
export MEDVERIF_SCORE_FLUSH_EVERY=20
export CUDA_VISIBLE_DEVICES=""

commit_pack() {
  local pack="$1"
  /usr/bin/git -C "${ROOT}" add \
    "results/raw/lane_b/${pack}" \
    "data/v3/instances_t14_pending_node30.jsonl" \
    "data/lane_b/m1_t7_e1_unit.jsonl" \
    "notes/lane_b_packs.json" \
    "notes/lane_b_instance_restore.md" \
    "scripts/lane_b_build_m1_packs.py" \
    2>/dev/null || true
  if /usr/bin/git -C "${ROOT}" diff --cached --quiet; then
    echo "nothing to commit for ${pack}"
    return 0
  fi
  /usr/bin/git -C "${ROOT}" commit -m "$(cat <<EOF
feat(lane_b): scores for ${pack} (restored instances)

cpuverif trio + V2a/V3; legacy checkers if calibration passed.

EOF
)"
  /usr/bin/git -C "${ROOT}" push origin master || true
}

score_one() {
  local pack="$1"
  local inst="$2"
  local m1="${3:-0}"
  echo "=== ${pack} === $(date -Is)"
  export MEDVERIF_M1="${m1}"
  python3 scripts/lane_b_score_pack.py --pack "${pack}" --instances "${inst}"
  if [[ -f notes/lane_b_checker_routing.json ]] && python3 -c "import json; print(len(json.load(open('notes/lane_b_checker_routing.json')).get('legacy_downstream_allowed') or []))" | grep -qv '^0$'; then
    python3 scripts/lane_b_score_pack.py --legacy-only --pack "${pack}" --instances "${inst}" || true
  fi
  commit_pack "${pack}"
}

score_one t14_pending "${ROOT}/data/v3/instances_t14_pending_node30.jsonl" 0
score_one m1_t7_e1_unit "${ROOT}/data/lane_b/m1_t7_e1_unit.jsonl" 0
echo "t14+m1 lane_b done $(date -Is)"
