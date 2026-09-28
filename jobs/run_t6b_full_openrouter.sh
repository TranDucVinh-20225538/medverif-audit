#!/usr/bin/env bash
# T6-B full zoo on instances_t6_scope.jsonl (cap $10). Inflight 2; lock t6b_full.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
if [[ -f "${ROOT}/notes/pause_t6_openrouter" ]]; then
  echo "paused: notes/pause_t6_openrouter"
  exit 3
fi
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock t6b_full

cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_API_LEDGER=1
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-2}"
export MEDVERIF_OR_MIN_CREDIT="${MEDVERIF_OR_MIN_CREDIT:-2}"
export MEDVERIF_T6B_BUDGET_USD="${MEDVERIF_T6B_BUDGET_USD:-10}"

LOG="${ROOT}/jobs/logs/t6b_full_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "t6b full start $(date -Is)"

python3 scripts/build_t6_scope.py
python3 scripts/openrouter_budget.py || exit 2
python3 scripts/t6_budget.py || exit 2

SCOPE="${ROOT}/data/v3/instances_t6_scope.jsonl"
RAW="${ROOT}/results/raw/t6b/full"
mkdir -p "${RAW}"

while IFS=$'\t' read -r slug module or_model provider; do
  echo "=== ${slug} ==="
  python3 scripts/openrouter_budget.py || exit 2
  python3 scripts/t6_budget.py || exit 2
  export MEDVERIF_V6_VERIFIER_SLUG="${slug}"
  export MEDVERIF_V6_OPENROUTER_MODEL="${or_model}"
  export MEDVERIF_V6_PROVIDER="${provider}"
  export MEDVERIF_V1C_OPENROUTER_MODEL="${or_model}"
  export MEDVERIF_V1C_PROVIDER="${provider}"
  python3 src/score_jsonl.py --verifier "${module}" --instances "${SCOPE}" \
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

python3 scripts/t6_budget.py
echo "t6b full done $(date -Is)"
