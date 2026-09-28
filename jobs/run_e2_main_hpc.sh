#!/usr/bin/env bash
# E2 x2 main: V1b, V5, five T6-B OpenRouter judges (budget cap $4).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_API_LEDGER=1
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-3}"
export MEDVERIF_OR_BUDGET_USD="${MEDVERIF_OR_BUDGET_USD:-4.0}"
export MEDVERIF_OR_MIN_CREDIT=1.5
export MEDVERIF_V1B_OPENROUTER_MODEL="${MEDVERIF_V1B_OPENROUTER_MODEL:-openai/gpt-4o}"
export MEDVERIF_V1B_PROVIDER="${MEDVERIF_V1B_PROVIDER:-OpenAI}"

python3 scripts/build_e2_main_instances.py
INST="${ROOT}/data/e2/instances_main_x2.jsonl"
RAW="${ROOT}/results/raw/e2_main"
mkdir -p "${RAW}"
LOG="${ROOT}/jobs/logs/e2_main_hpc_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "e2 main hpc start $(date -Is)"

for v in v1b_medscore v5_ragas_nli; do
  python3 scripts/openrouter_budget.py || exit 2
  python3 src/score_jsonl.py --verifier "${v}" --instances "${INST}" --out "${RAW}/${v}.jsonl"
done

while IFS=$'\t' read -r slug module or_model provider; do
  python3 scripts/openrouter_budget.py || exit 2
  export MEDVERIF_V6_VERIFIER_SLUG="${slug}"
  export MEDVERIF_V6_OPENROUTER_MODEL="${or_model}"
  export MEDVERIF_V6_PROVIDER="${provider}"
  export MEDVERIF_V1C_OPENROUTER_MODEL="${or_model}"
  export MEDVERIF_V1C_PROVIDER="${provider}"
  python3 src/score_jsonl.py --verifier "${module}" --instances "${INST}" \
    --out "${RAW}/${slug}.jsonl"
done < <(python3 - <<'PY'
import json
from pathlib import Path
ROOT = Path("/data2/hpcshared/medverif-audit")
models = json.loads((ROOT / "notes/t6_models.json").read_text())["t6b_openrouter"]
for m in models:
    print("\t".join([m["slug"], m["verifier_module"], m["openrouter_model"], m["provider"]]))
PY
)

python3 scripts/e2_t7_comparison_report.py
echo "e2 main hpc done $(date -Is)"
