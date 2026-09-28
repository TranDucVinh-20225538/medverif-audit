#!/usr/bin/env bash
# T6-B zoo on T3 INV-family instances only.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
INST="${ROOT}/data/v3/instances_inv_families.jsonl"
[[ -s "${INST}" ]] || { echo "empty ${INST}"; exit 0; }
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock t3_t6b_score

cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_API_LEDGER=1
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-2}"
export MEDVERIF_T6B_BUDGET_USD="${MEDVERIF_T6B_BUDGET_USD:-10}"

RAW="${ROOT}/results/raw/t3_t6b"
mkdir -p "${RAW}"
LOG="${ROOT}/jobs/logs/t3_t6b_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "t3 t6b score start $(date -Is) n=$(wc -l < "${INST}")"

while IFS=$'\t' read -r slug module or_model provider; do
  python3 scripts/t6_budget.py || exit 2
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
models = json.loads(Path("/data2/hpcshared/medverif-audit/notes/t6_models.json").read_text())["t6b_openrouter"]
for m in models:
    print("\t".join([m["slug"], m["verifier_module"], m["openrouter_model"], m["provider"]]))
PY
)
echo "t3 t6b score done $(date -Is)"
