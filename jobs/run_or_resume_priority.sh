#!/usr/bin/env bash
# OpenRouter resume chain: main 247 → T17 → T14 (each task stops on its own cap / credit preflight).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
LOG="${ROOT}/jobs/logs/or_resume_priority_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "or resume priority start $(date -Is)"

run_task() {
  local name="$1"
  shift
  echo "=== TASK ${name} === $(date -Is)"
  if "$@"; then
    echo "=== TASK ${name} OK === $(date -Is)"
    return 0
  fi
  local ec=$?
  echo "=== TASK ${name} STOPPED exit=${ec} === $(date -Is)"
  return "${ec}"
}

export MEDVERIF_MAIN_DOSE_BACKFILL_CAP_USD=4
export MEDVERIF_OR_TASK_CAP_USD=4
python3 - <<'PY'
import json, sys
from pathlib import Path
sys.path.insert(0, "scripts")
from main_dose_backfill_budget import BASELINE, write_baseline, load_baseline
if not BASELINE.is_file():
    print(json.dumps(write_baseline()))
else:
    print(json.dumps({"baseline_usd": load_baseline(), "note": "unchanged"}))
PY
run_task "main_dose_247" bash "${ROOT}/jobs/run_main_dose_or_backfill.sh" || true

export MEDVERIF_T17_BUDGET_USD=3
export MEDVERIF_OR_TASK_CAP_USD=3
run_task "t17_resume" bash "${ROOT}/jobs/run_t17_score_hpc_resume.sh" || true

export MEDVERIF_T14_BUDGET_USD=2
export MEDVERIF_OR_TASK_CAP_USD=2
run_task "t14_resume" bash "${ROOT}/jobs/run_t14_score_openrouter_resume.sh" || true

echo "or resume priority end $(date -Is)"
