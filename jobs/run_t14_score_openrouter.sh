#!/usr/bin/env bash
# T14 repr: V1, V4, V1b, V5 + T6-B (v6_*); budget ≤ USD 3 — run after PI review if desired.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock t14_or_score

cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_API_LEDGER=1
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-2}"
export MEDVERIF_T14_BUDGET_USD="${MEDVERIF_T14_BUDGET_USD:-3}"

python3 scripts/build_t14_score_pending.py
INST="${ROOT}/data/t14/instances_t14_pending_openrouter.jsonl"
OUT="${ROOT}/results/raw/t14"
mkdir -p "${OUT}"
LOG="${ROOT}/jobs/logs/t14_or_score_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "t14 or score start $(date -Is)"

for v in v1_medscore v4_ragas_nli v1b_medscore v5_ragas_nli; do
  python3 scripts/t14_openrouter_budget.py || exit 2
  python3 scripts/dedupe_score_jsonl.py "${OUT}/${v}.jsonl" --verifier "${v}" || true
  python3 src/score_jsonl.py --verifier "${v}" --instances "${INST}" --out "${OUT}/${v}.jsonl"
done

while IFS=$'\t' read -r slug module or_model provider; do
  echo "=== ${slug} ==="
  python3 scripts/t14_openrouter_budget.py || exit 2
  python3 scripts/dedupe_score_jsonl.py "${OUT}/${slug}.jsonl" --verifier "${slug}" || true
  export MEDVERIF_V6_VERIFIER_SLUG="${slug}"
  export MEDVERIF_V6_OPENROUTER_MODEL="${or_model}"
  export MEDVERIF_V6_PROVIDER="${provider}"
  python3 src/score_jsonl.py --verifier "${module}" --instances "${INST}" --out "${OUT}/${slug}.jsonl"
done < <(python3 - <<'PY'
import json
from pathlib import Path
ROOT = Path("/data2/hpcshared/medverif-audit")
models = json.loads((ROOT / "notes/t6_models.json").read_text())["t6b_openrouter"]
for m in models:
    print("\t".join([m["slug"], m["verifier_module"], m["openrouter_model"], m["provider"]]))
PY
)

python3 scripts/t14_c0_conditional_report.py
python3 scripts/t14_openrouter_budget.py
echo "t14 or score done $(date -Is)"
