#!/usr/bin/env bash
# Journal 4: frontier API LLMs (OpenAI / Anthropic / Gemini) as RAGAS-NLI fact-check judges on the 1451 real-dose answers.
# For every provider whose API key is set: smoke (10 rows, <= $1) -> sanity gate -> full subset -> report.
# Runs anywhere with internet egress (Mac, HPC LOGIN node; compute nodes are offline).  No GPU.  Resumable: re-run the same
# command after an interruption and finished rows are skipped (results/journal4/frontier/<model>.jsonl).
#
#   bash jobs/run_frontier_rd.sh                          # smoke + full (--subset all) for each provider with a key
#   bash jobs/run_frontier_rd.sh --smoke-only             # only the 10-row smoke per provider
#   bash jobs/run_frontier_rd.sh --dry-run                # cost estimates only, no API call
#   bash jobs/run_frontier_rd.sh --subset adjudicable     # skip the 249 not-adjudicable rows (~17% cheaper)
#   bash jobs/run_frontier_rd.sh --providers openai,gemini --with-card
# Env: OPENAI_API_KEY / ANTHROPIC_API_KEY / GEMINI_API_KEY (keys are never echoed)
#      PY (default python3), OPENAI_MODEL / ANTHROPIC_MODEL / GEMINI_MODEL (default: script defaults),
#      MAX_USD_OPENAI (75) / MAX_USD_ANTHROPIC (35) / MAX_USD_GEMINI (20)  = hard caps for the full run per model,
#      CONCURRENCY (4), EFFORT (low), FORCE=1 to continue to the full run even if the smoke gate fails.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"
PY="${PY:-python3}"
S=scripts/journal4/frontier_judges_rd.py
SUBSET=all; SMOKE_ONLY=0; DRY=0; CARD=0; PROVIDERS="openai,anthropic,gemini"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --smoke-only) SMOKE_ONLY=1 ;;
    --dry-run) DRY=1 ;;
    --subset) SUBSET="$2"; shift ;;
    --providers) PROVIDERS="$2"; shift ;;
    --with-card) CARD=1 ;;
    *) echo "unknown arg $1" >&2; exit 1 ;;
  esac; shift
done
"${PY}" -c 'import sys, pydantic, numpy; assert sys.version_info >= (3, 8); assert pydantic.VERSION.startswith("2")' 2>/dev/null || {
  echo "need python>=3.8 with pydantic>=2 and numpy:  ${PY} -m pip install --user 'pydantic>=2' numpy" >&2; exit 2; }

declare -A KEYVAR=([openai]=OPENAI_API_KEY [anthropic]=ANTHROPIC_API_KEY [gemini]=GEMINI_API_KEY)
declare -A MODEL=([openai]="${OPENAI_MODEL:-}" [anthropic]="${ANTHROPIC_MODEL:-}" [gemini]="${GEMINI_MODEL:-}")
declare -A CAP=([openai]="${MAX_USD_OPENAI:-75}" [anthropic]="${MAX_USD_ANTHROPIC:-35}" [gemini]="${MAX_USD_GEMINI:-20}")
COMMON=(--concurrency "${CONCURRENCY:-4}" --effort "${EFFORT:-low}")

has_key() {  # has_key provider  (gemini also accepts GOOGLE_API_KEY)
  local v="${KEYVAR[$1]}"
  [[ -n "${!v:-}" ]] && return 0
  [[ "$1" == gemini && -n "${GOOGLE_API_KEY:-}" ]] && return 0
  return 1
}
margs() { [[ -n "${MODEL[$1]}" ]] && echo "--model ${MODEL[$1]}"; }

smoke_gate() {  # smoke_gate provider -> 0 if the smoke run looks sane (<=3/10 strict parse fails, no truncation, 10 rows)
  "${PY}" - "$1" "${MODEL[$1]}" <<'PYEOF'
import json, sys
sys.path.insert(0, "scripts/journal4")
import frontier_judges_rd as f
prov, model = sys.argv[1], sys.argv[2] or f.PROVIDERS[sys.argv[1]]["model"]
ids = {r["instance_id"] for r in f.select_rows("rd", "smoke")}
recs = [r for r in f.read_jsonl(f.OUT_DIR / (f.slugify(model) + ".jsonl")) if r["instance_id"] in ids]
pf = sum(r["verdict"] == "PARSE_FAIL" for r in recs); tr = sum(bool(r.get("incomplete")) for r in recs)
cost = sum(r.get("cost_usd") or 0 for r in recs)
print("smoke gate %s: rows %d/10, strict parse fails %d, truncated %d, cost $%.4f, temperature sent %s"
      % (model, len(recs), pf, tr, cost, sorted({str(r.get("temperature_sent")) for r in recs})))
sys.exit(0 if len(recs) == len(ids) and pf <= 3 and tr == 0 else 1)
PYEOF
}

ran=()
for p in ${PROVIDERS//,/ }; do
  if ! has_key "$p"; then echo "== ${p}: ${KEYVAR[$p]} not set -> skipped"; continue; fi
  echo "== ${p}: estimates"
  "${PY}" "${S}" --provider "$p" $(margs "$p") --subset smoke --dry-run "${COMMON[@]}" | grep '"stage": "plan"'
  "${PY}" "${S}" --provider "$p" $(margs "$p") --subset "${SUBSET}" --dry-run "${COMMON[@]}" | grep '"stage": "plan"'
  [[ ${DRY} -eq 1 ]] && continue
  echo "== ${p}: smoke (10 rows, cap \$1)"
  if ! "${PY}" "${S}" --provider "$p" $(margs "$p") --subset smoke --max-usd 1 --yes "${COMMON[@]}"; then
    echo "== ${p}: smoke run FAILED (see errors above) -> not running the full set" >&2; continue
  fi
  if ! smoke_gate "$p"; then
    if [[ "${FORCE:-0}" != 1 ]]; then
      echo "== ${p}: smoke gate failed (parse fails / truncation). Inspect results/journal4/frontier/report_rd_smoke.md;" \
           "raise --max-output-tokens or change --effort, or FORCE=1 to continue" >&2; continue
    fi
    echo "== ${p}: smoke gate failed but FORCE=1 -> continuing"
  fi
  ran+=("$p")
  [[ ${SMOKE_ONLY} -eq 1 ]] && continue
  echo "== ${p}: full --subset ${SUBSET} (hard cap \$${CAP[$p]})"
  "${PY}" "${S}" --provider "$p" $(margs "$p") --subset "${SUBSET}" --max-usd "${CAP[$p]}" --yes "${COMMON[@]}" \
    || echo "== ${p}: full run stopped early (budget/errors); re-run the same command to resume" >&2
  if [[ ${CARD} -eq 1 ]]; then
    echo "== ${p}: frozen DOSE card (958 rows)"
    "${PY}" "${S}" --provider "$p" $(margs "$p") --pack card --subset all --max-usd "${CAP[$p]}" --yes "${COMMON[@]}" \
      || echo "== ${p}: card run stopped early" >&2
  fi
done
[[ ${DRY} -eq 1 ]] && exit 0
echo "== reports (all frontier models found in results/journal4/frontier)"
"${PY}" "${S}" --report-only --subset smoke --boot 2000
[[ ${SMOKE_ONLY} -eq 1 ]] || "${PY}" "${S}" --report-only --subset "${SUBSET}" --boot 10000
[[ ${CARD} -eq 1 && ${SMOKE_ONLY} -eq 0 ]] && "${PY}" "${S}" --report-only --pack card --subset all --boot 10000
echo "providers run: ${ran[*]:-none}.  Reports: results/journal4/frontier/report_rd_*.md"
