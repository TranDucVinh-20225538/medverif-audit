#!/bin/bash
# V1 on cpu_early first, then label_v3b (Phi only). Never cancels p3-noadv jobs.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
V1=$(sbatch --parsable "${ROOT}/jobs/stage3_v1.sbatch")
V3B=$(sbatch --parsable --dependency=afterok:"${V1}" "${ROOT}/jobs/label_v3b.sbatch")
echo "v1_job=${V1}"
echo "v3b_job=${V3B} (afterok ${V1})"
echo "${V1}" > jobs/logs/v1.pending
echo "${V3B}" > jobs/logs/v3b.pending
