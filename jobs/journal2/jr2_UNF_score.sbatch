#!/bin/bash
#SBATCH --job-name=jr2-UNF-score
#SBATCH --partition=defq
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=10:00:00
#SBATCH --array=0-4
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/jr2-UNF-score_%A_%a.out
# (UNF) re-score the unit-normalization-fix packs with one small checker per array task (cpuverif env, CPU):
#   0 MiniCheck-RoBERTa  1 MiniCheck-DeBERTa  2 AlignScore-base  3 MiniCheck-Flan-T5-Large  4 AlignScore-large
# pack orig = original text of the rows UNF changes (+ unchanged rows without a stored paper score),
# pack unf  = the same rows after UNF.  Resumable by instance_id.  Report + bootstrap CIs run in jr2_final.
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal2/jr2_env.sh"
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8} MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8} CUDA_VISIBLE_DEVICES=""
CHECKERS=(t6a_minicheck_roberta t6a_minicheck_deberta t6a_alignscore_base v2a_minicheck v3_alignscore)
CK="${CHECKERS[${SLURM_ARRAY_TASK_ID:-0}]}"
CPUPY="$(jr2_cpuverif_py)"
echo "checker=${CK} cpuverif_py=${CPUPY}"
export MEDVERIF_UNF_ENV=hpc_cpuverif
# cohort is committed; rebuilding is deterministic and only runs if a file is missing
if [[ ! -s data/journal2/unf/cohort_unf.jsonl || ! -s data/journal2/unf/cohort_orig.jsonl ]]; then
  "${PY}" -u scripts/journal2/unf_build.py
fi
LIM=(); [[ -n "${MEDVERIF_UNF_LIMIT:-}" ]] && LIM=(--limit "${MEDVERIF_UNF_LIMIT}")   # smoke tests only
"${CPUPY}" -u scripts/journal2/unf_score.py --pack orig --checker "${CK}" "${LIM[@]}"
"${CPUPY}" -u scripts/journal2/unf_score.py --pack unf  --checker "${CK}" "${LIM[@]}"
