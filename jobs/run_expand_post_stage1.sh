#!/usr/bin/env bash
# After Stage-1 LLM: rebuild → QC v3 → review packs → scoring packs → push → queue HPC.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
export PYTHONPATH="${ROOT}/src:${ROOT}/scripts/expand:${ROOT}/scripts"

python3 scripts/expand/rebuild_expand.py
python3 scripts/expand/prepare_expand_v3.py
python3 scripts/expand/build_expand_scoring_packs.py

python3 scripts/expand/build_review_packs.py
python3 scripts/expand/audit_pol_flips.py
python3 scripts/build_score_pending.py
python3 scripts/build_t6_scope.py 2>/dev/null || true
python3 scripts/expand/write_expand_status.py --statpearls chunked

YIELD="${ROOT}/data/expand/v3/prepare_stats.json"
if [[ -f "${YIELD}" ]]; then
  echo "post-QC yield:"
  cat "${YIELD}"
fi

bash "${ROOT}/scripts/expand/expand_git_push.sh"
bash "${ROOT}/jobs/run_expand_score_tmux.sh"
