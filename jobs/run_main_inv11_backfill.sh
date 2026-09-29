#!/usr/bin/env bash
# Backfill 11 main INV-unit rows into results/raw (before / M1 gap).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
export PYTHONPATH="${ROOT}/.cache/src/AlignScore/src:${ROOT}/src:${ROOT}/analysis"
export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export CUDA_VISIBLE_DEVICES=""
INST="${ROOT}/data/v3/instances_main_inv11_m1_gap.jsonl"
RAW="${ROOT}/results/raw"

python3 scripts/build_audit_gap_instance_packs.py

conda activate cpuverif
for v in v2a_minicheck v3_alignscore; do
  python3 src/score_jsonl.py --verifier "${v}" --instances "${INST}" --out "${RAW}/${v}.jsonl"
done

conda activate vllm
set -a && source ~/kkk/openrouter.env && set +a
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_GPU_GLOBAL_SCORE_LOCK=0
python3 src/score_jsonl.py --verifier v1_medscore --instances "${INST}" --out "${RAW}/v1_medscore.jsonl"

echo "inv11 backfill done $(date -Is)"
