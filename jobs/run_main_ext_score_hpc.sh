#!/usr/bin/env bash
# main_ext: OpenRouter verifiers after PI filters ($2 cap).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock main_ext_or_score

cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_API_LEDGER=1
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-2}"
export MEDVERIF_MAIN_EXT_BUDGET_USD="${MEDVERIF_MAIN_EXT_BUDGET_USD:-2}"

INST="${ROOT}/data/main_ext/instances_main_ext.jsonl"
RAW="${ROOT}/results/raw/main_ext"
mkdir -p "${RAW}"
LOG="${ROOT}/jobs/logs/main_ext_or_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "main_ext OR score start $(date -Is) n=$(python3 -c "import json; print(sum(1 for l in open('${INST}') if json.loads(l).get('valid',True)))")"

python3 scripts/openrouter_budget.py || exit 2

for v in v1_medscore v4_ragas_nli; do
  python3 scripts/openrouter_budget.py || exit 2
  python3 src/score_jsonl.py --verifier "${v}" --instances "${INST}" --out "${RAW}/${v}.jsonl"
done

python3 scripts/aggregate_api_cost.py 2>/dev/null || true
echo "main_ext OR score done $(date -Is)"
