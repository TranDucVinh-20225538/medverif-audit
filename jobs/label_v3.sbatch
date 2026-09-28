#!/bin/bash
#SBATCH --job-name=medverif-v3
#SBATCH --partition=defq
#SBATCH --exclude=node001,node002
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --cpus-per-task=8
#SBATCH --time=03:00:00
#SBATCH --open-mode=append
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/%x-%j.out

set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
mkdir -p jobs/logs

resubmit() {
  local why="$1"
  local n
  n=$(cat jobs/logs/v3.count 2>/dev/null || echo 0)
  echo "RESUBMIT ${why} count=${n} host=$(hostname) mem_kb=$(grep MemAvailable /proc/meminfo | awk '{print $2}') time=$(date -Is)"
  if [ "${n}" -ge 4 ]; then
    echo "BLOCKER v3 resubmit cap" >&2
    exit 1
  fi
  echo $((n + 1)) > jobs/logs/v3.count
  sbatch --begin=now+15minutes "${ROOT}/jobs/label_v3.sbatch"
  exit 0
}

mem_kb=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
echo "host=$(hostname) MemAvailable_kB=${mem_kb} time=$(date -Is)"
if [ "${mem_kb}" -lt 40000000 ]; then
  resubmit "low_host_ram"
fi

export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export VLLM_CACHE_ROOT="${ROOT}/.cache/vllm"
export HF_HUB_DISABLE_TELEMETRY=1
export HF_HUB_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
export PYTHONPATH="${ROOT}/src"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
python -u src/generate_v3.py
echo "v3 labels done $(date -Is)"
# Stage 3 only if V1 weights are already complete. Do not start a download here.
if python - << 'PY'
import json
from pathlib import Path
root = Path("/data2/hpcshared/medverif-audit/.cache/huggingface/hub")
snaps = list(root.glob("models--mistralai--Mistral-Small-24B-Instruct-2501/snapshots/*"))
if not snaps:
    raise SystemExit(1)
snap = snaps[0]
index = json.loads((snap / "model.safetensors.index.json").read_text())
wanted = sorted({name for name in index["weight_map"].values() if name.endswith(".safetensors")})
for name in wanted:
    path = snap / name
    if not path.is_file():
        raise SystemExit(1)
    with path.open("rb") as handle:
        n = int.from_bytes(handle.read(8), "little")
    if not (8 < n < 50_000_000):
        raise SystemExit(1)
print("v1 ready", len(wanted))
PY
then
  sbatch "${ROOT}/jobs/stage3_v1.sbatch"
fi
