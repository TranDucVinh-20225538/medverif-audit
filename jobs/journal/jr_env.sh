#!/usr/bin/env bash
# Common environment for the journal chain stages (sourced by jobs/journal/*.sbatch).
set -euo pipefail
ROOT="${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}"
cd "${ROOT}"
export PY="${MEDVERIF_PYTHON:-/data2/cmdir/home/toandq/.conda/envs/vllm/bin/python}"
export PYTHONUNBUFFERED=1 PYTHONNOUSERSITE=1 MPLBACKEND=Agg
export PYTHONPATH="${ROOT}/src:${ROOT}/analysis:${ROOT}/scripts:${ROOT}/scripts/journal:${ROOT}/.cache/src/MiniCheck:${ROOT}/.cache/src/AlignScore/src"
export NLTK_DATA="${ROOT}/.cache/nltk"
export MEDVERIF_JR_CAP_USD="${MEDVERIF_JR_CAP_USD:-5}"
# shared conda (needed for `conda run -n cpuverif` in the small-checker stage)
if [[ -f /data2/shared/apps/conda/etc/profile.d/conda.sh ]]; then
  set +u; source /data2/shared/apps/conda/etc/profile.d/conda.sh; set -u
fi
source "${ROOT}/jobs/lib/hf_env.sh"
medverif_hf_env
jr_load_api_env() {
  # .env on the HPC checkout (OPENROUTER_API_KEY); never echoed
  if [[ -f "${ROOT}/.env" ]]; then set -a; source "${ROOT}/.env"; set +a
  elif [[ -f "${HOME}/kkk/openrouter.env" ]]; then set -a; source "${HOME}/kkk/openrouter.env"; set +a; fi
  export MEDVERIF_USE_OPENROUTER=1 MEDVERIF_API_LEDGER=1
  export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-4}"
}
echo "=== $(basename "${0}") job=${SLURM_JOB_ID:-local} task=${SLURM_ARRAY_TASK_ID:-na} host=$(hostname) $(date -Is) py=${PY}"
