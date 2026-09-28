#!/usr/bin/env bash
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
jid=$(sbatch --parsable "${ROOT}/jobs/stage4.sbatch")
echo "stage4_job=${jid} (no GPU dependency)"
