#!/usr/bin/env bash
# Download 1–2 parquet shards of wikimedia/wikipedia 20231101.en for local T18 filter (no streaming).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
DEST="${ROOT}/.cache/huggingface/wikipedia_20231101.en_parquet"
mkdir -p "${DEST}"

source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate cpuverif

python3 <<'PY'
from huggingface_hub import hf_hub_download
import shutil
from pathlib import Path

repo = "wikimedia/wikipedia"
revision = "20231101.en"
dest = Path("/data2/hpcshared/medverif-audit/.cache/huggingface/wikipedia_20231101.en_parquet")
dest.mkdir(parents=True, exist_ok=True)
for i in (0, 1):
    name = f"train-{i:05d}-of-00041.parquet"
    p = hf_hub_download(repo_id=repo, repo_type="dataset", filename=name, revision=revision)
    target = dest / name
    if not target.exists() or target.stat().st_size != Path(p).stat().st_size:
        shutil.copy2(p, target)
    print("ok", target, target.stat().st_size)
PY

echo "T18 parquet shards ready under ${DEST}"
