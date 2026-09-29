#!/usr/bin/env bash
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
LOG="${ROOT}/jobs/logs/main_ext_continue_rerun_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "main_ext continue start $(date -Is)"

if [[ -f ~/kkk/openrouter.env ]]; then
  set -a && source ~/kkk/openrouter.env && set +a
fi
export PYTHONPATH="${ROOT}/src:${ROOT}/scripts/expand"
export MEDVERIF_USE_OPENROUTER=1
export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export MEDVERIF_EXPAND_GEN_TOKENIZER="${MEDVERIF_EXPAND_GEN_TOKENIZER:-Qwen/Qwen2.5-7B-Instruct}"

python3 scripts/main_ext_continue_stage1.py \
  --skip-candidate-append \
  --max-new-candidates 1000 \
  --target-bases 60 \
  --budget-usd 1.0

python3 scripts/main_ext_disjointness.py || true
echo "main_ext continue done $(date -Is)"

/usr/bin/git -C "${ROOT}" add \
  data/main_ext notes/main_ext_funnel.json notes/main_ext_funnel.md notes/main_ext_manifest.json \
  qc/main_ext_review.csv data/main_ext/stage1/llm_stats.json 2>/dev/null || true
if /usr/bin/git -C "${ROOT}" diff --cached --quiet; then
  echo "main_ext post-rerun: nothing to commit"
else
  MSG=$(mktemp)
  printf '%s\n\n%s\n' \
    'feat(main_ext): stage1 continue + updated funnel/manifest' \
    'Incremental textbook candidates; rebuild toward 60 whitelist-kept bases under $1 continue ledger.' >"${MSG}"
  /usr/bin/git -C "${ROOT}" commit -F "${MSG}"
  rm -f "${MSG}"
  /usr/bin/git -C "${ROOT}" push origin master || true
fi
