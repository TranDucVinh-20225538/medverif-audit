#!/usr/bin/env bash
# Submit T19 8B (full 1703) and 3B resume for main_pol (80 rows → same 3b jsonl).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
python3 scripts/build_t19_main_pol_instances.py

if squeue -u "${USER}" -h -o "%j" 2>/dev/null | rg -qx "t19-llama31_8b_local"; then
  echo "8B already queued"
else
  export MEDVERIF_T19_SLUG=llama31_8b_local
  export MEDVERIF_T19_HF_MODEL=meta-llama/Llama-3.1-8B-Instruct
  export MEDVERIF_T19_OUT=llama31_8b_instruct.jsonl
  export MEDVERIF_REQ_MEM_GB=96
  unset MEDVERIF_T19_INSTANCES
  j8=$(sbatch --parsable --mem=96G --exclude=node004 --job-name=t19-llama31_8b_local jobs/run_t19_model.sbatch)
  echo "submitted 8B ${j8}"
fi

if squeue -u "${USER}" -h -o "%j" 2>/dev/null | rg -qx "t19-llama32_3b_pol"; then
  echo "3B POL already queued"
else
  export MEDVERIF_T19_SLUG=llama32_3b_pol
  export MEDVERIF_T19_HF_MODEL=meta-llama/Llama-3.2-3B-Instruct
  export MEDVERIF_T19_OUT=llama32_3b_instruct.jsonl
  export MEDVERIF_T19_INSTANCES=data/t19/instances_t19_main_pol.jsonl
  export MEDVERIF_REQ_MEM_GB=48
  j3=$(sbatch --parsable --mem=48G --exclude=node004 --job-name=t19-llama32_3b_pol jobs/run_t19_model.sbatch)
  echo "submitted 3B POL ${j3}"
fi
