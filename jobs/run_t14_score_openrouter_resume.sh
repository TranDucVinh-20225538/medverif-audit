#!/usr/bin/env bash
# T14: finish v1b, v5, v6×4, v1c (skip complete v1/v4).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source "${ROOT}/jobs/lib/flock.sh"
source "${ROOT}/jobs/lib/hf_env.sh"
medverif_acquire_lock t14_or_score

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
export MEDVERIF_T14_BUDGET_USD="${MEDVERIF_T14_BUDGET_USD:-2}"
export MEDVERIF_OR_TASK_CAP_USD="${MEDVERIF_T14_BUDGET_USD}"

python3 scripts/build_t14_score_pending.py
INST="${ROOT}/data/t14/instances_t14_pending_openrouter.jsonl"
OUT="${ROOT}/results/raw/t14"
mkdir -p "${OUT}"
LOG="${ROOT}/jobs/logs/t14_or_resume_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "t14 or resume start $(date -Is)"

python3 - <<'PY'
import json, sys
sys.path.insert(0, "scripts")
from t14_openrouter_budget import write_baseline
print(json.dumps(write_baseline()))
PY
python3 scripts/openrouter_budget.py

for v in v1b_medscore v5_ragas_nli; do
  python3 scripts/t14_openrouter_budget.py || exit 2
  python3 scripts/openrouter_budget.py || exit 2
  python3 scripts/dedupe_score_jsonl.py "${OUT}/${v}.jsonl" --verifier "${v}" || true
  python3 src/score_jsonl.py --verifier "${v}" --instances "${INST}" --out "${OUT}/${v}.jsonl"
done

while IFS=$'\t' read -r slug module or_model provider; do
  echo "=== ${slug} ==="
  python3 scripts/t14_openrouter_budget.py || exit 2
  python3 scripts/openrouter_budget.py || exit 2
  export MEDVERIF_V6_VERIFIER_SLUG="${slug}"
  export MEDVERIF_V6_OPENROUTER_MODEL="${or_model}"
  export MEDVERIF_V6_PROVIDER="${provider}"
  export MEDVERIF_V1C_OPENROUTER_MODEL="${or_model}"
  export MEDVERIF_V1C_PROVIDER="${provider}"
  python3 scripts/dedupe_score_jsonl.py "${OUT}/${slug}.jsonl" --verifier "${slug}" || true
  python3 src/score_jsonl.py --verifier "${module}" --instances "${INST}" --out "${OUT}/${slug}.jsonl"
done < <(python3 - <<'PY'
import json
from pathlib import Path
models = json.loads(Path("/data2/hpcshared/medverif-audit/notes/t6_models.json").read_text())["t6b_openrouter"]
for m in models:
    print("\t".join([m["slug"], m["verifier_module"], m["openrouter_model"], m["provider"]]))
PY
)

python3 scripts/t14_c0_conditional_report.py
python3 scripts/t14_openrouter_budget.py
echo "t14 or resume done $(date -Is)"
