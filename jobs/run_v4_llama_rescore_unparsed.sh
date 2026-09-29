#!/usr/bin/env bash
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
python3 scripts/dedupe_score_jsonl.py results/raw/v4_ragas_nli.llama.jsonl --verifier v4_ragas_nli
python3 scripts/build_audit_gap_instance_packs.py
python3 - <<'PY'
import json, sys
from pathlib import Path
sys.path.insert(0, "/data2/hpcshared/medverif-audit/analysis")
from analyze import _parsed
ROOT = Path("/data2/hpcshared/medverif-audit")
p = ROOT / "results/raw/v4_ragas_nli.llama.jsonl"
ids = []
for line in p.open():
    r = json.loads(line)
    fake = {"verdict": r.get("verdict"), "score": r.get("score"), "raw_output": r.get("raw_output")}
    if not _parsed(fake):
        ids.append(r["instance_id"])
Path("/tmp/v4_unparsed_ids.txt").write_text("\n".join(ids) + "\n")
PY
if [ -s /tmp/v4_unparsed_ids.txt ]; then
  python3 scripts/strip_score_instance_ids.py results/raw/v4_ragas_nli.llama.jsonl --ids-file /tmp/v4_unparsed_ids.txt
fi

source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
set -a && source ~/kkk/openrouter.env && set +a
export PYTHONPATH="${ROOT}/src"
export MEDVERIF_USE_OPENROUTER=1
export MEDVERIF_GPU_GLOBAL_SCORE_LOCK=0

python3 src/score_jsonl.py --verifier v4_ragas_nli \
  --instances "${ROOT}/data/v3/v4_llama_unparsed_rescore.jsonl" \
  --out "${ROOT}/results/raw/v4_ragas_nli.llama.jsonl"
echo "v4 llama unparsed rescore done $(date -Is)"
