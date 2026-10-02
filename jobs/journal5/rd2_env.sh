#!/usr/bin/env bash
# Environment for journal 5 / RD2 (sourced by jobs/journal5/*.sbatch and jobs/run_rd2_chain.sh).
# Self-contained like jobs/journal3/jr3_env.sh (the HPC checkout has locally modified files elsewhere): PYTHONPATH carries
# only scripts/journal5 + the MiniCheck/AlignScore library sources; the RD2 scripts add src/ and scripts/journal{,2,3}
# themselves and verify the pre-registered files by sha256 (prereg/rd2_freeze.json) before generating / extracting.
set -euo pipefail
ROOT="${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}"
cd "${ROOT}"
export PY="${MEDVERIF_PYTHON:-/data2/cmdir/home/toandq/.conda/envs/vllm/bin/python}"
export PYTHONUNBUFFERED=1 PYTHONNOUSERSITE=1 MPLBACKEND=Agg
export PYTHONPATH="${ROOT}/scripts/journal5:${ROOT}/.cache/src/MiniCheck:${ROOT}/.cache/src/AlignScore/src"
export NLTK_DATA="${ROOT}/.cache/nltk"
if [[ -f /data2/shared/apps/conda/etc/profile.d/conda.sh ]]; then
  set +u; source /data2/shared/apps/conda/etc/profile.d/conda.sh; set -u
fi
# HF cache (identical to jobs/lib/hf_env.sh / jr3_env.sh)
export HF_HOME="${HF_HOME:-${ROOT}/.cache/huggingface}"
export HUGGINGFACE_HUB_CACHE="${HUGGINGFACE_HUB_CACHE:-${HF_HOME}/hub}"
export HF_HUB_CACHE="${HUGGINGFACE_HUB_CACHE}"
export HF_DATASETS_CACHE="${HF_DATASETS_CACHE:-${HF_HOME}/datasets}"
export HF_HUB_DISABLE_TELEMETRY=1 TOKENIZERS_PARALLELISM=false VLLM_NO_USAGE_STATS=1 DO_NOT_TRACK=1
if [[ -z "${HF_TOKEN:-}" && -z "${HF_TOKEN_PATH:-}" && -r "${HOME}/.cache/huggingface/token" ]]; then
  export HF_TOKEN_PATH="${HOME}/.cache/huggingface/token"
fi
# RD2 outputs: results/journal5/rd2 (own markers + own API ledger).  MEDVERIF_JR2_DIR makes the UNCHANGED journal-2 scorer
# (scripts/journal2/rd_score.py) read/write RD2 instead of results/journal2; MEDVERIF_RD_QC keeps rd_extract's QC sheet
# default (qc/real_dose_errors_check.csv) out of reach.
export MEDVERIF_JR2_DIR="${ROOT}/results/journal5/rd2"
export MEDVERIF_RD_QC="${ROOT}/results/journal5/rd2/qc/unused_rd_extract_qc.csv"
export MEDVERIF_RD2_MAX_USD="${MEDVERIF_RD2_MAX_USD:-3}"
export MEDVERIF_RD_CAP_USD="${MEDVERIF_RD2_MAX_USD}"   # one cap for ALL RD2 OpenRouter spend (generation + API judges)
export MEDVERIF_M1=0
rd2_load_api_env() {
  # OPENROUTER_API_KEY from ~/.medverif_keys (fallbacks: ${ROOT}/.env, ~/kkk/openrouter.env).  Never echoed.
  local had_x=0; [[ $- == *x* ]] && had_x=1 && set +x
  if [[ -r "${HOME}/.medverif_keys" ]]; then set -a; source "${HOME}/.medverif_keys"; set +a
  elif [[ -f "${ROOT}/.env" ]]; then set -a; source "${ROOT}/.env"; set +a
  elif [[ -f "${HOME}/kkk/openrouter.env" ]]; then set -a; source "${HOME}/kkk/openrouter.env"; set +a; fi
  export MEDVERIF_USE_OPENROUTER=1 MEDVERIF_API_LEDGER=0
  export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-4}"
  [[ ${had_x} -eq 1 ]] && set -x
  if [[ -n "${OPENROUTER_API_KEY:-}" ]]; then echo "OPENROUTER_API_KEY: set"; else echo "OPENROUTER_API_KEY: NOT set"; fi
}
rd2_cpuverif_py() {
  if [[ -n "${MEDVERIF_CPUVERIF_PY:-}" ]]; then echo "${MEDVERIF_CPUVERIF_PY}"; return; fi
  env -u PYTHONPATH conda run -n "${MEDVERIF_CPUVERIF_CONDA:-cpuverif}" python -c 'import sys; print(sys.executable)'
}
mkdir -p "${ROOT}/results/journal5/rd2/markers" "${ROOT}/jobs/logs"
echo "=== $(basename "${0}") job=${SLURM_JOB_ID:-local} task=${SLURM_ARRAY_TASK_ID:-na} host=$(hostname) $(date -Is) py=${PY}"
