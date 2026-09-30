#!/bin/bash
#SBATCH --job-name=t15_pack_ft
#SBATCH --partition=defq
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/t15_pack_ft-%j.out
#SBATCH --error=/data2/hpcshared/medverif-audit/jobs/logs/t15_pack_ft-%j.err

set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
export HF_HOME="${ROOT}/.cache/huggingface"
export PYTHONUNBUFFERED=1
export PYTHONPATH="${ROOT}/.cache/src/MiniCheck:${ROOT}/src:${ROOT}/analysis"
export MEDVERIF_ROOT="${ROOT}"
export MEDVERIF_MINICHECK_BATCH=16
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
source "${ROOT}/jobs/lib/hf_env.sh"
medverif_hf_env
bash "${ROOT}/jobs/lib/install_minicheck_gpu.sh"
ARCH="${ROOT}/results/raw/t15/_archive_ft_packs_hf_$(date +%Y%m%d)"
mkdir -p "${ARCH}"
for f in ft_main_dose.jsonl ft_main_ext.jsonl ft_t14.jsonl ft_t17.jsonl ft_t18.jsonl ft_t18_medical_expand.jsonl; do
  [[ -f "${ROOT}/results/raw/t15/${f}" ]] && mv "${ROOT}/results/raw/t15/${f}" "${ARCH}/"
done
python3 -u scripts/t15_eval.py --packs all --pack-leg ft --packs-only
