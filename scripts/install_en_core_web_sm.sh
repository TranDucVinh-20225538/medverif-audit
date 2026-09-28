#!/usr/bin/env bash
# Install spaCy en_core_web_sm for AlignScore (__init__ requires it; nli_sp scoring uses NLTK in inference_per_example).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
python -m spacy download en_core_web_sm
python -c "import spacy; nlp=spacy.load('en_core_web_sm'); print('ok', nlp.meta['name'])"
