#!/bin/bash
#SBATCH --job-name=jr2-UNFHO
#SBATCH --partition=defq
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --array=0-4
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/jr2-UNFHO_%A_%a.out
# (UNF-HO) HELD-OUT evaluation of UNF v1 vs FROZEN v2 (results/journal2/unf_v2_freeze.json); one small checker per
# array task, CPU only, paper's cpuverif env (mirrors jr2_UNFADV.sbatch):
#   0 MiniCheck-RoBERTa  1 MiniCheck-DeBERTa  2 AlignScore-base  3 MiniCheck-Flan-T5-Large  4 AlignScore-large
# (1) held-out real-dose-string set  data/journal2/unf_heldout.jsonl (S/U/anchor), packs orig / unf (v1) / unf_v2
#     -> results/journal2/unf_heldout/scores/<pack>/<checker>.jsonl
# (2) RD pairs changed by v1 or v2   results/journal2/unf_heldout/rd_pack.jsonl, packs orig / unf / unf_v2
#     -> results/journal2/unf_heldout/rd_scores/<pack>/<checker>.jsonl
# Resumable by instance_id.  Identical (claim, evidence) texts reuse scores from other packs and, READ-ONLY, from the
# UNF-ADV caches (results/journal2/unf_adv/scores, results/journal2/impact/rd_unf_scores) -- never written here, so a
# running jr2_UNFADV job is not disturbed; submit with --dependency=afterany:<UNFADV job> to reuse its full caches.
# Markers results/journal2/markers/UNFHO_<checker>.done; the LAST finisher runs scripts/journal2/unf_heldout_report.py
# (notes/unf_heldout.md, results/journal2/unf_heldout/report.json).  No commit, no push, no API calls.
# Smoke test: MEDVERIF_UNFHO_LIMIT=3 sbatch --array=0 jobs/journal2/jr2_UNFHO.sbatch   (no marker, no report)
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal2/jr2_env.sh"
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8} MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8} CUDA_VISIBLE_DEVICES=""
CHECKERS=(t6a_minicheck_roberta t6a_minicheck_deberta t6a_alignscore_base v2a_minicheck v3_alignscore)
CK="${CHECKERS[${SLURM_ARRAY_TASK_ID:-0}]}"
CPUPY="$(jr2_cpuverif_py)"
echo "checker=${CK} cpuverif_py=${CPUPY}"
export MEDVERIF_UNF_ENV=hpc_cpuverif
mkdir -p results/journal2/markers
# inputs are committed; rebuilding is deterministic and only happens if a file is missing
[[ -s data/journal2/unf_heldout.jsonl ]] || "${PY}" -u scripts/journal2/unf_heldout_build.py --stage build
[[ -s results/journal2/unf_heldout/rd_pack.jsonl ]] || "${PY}" -u scripts/journal2/unf_heldout_rdpack.py
LIM=(); [[ -n "${MEDVERIF_UNFHO_LIMIT:-}" ]] && LIM=(--limit "${MEDVERIF_UNFHO_LIMIT}")   # smoke tests only
"${CPUPY}" -u scripts/journal2/unf_heldout_score.py --set ho --checker "${CK}" "${LIM[@]}"
"${CPUPY}" -u scripts/journal2/unf_heldout_score.py --set rd --checker "${CK}" "${LIM[@]}"
if [[ -z "${MEDVERIF_UNFHO_LIMIT:-}" ]]; then
  printf '{"stage":"UNFHO_%s","finished":"%s","slurm_job":"%s_%s"}\n' "${CK}" "$(date -Is)" "${SLURM_ARRAY_JOB_ID:-local}" \
    "${SLURM_ARRAY_TASK_ID:-0}" > "results/journal2/markers/UNFHO_${CK}.done"
fi
(
  flock -x 9
  n=0; for c in "${CHECKERS[@]}"; do [[ -f "results/journal2/markers/UNFHO_${c}.done" ]] && n=$((n+1)); done
  if [[ ${n} -eq ${#CHECKERS[@]} && ! -f results/journal2/markers/UNFHO_report.done ]]; then
    set +e
    "${PY}" -u scripts/journal2/unf_heldout_report.py || echo "unf_heldout_report failed (rerun by hand, CPU only)"
    set -e
    date -Is > results/journal2/markers/UNFHO_report.done
    echo "REPORT WRITTEN: notes/unf_heldout.md results/journal2/unf_heldout/report.json"
  else
    echo "report deferred (${n}/${#CHECKERS[@]} checkers done)"
  fi
) 9> results/journal2/markers/.UNFHO_report.lock
