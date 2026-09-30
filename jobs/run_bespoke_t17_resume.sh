#!/usr/bin/env bash
# Resume v2b_bespoke on t17_downdose only (missing rows).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
export PYTHONPATH="${ROOT}/src:${ROOT}/.cache/src/MiniCheck"
export MEDVERIF_GPU_GLOBAL_SCORE_LOCK=1
source "${ROOT}/jobs/lib/hf_env.sh"
medverif_hf_env
python3 src/score_jsonl.py --verifier v2b_bespoke \
  --instances "${ROOT}/data/v3/t17_downdose.jsonl" \
  --out "${ROOT}/results/raw/lane_b/t17_downdose/v2b_bespoke.jsonl"
