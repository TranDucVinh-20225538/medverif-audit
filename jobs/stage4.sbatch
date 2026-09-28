#!/bin/bash
#SBATCH --job-name=medverif-s4
#SBATCH --partition=defq
#SBATCH --exclude=node001
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/%x-%j.out

set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
export PYTHONPATH="${ROOT}/src:${ROOT}/.cache/pydeps"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm

INST="${ROOT}/data/v3/instances_main.jsonl"
if [ ! -f "${INST}" ]; then
  echo "missing ${INST}" >&2
  exit 1
fi

python - << 'PY'
import json
from pathlib import Path
root = Path("/data2/hpcshared/medverif-audit/results/raw")
present = sorted(p.stem for p in root.glob("*.jsonl") if p.is_file())
print(json.dumps({"verdict_files": present}))
PY

python analysis/analyze.py \
  --instances "${INST}" \
  --verdicts "${ROOT}/results/raw" \
  --outdir "${ROOT}/results"
echo "stage4 done $(date -Is) checklist=${ROOT}/results/tables/phenomenon_checklist.md"
