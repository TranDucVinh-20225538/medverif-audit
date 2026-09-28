#!/usr/bin/env bash
# node30: T4c encoders (V2/V3 + T6-A + Bespoke) on eco_instances_t4c.jsonl
set -euo pipefail
ROOT="${MEDVERIF_ROOT:-/root/medverif-audit}"
cd "${ROOT}"
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_ROOT="${ROOT}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
export HF_HOME="${HF_HOME:-${ROOT}/.cache/huggingface}"
export HUGGINGFACE_HUB_CACHE="${HUGGINGFACE_HUB_CACHE:-${HF_HOME}/hub}"
export NLTK_DATA="${NLTK_DATA:-${ROOT}/.cache/nltk}"
LOG="${ROOT}/jobs/logs/t4c_eco_node30_$(date +%Y%m%dT%H%M).log"
mkdir -p "${ROOT}/jobs/logs" "${ROOT}/results/raw/t4c_eco"
exec >>"${LOG}" 2>&1
echo "t4c eco node30 start $(date -Is)"
python3 scripts/t4c_build_eco_instances.py
INST="${ROOT}/data/t4/eco_instances_t4c.jsonl"
RAW="${ROOT}/results/raw/t4c_eco"
python3 - <<'PY'
import os, sys
from pathlib import Path
ROOT = Path(os.environ["MEDVERIF_ROOT"])
sys.path.insert(0, str(ROOT / "src"))
import cpu_early as ce
from verifiers.io_utils import read_jsonl
inst = ROOT / "data/t4/eco_instances_t4c.jsonl"
rows = read_jsonl(inst)
raw = ROOT / "results/raw/t4c_eco"
raw.mkdir(parents=True, exist_ok=True)
ce.ensure_nltk()
ckpt = ce.prepare_weights()
from verifiers import v2a_minicheck, v3_alignscore
v2a, _ = v2a_minicheck.load()
v3, _ = v3_alignscore.load(str(ckpt))
for kind, model, name in (
    ("v2a", v2a, "v2a_minicheck.jsonl"),
    ("v3", v3, "v3_alignscore.jsonl"),
):
    ce.score_rows(kind, model, rows, raw / name)
PY
python3 scripts/t6a_score_instances.py --instances "${INST}" --outdir "${RAW}" --checker all
if python3 -c "import verifiers.v2b_bespoke" 2>/dev/null; then
  python3 src/score_jsonl.py --verifier v2b_bespoke --instances "${INST}" \
    --out "${RAW}/t6_bespoke_minicheck.jsonl" || true
fi
python3 scripts/t4c_eco_report.py
echo "t4c eco node30 done $(date -Is)"
