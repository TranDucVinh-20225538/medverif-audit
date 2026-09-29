#!/usr/bin/env bash
set -euo pipefail
ROOT="${MEDVERIF_ROOT:-/root/medverif-audit}"
V9="${ROOT}/.venv_t9_alignscore"
python3.10 -m venv "${V9}"
"${V9}/bin/pip" install -U pip wheel 'setuptools==69.5.1'
"${V9}/bin/pip" install \
  torch pytorch-lightning 'transformers==4.30.2' 'tokenizers==0.13.3' \
  'spacy==3.5.4' 'pydantic>=1.10,<2' 'fastapi==0.95.2' uvicorn typer nltk numpy scikit-learn scipy
"${V9}/bin/pip" install -e "${ROOT}/.cache/src/AlignScore"
"${V9}/bin/python" -m spacy download en_core_web_sm
echo "OK: ${V9}"
