#!/usr/bin/env bash
# Journal chain 3 (ONE submission): (FT) chain-1 fine-tuned checkers on the real-dose answers + FT x UNF (held-out
# set and RD pairs, raw / UNF v1 / frozen UNF v2), (JG) small local LLM judges with vLLM (Qwen2.5 0.5B-14B ladder,
# Llama-3.1-8B, MedGemma-4B-it; RAGAS-NLI paper prompt) on the DOSE card, the journal RAG pack and RD
# -> final report + LOCAL commit of chain-3 outputs only.  Own results/journal3/ and markers; no API calls.
# Run on the HPC LOGIN node (the model download step needs Hub egress; compute nodes run offline).
#
#   bash jobs/run_journal_chain3.sh --dry-run        # preflight + download check (no download) + `sbatch --test-only`
#   bash jobs/run_journal_chain3.sh                  # download missing judge weights here, then submit everything
#   bash jobs/run_journal_chain3.sh --only FT        # subset (FT, JG; final stage always added)
#   options: --with-32b (adds Qwen2.5-32B, +65.5 GB), --no-download (use what is cached), --judges 0,3-5 (array spec)
# Env: MEDVERIF_PYTHON (default vllm env python), MEDVERIF_CPUVERIF_PY, HF_TOKEN (else ~/.cache/huggingface/token).
set -euo pipefail
ROOT="${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}"
DRY=0; ONLY="FT,JG"; DL=1; W32=0; JSPEC="0-6"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY=1 ;;
    --only) ONLY="$2"; shift ;;
    --no-download) DL=0 ;;
    --with-32b) W32=1 ;;
    --judges) JSPEC="$2"; shift ;;
    *) echo "unknown arg $1" >&2; exit 1 ;;
  esac; shift
done
source "${ROOT}/jobs/journal3/jr3_env.sh"
J=jobs/journal3
has() { [[ ",${ONLY}," == *",$1,"* ]]; }
DLSPEC="${JSPEC}"; [[ ${W32} -eq 1 ]] && DLSPEC="${JSPEC},7"

echo "== preflight (no GPU, no API)"
"${PY}" scripts/journal3/j3_preflight.py --stages "${ONLY}" --judges "${DLSPEC}" || {
  echo "preflight found blockers (see 'blockers' above); fix them before submitting" >&2; [[ ${DRY} -eq 1 ]] || exit 2; }
if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
  echo "NOTE: tracked files modified in ${ROOT} (known local edits); chain 3 does not import them and commits only chain-3 outputs"
fi

if has JG && [[ ${DL} -eq 1 ]]; then
  echo "== judge weights: access check$([[ ${DRY} -eq 1 ]] && echo ' (check only)' || echo ' + download') -> results/journal3/models.json"
  ( unset HF_HUB_OFFLINE TRANSFORMERS_OFFLINE
    "${PY}" -u scripts/journal3/j3_download.py --models "${DLSPEC}" $([[ ${DRY} -eq 1 ]] && echo --check-only) ) || {
    echo "download step failed (see above); judge tasks without weights will fail, FT is unaffected" >&2; }
fi

declare -A ID
sub() {  # sub NAME DEPSPEC SCRIPT [extra sbatch args...]
  local name="$1" dep="$2" script="$3"; shift 3
  local args=(--parsable --kill-on-invalid-dep=yes "$@")
  [[ -n "${dep}" ]] && args+=(--dependency="${dep}")
  if [[ ${DRY} -eq 1 ]]; then
    echo "-- sbatch ${args[*]} ${script}"
    sbatch --test-only "$@" "${script}" 2>&1 | sed 's/^/   /' || true
    ID[$name]="DRY_${name}"
  else
    ID[$name]=$(sbatch "${args[@]}" "${script}")
    echo "submitted ${name}: ${ID[$name]}  (${script} $*${dep:+, dep ${dep}})"
  fi
}
FINAL_DEPS=()
if has FT; then sub FT "" ${J}/jr3_FT.sbatch; FINAL_DEPS+=("${ID[FT]}"); fi
if has JG; then
  sub JG "" ${J}/jr3_JG.sbatch --array="${JSPEC}%3"; FINAL_DEPS+=("${ID[JG]}")
  if [[ ${W32} -eq 1 ]]; then sub JG32 "" ${J}/jr3_JG.sbatch --array=7 --mem=128G --time=10:00:00; FINAL_DEPS+=("${ID[JG32]}"); fi
fi
if [[ ${#FINAL_DEPS[@]} -eq 0 ]]; then echo "nothing selected (--only FT,JG)" >&2; exit 1; fi
FDEP="afterany$(printf ':%s' "${FINAL_DEPS[@]}")"
sub FINAL "${FDEP}" ${J}/jr3_final.sbatch

if [[ ${DRY} -eq 0 ]]; then
  { printf '{'; first=1; for k in "${!ID[@]}"; do [[ $first -eq 0 ]] && printf ','; printf '"%s":"%s"' "$k" "${ID[$k]}"; first=0; done
    printf ',"submitted":"%s"}\n' "$(date -Is)"; } > results/journal3/chain_jobs.json
  echo "job ids -> results/journal3/chain_jobs.json"
fi
cat <<MSG

Monitor:
  squeue -u \$USER -o '%.14i %.12j %.8T %.10M %.22R' | grep -E 'jr3-|JOBID'
  tail -f jobs/logs/jr3-JG_<arrayid>_<i>.out    (FT: jobs/logs/jr3-FT_<arrayid>_<i>.out)
  ls results/journal3/markers/                  (J3_FT_<run>.done / J3_JG_<slug>.done; 'skipped' inside = gated/unavailable)
  wc -l results/journal3/ft/scores/*.jsonl results/journal3/judges/scores/*.jsonl
  cat notes/journal3_chain_status.md            (after the final stage)
Rerun a failed task: sbatch --array=<i> jobs/journal3/jr3_JG.sbatch (or jr3_FT.sbatch) -- resumes by instance_id --
  then sbatch jobs/journal3/jr3_final.sbatch.  MEDVERIF_J3_FORCE=<stage>|all ignores a marker.  Final stage commits locally only.
MSG
