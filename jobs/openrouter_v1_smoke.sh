#!/usr/bin/env bash
# Smoke 5 instances — requires OPENROUTER_API_KEY and MEDVERIF_OPENROUTER_PROVIDER (recommended).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
python src/score_jsonl.py --verifier v1_medscore \
  --instances tests/smoke_v1_all.jsonl \
  --out tests/smoke_results/v1_medscore_openrouter.jsonl \
  --limit 5
