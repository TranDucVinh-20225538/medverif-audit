#!/usr/bin/env bash
# Score combined pending (incl. POL flip + T3) on node30 → results/raw/
set -euo pipefail
ROOT="${MEDVERIF_ROOT:-/data2/hpcshared/medverif-audit}"
cd "${ROOT}"
source /data2/shared/apps/conda/etc/profile.d/conda.sh 2>/dev/null || true
conda activate vllm 2>/dev/null || true
export PYTHONPATH="${ROOT}/src"
export CUDA_VISIBLE_DEVICES=""
export HF_HOME="${HF_HOME:-${ROOT}/.cache/huggingface}"

LOG="${ROOT}/jobs/logs/node30_score_pending_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "node30 score pending start $(date -Is)"

python3 scripts/build_pol_flip_pending_node30.py
python3 scripts/build_score_pending.py

INST="${ROOT}/data/v3/instances_score_pending_node30.jsonl"
RAW="${ROOT}/results/raw"
mkdir -p "${RAW}"

python3 - <<'PY'
import os, sys
from pathlib import Path
ROOT = Path(os.environ.get("MEDVERIF_ROOT", "/data2/hpcshared/medverif-audit"))
sys.path.insert(0, str(ROOT / "src"))
import cpu_early as ce
from verifiers.io_utils import read_jsonl
rows = read_jsonl(ROOT / "data/v3/instances_score_pending_node30.jsonl")
raw = ROOT / "results/raw"
ce.ensure_nltk()
ckpt = ce.prepare_weights()
from verifiers import v2a_minicheck, v3_alignscore
v2a, _ = v2a_minicheck.load()
v3, _ = v3_alignscore.load(str(ckpt))
for kind, model, name in (("v2a", v2a, "v2a_minicheck.jsonl"), ("v3", v3, "v3_alignscore.jsonl")):
    ce.score_rows(kind, model, rows, raw / name)
PY

python3 scripts/t6a_score_instances.py --instances "${INST}" --outdir "${RAW}" --checker all
python3 scripts/build_polarity_all_verifiers.py
python3 scripts/t3_family_report.py
echo "node30 score pending done $(date -Is)"
