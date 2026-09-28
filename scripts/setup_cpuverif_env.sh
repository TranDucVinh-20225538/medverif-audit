#!/usr/bin/env bash
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source /data2/shared/apps/conda/etc/profile.d/conda.sh
if conda env list | awk '{print $1}' | grep -qx cpuverif; then
  echo "cpuverif exists"
else
  conda create -n cpuverif python=3.11 -y
fi
conda activate cpuverif
pip install -q --upgrade pip
pip install -q torch --index-url https://download.pytorch.org/whl/cpu
pip install -q transformers pytorch-lightning scikit-learn nltk spacy huggingface_hub
python -m spacy download en_core_web_sm
pip install -q -e "${ROOT}/.cache/src/MiniCheck" 2>/dev/null || true
python - <<'PY'
import json, subprocess, sys
from pathlib import Path
root = Path("/data2/hpcshared/medverif-audit")
vers = {}
for mod in ("torch", "transformers", "spacy", "sklearn", "pytorch_lightning"):
    m = __import__(mod)
    vers[mod] = getattr(m, "__version__", "?")
note = root / "notes" / "cpuverif_versions.json"
note.write_text(json.dumps(vers, indent=2) + "\n")
print(json.dumps(vers))
PY
echo "cpuverif ready"
