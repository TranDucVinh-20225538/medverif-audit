#!/usr/bin/env bash
# M1-strong + repair + T9 nat3 + T24 (priority CSV) in parallel Slurm jobs.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
mkdir -p jobs/logs results/cache

submit() {
  local name="$1"
  shift
  sbatch --job-name="${name}" "$@" 2>&1 | tee -a jobs/logs/batch_oct_submit.log
}

submit m1_strong jobs/run_m1_strong.sbatch

submit m1_repair <<'SB'
#!/bin/bash
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/m1_repair_%j.out
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
export PYTHONPATH="${ROOT}/src:${ROOT}/analysis:${ROOT}/scripts"
echo "m1_repair start $(date -Is)"
python3 scripts/m1_e1_unit_repair_report.py
echo "m1_repair done $(date -Is)"
SB

submit t9_nat3 <<'SB'
#!/bin/bash
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/t9_nat3_%j.out
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
export PYTHONPATH="${ROOT}/src:${ROOT}/analysis:${ROOT}/scripts"
echo "t9_nat3 start $(date -Is)"
python3 scripts/t9_inv_nat3_report.py
echo "t9_nat3 done $(date -Is)"
SB

submit t24_mini <<'SB'
#!/bin/bash
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:30:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/t24_mini_%j.out
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm 2>/dev/null || true
export PYTHONPATH="${ROOT}/src:${ROOT}/scripts"
echo "t24 start $(date -Is)"
python3 scripts/t24_real_rag_study.py
echo "t24 done $(date -Is)"
SB

echo "batch_oct parallel submit complete $(date -Is)"
