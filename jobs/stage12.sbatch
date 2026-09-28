#!/bin/bash
#SBATCH --job-name=medverif-s12
#SBATCH --partition=defq
#SBATCH --exclude=node001
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --cpus-per-task=8
#SBATCH --time=08:00:00
#SBATCH --open-mode=append
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/%x-%j.out

# Releases the GPU and resubmits 15 minutes later when the node has no RAM
# or the weights are not on disk yet. Does not target node001.

set -euo pipefail

ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
mkdir -p jobs/logs data/smoke

resubmit() {
  local why="$1"
  local n
  n=$(cat jobs/logs/s12.count 2>/dev/null || echo 0)
  echo "RESUBMIT ${why} count=${n} host=$(hostname) time=$(date -Is)"
  if [ "${n}" -ge 96 ]; then
    python src/append_report.py --blocker "Stage 1-2 stopped after ${n} resubmits. Last reason: ${why}"
    exit 1
  fi
  echo $((n + 1)) > jobs/logs/s12.count
  local jid
  jid=$(sbatch --parsable --begin=now+15minutes "${ROOT}/jobs/stage12.sbatch")
  echo "${jid}" > jobs/logs/s12.pending
  echo "queued ${jid} to start in 15 minutes"
  exit 0
}

export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export TRANSFORMERS_CACHE="${HF_HOME}/transformers"
export VLLM_CACHE_ROOT="${ROOT}/.cache/vllm"
export HF_HUB_DISABLE_TELEMETRY=1
export TOKENIZERS_PARALLELISM=false

avail_kb=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
echo "host=$(hostname) MemAvailable_kB=${avail_kb}"
if [ "${avail_kb}" -lt 40000000 ]; then
  resubmit "MemAvailable_kB=${avail_kb}"
fi

source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
export PYTHONPATH="${ROOT}/src"

if ! python - << 'PY'
import sys
from pathlib import Path
need = {
    "models--Qwen--Qwen2.5-32B-Instruct": 17,
    "models--microsoft--phi-4": 6,
}
root = Path("/data2/hpcshared/medverif-audit/.cache/huggingface/hub")
for name, n_shards in need.items():
    base = root / name
    done = list(base.glob("**/model-*.safetensors"))
    incomplete = list(base.glob("**/*.incomplete"))
    print(name, "shards", len(done), "incomplete", len(incomplete))
    if len(done) < n_shards or incomplete:
        sys.exit(1)
print("weights ready")
PY
then
  resubmit "weights not local yet"
fi

echo "smoke start $(date -Is)"
python src/stage12_llm.py \
  --candidates "${ROOT}/data/candidates.jsonl" \
  --outdir "${ROOT}/data/smoke" \
  --limit-per-type 16 \
  --template-note "${ROOT}/notes/chat_template_smoke.md"
cp -f "${ROOT}/data/smoke/llm_stats.json" "${ROOT}/data/smoke_llm_stats.json"
kept=$(python -c "import json; print(json.load(open('${ROOT}/data/smoke_llm_stats.json'))['bases_kept'])")
echo "smoke bases_kept=${kept}"
if [ "${kept}" -lt 1 ]; then
  python src/append_report.py --blocker "Smoke run kept 0 base pairs. Full run was not started. See data/smoke_llm_stats.json"
  exit 1
fi

echo "full start $(date -Is)"
python src/stage12_llm.py \
  --candidates "${ROOT}/data/candidates.jsonl" \
  --outdir "${ROOT}/data" \
  --limit-per-type 0 \
  --template-note "${ROOT}/notes/chat_template_calls.md"
python src/write_qc.py \
  --extract-stats "${ROOT}/data/extract_stats.json" \
  --llm-stats "${ROOT}/data/llm_stats.json" \
  --instances "${ROOT}/data/instances.jsonl" \
  --samples-out "${ROOT}/qc/qc_samples.md" \
  --stats-out "${ROOT}/qc/qc_stats.md"
python src/append_report.py
echo "done $(date -Is)"
