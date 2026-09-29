#!/usr/bin/env bash
# Lane C: M1 before/after API scoring on main H2 pack (cap $3; night total ≤ $10).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock lane_c_m1_h2

cd "${ROOT}"
LOG="${ROOT}/jobs/logs/lane_c_m1_h2_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "lane C start $(date -Is)"

set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_M1=1
export MEDVERIF_GPU_GLOBAL_SCORE_LOCK=0
export MEDVERIF_API_LEDGER=1
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-2}"
export MEDVERIF_OR_MIN_CREDIT="${MEDVERIF_OR_MIN_CREDIT:-2}"
export MEDVERIF_LANE_C_CAP_USD="${MEDVERIF_LANE_C_CAP_USD:-3}"
export MEDVERIF_OR_NIGHT_CAP_USD="${MEDVERIF_OR_NIGHT_CAP_USD:-10}"

python3 scripts/openrouter_budget.py
python3 scripts/lane_or_night_budget.py
python3 scripts/lane_c_build_m1_pack.py

INST="${ROOT}/data/lane_c/m1_h2_main.jsonl"
OUT="${ROOT}/results/raw_m1/lane_c"
mkdir -p "${OUT}"
LEDGER="${ROOT}/notes/lane_c_or_spend.json"
echo "{\"started\": \"$(date -Is)\"}" > "${LEDGER}"

score_one() {
  local v="$1"
  python3 scripts/lane_or_night_budget.py
  python3 scripts/openrouter_budget.py || return 2
  python3 src/score_jsonl.py --verifier "${v}" --instances "${INST}" --out "${OUT}/${v}.jsonl"
}

# V4: verifier_registry pins meta-llama/llama-3.3-70b-instruct (not Qwen3-14B yaml default).
for v in v1_medscore v1b_medscore v1c_medscore v4_ragas_nli; do
  echo "=== ${v} === $(date -Is)"
  score_one "${v}" || break
done

if ! python3 scripts/openrouter_pause_before_expensive.py --min-usd 3; then
  echo "PAUSE: OR balance below \$3 — skipping v5/v6 (report in log; re-run later)"
  python3 scripts/openrouter_pause_before_expensive.py --min-usd 3 || true
  exit 0
fi

for v in v5_ragas_nli v6_ragas_gpt4o_mini v6_ragas_haiku45 v6_ragas_llama31_8b v6_ragas_mistral_small32; do
  echo "=== ${v} === $(date -Is)"
  score_one "${v}" || break
done

python3 scripts/lane_c_m1_repair_report.py
python3 scripts/lane_or_night_budget.py > "${ROOT}/notes/lane_c_or_spend_final.json"
echo "lane C done $(date -Is)"

/usr/bin/git -C "${ROOT}" add \
  scripts/lane_c_build_m1_pack.py \
  scripts/lane_c_m1_repair_report.py \
  scripts/lane_or_night_budget.py \
  jobs/run_lane_c_m1_h2.sh \
  data/lane_c \
  notes/lane_c_m1_pack.json \
  notes/m1_repair_after_norm.md \
  notes/lane_c_or_spend.json \
  notes/lane_c_or_spend_final.json \
  results/raw_m1/lane_c 2>/dev/null || true
if /usr/bin/git -C "${ROOT}" diff --cached --quiet; then
  echo "lane C: nothing to commit"
else
  /usr/bin/git -C "${ROOT}" commit -m "$(cat <<'EOF'
feat: Lane C M1 H2 API rescore on main pack (partial/full)

OpenRouter M1=1 scores for V1/V1b/V1c/V4/V5/V6 judges; repair-after-norm notes.

EOF
)"
  /usr/bin/git -C "${ROOT}" push origin master || true
fi
