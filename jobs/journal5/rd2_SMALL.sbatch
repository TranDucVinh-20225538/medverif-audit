#!/bin/bash
#SBATCH --job-name=rd2-SMALL
#SBATCH --partition=defq
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --array=0-4
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/rd2-SMALL_%A_%a.out
# (RD2-4a) the five small paper checkers in the paper's cpuverif env (CPU, same loaders as RD: scripts/journal2/small_checkers.py)
# on RD2 instances (-> results/journal5/rd2/real_dose/scores/) and on the UNF v1 / frozen UNF v2 rewrites of the changed
# rows (-> real_dose/unf/scores_unf_v1|v2/).  One checker per task:
#   0 t6a_minicheck_roberta  1 t6a_minicheck_deberta  2 t6a_alignscore_base  3 v2a_minicheck (Flan-T5-L)  4 v3_alignscore (AS-large)
# Resumable by instance_id.
source "${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}/jobs/journal5/rd2_env.sh"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 CUDA_VISIBLE_DEVICES=""
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16} MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-16}
export MEDVERIF_LANE_B_ENV_PROFILE=cpuverif MEDVERIF_SCORE_ENV_TAG=hpc_cpuverif
CHK=(t6a_minicheck_roberta t6a_minicheck_deberta t6a_alignscore_base v2a_minicheck v3_alignscore)
C="${CHK[${SLURM_ARRAY_TASK_ID}]}"
SPY="$(rd2_cpuverif_py)"
export PYTHONPATH="${ROOT}/src:${ROOT}/.cache/src/MiniCheck:${ROOT}/.cache/src/AlignScore/src:${ROOT}/analysis:${ROOT}/scripts"
D=results/journal5/rd2/real_dose
"${SPY}" -u scripts/journal2/small_checkers.py --instances "${D}/instances.jsonl" --outdir "${D}/scores" --checker "${C}"
for v in v1 v2; do
  if [[ -s "${D}/unf/instances_unf_${v}.jsonl" ]]; then
    "${SPY}" -u scripts/journal2/small_checkers.py --instances "${D}/unf/instances_unf_${v}.jsonl" --outdir "${D}/unf/scores_unf_${v}" --checker "${C}"
  fi
done
