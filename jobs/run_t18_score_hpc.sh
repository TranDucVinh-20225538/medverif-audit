#!/usr/bin/env bash
# T18 scoring pack: OR judges ($2) + CPU/GPU checkers.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
source "${ROOT}/jobs/lib/flock.sh"
medverif_acquire_lock t18_score

cd "${ROOT}"
INST="${ROOT}/data/t18/instances_t18.jsonl"
RAW="${ROOT}/results/raw/t18"
mkdir -p "${RAW}"
LOG="${ROOT}/jobs/logs/t18_score_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "t18 score start $(date -Is)"

set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_API_LEDGER=1
export MEDVERIF_OR_MAX_INFLIGHT="${MEDVERIF_OR_MAX_INFLIGHT:-2}"
export MEDVERIF_T18_BUDGET_USD="${MEDVERIF_T18_BUDGET_USD:-2}"

for v in v1_medscore v4_ragas_nli; do
  python3 scripts/openrouter_budget.py || exit 2
  python3 src/score_jsonl.py --verifier "${v}" --instances "${INST}" --out "${RAW}/${v}.jsonl"
done

source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate cpuverif
export CUDA_VISIBLE_DEVICES=""
export HF_HOME="${ROOT}/.cache/huggingface"
export ALIGNScore_SRC="${ROOT}/.cache/src/AlignScore/src"
export PYTHONPATH="${ALIGNScore_SRC}:${ROOT}/src:${ROOT}/analysis:${ROOT}/scripts"
export MEDVERIF_SCORE_ENV=hpc

for cid in t6a_minicheck_roberta t6a_minicheck_deberta t6a_alignscore_base; do
  python3 scripts/t6a_score_instances.py --instances "${INST}" --outdir "${RAW}" --checker "${cid}"
done

conda run -n cpuverif_legacy python3 scripts/t6a_score_instances.py \
  --instances "${INST}" --outdir "${RAW}" --checker t6a_summac_zs || true
conda run -n cpuverif_legacy python3 scripts/t6a_score_instances.py \
  --instances "${INST}" --outdir "${RAW}" --checker t6a_granite_guardian || true

python3 src/score_jsonl.py --verifier v3_alignscore --instances "${INST}" --out "${RAW}/v3_alignscore.jsonl"
python3 src/score_jsonl.py --verifier t15_minicheck_roberta --instances "${INST}" --out "${RAW}/t15_minicheck_roberta.jsonl"

echo "t18 OR+CPU done; submit bespoke GPU separately if needed"
echo "t18 score pass1 done $(date -Is)"
