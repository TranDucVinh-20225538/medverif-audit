#!/usr/bin/env bash
# T14 repr: V1, V4, V1b, V5 + T6-B (v6_*); budget ≤ USD 3 — run after PI review if desired.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
python3 scripts/build_t14_score_pending.py
INST="${ROOT}/data/t14/instances_t14_pending_openrouter.jsonl"
OUT="${ROOT}/results/raw/t14"
mkdir -p "${OUT}"
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
for v in v1_medscore v4_ragas_nli v1b_medscore v5_ragas_nli \
  v6_ragas_gpt4o_mini v6_ragas_haiku45 v6_ragas_llama31_8b v6_ragas_mistral_small32; do
  python3 src/score_jsonl.py --verifier "${v}" --instances "${INST}" --out "${OUT}/${v}.jsonl" || true
done
