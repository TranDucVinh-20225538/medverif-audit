#!/bin/bash
#SBATCH --job-name=medverif-cpu
#SBATCH --partition=defq
#SBATCH --exclude=node001
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/%x-%j.out

set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
export CUDA_VISIBLE_DEVICES=""
export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export HF_HUB_DISABLE_TELEMETRY=1
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=4
export MKL_NUM_THREADS=4
export OPENBLAS_NUM_THREADS=4
export NLTK_DATA="${ROOT}/.cache/nltk"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
# cpu_early.py sets PYTHONPATH (skips .cache/cpu_extra when conda has spacy — avoids torch/torchvision clash).
nice -n 19 python -u src/cpu_early.py

# Stage 4 on the MAIN verdicts only. Threshold, if scored, stays in results/raw_threshold.
mkdir -p "${ROOT}/results/prelim" "${ROOT}/results/tables"
PYTHONPATH="${ROOT}/src:${ROOT}/.cache/pydeps" python analysis/analyze.py \
  --instances "${ROOT}/data/v3/instances_cpu_main.jsonl" \
  --verdicts "${ROOT}/results/raw" \
  --outdir "${ROOT}/results/prelim" \
  --stamp "PRELIMINARY: 2 verifiers, INV-unit only"
python - << 'PY'
from pathlib import Path
src = Path("/data2/hpcshared/medverif-audit/results/prelim/tables/phenomenon_checklist.md")
dst = Path("/data2/hpcshared/medverif-audit/results/tables/phenomenon_checklist_PRELIM.md")
body = src.read_text() if src.exists() else ""
banner = (
    "PRELIMINARY: 2 verifiers (v2a_minicheck, v3_alignscore), INV-unit only.\n"
    "INV-paraphrase was not scored. V1, V2b, and V4 are absent.\n"
    "Numbers only.\n\n"
)
dst.write_text(banner + body)
print(dst, dst.stat().st_size)
PY
echo "cpu early done $(date -Is)"
