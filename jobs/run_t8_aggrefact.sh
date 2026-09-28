#!/usr/bin/env bash
# T8: audit stats, ~200 INV sample, v1b score (budget ≤$5 OR). HF cache must exist.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock t8_aggrefact

cd "${ROOT}"
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_T8_BUDGET_USD="${MEDVERIF_T8_BUDGET_USD:-3}"

LOG="${ROOT}/jobs/logs/t8_aggrefact_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "t8 start $(date -Is)"

if [[ ! -f "${ROOT}/data/t8/aggrefact/dev.jsonl" ]]; then
  set -a && source ~/kkk/openrouter.env && set +a
  python3 scripts/t8_download_aggrefact.py
fi

python3 scripts/t8_aggrefact_analysis.py --splits dev,test
python3 scripts/t8_build_aggrefact_inv_sample.py

INST="${ROOT}/data/t8/instances_aggrefact_inv.jsonl"
RAW="${ROOT}/results/raw/t8"
mkdir -p "${RAW}"

set -a && source ~/kkk/openrouter.env && set +a
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_API_LEDGER=1
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-2}"
export MEDVERIF_V1B_OPENROUTER_MODEL="${MEDVERIF_V1B_OPENROUTER_MODEL:-openai/gpt-4o}"
export MEDVERIF_V1B_PROVIDER="${MEDVERIF_V1B_PROVIDER:-OpenAI}"

echo "t8 score start $(date -Is)"
python3 scripts/openrouter_budget.py || exit 2
python3 scripts/t8_budget.py || exit 2
python3 src/score_jsonl.py --verifier v1b_medscore --instances "${INST}" --out "${RAW}/v1b_medscore.jsonl"

python3 scripts/t8_aggrefact_inv_report.py
echo "t8 done $(date -Is) — node30: jobs/run_t8_aggrefact_node30.sh"
