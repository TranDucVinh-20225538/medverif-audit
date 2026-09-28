#!/usr/bin/env bash
# T8b: build supported sample, v1b score (≤$3), report. Encoders: run_t8b_aggrefact_node30.sh
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock t8b_aggrefact

cd "${ROOT}"
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_T8_BUDGET_USD="${MEDVERIF_T8B_BUDGET_USD:-3}"
export MEDVERIF_T8_BUDGET_SCOPE=t8b

if [[ ! -f "${ROOT}/data/t8/aggrefact/dev.jsonl" ]]; then
  set -a && source ~/kkk/openrouter.env && set +a
  python3 scripts/t8_download_aggrefact.py
fi

python3 scripts/t8b_build_supported_sample.py

INST="${ROOT}/data/t8/instances_aggrefact_t8b.jsonl"
RAW="${ROOT}/results/raw/t8"
mkdir -p "${RAW}"

set -a && source ~/kkk/openrouter.env && set +a
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_API_LEDGER=1
export MEDVERIF_V1B_PROVIDER=OpenAI
python3 scripts/t8_budget.py || exit 2
python3 src/score_jsonl.py --verifier v1b_medscore --instances "${INST}" --out "${RAW}/v1b_medscore_t8b.jsonl"

python3 scripts/t8b_report.py
echo "T8b v1b done — node30: jobs/run_t8b_aggrefact_node30.sh"
