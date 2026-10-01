#!/usr/bin/env bash
# Common environment for journal chain 2 (RD real-dose errors, UNF unit-normalization fix, AT attribution).
# Sources chain 1's jr_env.sh (same python / HF cache / conda) and then separates chain 2's outputs:
#   results/journal2/ (own markers), real-dose API ledger capped by MEDVERIF_RD_CAP_USD (default $5),
#   MEDVERIF_API_LEDGER=0 so results/api_cost.json (chain 1) is never written.
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal/jr_env.sh"
export PYTHONPATH="${ROOT}/scripts/journal2:${PYTHONPATH}"
export MEDVERIF_RD_CAP_USD="${MEDVERIF_RD_CAP_USD:-5}"
export MEDVERIF_M1=0
jr2_load_api_env() {
  jr_load_api_env            # OPENROUTER_API_KEY from ${ROOT}/.env or ~/kkk/openrouter.env (never echoed)
  export MEDVERIF_API_LEDGER=0
}
jr2_cpuverif_py() {
  # the paper's CPU-checker env (same as chain 1's small-checker stage); override with MEDVERIF_CPUVERIF_PY
  if [[ -n "${MEDVERIF_CPUVERIF_PY:-}" ]]; then echo "${MEDVERIF_CPUVERIF_PY}"; return; fi
  env -u PYTHONPATH conda run -n "${MEDVERIF_CPUVERIF_CONDA:-cpuverif}" python -c 'import sys; print(sys.executable)'
}
mkdir -p "${ROOT}/results/journal2" "${ROOT}/jobs/logs"
