# Graceful GPU job shutdown on SLURM SIGTERM (e.g. --signal=B:TERM@120) or SIGUSR1.
# Source after `conda activate`. Use gpu_run for long-running Python (vLLM / GPU scoring).

_gpu_child=""

_gpu_cleanup() {
  local sig="${1:-?}"
  echo "[gpu_graceful] signal=${sig} job=${SLURM_JOB_ID:-n/a} host=$(hostname) at $(date -Is)" >&2
  if [ -n "${_gpu_child}" ] && kill -0 "${_gpu_child}" 2>/dev/null; then
    kill -TERM "${_gpu_child}" 2>/dev/null || true
    local i
    for i in $(seq 1 40); do
      kill -0 "${_gpu_child}" 2>/dev/null || break
      sleep 3
    done
    kill -KILL "${_gpu_child}" 2>/dev/null || true
  fi
  # vLLM worker / engine-core processes can outlive the parent Python on NFS cancel.
  pkill -u "$(id -un)" -f 'vllm\.(v1|entrypoints)|EngineCore|VLLM::' 2>/dev/null || true
  wait "${_gpu_child}" 2>/dev/null || true
  _gpu_child=""
  exit 143
}

gpu_graceful_init() {
  trap '_gpu_cleanup TERM' TERM
  trap '_gpu_cleanup USR1' USR1
  export MEDVERIF_VLLM_GRACEFUL=1
}

gpu_run() {
  "$@" &
  _gpu_child=$!
  wait "${_gpu_child}"
  local st=$?
  _gpu_child=""
  return "${st}"
}
