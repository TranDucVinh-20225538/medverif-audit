#!/bin/bash
#SBATCH --job-name=jr2-UNFADV
#SBATCH --partition=defq
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --array=0-4
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/jr2-UNFADV_%A_%a.out
# (UNF-ADV + IMPACT) one small checker per array task, CPU only, paper's cpuverif env:
#   0 MiniCheck-RoBERTa  1 MiniCheck-DeBERTa  2 AlignScore-base  3 MiniCheck-Flan-T5-Large  4 AlignScore-large
# (1) adversarial unit-spelling set   data/journal2/unf_adversarial.jsonl, packs orig / unf (v1) / unf_v2 (post-hoc)
#     -> results/journal2/unf_adv/scores/<pack>/<checker>.jsonl
# (2) real-dose pairs changed by UNF  results/journal2/impact/rd_unf_pack.jsonl, packs orig / unf
#     -> results/journal2/impact/rd_unf_scores/<pack>/<checker>.jsonl
# Resumable by instance_id (identical inputs across packs reuse one score).  Markers:
# results/journal2/markers/UNFADV_<checker>.done.  The LAST task to finish (all 5 markers present) runs the CPU
# reports: scripts/journal2/unf_adv_report.py (notes/unf_adversarial.md) and scripts/journal2/impact_estimate.py
# (notes/impact_estimate.md).  No commit, no push, no API calls.
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal2/jr2_env.sh"
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8} MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8} CUDA_VISIBLE_DEVICES=""
CHECKERS=(t6a_minicheck_roberta t6a_minicheck_deberta t6a_alignscore_base v2a_minicheck v3_alignscore)
CK="${CHECKERS[${SLURM_ARRAY_TASK_ID:-0}]}"
CPUPY="$(jr2_cpuverif_py)"
echo "checker=${CK} cpuverif_py=${CPUPY}"
export MEDVERIF_UNF_ENV=hpc_cpuverif
mkdir -p results/journal2/markers
# both inputs are committed; rebuilding is deterministic and only happens if a file is missing
[[ -s data/journal2/unf_adversarial.jsonl ]] || "${PY}" -u scripts/journal2/unf_adv_build.py
[[ -s results/journal2/impact/rd_unf_pack.jsonl ]] || "${PY}" -u scripts/journal2/impact_estimate.py
LIM=(); [[ -n "${MEDVERIF_UNFADV_LIMIT:-}" ]] && LIM=(--limit "${MEDVERIF_UNFADV_LIMIT}")   # smoke tests only
"${CPUPY}" -u scripts/journal2/unf_adv_score.py --set adv    --checker "${CK}" "${LIM[@]}"
"${CPUPY}" -u scripts/journal2/unf_adv_score.py --set rd_unf --checker "${CK}" "${LIM[@]}"
if [[ -z "${MEDVERIF_UNFADV_LIMIT:-}" ]]; then
  printf '{"stage":"UNFADV_%s","finished":"%s","slurm_job":"%s_%s"}\n' "${CK}" "$(date -Is)" "${SLURM_ARRAY_JOB_ID:-local}" \
    "${SLURM_ARRAY_TASK_ID:-0}" > "results/journal2/markers/UNFADV_${CK}.done"
fi
# last finisher writes the reports (flock: only one task at a time)
(
  flock -x 9
  n=0; for c in "${CHECKERS[@]}"; do [[ -f "results/journal2/markers/UNFADV_${c}.done" ]] && n=$((n+1)); done
  if [[ ${n} -eq ${#CHECKERS[@]} && ! -f results/journal2/markers/UNFADV_report.done ]]; then
    set +e
    "${PY}" -u scripts/journal2/unf_adv_report.py  || echo "unf_adv_report failed (rerun by hand, CPU only)"
    "${PY}" -u scripts/journal2/impact_estimate.py || echo "impact_estimate failed (rerun by hand, CPU only)"
    set -e
    date -Is > results/journal2/markers/UNFADV_report.done
    echo "REPORTS WRITTEN: notes/unf_adversarial.md notes/impact_estimate.md"
  else
    echo "reports deferred (${n}/${#CHECKERS[@]} checkers done)"
  fi
) 9> results/journal2/markers/.UNFADV_report.lock
