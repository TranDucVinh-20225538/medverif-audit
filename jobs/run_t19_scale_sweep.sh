#!/usr/bin/env bash
# T19: serial local Llama RAGAS scale sweep (1 GPU / job). Check squeue before submit.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"

if squeue -u "${USER}" -h -o "%j" 2>/dev/null | rg -q "^t19-"; then
  echo "t19: job already queued/running; not submitting duplicates" >&2
  exit 0
fi

python3 scripts/t19_build_instances.py

submit_one() {
  local slug="$1"
  local model="$2"
  local out="$3"
  if [[ -f "${ROOT}/results/raw/t19/${out}" ]]; then
    local n_inst n_score
    n_inst=$(wc -l < "${ROOT}/data/t19/instances_t19.jsonl")
    n_score=$(wc -l < "${ROOT}/results/raw/t19/${out}" || echo 0)
    if [[ "${n_score}" -ge "${n_inst}" ]]; then
      echo "skip ${slug}: scores complete (${n_score}/${n_inst})"
      return 0
    fi
  fi
  export MEDVERIF_T19_SLUG="${slug}"
  export MEDVERIF_T19_HF_MODEL="${model}"
  export MEDVERIF_T19_OUT="${out}"
  sbatch --job-name="t19-${slug}" jobs/run_t19_model.sbatch
}

# Serial chain via dependency would queue all at once — user asked serial: submit only first missing.
if [[ ! -f "${ROOT}/results/raw/t19/llama32_1b_instruct.jsonl" ]] || \
   [[ $(wc -l < "${ROOT}/results/raw/t19/llama32_1b_instruct.jsonl") -lt $(wc -l < "${ROOT}/data/t19/instances_t19.jsonl") ]]; then
  submit_one "llama32_1b" "meta-llama/Llama-3.2-1B-Instruct" "llama32_1b_instruct.jsonl"
  echo "submitted 1B; re-run this script after it finishes for 3B/8B"
  exit 0
fi
if [[ ! -f "${ROOT}/results/raw/t19/llama32_3b_instruct.jsonl" ]] || \
   [[ $(wc -l < "${ROOT}/results/raw/t19/llama32_3b_instruct.jsonl") -lt $(wc -l < "${ROOT}/data/t19/instances_t19.jsonl") ]]; then
  submit_one "llama32_3b" "meta-llama/Llama-3.2-3B-Instruct" "llama32_3b_instruct.jsonl"
  echo "submitted 3B; re-run after finish for 8B"
  exit 0
fi
if [[ ! -f "${ROOT}/results/raw/t19/llama31_8b_instruct.jsonl" ]] || \
   [[ $(wc -l < "${ROOT}/results/raw/t19/llama31_8b_instruct.jsonl") -lt $(wc -l < "${ROOT}/data/t19/instances_t19.jsonl") ]]; then
  submit_one "llama31_8b_local" "meta-llama/Llama-3.1-8B-Instruct" "llama31_8b_instruct.jsonl"
  echo "submitted 8B local"
  exit 0
fi

python3 scripts/t19_report.py
echo "T19 sweep complete — see notes/t19_scale_sweep.md"
