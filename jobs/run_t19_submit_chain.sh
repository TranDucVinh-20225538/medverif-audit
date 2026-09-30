#!/usr/bin/env bash
# Queue 3B → 8B → CPU report after 1B (dependency chain). Idempotent.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"

job_running() { squeue -u "${USER}" -h -o "%j" 2>/dev/null | rg -qx "$1"; }

if job_running "t19-llama32_3b" || job_running "t19-llama32_3b_instruct"; then
  echo "3B already queued"
elif job_running "t19-llama32_1b"; then
  j1=$(squeue -u "${USER}" -h -o "%i %j" | awk '$2=="t19-llama32_1b"{print $1; exit}')
  if [[ -z "${j1}" ]]; then
    echo "1B name in queue but id not found" >&2
    exit 1
  fi
  export MEDVERIF_T19_SLUG=llama32_3b
  export MEDVERIF_T19_HF_MODEL=meta-llama/Llama-3.2-3B-Instruct
  export MEDVERIF_T19_OUT=llama32_3b_instruct.jsonl
  export MEDVERIF_REQ_MEM_GB=48
  j3=$(sbatch --parsable --mem=48G --exclude=node004 --dependency=afterany:"${j1}" --job-name=t19-llama32_3b jobs/run_t19_model.sbatch)
  echo "submitted 3B job ${j3} after 1B ${j1}"
else
  echo "no 1B running; use run_t19_scale_sweep.sh or submit 3B manually" >&2
  exit 1
fi

# If 3B just submitted or already running, chain 8B after latest 3B
sleep 1
j3=$(squeue -u "${USER}" -h -o "%i %j" | awk '$2 ~ /^t19-llama32_3b/{print $1; exit}')
if [[ -n "${j3}" ]] && ! job_running "t19-llama31_8b_local"; then
  export MEDVERIF_T19_SLUG=llama31_8b_local
  export MEDVERIF_T19_HF_MODEL=meta-llama/Llama-3.1-8B-Instruct
  export MEDVERIF_T19_OUT=llama31_8b_instruct.jsonl
  export MEDVERIF_REQ_MEM_GB=96
  j8=$(sbatch --parsable --mem=96G --exclude=node004 --dependency=afterany:"${j3}" --job-name=t19-llama31_8b_local jobs/run_t19_model.sbatch)
  echo "submitted 8B job ${j8} after 3B ${j3}"
  jrep=$(sbatch --parsable --dependency=afterany:"${j8}" jobs/run_t19_report.sbatch)
  echo "submitted report job ${jrep} after 8B ${j8}"
elif job_running "t19-llama31_8b_local"; then
  j8=$(squeue -u "${USER}" -h -o "%i %j" | awk '$2 ~ /^t19-llama31_8b/{print $1; exit}')
  if [[ -n "${j8}" ]] && ! squeue -u "${USER}" -h -o "%j" | rg -q "^t19-report\$"; then
    jrep=$(sbatch --parsable --dependency=afterany:"${j8}" jobs/run_t19_report.sbatch)
    echo "submitted report job ${jrep} after 8B ${j8}"
  fi
fi
