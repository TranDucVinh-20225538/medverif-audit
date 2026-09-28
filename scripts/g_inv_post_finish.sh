#!/usr/bin/env bash
# Run after G full job completes (instances + attempts present).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
export PYTHONPATH="${ROOT}/src"
export HF_HOME="${ROOT}/.cache/huggingface"
export MEDVERIF_PARA_VAL_MODEL="${MEDVERIF_PARA_VAL_MODEL:-google/gemini-2.5-flash}"

INST="${ROOT}/data/v3/instances_g_inv_paraphrase.jsonl"
ATT="${ROOT}/data/v3/para_attempts_g.jsonl"
if [[ ! -f "${ATT}" ]]; then
  echo "missing ${ATT}" >&2
  exit 1
fi

echo "=== Gemini-only pilot audit ==="
python3 scripts/g_inv_gemini_audit.py | tee -a "${ROOT}/jobs/logs/g_post_finish.log"

echo "=== Rejection report ==="
python3 scripts/g_inv_rejection_report.py | tee -a "${ROOT}/jobs/logs/g_post_finish.log"

if [[ -f "${INST}" ]]; then
  echo "=== Manual review CSV ==="
  python3 scripts/rebuild_inv_manual_review_csv.py | tee -a "${ROOT}/jobs/logs/g_post_finish.log"
else
  echo "warn: ${INST} not found; skip CSV rebuild" >&2
fi

echo "post_finish done $(date -Is)"

if git -C "${ROOT}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  cd "${ROOT}"
  git add \
    src/inv_paraphrase_rules.py \
    src/inv_paraphrase_validator.py \
    src/inv_paraphrase_full_openrouter.py \
    src/inv_paraphrase_openrouter.py \
    src/inv_manual_review_csv.py \
    src/llm_client.py \
    src/score_jsonl.py \
    scripts/g_inv_gemini_audit.py \
    scripts/g_inv_rejection_report.py \
    scripts/g_inv_post_finish.sh \
    scripts/rebuild_inv_manual_review_csv.py \
    jobs/run_g_full.sh \
    jobs/run_g_full_tmux.sh \
    jobs/lib/openrouter_retry.sh \
    data/v3/para_attempts_g.jsonl \
    data/v3/instances_g_inv_paraphrase.jsonl \
    qc/inv_manual_review.csv \
    notes/g_full_run_report.md \
    notes/g_inv_gemini_audit.json \
    notes/g_inv_rejection_report.md \
    notes/g_inv_rejection_report.json \
    notes/g_inv_validator_model.json 2>/dev/null || true
  if ! git diff --staged --quiet; then
    git commit -m "$(cat <<'EOF'
G full INV paraphrase: resume, retries, incremental QC outputs.

OpenRouter backoff and gen_error handling; Gemini validator audit and rejection report after full run.
EOF
)"
    git push origin HEAD
  fi
fi
