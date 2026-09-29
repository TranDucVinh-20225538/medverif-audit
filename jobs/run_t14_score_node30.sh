#!/usr/bin/env bash
# T14 repr: V2, V3, T6-A×7, Bespoke → results/raw/t14/
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
python3 scripts/build_t14_score_pending.py
INST="${ROOT}/data/v3/instances_t14_pending_node30.jsonl"
OUT="${ROOT}/results/raw/t14"
mkdir -p "${OUT}"
export PYTHONPATH="${ROOT}/src:${ROOT}/analysis"
for v in v2a_minicheck v3_alignscore v2b_bespoke \
  t6a_minicheck_roberta t6a_minicheck_deberta t6a_alignscore_base \
  t6a_summac_zs t6a_summac_conv t6a_hhem t6a_granite_guardian; do
  python3 src/score_jsonl.py --verifier "${v}" --instances "${INST}" --out "${OUT}/${v}.jsonl" || true
done
