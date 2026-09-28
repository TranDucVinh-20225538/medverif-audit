#!/usr/bin/env bash
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_OR_MIN_CREDIT=1.5
export T10_OR_BUDGET_USD=4
export T10_N_PASSAGES=40
LOG="${ROOT}/jobs/logs/t10_summaries_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
python3 scripts/openrouter_budget.py
python3 scripts/t10_generate_summaries_openrouter.py || true
python3 scripts/t10_build_hhem_inputs.py
python3 scripts/aggregate_api_cost.py || true
/usr/bin/git add data/t10 qc/t10_sample.csv notes/t10_or_summaries.json scripts/t10_generate_summaries_openrouter.py jobs/run_t10_summaries_openrouter.sh 2>/dev/null || true
/usr/bin/git diff --cached --quiet || /usr/bin/git commit -m "T10: OpenRouter Vectara-style summaries + HHEM inputs."
/usr/bin/git push origin master || true
