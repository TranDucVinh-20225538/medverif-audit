#!/usr/bin/env bash
# T8b supported sample: V2, V3, 7× T6-A, Bespoke (+ merge into results/raw/t8 for report).
set -euo pipefail
ROOT="${MEDVERIF_ROOT:-/root/medverif-audit}"
cd "${ROOT}"
export PYTHONPATH="${ROOT}/src"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"

INST="${ROOT}/data/t8/instances_aggrefact_t8b.jsonl"
[[ -f "${INST}" ]] || INST="${ROOT}/data/v3/instances_aggrefact_t8b.jsonl"
RAW="${ROOT}/results/raw/t8"
mkdir -p "${RAW}"

score_one() {
  local verifier="$1"
  local out="$2"
  python3 src/score_jsonl.py --verifier "${verifier}" --instances "${INST}" --out "${out}" || true
}

# V2/V3 via cpu_early pattern
python3 src/cpu_early.py --instances "${INST}" --outdir "${RAW}" 2>/dev/null || true

for v in v2a_minicheck v3_alignscore; do
  out="${RAW}/${v}_t8b.jsonl"
  [[ -f "${RAW}/${v}.jsonl" && ! -f "${out}" ]] && cp -a "${RAW}/${v}.jsonl" "${out}"
done

python3 scripts/t6a_score_instances.py --instances "${INST}" --outdir "${RAW}" --checker all --out-suffix t8b

if python3 -c "import verifiers.v2b_bespoke" 2>/dev/null; then
  score_one v2b_bespoke "${RAW}/v2b_bespoke_t8b.jsonl"
fi

python3 scripts/t8b_report.py
