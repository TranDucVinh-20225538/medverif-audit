#!/usr/bin/env bash
# E2-unit T7: V2, V3, 7× T6-A, Bespoke on node30.
set -euo pipefail
ROOT="${MEDVERIF_ROOT:-/root/medverif-audit}"
cd "${ROOT}"
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_ROOT="${ROOT}"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
python3 scripts/build_e2_unit_instances.py
INST="${ROOT}/data/e2/instances_e2_unit_t7.jsonl"
RAW="${ROOT}/results/raw/e2_unit"
mkdir -p "${RAW}" "${ROOT}/jobs/logs"
LOG="${ROOT}/jobs/logs/e2_unit_node30_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "e2 unit node30 start $(date -Is)"
python3 - <<'PY'
import os, sys
from pathlib import Path
ROOT = Path(os.environ["MEDVERIF_ROOT"])
sys.path.insert(0, str(ROOT / "src"))
import cpu_early as ce
from verifiers.io_utils import read_jsonl
rows = read_jsonl(ROOT / "data/e2/instances_e2_unit_t7.jsonl")
raw = ROOT / "results/raw/e2_unit"
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
python3 scripts/e2_unit_comparison_report.py
echo "e2 unit node30 done $(date -Is)"
