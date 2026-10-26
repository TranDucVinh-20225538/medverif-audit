#!/bin/bash
#SBATCH -J rd2-dosej
#SBATCH -c 4
#SBATCH --mem=8G
#SBATCH --time=24:00:00
#SBATCH --exclude=node002
#SBATCH -o /data2/hpcshared/medverif-audit/results/journal5/rd2/frontier_judges_dose_focused/slurm-%j.out
# Dose-focused frontier judges (NOT HTML RAGAS). Does not touch frontier_judges/.
# Usage:
#   sbatch --export=ALL,MODE=smoke scripts/journal5/run_rd2_frontier_dose_focused.sh
#   sbatch --export=ALL,MODE=full scripts/journal5/run_rd2_frontier_dose_focused.sh
set -euo pipefail
cd /data2/hpcshared/medverif-audit
PY=${MEDVERIF_PYTHON:-/data2/cmdir/home/toandq/.conda/envs/vllm/bin/python}
mkdir -p results/journal5/rd2/frontier_judges_dose_focused

unset OPENROUTER_API_KEY || true
ENVF="${HOME}/kkk/openrouter.env"
if [[ ! -r "$ENVF" ]]; then
  echo "STOP: missing readable $ENVF"
  exit 1
fi
set -a
# shellcheck disable=SC1090
source "$ENVF"
set +a
if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
  echo "STOP: OPENROUTER_API_KEY empty"
  exit 1
fi
echo "OPENROUTER_API_KEY loaded (len=${#OPENROUTER_API_KEY}); not printing value"

MODE=${MODE:-smoke}
if [[ "$MODE" == "smoke" ]]; then
  exec "$PY" scripts/journal5/rd2_frontier_dose_focused.py --smoke --max-usd "${MAX_USD:-2}" --workers "${WORKERS:-4}"
elif [[ "$MODE" == "full" ]]; then
  exec "$PY" scripts/journal5/rd2_frontier_dose_focused.py --full --max-usd "${MAX_USD:-50}" --workers "${WORKERS:-4}"
elif [[ "$MODE" == "report" ]]; then
  exec "$PY" scripts/journal5/rd2_frontier_dose_focused.py --report-only
else
  echo "STOP: MODE must be smoke|full|report"
  exit 1
fi
