#!/usr/bin/env bash
# E2-unit T7: V1, V4 Llama, V1b, V5, T6-B (budget cap $1.5).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_API_LEDGER=1
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-3}"
export MEDVERIF_OR_BUDGET_USD="${MEDVERIF_OR_BUDGET_USD:-1.5}"
export MEDVERIF_OR_MIN_CREDIT=0.5

python3 scripts/build_e2_unit_instances.py
INST="${ROOT}/data/e2/instances_e2_unit_t7.jsonl"
RAW="${ROOT}/results/raw/e2_unit"
mkdir -p "${RAW}"
LOG="${ROOT}/jobs/logs/e2_unit_hpc_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "e2 unit hpc start $(date -Is)"

for v in v1_medscore v4_ragas_nli v1b_medscore v5_ragas_nli; do
  python3 scripts/openrouter_budget.py || exit 2
  out="${RAW}/${v}.jsonl"
  if [[ "${v}" == "v4_ragas_nli" ]]; then
    out="${RAW}/${v}.llama.jsonl"
  fi
  python3 src/score_jsonl.py --verifier "${v}" --instances "${INST}" --out "${out}"
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

python3 scripts/e2_unit_comparison_report.py
echo "e2 unit hpc done $(date -Is)"
