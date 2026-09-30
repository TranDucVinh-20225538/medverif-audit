#!/usr/bin/env bash
# Create cpuverif_legacy on login node (node30-aligned pins for SummaC/HHEM/Granite).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source /data2/shared/apps/conda/etc/profile.d/conda.sh

ENV_NAME="${MEDVERIF_LEGACY_CONDA:-cpuverif_legacy}"
if conda env list | awk '{print $1}' | grep -qx "${ENV_NAME}"; then
  echo "conda env ${ENV_NAME} already exists"
else
  conda create -y -n "${ENV_NAME}" python=3.10 pip
fi
conda activate "${ENV_NAME}"
export PIP_INDEX_URL=https://pypi.org/simple
export PIP_EXTRA_INDEX_URL=
pip install -U pip wheel
pip install -r "${ROOT}/notes/cpuverif_legacy-pip.txt"
python -c "import transformers, torch, summac, sentencepiece; print('ok', transformers.__version__, torch.__version__)"

cd "${ROOT}"
export PYTHONPATH="${ROOT}/src:${ROOT}/analysis:${ROOT}/scripts"
export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export MEDVERIF_LANE_B_ENV_PROFILE=legacy
python3 scripts/lane_b_record_env.py --legacy --reason setup_cpuverif_legacy
echo "Recorded $(cat notes/lane_b_env_legacy.json | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"env_id\"])')"
