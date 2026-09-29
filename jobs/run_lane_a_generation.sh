#!/usr/bin/env bash
# Lane A: main_ext + IAA + T18 packs (generation/build only; cap $2 for any OR sidecars).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock lane_a_generation

cd "${ROOT}"
LOG="${ROOT}/jobs/logs/lane_a_generation_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "lane A start $(date -Is)"
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_LANE_A_CAP_USD="${MEDVERIF_LANE_A_CAP_USD:-2}"
python3 scripts/lane_a_budget.py || true

echo "=== smoke main_ext (5 bases) ==="
python3 scripts/build_main_ext_pack.py --smoke-bases 5
echo "=== smoke t18 (5 bases) ==="
python3 scripts/build_t18_wikipedia_pack.py --smoke-bases 5

echo "=== full main_ext ==="
python3 scripts/build_main_ext_pack.py --max-bases 40
echo "=== IAA sample (no OR) ==="
python3 scripts/build_iaa_sample.py
python3 scripts/iaa_cohen_kappa.py || true
echo "=== full t18 ==="
python3 scripts/build_t18_wikipedia_pack.py --max-bases 30

python3 scripts/lane_a_budget.py
echo "lane A done $(date -Is)"

/usr/bin/git -C "${ROOT}" add \
  scripts/build_main_ext_pack.py \
  scripts/build_iaa_sample.py \
  scripts/build_t18_wikipedia_pack.py \
  scripts/iaa_cohen_kappa.py \
  scripts/lane_a_budget.py \
  jobs/run_lane_a_generation.sh \
  data/main_ext data/t18 qc/main_ext_review.csv qc/iaa_sample.csv qc/iaa_guidelines.md qc/t18_sample.csv \
  notes/main_ext_manifest.json notes/iaa_sample_manifest.json notes/t18_manifest.json \
  notes/lane_a_spend.json 2>/dev/null || true
if /usr/bin/git -C "${ROOT}" diff --cached --quiet; then
  echo "lane A: nothing to commit"
else
  /usr/bin/git -C "${ROOT}" commit -m "$(cat <<'EOF'
feat: Lane A packs — main_ext, IAA sample, T18 eval cohort

Author-whitelist perturb bases disjoint from main/T15; QC CSVs and kappa helper; no scoring.

EOF
)"
  /usr/bin/git -C "${ROOT}" push origin master || true
fi
