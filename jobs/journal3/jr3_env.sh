#!/usr/bin/env bash
# Environment for journal chain 3 (sourced by jobs/journal3/*.sbatch and jobs/run_journal_chain3.sh).
# Self-contained on purpose: the HPC checkout has locally modified files (scripts/*.py, ...), so chain 3 puts ONLY
# scripts/journal3 + the MiniCheck/AlignScore library sources on PYTHONPATH (no src/, analysis/, scripts/, scripts/journal*)
# and re-implements the HF cache setup of jobs/lib/hf_env.sh here (same paths).
set -euo pipefail
ROOT="${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}"
cd "${ROOT}"
export PY="${MEDVERIF_PYTHON:-/data2/cmdir/home/toandq/.conda/envs/vllm/bin/python}"
export PYTHONUNBUFFERED=1 PYTHONNOUSERSITE=1 MPLBACKEND=Agg
export PYTHONPATH="${ROOT}/scripts/journal3:${ROOT}/.cache/src/MiniCheck:${ROOT}/.cache/src/AlignScore/src"
export NLTK_DATA="${ROOT}/.cache/nltk"
if [[ -f /data2/shared/apps/conda/etc/profile.d/conda.sh ]]; then
  set +u; source /data2/shared/apps/conda/etc/profile.d/conda.sh; set -u
fi
# HF cache (identical to jobs/lib/hf_env.sh::medverif_hf_env); token: HF_TOKEN if set, else the user's token file by path
export HF_HOME="${HF_HOME:-${ROOT}/.cache/huggingface}"
export HUGGINGFACE_HUB_CACHE="${HUGGINGFACE_HUB_CACHE:-${HF_HOME}/hub}"
export HF_HUB_CACHE="${HUGGINGFACE_HUB_CACHE}"
export HF_DATASETS_CACHE="${HF_DATASETS_CACHE:-${HF_HOME}/datasets}"
export HF_HUB_DISABLE_TELEMETRY=1 TOKENIZERS_PARALLELISM=false VLLM_NO_USAGE_STATS=1 DO_NOT_TRACK=1
if [[ -z "${HF_TOKEN:-}" && -z "${HF_TOKEN_PATH:-}" && -r "${HOME}/.cache/huggingface/token" ]]; then
  export HF_TOKEN_PATH="${HOME}/.cache/huggingface/token"
fi
jr3_cpuverif_py() {
  # the paper's CPU-checker env (chain 1 C3 fallback when the vllm env lacks pytorch_lightning/alignscore)
  if [[ -n "${MEDVERIF_CPUVERIF_PY:-}" ]]; then echo "${MEDVERIF_CPUVERIF_PY}"; return; fi
  env -u PYTHONPATH conda run -n "${MEDVERIF_CPUVERIF_CONDA:-cpuverif}" python -c 'import sys; print(sys.executable)'
}
mkdir -p "${ROOT}/results/journal3/markers" "${ROOT}/jobs/logs"
echo "=== $(basename "${0}") job=${SLURM_JOB_ID:-local} task=${SLURM_ARRAY_TASK_ID:-na} host=$(hostname) $(date -Is) py=${PY}"
