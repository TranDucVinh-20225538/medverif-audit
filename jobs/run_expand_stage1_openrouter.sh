#!/usr/bin/env bash
# Expansion Stage-1: OpenRouter Qwen-72B + Phi-4 validator (POL then DOSE). Resumable.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
# shellcheck source=jobs/lib/flock.sh
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock expand_stage1

cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src:${ROOT}/scripts/expand"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_API_LEDGER=1
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-2}"
export MEDVERIF_OR_MIN_CREDIT="${MEDVERIF_OR_MIN_CREDIT:-2}"
export MEDVERIF_EXPAND_GEN_MODEL="${MEDVERIF_EXPAND_GEN_MODEL:-qwen/qwen-2.5-72b-instruct}"
export MEDVERIF_EXPAND_VAL_MODEL="${MEDVERIF_EXPAND_VAL_MODEL:-microsoft/phi-4}"
export MEDVERIF_EXPAND_GEN_PROVIDER="${MEDVERIF_EXPAND_GEN_PROVIDER:-${MEDVERIF_V1_PROVIDER:-DeepInfra}}"

LOG="${ROOT}/jobs/logs/expand_stage1_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "expand stage1 start $(date -Is)"

rm -f "${ROOT}/notes/pause_expand_openrouter"

python3 scripts/openrouter_budget.py || { echo "global credit stop"; exit 2; }
python3 scripts/expand/expand_budget.py || { echo "expand budget stop"; exit 2; }

python3 src/stage12_openrouter.py \
  --candidates "${ROOT}/data/expand/candidates_selected.jsonl" \
  --outdir "${ROOT}/data/expand/stage1" \
  --template-note "${ROOT}/notes/expand_chat_template.md"

bash "${ROOT}/jobs/run_expand_post_stage1.sh"
echo "expand stage1 pipeline done $(date -Is)"
