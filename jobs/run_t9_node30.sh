#!/usr/bin/env bash
# T9 on node30 only: AlignScore server (base ckpt) + NeMo Guardrails-equivalent batch scorer.
# Do not run on HPC login nodes.
set -euo pipefail
ROOT="${MEDVERIF_ROOT:-/root/medverif-audit}"
cd "${ROOT}"
export PYTHONPATH="${ROOT}/src"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"

ALIGN_PORT="${T9_ALIGN_SCORE_PORT:-5000}"
ALIGN_ENDPOINT="http://127.0.0.1:${ALIGN_PORT}/alignscore_base"
export T9_ALIGN_SCORE_ENDPOINT="${T9_ALIGN_SCORE_ENDPOINT:-${ALIGN_ENDPOINT}}"

python3 scripts/t9_build_input_sets.py

INST="${ROOT}/data/t9/instances_all.jsonl"
RAW="${ROOT}/results/raw/t9"
mkdir -p "${RAW}"
LOG="${ROOT}/jobs/logs/t9_node30_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "t9 node30 start $(date -Is)"

# AlignScore checkpoints (official NeMo Guardrails server defaults to model=base).
export ALIGN_SCORE_PATH="${ALIGN_SCORE_PATH:-${ROOT}/.cache/alignscore_ckpts}"
export ALIGN_SCORE_DEVICE="${ALIGN_SCORE_DEVICE:-cuda}"
mkdir -p "${ALIGN_SCORE_PATH}"
if [[ ! -f "${ALIGN_SCORE_PATH}/AlignScore-base.ckpt" ]]; then
  echo "download AlignScore-base.ckpt to ${ALIGN_SCORE_PATH}"
  curl -fsSL -o "${ALIGN_SCORE_PATH}/AlignScore-base.ckpt" \
    "https://huggingface.co/yzha/AlignScore/resolve/main/AlignScore-base.ckpt"
fi

python3 -m pip show nemoguardrails >/dev/null 2>&1 || python3 -m pip install 'nemoguardrails==0.24.1' -q
python3 - <<'PY'
import json
import nemoguardrails
from pathlib import Path
ROOT = Path("/root/medverif-audit")
meta = {"nemoguardrails": nemoguardrails.__version__}
(ROOT / "notes/t9_nemoguardrails_version.json").write_text(json.dumps(meta, indent=2) + "\n")
print(meta)
PY

SERVER_PID=""
cleanup() {
  if [[ -n "${SERVER_PID}" ]] && kill -0 "${SERVER_PID}" 2>/dev/null; then
    kill "${SERVER_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT

NGR_SERVER="$(python3 - <<'PY'
import nemoguardrails
from pathlib import Path
print(Path(nemoguardrails.__file__).parent / "library/factchecking/align_score/server.py")
PY
)"
python3 "${NGR_SERVER}" start --port "${ALIGN_PORT}" --models base &
SERVER_PID=$!
for _ in $(seq 1 120); do
  if curl -sf "http://127.0.0.1:${ALIGN_PORT}/" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

python3 scripts/t9_score_alignscore_rail.py \
  --instances "${INST}" \
  --out "${RAW}/alignscore_rail.jsonl" \
  --endpoint "${T9_ALIGN_SCORE_ENDPOINT}"

python3 scripts/t9_report.py --scores "${RAW}/alignscore_rail.jsonl"
echo "t9 node30 done $(date -Is)"
