#!/usr/bin/env bash
# Expansion CPU pipeline: StatPearls download/chunk, unused Textbooks mine, candidate pool.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
# shellcheck source=jobs/lib/flock.sh
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock expand_cpu

cd "${ROOT}"
export PYTHONPATH="${ROOT}/src"
export HF_HOME="${ROOT}/.cache/huggingface"
LOG="${ROOT}/jobs/logs/expand_cpu_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "expand_cpu start $(date -Is)"

CACHE="${ROOT}/.cache/statpearls"
TAR="${CACHE}/statpearls_NBK430685.tar.gz"
NXML="${CACHE}/statpearls_NBK430685"
CHUNK="${CACHE}/chunk"
TB="${HF_HOME}/hub/datasets--MedRAG--textbooks/snapshots"
TB_CHUNK="$(find "${TB}" -type d -name chunk 2>/dev/null | head -1 || true)"
EXP="${ROOT}/data/expand"
mkdir -p "${CACHE}" "${EXP}" "${CHUNK}"

STAT="pending"
if [[ -f "${CHUNK}/.done" ]]; then
  STAT="chunked"
elif [[ -d "${NXML}" ]] && ls "${NXML}"/*.nxml &>/dev/null; then
  STAT="extracted"
elif [[ -f "${TAR}" ]]; then
  STAT="downloaded"
fi

if [[ ! -f "${TAR}" ]]; then
  echo "downloading StatPearls tar..."
  wget -c -O "${TAR}.part" "https://ftp.ncbi.nlm.nih.gov/pub/litarch/3d/12/statpearls_NBK430685.tar.gz"
  mv "${TAR}.part" "${TAR}"
  STAT="downloaded"
fi

if [[ "${STAT}" == "downloaded" ]] || [[ ! -d "${NXML}" ]] || ! compgen -G "${NXML}/*.nxml" >/dev/null; then
  echo "extracting tar..."
  mkdir -p "${NXML}"
  tar -xzf "${TAR}" -C "${CACHE}"
  if ! compgen -G "${NXML}/*.nxml" >/dev/null; then
    NXML="$(find "${CACHE}" -type f -name '*.nxml' -printf '%h\n' 2>/dev/null | sort -u | head -1 || true)"
    echo "nxml dir resolved to ${NXML:-MISSING}"
  fi
  STAT="extracted"
fi

if [[ ! -f "${CHUNK}/.done" ]] && [[ -n "${NXML:-}" ]] && compgen -G "${NXML}/*.nxml" >/dev/null; then
  echo "chunking StatPearls..."
  python3 "${ROOT}/scripts/expand/chunk_statpearls.py" \
    --nxml-dir "${NXML}" \
    --out-dir "${CHUNK}"
  touch "${CHUNK}/.done"
  STAT="chunked"
fi

CORPUS_ARGS=(--corpus-dir "${CHUNK}")
if [[ -n "${TB_CHUNK}" ]]; then
  echo "textbooks chunk=${TB_CHUNK}"
  CORPUS_ARGS+=(--corpus-dir "${TB_CHUNK}")
else
  echo "WARN: textbooks chunk dir not found"
fi

python3 "${ROOT}/scripts/expand/extract_expand_pool.py" \
  "${CORPUS_ARGS[@]}" \
  --out-pool "${EXP}/candidates_pool.jsonl" \
  --out-selected "${EXP}/candidates_selected.jsonl" \
  --stats "${EXP}/extract_stats.json" \
  --attempt 400 \
  --seed 2026

python3 "${ROOT}/scripts/expand/write_expand_status.py" --statpearls "${STAT}"

echo "expand_cpu done $(date -Is)"
