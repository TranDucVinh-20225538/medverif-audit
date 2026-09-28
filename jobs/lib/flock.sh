#!/usr/bin/env bash
# Non-blocking flock for long-running medverif jobs (source from runner scripts).
MEDVERIF_LOCKDIR="${MEDVERIF_LOCKDIR:-/data2/hpcshared/medverif-audit/jobs/locks}"

medverif_acquire_lock() {
  local name="${1:?lock name}"
  mkdir -p "${MEDVERIF_LOCKDIR}"
  exec 9>"${MEDVERIF_LOCKDIR}/${name}.lock"
  if ! flock -n 9; then
    echo "medverif: already running (${name}); exiting" >&2
    exit 0
  fi
}
