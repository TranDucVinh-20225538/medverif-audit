#!/usr/bin/env bash
# Journal (JHIR) revision chain: (A) threshold robustness + bootstrap CIs, (B) real-RAG expansion,
# (C) second fine-tune (AlignScore-large, MiniCheck-Flan-T5; ANLI ratios 0.5/1/2) -> final local commit.
# Submits dependent Slurm jobs (afterok / afterany, --kill-on-invalid-dep=yes). Run on the HPC login node.
#
#   bash jobs/run_journal_chain.sh --dry-run        # preflight + `sbatch --test-only` for every stage, submits nothing
#   bash jobs/run_journal_chain.sh                  # submit everything
#   bash jobs/run_journal_chain.sh --only A,C       # subset (final stage always added)
# Env: MEDVERIF_PYTHON (default vllm env python), MEDVERIF_JR_CAP_USD (default 5), JR_N_QUESTIONS (200).
set -euo pipefail
ROOT="${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}"
cd "${ROOT}"
export MEDVERIF_PYTHON="${MEDVERIF_PYTHON:-/data2/cmdir/home/toandq/.conda/envs/vllm/bin/python}"
DRY=0; ONLY="A,B,C"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY=1 ;;
    --only) ONLY="$2"; shift ;;
    *) echo "unknown arg $1" >&2; exit 1 ;;
  esac; shift
done
J=jobs/journal
mkdir -p jobs/logs results/journal
has() { [[ ",${ONLY}," == *",$1,"* ]]; }

echo "== preflight (no API calls)"
PYTHONPATH="${ROOT}/src:${ROOT}/analysis:${ROOT}/scripts:${ROOT}/scripts/journal" "${MEDVERIF_PYTHON}" scripts/journal/jr_preflight.py --stages "${ONLY}" || {
  echo "preflight found blockers (see 'blockers' above); fix them before submitting" >&2; [[ ${DRY} -eq 1 ]] || exit 2; }
if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then echo "WARNING: tracked files modified in ${ROOT}; final stage commits only journal outputs"; fi

declare -A ID
sub() {  # sub NAME DEPSPEC SCRIPT
  local name="$1" dep="$2" script="$3" args=(--parsable --kill-on-invalid-dep=yes)
  [[ -n "${dep}" ]] && args+=(--dependency="${dep}")
  if [[ ${DRY} -eq 1 ]]; then
    echo "-- sbatch ${args[*]} ${script}"
    sbatch --test-only "${script}" 2>&1 | sed 's/^/   /' || true
    ID[$name]="DRY_${name}"
  else
    ID[$name]=$(sbatch "${args[@]}" "${script}")
    echo "submitted ${name}: ${ID[$name]}  (${script}${dep:+, dep ${dep}})"
  fi
}
FINAL_DEPS=()
if has A; then sub A "" ${J}/jr_A_threshold.sbatch; FINAL_DEPS+=("${ID[A]}"); fi
if has B; then
  sub B1 "" ${J}/jr_B1_questions.sbatch
  sub B2 "afterok:${ID[B1]}" ${J}/jr_B2_retrieve.sbatch
  sub B3 "afterok:${ID[B2]}" ${J}/jr_B3_generate.sbatch
  sub B4 "afterok:${ID[B3]}" ${J}/jr_B4_small.sbatch
  sub B4g "afterok:${ID[B3]}" ${J}/jr_B4_bespoke.sbatch
  FINAL_DEPS+=("${ID[B4]}" "${ID[B4g]}")
fi
if has C; then
  sub C1 "" ${J}/jr_C1_ftdata.sbatch
  sub C2 "afterok:${ID[C1]}" ${J}/jr_C2_train.sbatch
  CDEP="afterok:${ID[C2]}"
  if has B; then CDEP="${CDEP},afterany:${ID[B3]}"; fi   # RAG pack if it exists; eval still runs if B failed
  sub C3 "${CDEP}" ${J}/jr_C3_eval.sbatch
  FINAL_DEPS+=("${ID[C3]}")
fi
FDEP="afterany$(printf ':%s' "${FINAL_DEPS[@]}")"
sub FINAL "${FDEP}" ${J}/jr_final.sbatch

if [[ ${DRY} -eq 0 ]]; then
  { printf '{'; first=1; for k in "${!ID[@]}"; do [[ $first -eq 0 ]] && printf ','; printf '"%s":"%s"' "$k" "${ID[$k]}"; first=0; done
    printf ',"submitted":"%s"}\n' "$(date -Is)"; } > results/journal/chain_jobs.json
  echo "job ids -> results/journal/chain_jobs.json"
fi
cat <<MSG

Monitor:
  squeue -u \$USER -o '%.10i %.14j %.8T %.10M %.20R' | grep -E 'jr-|JOBID'
  tail -f jobs/logs/jr-*_<jobid>.out          (array tasks: jr-C2-train_<arrayid>_<task>.out)
  ls results/journal/markers/                 (one .done per finished stage)
  cat notes/journal_chain_status.md           (after the final stage)
Rerun a failed stage: sbatch jobs/journal/<stage>.sbatch   (resumable; finished stages skip via markers;
  MEDVERIF_JR_FORCE=<stage> forces one stage). Final stage commits locally only; then: git pull --rebase && git push origin HEAD:master
MSG
