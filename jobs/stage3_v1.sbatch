#!/bin/bash
#SBATCH --job-name=medverif-v1
#SBATCH --partition=defq
#SBATCH --exclude=node001,node002
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --cpus-per-task=8
#SBATCH --time=04:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/%x-%j.out

set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export VLLM_CACHE_ROOT="${ROOT}/.cache/vllm"
export HF_HUB_DISABLE_TELEMETRY=1
export TOKENIZERS_PARALLELISM=false
export PYTHONPATH="${ROOT}/src"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm

python - << 'PY'
import json
from pathlib import Path
root = Path("/data2/hpcshared/medverif-audit/.cache/huggingface/hub")
snap = next(root.glob("models--mistralai--Mistral-Small-24B-Instruct-2501/snapshots/*"))
index = json.loads((snap / "model.safetensors.index.json").read_text())
wanted = sorted({name for name in index["weight_map"].values() if name.endswith(".safetensors")})
bad = []
for name in wanted:
    path = snap / name
    if not path.is_file():
        bad.append(name + ":missing")
        continue
    with path.open("rb") as handle:
        n = int.from_bytes(handle.read(8), "little")
    if not (8 < n < 50_000_000):
        bad.append(name + ":bad_header")
if bad:
    raise SystemExit("V1 weights not ready: " + ",".join(bad[:8]))
print("v1 weights ready", len(wanted))
PY

python src/split_cpu_early.py
mkdir -p tests/smoke_results results/raw results/raw_threshold

python src/score_jsonl.py --verifier v1_medscore --instances tests/smoke_v1_all.jsonl --out tests/smoke_results/v1_medscore.jsonl
python src/score_jsonl.py --verifier v1_medscore --instances data/v3/instances_cpu_main.jsonl --out results/raw/v1_medscore.jsonl
python src/score_jsonl.py --verifier v1_medscore --instances data/v3/instances_cpu_threshold.jsonl --out results/raw_threshold/v1_medscore.jsonl
python src/reparse_v1_study.py --in-place tests/smoke_results/v1_medscore.jsonl results/raw/v1_medscore.jsonl results/raw_threshold/v1_medscore.jsonl
echo "v1 stage3 (cpu_early) done $(date -Is)"
sbatch --dependency=afterok:"${SLURM_JOB_ID}" "${ROOT}/jobs/stage4.sbatch"
