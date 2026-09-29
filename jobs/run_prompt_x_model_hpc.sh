#!/usr/bin/env bash
# Prompt×model 2×2: gpt-4o×RAGAS, Sonnet×MedScore (≤$2).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_API_LEDGER=1
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-2}"
export MEDVERIF_OR_MIN_CREDIT=1.5

python3 scripts/build_prompt_x_model_instances.py
INST="${ROOT}/data/pxm/instances_e1evid_e2.jsonl"
RAW="${ROOT}/results/raw/pxm"
mkdir -p "${RAW}"
LOG="${ROOT}/jobs/logs/prompt_x_model_hpc_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "pxm start $(date -Is)"

python3 scripts/openrouter_budget.py || exit 2
export MEDVERIF_V4_OPENROUTER_MODEL=openai/gpt-4o
export MEDVERIF_V4_PROVIDER=OpenAI
export MEDVERIF_V4_TOKENIZER_MODEL=mistralai/Mistral-Small-24B-Instruct-2501
export MEDVERIF_V4_TOKENIZER_REVISION=9527884be6e5616bdd54de542f9ae13384489724
python3 src/score_jsonl.py --verifier v4_ragas_nli --instances "${INST}" \
  --out "${RAW}/pxm_gpt4o_ragas.jsonl"

python3 scripts/openrouter_budget.py || exit 2
export MEDVERIF_V1B_OPENROUTER_MODEL=anthropic/claude-sonnet-4.6
export MEDVERIF_V1B_PROVIDER=Anthropic
export MEDVERIF_V1B_TOKENIZER_MODEL=HuggingFaceH4/zephyr-7b-beta
python3 src/score_jsonl.py --verifier v1b_medscore --instances "${INST}" \
  --out "${RAW}/pxm_sonnet_medscore.jsonl"

python3 scripts/prompt_x_model_report.py
echo "pxm done $(date -Is)"
