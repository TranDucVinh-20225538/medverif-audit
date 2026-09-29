#!/usr/bin/env bash
# Backfill 247 main-dose ids (C0 + E1 + INV-unit) into t2_full / t6b/full encoders.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock main_dose_or_backfill

cd "${ROOT}"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_API_LEDGER=1
export MEDVERIF_GPU_GLOBAL_SCORE_LOCK=0
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-2}"
export MEDVERIF_OR_MIN_CREDIT="${MEDVERIF_OR_MIN_CREDIT:-1.0}"
export MEDVERIF_MAIN_DOSE_BACKFILL_CAP_USD="${MEDVERIF_MAIN_DOSE_BACKFILL_CAP_USD:-4}"
export MEDVERIF_OR_TASK_CAP_USD="${MEDVERIF_MAIN_DOSE_BACKFILL_CAP_USD}"

export MEDVERIF_V1B_OPENROUTER_MODEL="${MEDVERIF_V1B_OPENROUTER_MODEL:-openai/gpt-4o}"
export MEDVERIF_V1B_PROVIDER="${MEDVERIF_V1B_PROVIDER:-OpenAI}"
export MEDVERIF_V5_OPENROUTER_MODEL="${MEDVERIF_V5_OPENROUTER_MODEL:-anthropic/claude-sonnet-4.6}"
export MEDVERIF_V5_TOKENIZER_MODEL="${MEDVERIF_V5_TOKENIZER_MODEL:-HuggingFaceH4/zephyr-7b-beta}"
export MEDVERIF_V5_PROVIDER="${MEDVERIF_V5_PROVIDER:-Anthropic}"

INST="${ROOT}/data/v3/instances_main_dose_or_backfill.jsonl"
LOG="${ROOT}/jobs/logs/main_dose_or_backfill_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "main_dose OR backfill start $(date -Is)"

python3 scripts/build_main_dose_backfill_instances.py

T2="${ROOT}/results/raw/t2_full"
T6="${ROOT}/results/raw/t6b/full"
mkdir -p "${T2}" "${T6}"

for v in v1b_medscore v5_ragas_nli; do
  python3 scripts/main_dose_backfill_budget.py || exit 2
  python3 scripts/openrouter_budget.py || exit 2
  python3 scripts/dedupe_score_jsonl.py "${T2}/${v}.jsonl" --verifier "${v}" 2>/dev/null || true
  python3 src/score_jsonl.py --verifier "${v}" --instances "${INST}" --out "${T2}/${v}.jsonl"
  python3 scripts/main_dose_backfill_budget.py || true
done

while IFS=$'\t' read -r slug module or_model provider; do
  echo "=== ${slug} ==="
  python3 scripts/main_dose_backfill_budget.py || exit 2
  python3 scripts/openrouter_budget.py || exit 2
  export MEDVERIF_V6_VERIFIER_SLUG="${slug}"
  export MEDVERIF_V6_OPENROUTER_MODEL="${or_model}"
  export MEDVERIF_V6_PROVIDER="${provider}"
  export MEDVERIF_V1C_OPENROUTER_MODEL="${or_model}"
  export MEDVERIF_V1C_PROVIDER="${provider}"
  out="${T6}/${slug}.jsonl"
  python3 scripts/dedupe_score_jsonl.py "${out}" --verifier "${slug}" 2>/dev/null || true
  python3 src/score_jsonl.py --verifier "${module}" --instances "${INST}" --out "${out}"
  python3 scripts/main_dose_backfill_budget.py || true
done < <(python3 - <<'PY'
import json
from pathlib import Path
models = json.loads(Path("/data2/hpcshared/medverif-audit/notes/t6_models.json").read_text())["t6b_openrouter"]
for m in models:
    print("\t".join([m["slug"], m["verifier_module"], m["openrouter_model"], m["provider"]]))
PY
)

python3 scripts/aggregate_api_cost.py 2>/dev/null || true
python3 scripts/main_dose_backfill_budget.py || true
echo "main_dose OR backfill done $(date -Is)"
