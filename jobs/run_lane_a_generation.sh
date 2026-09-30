#!/usr/bin/env bash
# Lane A v2: main_ext (Textbooks+OR) + IAA 120 + T18 Wikipedia (no scoring).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock lane_a_generation

cd "${ROOT}"
LOG="${ROOT}/jobs/logs/lane_a_generation_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "lane A v2 start $(date -Is)"

export PYTHONPATH="${ROOT}/src:${ROOT}/scripts/expand:${ROOT}/scripts"
export MEDVERIF_LANE_A_CAP_USD="${MEDVERIF_LANE_A_CAP_USD:-3}"
export MEDVERIF_LANE_A_SYNC=1
export MEDVERIF_EXPAND_LEDGER="${ROOT}/data/main_ext/stage1/api_spend.jsonl"
export MEDVERIF_EXPAND_BUDGET_USD="${MEDVERIF_LANE_A_CAP_USD}"

if [[ -f ~/kkk/openrouter.env ]]; then
  set -a && source ~/kkk/openrouter.env && set +a
fi
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_API_LEDGER=1
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-2}"

python3 scripts/lane_a_budget.py || true
python3 scripts/openrouter_budget.py || { echo "OR credit stop"; exit 2; }

echo "=== smoke main_ext (5 bases) ==="
python3 scripts/build_main_ext_pack.py --smoke-bases 5 --max-stage1 15

echo "=== IAA 120 (no OR) ==="
python3 scripts/build_iaa_sample.py
python3 scripts/iaa_kappa.py || true

echo "=== T18 Wikipedia smoke (5 bases) ==="
python3 scripts/build_t18_wikipedia_pack.py --smoke-bases 5 --max-articles 4000 || echo "WARN: T18 smoke failed (continuing)"

echo "=== full main_ext (target 80+ whitelist INV bases) ==="
python3 scripts/build_main_ext_pack.py --target-bases 80 --max-stage1 250

echo "=== full T18 (30 bases) ==="
python3 scripts/build_t18_wikipedia_pack.py --max-bases 30 --max-articles 12000 || echo "WARN: T18 full failed (continuing)"

python3 scripts/lane_a_budget.py
echo "lane A v2 done $(date -Is)"

/usr/bin/git -C "${ROOT}" add \
  scripts/build_main_ext_pack.py \
  scripts/main_ext_select_candidates.py \
  scripts/main_ext_disjointness.py \
  scripts/build_iaa_sample.py \
  scripts/build_t18_wikipedia_pack.py \
  scripts/lane_a_budget.py \
  scripts/lane_a_instance_filters.py \
  scripts/lane_b_build_packs.py \
  scripts/expand/expand_budget.py \
  src/text_utils.py \
  src/perturb.py \
  src/t15_disjoint.py \
  jobs/run_lane_a_generation.sh \
  data/main_ext data/t18 data/t18_medical_expand \
  qc/main_ext_review.csv qc/iaa_sample.csv qc/iaa_guidelines.md scripts/iaa_kappa.py qc/t18_sample.csv \
  notes/main_ext_manifest.json notes/iaa_sample_manifest.json notes/t18_manifest.json \
  notes/main_ext_candidate_stats.json notes/lane_a_spend.json 2>/dev/null || true
if /usr/bin/git -C "${ROOT}" diff --cached --quiet; then
  echo "lane A: nothing to commit"
else
  /usr/bin/git -C "${ROOT}" commit -m "$(cat <<'EOF'
feat: Lane A v2 — Textbooks main_ext, Wikipedia T18, IAA 120

MedRAG Textbooks stage1 (Qwen72B+Phi-4), disjointness check, full INV QC; rename medical expand artifact; HF wiki T18; stratified blind IAA.

EOF
)"
  /usr/bin/git -C "${ROOT}" push origin master || true
fi
