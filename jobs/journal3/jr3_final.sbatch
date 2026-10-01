#!/bin/bash
#SBATCH --job-name=jr3-final
#SBATCH --partition=defq
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --exclude=node001
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/jr3-final_%j.out
# (J3-FINAL) report (notes/journal3_report.md + results/journal3/report.json) + status note, then a LOCAL commit of
# chain-3 outputs only (audit-bot).  No push -- Vinh pushes.
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal3/jr3_env.sh"
set +e
"${PY}" -u scripts/journal3/j3_report.py || echo "chain-3 report failed (see above)"
"${PY}" -u scripts/journal3/j3_status.py || echo "status note failed"
set -e
GIT=/usr/bin/git
paths=()
for p in results/journal3 notes/journal3_report.md notes/journal3_chain_status.md; do [[ -e "$p" ]] && paths+=("$p"); done
[[ ${#paths[@]} -eq 0 ]] && { echo "nothing to commit"; exit 0; }
"${GIT}" add -- "${paths[@]}"
staged=$("${GIT}" diff --cached --name-only -- "${paths[@]}")
if echo "${staged}" | grep -E -i '(iaa_key|answer_key|private_key|\.env$|secret|credential|token)'; then
  echo "ABORT: forbidden file staged" >&2; "${GIT}" reset -q -- "${paths[@]}"; exit 4
fi
if echo "${staged}" | grep -v -E '^(results/journal3/|notes/journal3_report\.md$|notes/journal3_chain_status\.md$)' | grep -q .; then
  echo "ABORT: non-chain-3 path staged" >&2; "${GIT}" reset -q -- "${paths[@]}"; exit 6
fi
big=$(echo "${staged}" | while read -r f; do if [[ -n "$f" && -f "$f" ]] && [[ $(stat -c %s "$f") -gt 50000000 ]]; then echo "$f"; fi; done || true)
if [[ -n "${big}" ]]; then echo "ABORT: staged file >50MB: ${big}" >&2; "${GIT}" reset -q -- "${paths[@]}"; exit 5; fi
if [[ -z "${staged}" ]]; then echo "nothing to commit"; exit 0; fi
# pathspec commit: only chain-3 paths go in, even if other files happen to be staged in this checkout
"${GIT}" -c user.name='audit-bot' -c user.email='audit-bot@users.noreply.github.com' commit -q \
  -m "Journal chain 3 (job ${SLURM_JOB_ID:-local}): FT on real doses, FT x UNF, small local LLM judges" -- "${paths[@]}"
echo "COMMITTED (not pushed): $("${GIT}" log --oneline -1)"
echo "Next: cd ${ROOT} && git pull --rebase --autostash origin master && git push <remote> master"
