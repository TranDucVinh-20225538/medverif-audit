#!/bin/bash
#SBATCH --job-name=jr-final
#SBATCH --partition=defq
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=01:30:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/jr-final_%j.out
# Final: reports + status note, then a LOCAL commit (neutral author). No push -- the user pushes.
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal/jr_env.sh"
set +e
"${PY}" -u scripts/journal/jr_rag_report.py  || echo "rag report failed (see above)"
"${PY}" -u scripts/journal/jr_ft_report.py   || echo "ft report failed (see above)"
"${PY}" -u scripts/journal/jr_status.py      || echo "status note failed"
set -e
GIT=/usr/bin/git
paths=(notes/threshold_robustness.md notes/journal_rag_expansion.md notes/journal_second_finetune.md
       notes/journal_chain_status.md results/journal data/journal qc/jr_rag_human_check.csv)
for p in "${paths[@]}"; do [[ -e "$p" ]] && "${GIT}" add -- "$p"; done
if "${GIT}" diff --cached --name-only | grep -E -i '(iaa_key|answer_key|private_key|\.env$|openrouter\.env|secret|credential|token)'; then
  echo "ABORT: forbidden file staged" >&2; "${GIT}" reset -q; exit 4
fi
big=$("${GIT}" diff --cached --name-only | while read -r f; do if [[ -f "$f" ]] && [[ $(stat -c %s "$f") -gt 50000000 ]]; then echo "$f"; fi; done || true)
if [[ -n "${big}" ]]; then echo "ABORT: staged file >50MB: ${big}" >&2; "${GIT}" reset -q; exit 5; fi
if "${GIT}" diff --cached --quiet; then echo "nothing to commit"; exit 0; fi
"${GIT}" -c user.name='audit-bot' -c user.email='audit-bot@users.noreply.github.com' commit -q \
  -m "Journal chain (job ${SLURM_JOB_ID:-local}): threshold robustness, real-RAG expansion, second fine-tune outputs"
echo "COMMITTED (not pushed): $("${GIT}" log --oneline -1)"
echo "Next: cd ${ROOT} && git pull --rebase && git push origin HEAD:master"
