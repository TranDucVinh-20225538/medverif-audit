#!/usr/bin/env bash
# Overnight: wait for OR jobs, dedupe V4, expand v1b/v5 T2, optional T10 prep, morning report.
# Stops API work if credit < $1.5 or openrouter_budget exits 2.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
LOG="${ROOT}/jobs/logs/overnight_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "overnight orchestrator start $(date -Is)"

export MEDVERIF_OR_MIN_CREDIT="${MEDVERIF_OR_MIN_CREDIT:-1.5}"
STATUS="${ROOT}/notes/overnight_status.json"

write_status() {
  python3 - "${1}" "${2}" <<'PY'
import json, sys
from pathlib import Path
p = Path("/data2/hpcshared/medverif-audit/notes/overnight_status.json")
cur = json.loads(p.read_text()) if p.is_file() else {}
cur[sys.argv[1]] = sys.argv[2]
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(cur, indent=2) + "\n")
PY
}

wait_tmux() {
  local session="$1"
  local key="$2"
  while tmux has-session -t "${session}" 2>/dev/null; do
    if ! ( set -a && source ~/kkk/openrouter.env && set +a && python3 scripts/openrouter_budget.py ); then
      write_status budget_stop "credit floor ${MEDVERIF_OR_MIN_CREDIT} or HTTP 402 @ $(date -Is)"
      exit 2
    fi
    sleep 120
  done
  write_status "${key}" "done $(date -Is)"
}

for pair in "t7:t7" "t4_eco:t4_eco" "v4_resume_missing:v4_resume" "t6b_full:t6b_full" "expand_score:expand_score"; do
  sess="${pair%%:*}"
  key="${pair##*:}"
  if tmux has-session -t "${sess}" 2>/dev/null; then
    echo "waiting tmux ${sess}..."
    wait_tmux "${sess}" "${key}" || exit $?
  else
    write_status "${key}" "no session $(date -Is)"
  fi
done

echo "V4 dedupe dry-run..."
python3 scripts/dedupe_verifier_jsonl.py \
  --instances data/v3/instances_cpu_main.jsonl \
  --scores results/raw/v4_ragas_nli.jsonl \
  --dry-run \
  --report notes/dedupe_v4_ragas_nli.json

echo "V4 dedupe write..."
python3 scripts/dedupe_verifier_jsonl.py \
  --instances data/v3/instances_cpu_main.jsonl \
  --scores results/raw/v4_ragas_nli.jsonl \
  --report notes/dedupe_v4_ragas_nli.json

if ( set -a && source ~/kkk/openrouter.env && set +a && python3 scripts/openrouter_budget.py ); then
  bash "${ROOT}/jobs/run_expand_v1b_v5_t2_scope.sh" || write_status expand_v1b_v5_t2 "failed $(date -Is)"
else
  write_status budget_stop "skipped expand v1b/v5 t2 $(date -Is)"
fi

python3 scripts/t7_e1_unit_report.py || true
python3 scripts/t4_eco_report.py || true
python3 scripts/m1_before_after_report.py || true
python3 scripts/build_score_pending.py || true
python3 scripts/aggregate_api_cost.py || true
( set -a && source ~/kkk/openrouter.env && set +a && python3 scripts/openrouter_budget.py ) || true

CREDIT=$(python3 - <<'PY'
import json
from pathlib import Path
p=Path("/data2/hpcshared/medverif-audit/notes/openrouter_credit.json")
print(json.loads(p.read_text()).get("limit_remaining") or 0)
PY
)
if python3 - <<PY
import sys
sys.exit(0 if float("${CREDIT}") >= 5.0 else 1)
PY
then
  echo "T10 prep (credit >= 5)..."
  python3 scripts/t10_fetch_leaderboard.py || true
  python3 scripts/t10_build_hhem_inputs.py || true
  write_status t10 "prep pushed $(date -Is)"
else
  write_status t10 "skipped credit ${CREDIT} $(date -Is)"
fi

python3 scripts/t9_build_input_sets.py
python3 scripts/morning_report.py

/usr/bin/git -C "${ROOT}" add notes/morning_report.md notes/overnight_status.json notes/dedupe_v4_ragas_nli.json \
  data/t9 notes/t9_setup.md config/t9 qc/t10_sample.csv data/t10 notes/t10_sources.json 2>/dev/null || true
/usr/bin/git -C "${ROOT}" add -u notes data/t9 config/t9 qc jobs scripts 2>/dev/null || true
if /usr/bin/git -C "${ROOT}" diff --cached --quiet; then
  echo "nothing to commit"
else
  /usr/bin/git -C "${ROOT}" commit -m "$(cat <<'EOF'
Overnight: V4 dedupe, expand T2 v1b/v5, T9/T10 prep, morning report.

EOF
)"
  /usr/bin/git -C "${ROOT}" push origin master || true
fi
echo "overnight orchestrator done $(date -Is)"
