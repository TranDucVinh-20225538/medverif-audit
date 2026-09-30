#!/bin/bash
#SBATCH --job-name=t19-report
#SBATCH --partition=defq
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/t19-report-%j.out

set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock t19_report

export PYTHONPATH="${ROOT}/src:${ROOT}/analysis:${ROOT}/scripts"
source "${ROOT}/jobs/lib/job_elapsed.sh"
medverif_job_elapsed_begin --pack "notes/t19_scale_sweep.md" --verifier "t19_report" --machine "hpc"
python3 scripts/t19_report.py
python3 scripts/reconcile_llama70b_qi.py
medverif_job_elapsed_end --rows 0
echo "T19 report done $(date -Is)"
