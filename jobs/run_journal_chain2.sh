#!/usr/bin/env bash
# Journal (JHIR) chain 2: (RD) real-world dose errors from FDA labels, (UNF) unit-normalization fix re-scored
# with the five small checkers + paired bootstrap CIs, (AT) token attributions / surface-overlap mechanism
# -> final reports + LOCAL commit.  Independent of chain 1 (jobs 62055-62064): own results/journal2/, own
# markers, own real-dose API ledger (MEDVERIF_RD_CAP_USD, default $5).  Run on the HPC login node.
#
#   bash jobs/run_journal_chain2.sh --dry-run          # preflight + `sbatch --test-only` for every stage, submits nothing
#   bash jobs/run_journal_chain2.sh                    # submit everything
#   bash jobs/run_journal_chain2.sh --only UNF,AT      # subset (final stage always added)
# Env: MEDVERIF_PYTHON (default vllm env python), MEDVERIF_CPUVERIF_PY (default: conda env cpuverif),
#      MEDVERIF_RD_CAP_USD (default 5).
set -euo pipefail
ROOT="${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}"
cd "${ROOT}"
export MEDVERIF_PYTHON="${MEDVERIF_PYTHON:-/data2/cmdir/home/toandq/.conda/envs/vllm/bin/python}"
DRY=0; ONLY="RD,UNF,AT"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY=1 ;;
    --only) ONLY="$2"; shift ;;
    *) echo "unknown arg $1" >&2; exit 1 ;;
  esac; shift
done
J=jobs/journal2
mkdir -p jobs/logs results/journal2
has() { [[ ",${ONLY}," == *",$1,"* ]]; }

echo "== preflight (no API calls)"
if [[ -f /data2/shared/apps/conda/etc/profile.d/conda.sh ]]; then set +u; source /data2/shared/apps/conda/etc/profile.d/conda.sh; set -u; fi
source "${ROOT}/jobs/lib/hf_env.sh"; medverif_hf_env
PYTHONPATH="${ROOT}/src:${ROOT}/analysis:${ROOT}/scripts:${ROOT}/scripts/journal:${ROOT}/scripts/journal2" \
  "${MEDVERIF_PYTHON}" scripts/journal2/jr2_preflight.py --stages "${ONLY}" || {
  echo "preflight found blockers (see 'blockers' above); fix them before submitting" >&2; [[ ${DRY} -eq 1 ]] || exit 2; }
if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then echo "WARNING: tracked files modified in ${ROOT}; final stage commits only chain-2 outputs"; fi

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
if has RD; then
  sub RD1 "" ${J}/jr2_RD1_generate.sbatch
  sub RD4j "afterok:${ID[RD1]}" ${J}/jr2_RD4_judges.sbatch
  sub RD4s "afterok:${ID[RD1]}" ${J}/jr2_RD4_small.sbatch
  FINAL_DEPS+=("${ID[RD4j]}" "${ID[RD4s]}")
fi
if has UNF; then sub UNF "" ${J}/jr2_UNF_score.sbatch; FINAL_DEPS+=("${ID[UNF]}"); fi
if has AT; then sub AT1 "" ${J}/jr2_AT1_attribution.sbatch; FINAL_DEPS+=("${ID[AT1]}"); fi
if [[ ${#FINAL_DEPS[@]} -eq 0 ]]; then echo "nothing selected (--only RD,UNF,AT)" >&2; exit 1; fi
FDEP="afterany$(printf ':%s' "${FINAL_DEPS[@]}")"
sub FINAL "${FDEP}" ${J}/jr2_final.sbatch

if [[ ${DRY} -eq 0 ]]; then
  { printf '{'; first=1; for k in "${!ID[@]}"; do [[ $first -eq 0 ]] && printf ','; printf '"%s":"%s"' "$k" "${ID[$k]}"; first=0; done
    printf ',"submitted":"%s"}\n' "$(date -Is)"; } > results/journal2/chain_jobs.json
  echo "job ids -> results/journal2/chain_jobs.json"
fi
cat <<MSG

Monitor:
  squeue -u \$USER -o '%.12i %.16j %.8T %.10M %.20R' | grep -E 'jr2-|JOBID'
  tail -f jobs/logs/jr2-*_<jobid>.out         (UNF array: jobs/logs/jr2-UNF-score_<arrayid>_<0-4>.out)
  ls results/journal2/markers/                (one .done per finished RD stage)
  wc -l results/journal2/unf/scores/*/*.jsonl results/journal2/attribution/attr_*.jsonl
  cat notes/journal_chain2_status.md          (after the final stage)
Rerun a failed stage: sbatch jobs/journal2/<stage>.sbatch   (all stages resume; MEDVERIF_JR2_FORCE=<stage> forces an
  RD stage), then sbatch jobs/journal2/jr2_final.sbatch.  Final stage commits locally only; then push.
MSG
