#!/usr/bin/env bash
# T4c: OpenRouter LLM judges on sentence-level eco instances (budget cap).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_API_LEDGER=1
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-2}"
export MEDVERIF_OR_BUDGET_USD="${MEDVERIF_OR_BUDGET_USD:-2.0}"
export MEDVERIF_OR_MIN_CREDIT=1.5

python3 scripts/t4c_build_eco_instances.py
INST="${ROOT}/data/t4/eco_instances_t4c.jsonl"
RAW="${ROOT}/results/raw/t4c_eco"
mkdir -p "${RAW}"
LOG="${ROOT}/jobs/logs/t4c_eco_hpc_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "t4c hpc start $(date -Is) budget=${MEDVERIF_OR_BUDGET_USD}"

for v in v1b_medscore v5_ragas_nli v4_ragas_nli v1c_medscore; do
  python3 scripts/openrouter_budget.py || exit 2
  python3 src/score_jsonl.py --verifier "${v}" --instances "${INST}" --out "${RAW}/${v}.jsonl"
done

export MEDVERIF_V6_VERIFIER_SLUG=v6_ragas_nli
export MEDVERIF_V6_OPENROUTER_MODEL="${MEDVERIF_V6_OPENROUTER_MODEL:-openai/gpt-4o-mini}"
export MEDVERIF_V6_PROVIDER="${MEDVERIF_V6_PROVIDER:-OpenAI}"
python3 scripts/openrouter_budget.py || exit 2
python3 src/score_jsonl.py --verifier v6_ragas_nli --instances "${INST}" --out "${RAW}/v6_ragas_nli.jsonl"

python3 scripts/t4c_eco_report.py
echo "t4c hpc done $(date -Is)"
