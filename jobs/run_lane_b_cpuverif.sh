#!/usr/bin/env bash
# Lane B: T6-A CPU verifiers — 200-row calibration then main E1-evid (no Bespoke GPU here).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock lane_b_cpuverif

cd "${ROOT}"
LOG="${ROOT}/jobs/logs/lane_b_cpuverif_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "lane B start $(date -Is)"

source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate cpuverif
export PYTHONPATH="${ROOT}/src:${ROOT}/analysis"
export CUDA_VISIBLE_DEVICES=""
export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export MEDVERIF_SCORE_FLUSH_EVERY=20
export ALIGNScore_SRC="${ROOT}/.cache/src/AlignScore/src"
export PYTHONPATH="${ALIGNScore_SRC}:${PYTHONPATH}"

python3 scripts/lane_b_build_packs.py

OUT="${ROOT}/results/raw/lane_b"
mkdir -p "${OUT}"

run_pack() {
  local inst="$1"
  local label="$2"
  echo "=== score ${label} === $(date -Is)"
  python3 scripts/t6a_score_instances.py --instances "${inst}" --outdir "${OUT}" --checker all
}

run_pack "${ROOT}/data/lane_b/calibration_200.jsonl" "calibration_200"
python3 scripts/lane_b_calibration_report.py

run_pack "${ROOT}/data/lane_b/main_e1_evid.jsonl" "main_e1_evid"

python3 scripts/lane_b_calibration_report.py
echo "lane B done $(date -Is)"

/usr/bin/git -C "${ROOT}" add \
  scripts/lane_b_build_packs.py \
  scripts/lane_b_calibration_report.py \
  jobs/run_lane_b_cpuverif.sh \
  data/lane_b \
  notes/lane_b_packs.json \
  notes/lane_b_calibration_agreement.json \
  notes/lane_b_calibration_agreement.md \
  results/raw/lane_b 2>/dev/null || true
if /usr/bin/git -C "${ROOT}" diff --cached --quiet; then
  echo "lane B: nothing to commit"
else
  /usr/bin/git -C "${ROOT}" commit -m "$(cat <<'EOF'
feat: Lane B local T6-A calibration + main E1-evid scores

CPU verifiers on 200-row node30 calibration and main E1-evid pack; agreement report vs node30.

EOF
)"
  /usr/bin/git -C "${ROOT}" push origin master || true
fi
