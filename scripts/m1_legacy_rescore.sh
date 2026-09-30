#!/usr/bin/env bash
# Rescore SummaC-ZS + Granite on M1 US_up and T17 down-dose only.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "$ROOT"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
export PYTHONPATH="${ROOT}/src:${ROOT}/analysis:${ROOT}/scripts"
export MEDVERIF_LEGACY_ONLY=1
"${CONDA_PREFIX}/bin/python3" scripts/m1_strong_score_missing.py
