#!/usr/bin/env bash
# Record Slurm wall time + pack/verifier metadata into notes/job_elapsed.json (H11).
set -euo pipefail

_MEDVERIF_ELAPSED_ROOT="${MEDVERIF_ELAPSED_ROOT:-/data2/hpcshared/medverif-audit}"
_MEDVERIF_ELAPSED_PACK=""
_MEDVERIF_ELAPSED_VERIFIER=""
_MEDVERIF_ELAPSED_MACHINE="hpc"
_MEDVERIF_ELAPSED_API_USD=""
_MEDVERIF_ELAPSED_BEGIN_ISO=""

medverif_job_elapsed_begin() {
  _MEDVERIF_ELAPSED_BEGIN_ISO="$(date -Is)"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --pack) _MEDVERIF_ELAPSED_PACK="$2"; shift 2 ;;
      --verifier) _MEDVERIF_ELAPSED_VERIFIER="$2"; shift 2 ;;
      --machine) _MEDVERIF_ELAPSED_MACHINE="$2"; shift 2 ;;
      --api_usd) _MEDVERIF_ELAPSED_API_USD="$2"; shift 2 ;;
      *) shift ;;
    esac
  done
  export _MEDVERIF_ELAPSED_BEGIN_ISO
}

medverif_job_elapsed_end() {
  local n_rows=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --rows) n_rows="$2"; shift 2 ;;
      *) shift ;;
    esac
  done
  if [[ -z "${SLURM_JOB_ID:-}" ]]; then
    return 0
  fi
  python3 "${_MEDVERIF_ELAPSED_ROOT}/scripts/job_elapsed_record.py" \
    --job-id "${SLURM_JOB_ID}" \
    --job-name "${SLURM_JOB_NAME:-}" \
    --partition "${SLURM_JOB_PARTITION:-}" \
    --node "${SLURMD_NODENAME:-${SLURM_NODELIST:-}}" \
    --pack "${_MEDVERIF_ELAPSED_PACK}" \
    --verifier "${_MEDVERIF_ELAPSED_VERIFIER}" \
    --machine "${_MEDVERIF_ELAPSED_MACHINE}" \
    --n-rows "${n_rows}" \
    --started "${_MEDVERIF_ELAPSED_BEGIN_ISO:-}" \
    --api-usd "${_MEDVERIF_ELAPSED_API_USD}" \
    || true
}
