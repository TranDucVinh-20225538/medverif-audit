#!/usr/bin/env bash
# Lane B: T6-A CPU (+ V2a/V3) on login node; resume; per-pack under results/raw/lane_b/<pack>/.
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
export PYTHONPATH="${ROOT}/src:${ROOT}/analysis:${ROOT}/scripts"
export CUDA_VISIBLE_DEVICES=""
export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export MEDVERIF_SCORE_FLUSH_EVERY=20
export ALIGNScore_SRC="${ROOT}/.cache/src/AlignScore/src"
export PYTHONPATH="${ALIGNScore_SRC}:${PYTHONPATH}"

python3 -c "import summac" 2>/dev/null || PIP_INDEX_URL=https://pypi.org/simple PIP_EXTRA_INDEX_URL= pip install --index-url https://pypi.org/simple -r notes/cpuverif-pip-extras.txt

python3 scripts/lane_b_build_packs.py

# Migrate flat legacy scores into pack subdirs (resume-safe)
LEG="${ROOT}/results/raw/lane_b"
mkdir -p "${LEG}/calibration_200"
for f in "${LEG}"/t6_*.jsonl; do
  [[ -f "$f" ]] || continue
  base=$(basename "$f")
  [[ -f "${LEG}/calibration_200/${base}" ]] || mv "$f" "${LEG}/calibration_200/${base}"
done

score_pack() {
  local pack="$1"
  local inst="$2"
  echo "=== lane_b score pack=${pack} === $(date -Is)"
  python3 scripts/lane_b_score_pack.py --pack "${pack}" --instances "${inst}"
  /usr/bin/git -C "${ROOT}" add "results/raw/lane_b/${pack}" "notes/lane_b_packs.json" 2>/dev/null || true
  if /usr/bin/git -C "${ROOT}" diff --cached --quiet; then
    echo "lane B ${pack}: nothing to commit"
  else
    /usr/bin/git -C "${ROOT}" commit -m "$(cat <<EOF
feat(lane_b): HPC scores for ${pack} (T6-A + V2a/V3)

env=hpc; skip rows already scored / node30 overlap.

EOF
)"
    /usr/bin/git -C "${ROOT}" push origin master || true
  fi
}

score_pack calibration_200 "${ROOT}/data/lane_b/calibration_200.jsonl"
python3 scripts/lane_b_calibration_report.py

score_pack main_e1_evid "${ROOT}/data/lane_b/main_e1_evid.jsonl"
python3 scripts/lane_b_calibration_report.py

# node30 leftovers (same verifiers; skip if raw_node30 complete)
score_pack t17_downdose "${ROOT}/data/v3/t17_downdose.jsonl"
score_pack t14_pending "${ROOT}/data/v3/instances_t14_pending_node30.jsonl"

# M1 T7 E1-unit + main slices (MEDVERIF_M1=1 for API paths in score_jsonl when used)
export MEDVERIF_M1=1
python3 scripts/lane_b_build_m1_packs.py
score_pack m1_t7_e1_unit "${ROOT}/data/lane_b/m1_t7_e1_unit.jsonl"
score_pack m1_main_inv_e1_c0 "${ROOT}/data/lane_b/m1_main_inv_e1_c0.jsonl"

python3 scripts/build_e2_unit_instances.py 2>/dev/null || true
score_pack e2_unit "${ROOT}/data/e2/instances_e2_unit_t7.jsonl" || echo "WARN: e2_unit pack missing"

export MEDVERIF_M1=1
score_pack m1_plus_v2v3 "${ROOT}/data/lane_b/m1_plus_930.jsonl" || echo "WARN: m1_plus pack optional"

echo "lane B CPU queue done $(date -Is)"
echo "Bespoke-7B: submit jobs/run_lane_b_bespoke_gpu.sh when a GPU frees (after T19/T15)"
