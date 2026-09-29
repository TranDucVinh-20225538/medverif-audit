#!/usr/bin/env bash
# Score current T9 manifest (457) via NeMo 0.24.1 rail: AlignScore-base then -large.
set -euo pipefail
ROOT="${MEDVERIF_ROOT:-/root/medverif-audit}"
cd "${ROOT}"
export PYTHONPATH="${ROOT}/src"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
RAW="${ROOT}/results/raw/t9"
mkdir -p "${RAW}" "${ROOT}/jobs/logs"
LOG="${ROOT}/jobs/logs/t9_both_rails_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "t9 both rails start $(date -Is)"

LEGACY="${RAW}/alignscore_rail.legacy_536.jsonl"
if [[ -f "${RAW}/alignscore_rail.jsonl" && ! -f "${LEGACY}" ]]; then
  mv "${RAW}/alignscore_rail.jsonl" "${LEGACY}"
  echo "renamed base scores to alignscore_rail.legacy_536.jsonl"
fi

"${ROOT}/.venv/bin/python" scripts/t9_build_input_sets.py
INST="${ROOT}/data/t9/instances_all.jsonl"
N="$(wc -l <"${INST}")"
echo "instances_all.jsonl lines=${N}"

CKPT_DIR="${ALIGN_SCORE_PATH:-${ROOT}/.cache/alignscore_ckpts}"
export ALIGN_SCORE_PATH="${CKPT_DIR}"
mkdir -p "${CKPT_DIR}"
for f in AlignScore-base.ckpt AlignScore-large.ckpt; do
  [[ -f "${CKPT_DIR}/${f}" ]] || curl -fsSL -o "${CKPT_DIR}/${f}" \
    "https://huggingface.co/yzha/AlignScore/resolve/main/${f}"
done

PY="${ROOT}/.venv_t9_alignscore/bin/python"
[[ -x "${PY}" ]] || bash "${ROOT}/jobs/bootstrap_t9_alignscore_venv.sh"

score_ckpt() {
  local model="$1" port="$2" route="$3" out="$4"
  local pid=""
  cleanup() { [[ -n "${pid}" ]] && kill "${pid}" 2>/dev/null || true; }
  trap cleanup EXIT
  export ALIGN_SCORE_DEVICE="${ALIGN_SCORE_DEVICE:-cuda:0}"
  "${PY}" -u "${ROOT}/scripts/nemo_alignscore_http_server.py" start --port "${port}" --models "${model}" &
  pid=$!
  for _ in $(seq 1 180); do
    curl -sf "http://127.0.0.1:${port}/" >/dev/null 2>&1 && break
    sleep 2
  done
  "${ROOT}/.venv/bin/python" scripts/t9_score_alignscore_rail.py \
    --instances "${INST}" \
    --out "${out}" \
    --endpoint "http://127.0.0.1:${port}/${route}"
  kill "${pid}" 2>/dev/null || true
  trap - EXIT
  sleep 3
}

rm -f "${RAW}/alignscore_rail.jsonl" "${RAW}/alignscore_rail_large.jsonl"
score_ckpt base 5000 alignscore_base "${RAW}/alignscore_rail.jsonl"
score_ckpt large 5001 alignscore_large "${RAW}/alignscore_rail_large.jsonl"

"${ROOT}/.venv/bin/python" scripts/t9_manifest_delta.py
"${ROOT}/.venv/bin/python" scripts/t9_report.py \
  --scores-base "${RAW}/alignscore_rail.jsonl" \
  --scores-large "${RAW}/alignscore_rail_large.jsonl"

echo "t9 both rails done $(date -Is)"
