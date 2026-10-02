#!/usr/bin/env bash
# Journal 5 / RD2: pre-registered expansion of the real-dose set.  Run on the HPC LOGIN node (bright92), step by step:
#
#   bash jobs/run_rd2_chain.sh preflight          # prereg commit + freeze + weights + env + key presence + cost dry-run (no GPU/API)
#   bash jobs/run_rd2_chain.sh gen [--parallel N] # sbatch the 4 open generators (array 0-3, default %1 = one GPU at a time)
#   bash jobs/run_rd2_chain.sh or-gen             # OpenRouter generators (gpt-4o-mini, gemma-3-27b) HERE (needs egress), $ cap
#   bash jobs/run_rd2_chain.sh post               # merge answers -> extract/classify -> basis check -> UNF packs -> adjudication sheet (CPU, seconds)
#   bash jobs/run_rd2_chain.sh score [--judges SPEC] [--parallel N]   # sbatch small checkers (CPU), local LLM judges + FT (GPU)
#   bash jobs/run_rd2_chain.sh api-judges         # the 2 API paper judges (Llama-3.3-70B RAGAS, Mistral-24B MedScore) HERE, $ cap
#   bash jobs/run_rd2_chain.sh report             # PROVISIONAL report (auto labels) until the pharmacist sheet is filled
#   bash jobs/run_rd2_chain.sh status             # counts per stage
#   bash jobs/run_rd2_chain.sh commit             # git add ONLY RD2 outputs, commit, pull --no-rebase, push (never force)
# Env: MEDVERIF_PYTHON (vllm env), MEDVERIF_CPUVERIF_PY, MEDVERIF_RD2_MAX_USD (default 3 = cap for ALL RD2 OpenRouter spend).
set -euo pipefail
ROOT="${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}"
CMD="${1:-}"; shift || true
PAR=1; JSPEC="0-6,8-9"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --parallel) PAR="$2"; shift ;;
    --judges) JSPEC="$2"; shift ;;
    *) echo "unknown arg $1" >&2; exit 1 ;;
  esac; shift
done
source "${ROOT}/jobs/journal5/rd2_env.sh"
J=jobs/journal5
R=results/journal5/rd2
D=${R}/real_dose

prereg_commit() { git log --diff-filter=A --format=%H -- prereg/rd2_prereg.md | tail -1; }

case "${CMD}" in
preflight)
  PC="$(prereg_commit)"
  [[ -n "${PC}" ]] || { echo "BLOCKER: prereg/rd2_prereg.md not in git history" >&2; exit 2; }
  echo "prereg commit: ${PC} ($(git log -1 --format='%ci %s' "${PC}"))"
  if git ls-tree -r --name-only "${PC}" -- "${D}" | grep -qE 'answers|instances|scores'; then
    echo "BLOCKER: the prereg commit already contains answers/instances/scores" >&2; exit 2; fi
  CH="$(git diff --name-only "${PC}" -- prereg/rd2_prereg.md prereg/rd2_freeze.json "${D}/questions.jsonl" "${R}/labels/labels.jsonl")"
  [[ -z "${CH}" ]] || { echo "BLOCKER: pre-registered files changed since ${PC}: ${CH}" >&2; exit 2; }
  FIRST_ANS="$(git log --diff-filter=A --format=%H -- "${D}/answers.jsonl" | tail -1)"
  if [[ -n "${FIRST_ANS}" ]] && ! git merge-base --is-ancestor "${PC}" "${FIRST_ANS}"; then
    echo "BLOCKER: answers were committed before the prereg commit" >&2; exit 2; fi
  "${PY}" - <<'PYEOF'
import json, sys
sys.path.insert(0, "scripts/journal5")
import rd2_common as C
p = C.freeze_problems()
print("freeze check:", "OK" if not p else p)
print("runner/analysis files changed since freeze (document in prereg/rd2_amendments.md):", C.runner_changes() or "none")
m = json.load(open("results/journal3/models.json"))
for s in ("llama31_8b", "qwen25_14b", "medgemma_27b", "baichuan_m2_32b", "qwen25_7b", "medgemma_4b", "qwen25_0p5b", "qwen25_1p5b", "qwen25_3b"):
    r = m.get(s) or {}
    print("weights %-16s %-4s %s" % (s, r.get("status"), (r.get("revision") or "")[:12]))
sys.exit(1 if p else 0)
PYEOF
  "${PY}" -c "import vllm, sys; print('vllm', vllm.__version__, 'python', sys.version.split()[0])" || echo "WARNING: vllm not importable with ${PY}"
  ( rd2_load_api_env; "${PY}" scripts/journal5/rd2_generate.py --backend openrouter --dry-run | tail -1 )
  "${PY}" scripts/journal5/rd2_generate.py --backend vllm --dry-run | tail -4
  df -h "${ROOT}" | tail -1
  sinfo -p defq -o '%N %G %t' 2>/dev/null | head -5 || true
  ;;
gen)
  JID=$(sbatch --parsable --array="0-3%${PAR}" ${J}/rd2_GEN.sbatch)
  echo "submitted rd2-GEN ${JID} (array 0-3%${PAR}); logs: jobs/logs/rd2-GEN_${JID}_<i>.out"
  echo "${JID}" > ${R}/gen_job_id.txt
  ;;
or-gen)
  rd2_load_api_env
  for attempt in 1 2 3; do
    if "${PY}" -u scripts/journal5/rd2_generate.py --backend openrouter --max-usd "${MEDVERIF_RD2_MAX_USD}" --passes 3; then break; fi
    echo "or-gen attempt ${attempt} failed; retrying in 60 s (resumes)" >&2; sleep 60
  done
  ;;
post)
  "${PY}" -u scripts/journal5/rd2_generate.py --merge
  "${PY}" -u scripts/journal5/rd2_extract.py --force
  "${PY}" -u scripts/journal5/rd2_basis_check.py
  "${PY}" -u scripts/journal5/rd2_unf_pack.py
  "${PY}" -u scripts/journal5/rd2_adjudication_sheet.py
  ;;
score)
  [[ -s ${D}/instances.jsonl && -s ${D}/unf/rd_pack.jsonl ]] || { echo "run 'post' first" >&2; exit 2; }
  S=$(sbatch --parsable ${J}/rd2_SMALL.sbatch); echo "submitted rd2-SMALL ${S} (CPU, 5 checkers)"
  G=$(sbatch --parsable --array="${JSPEC}%${PAR}" ${J}/rd2_JG.sbatch); echo "submitted rd2-JG ${G} (array ${JSPEC}%${PAR})"
  F=$(sbatch --parsable --array="0-7%${PAR}" ${J}/rd2_FT.sbatch); echo "submitted rd2-FT ${F} (array 0-7%${PAR})"
  printf '{"small":"%s","judges":"%s","ft":"%s","submitted":"%s"}\n' "$S" "$G" "$F" "$(date -Is)" > ${R}/score_jobs.json
  ;;
api-judges)
  rd2_load_api_env
  export MEDVERIF_JR_API_PY="${PY}"
  for attempt in 1 2 3; do
    if "${PY}" -u scripts/journal2/rd_score.py --part judges --instances ${D}/instances.jsonl --chunk 100; then break; fi
    echo "api-judges attempt ${attempt} failed; retrying in 60 s (resumes by instance_id)" >&2; sleep 60
  done
  ;;
report)
  "${PY}" -u scripts/journal5/rd2_report.py ${RD2_ADJUDICATED:+--adjudicated "${RD2_ADJUDICATED}"}
  echo "-> ${R}/report.md"
  ;;
status)
  wc -l ${D}/answers/*.jsonl ${D}/answers.jsonl ${D}/instances.jsonl ${D}/scores/*.jsonl ${D}/unf/*.jsonl \
        ${D}/unf/scores_unf_v*/*.jsonl ${R}/judges/*.jsonl ${R}/ft/*.jsonl 2>/dev/null || true
  ls ${R}/markers ${R}/markers_j3 2>/dev/null || true
  "${PY}" - <<'PYEOF'
import sys; sys.path.insert(0, "scripts/journal5")
import rd2_generate as G
print("RD2 OpenRouter spend so far: $%.4f (cap $%s)" % (G.rd2_spent_usd(), __import__("os").environ.get("MEDVERIF_RD2_MAX_USD")))
PYEOF
  squeue -u "${USER}" -o '%.14i %.12j %.8T %.10M %.22R' 2>/dev/null | grep -E 'rd2-|JOBID' || true
  ;;
commit)
  git add -- ${R} notes/rd2_run_status.md prereg/rd2_amendments.md 2>/dev/null || git add -- ${R}
  git status --short -- ${R} | head -20
  git -c user.name="${GIT_AUTHOR_NAME:-audit-bot}" -c user.email="${GIT_AUTHOR_EMAIL:-audit-bot@users.noreply.github.com}" \
    commit -m "journal5: RD2 answers, instances, scores (provisional report)" -- ${R} $(ls notes/rd2_run_status.md prereg/rd2_amendments.md 2>/dev/null) || true
  git pull --no-rebase --no-edit
  git push
  ;;
*)
  sed -n '2,15p' "$0"; exit 1 ;;
esac
