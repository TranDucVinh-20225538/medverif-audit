#!/usr/bin/env bash
# T7 E1-unit on node30: V2, V3, 7× T6-A, Bespoke (v2b if weights present).
set -euo pipefail
ROOT="${MEDVERIF_ROOT:-/root/medverif-audit}"
cd "${ROOT}"
export PYTHONPATH="${ROOT}/src"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"

INST="${ROOT}/data/t7/instances_e1_unit.jsonl"
RAW="${ROOT}/results/raw/t7"
mkdir -p "${RAW}"

python3 - <<'PY'
import os, subprocess, sys
from pathlib import Path
ROOT = Path(os.environ.get("MEDVERIF_ROOT", "/root/medverif-audit"))
subprocess.check_call([sys.executable, str(ROOT / "scripts/t7_build_e1_unit_instances.py")])
PY

python3 src/cpu_early.py --instances "${INST}" --outdir "${RAW}" 2>/dev/null || \
  python3 - <<'PY'
import os, sys
from pathlib import Path
ROOT = Path(os.environ.get("MEDVERIF_ROOT", "/root/medverif-audit"))
sys.path.insert(0, str(ROOT / "src"))
import cpu_early as ce
from verifiers.io_utils import read_jsonl
inst = ROOT / "data/t7/instances_e1_unit.jsonl"
rows = read_jsonl(inst)
raw = ROOT / "results/raw/t7"
raw.mkdir(parents=True, exist_ok=True)
ce.ensure_nltk()
ckpt = ce.prepare_weights()
from verifiers import v2a_minicheck, v3_alignscore
for kind, loader, name in (
    ("v2a", v2a_minicheck.load, "v2a_minicheck.jsonl"),
    ("v3", lambda: v3_alignscore.load(str(ckpt)), "v3_alignscore.jsonl"),
):
    model, _ = loader() if kind == "v2a" else loader()
    ce.score_rows(kind, model, rows, raw / name)
PY

python3 scripts/t6a_score_instances.py --instances "${INST}" --outdir "${RAW}" --checker all

if python3 -c "import verifiers.v2b_bespoke" 2>/dev/null; then
  python3 src/score_jsonl.py --verifier v2b_bespoke --instances "${INST}" --out "${RAW}/v2b_bespoke.jsonl" || true
fi

python3 scripts/t7_e1_unit_report.py
