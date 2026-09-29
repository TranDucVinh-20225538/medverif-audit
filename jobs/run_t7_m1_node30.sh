#!/usr/bin/env bash
# T7 M1: V2, V3, T6-A, Bespoke on M1-normalized E1-unit + C0 → results/raw_m1/t7/
set -euo pipefail
ROOT="${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}"
cd "${ROOT}"
source /data2/shared/apps/conda/etc/profile.d/conda.sh 2>/dev/null || true
conda activate vllm 2>/dev/null || true
export PYTHONPATH="${ROOT}/src"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-}"
export MEDVERIF_M1="${MEDVERIF_M1:-0}"
export HF_HOME="${HF_HOME:-${ROOT}/.cache/huggingface}"
export HUGGINGFACE_HUB_CACHE="${HUGGINGFACE_HUB_CACHE:-${HF_HOME}/hub}"

LOG="${ROOT}/jobs/logs/t7_m1_node30_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "t7 m1 node30 start $(date -Is)"

python3 scripts/build_t7_m1_pending.py
INST="${ROOT}/data/t7/instances_e1_unit_m1_pending.jsonl"
RAW="${ROOT}/results/raw_m1/t7"
mkdir -p "${RAW}"

python3 scripts/t7_score_pending_m1.py
python3 scripts/t6a_score_instances.py --instances "${INST}" --outdir "${RAW}" --checker all
if python3 -c "import verifiers.v2b_bespoke" 2>/dev/null; then
  python3 src/score_jsonl.py --verifier v2b_bespoke --instances "${INST}" --out "${RAW}/v2b_bespoke.jsonl" || true
fi
python3 scripts/t7_m1_mcnemar_report.py
echo "t7 m1 node30 done $(date -Is)"
