#!/bin/bash
#SBATCH --job-name=jr2-final
#SBATCH --partition=defq
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/jr2-final_%j.out
# Final: RD5 / UNF / AT2 reports (bootstrap CIs, CPU) + status note, then a LOCAL commit of chain-2 outputs
# only (neutral author). No push -- the user pushes.
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal2/jr2_env.sh"
set +e
[[ -s results/journal2/real_dose/instances.jsonl ]] && { "${PY}" -u scripts/journal2/rd_report.py || echo "RD report failed (see above)"; }
ls results/journal2/unf/scores/unf/*.jsonl >/dev/null 2>&1 && { "${PY}" -u scripts/journal2/unf_report.py || echo "UNF report failed (see above)"; }
ls results/journal2/attribution/attr_*.jsonl >/dev/null 2>&1 && { "${PY}" -u scripts/journal2/at_report.py || echo "AT report failed (see above)"; }
"${PY}" -u scripts/journal2/jr2_status.py || echo "status note failed"
set -e
GIT=/usr/bin/git
paths=(notes/real_dose_errors.md notes/unit_normalization_fix.md notes/attribution_mechanism.md
       notes/journal_chain2_status.md results/journal2 data/journal2 qc/real_dose_errors_check.csv)
for p in "${paths[@]}"; do [[ -e "$p" ]] && "${GIT}" add -- "$p"; done
if "${GIT}" diff --cached --name-only | grep -E -i '(iaa_key|answer_key|private_key|\.env$|openrouter\.env|secret|credential|token)'; then
  echo "ABORT: forbidden file staged" >&2; "${GIT}" reset -q; exit 4
fi
if "${GIT}" diff --cached --name-only | grep -E '^(results/journal/|scripts/journal/|jobs/journal/|jobs/run_journal_chain\.sh)'; then
  echo "ABORT: chain-1 file staged" >&2; "${GIT}" reset -q; exit 6
fi
big=$("${GIT}" diff --cached --name-only | while read -r f; do if [[ -f "$f" ]] && [[ $(stat -c %s "$f") -gt 50000000 ]]; then echo "$f"; fi; done || true)
if [[ -n "${big}" ]]; then echo "ABORT: staged file >50MB: ${big}" >&2; "${GIT}" reset -q; exit 5; fi
if "${GIT}" diff --cached --quiet; then echo "nothing to commit"; exit 0; fi
"${GIT}" -c user.name='audit-bot' -c user.email='audit-bot@users.noreply.github.com' commit -q \
  -m "Journal chain 2 (job ${SLURM_JOB_ID:-local}): real-dose errors, unit-normalization fix, attribution outputs"
echo "COMMITTED (not pushed): $("${GIT}" log --oneline -1)"
echo "Next: cd ${ROOT} && git pull --rebase && git push origin HEAD:master"
