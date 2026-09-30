#!/usr/bin/env bash
# Call after #SBATCH --mem is set; export MEDVERIF_REQ_MEM_GB to match (integer GB).
medverif_gpu_node_precheck() {
  local req_gb="${MEDVERIF_REQ_MEM_GB:?set MEDVERIF_REQ_MEM_GB before precheck}"
  echo "=== gpu_node_precheck $(date -Is) host=$(hostname) slurm_job=${SLURM_JOB_ID:-na} ==="
  echo "requested_mem_GB=${req_gb}"
  free -h || true
  if [[ -r /proc/meminfo ]]; then
    grep -E '^(MemTotal|MemAvailable|MemFree):' /proc/meminfo || true
  fi
  nvidia-smi -L 2>/dev/null || echo "nvidia-smi -L: no GPU visible"
  nvidia-smi --query-gpu=index,memory.used,memory.total,utilization.gpu --format=csv,noheader 2>/dev/null || true
  local avail_kb need_kb
  avail_kb="$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo 2>/dev/null || echo 0)"
  need_kb=$((req_gb * 1024 * 1024))
  echo "MemAvailable_kB=${avail_kb} need_kB=${need_kb}"
  if [[ "${avail_kb}" -lt "${need_kb}" ]]; then
    echo "FATAL: MemAvailable ${avail_kb} kB < requested ${need_kb} kB (${req_gb}G)" >&2
    exit 86
  fi
  echo "precheck ok"
}
