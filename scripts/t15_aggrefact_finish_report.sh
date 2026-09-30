#!/usr/bin/env bash
# Run after base+ft AggreFact jsonl both complete (parallel legs).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
BASE="${ROOT}/results/raw/t15/base_aggrefact_test.jsonl"
FT="${ROOT}/results/raw/t15/ft_aggrefact_test.jsonl"
need=29320
b=$(wc -l < "${BASE}")
f=$(wc -l < "${FT}")
if [[ "${b}" -lt "${need}" ]] || [[ "${f}" -lt "${need}" ]]; then
  echo "not ready: base=${b} ft=${f} need=${need}"
  exit 1
fi
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate cpuverif
export PYTHONPATH="${ROOT}/src:${ROOT}/analysis"
python3 scripts/t15_aggrefact_report.py
python3 scripts/t15_eval.py --packs __none__ 2>/dev/null || true
