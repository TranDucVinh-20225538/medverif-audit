#!/usr/bin/env bash
# T17 down-dose: HPC OpenRouter verifiers (budget ≤ USD 5).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source "${ROOT}/jobs/lib/flock.sh"
source "${ROOT}/jobs/lib/hf_env.sh"
medverif_acquire_lock t17_hpc_score

cd "${ROOT}"
medverif_hf_env
set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_API_LEDGER=1
export MEDVERIF_GPU_GLOBAL_SCORE_LOCK=0
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-2}"
export MEDVERIF_T17_BUDGET_USD="${MEDVERIF_T17_BUDGET_USD:-5}"

INST="${ROOT}/data/v3/t17_downdose.jsonl"
RAW="${ROOT}/results/raw/t17"
mkdir -p "${RAW}"
LOG="${ROOT}/jobs/logs/t17_hpc_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "t17 hpc score start $(date -Is)"

for v in v1_medscore v4_ragas_nli v1b_medscore v5_ragas_nli; do
  python3 scripts/t17_openrouter_budget.py || exit 2
  python3 scripts/dedupe_score_jsonl.py "${RAW}/${v}.jsonl" --verifier "${v}" 2>/dev/null || true
  python3 src/score_jsonl.py --verifier "${v}" --instances "${INST}" --out "${RAW}/${v}.jsonl" || {
    echo "t17: verifier ${v} failed $(date -Is)" >&2
    exit 1
  }
done

while IFS=$'\t' read -r slug module or_model provider; do
  echo "=== ${slug} ==="
  python3 scripts/t17_openrouter_budget.py || exit 2
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

python3 scripts/t17_openrouter_budget.py
echo "t17 hpc score done $(date -Is)"
