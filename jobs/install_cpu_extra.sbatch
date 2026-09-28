#!/bin/bash
#SBATCH --job-name=medverif-cpu-deps
#SBATCH --partition=defq
#SBATCH --exclude=node001
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/%x-%j.out

set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
TARGET="${ROOT}/.cache/cpu_extra"
export MAKEFLAGS=-j1
export MAX_JOBS=1
export PIP_NO_BUILD_ISOLATION=0
PY=/data2/cmdir/home/toandq/.conda/envs/vllm/bin/pip
mkdir -p "${ROOT}/jobs/logs" "${TARGET}"
cd "${ROOT}"
if "${PY}" show spacy >/dev/null 2>&1; then
  echo "spacy already in env; installing to ${TARGET} only"
fi
"${PY}" install --target="${TARGET}" --no-cache-dir 'spacy>=3.7,<3.8'
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
export PYTHONPATH="${ROOT}/src:${TARGET}:${ROOT}/.cache/src/MiniCheck:${ROOT}/.cache/src/AlignScore/src"
python -c "import nltk, spacy; from alignscore.alignscore import AlignScore; print('cpu_extra_ok')"
echo "install_cpu_extra done $(date -Is)"
