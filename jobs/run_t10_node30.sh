#!/usr/bin/env bash
# T10 HHEM-2.1-open scoring on node30 (pairs in data/t10/hhem_pairs.jsonl).
set -euo pipefail
ROOT="${MEDVERIF_ROOT:-/root/medverif-audit}"
cd "${ROOT}"
export PYTHONPATH="${ROOT}/src"
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"

PAIRS="${ROOT}/data/t10/hhem_pairs.jsonl"
RAW="${ROOT}/results/raw/t10"
mkdir -p "${RAW}"
LOG="${ROOT}/jobs/logs/t10_node30_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "t10 hhem node30 start $(date -Is)"

python3 - <<'PY'
import json
from pathlib import Path
ROOT = Path("/root/medverif-audit")
pairs = ROOT / "data/t10/hhem_pairs.jsonl"
inst = ROOT / "data/t10/instances_hhem.jsonl"
rows = []
for line in pairs.open():
    if not line.strip():
        continue
    r = json.loads(line)
    for suffix, claim_key in (("orig", "claim_original"), ("rex", "claim_reexpressed")):
        rows.append({
            "instance_id": f"{r['instance_id']}__{suffix}",
            "claim": r[claim_key],
            "evidence": r.get("evidence") or r.get("claim_original"),
            "variant": suffix,
            "parent_id": r["instance_id"],
        })
inst.parent.mkdir(parents=True, exist_ok=True)
inst.write_text("".join(json.dumps(x)+"\n" for x in rows))
print({"n_instances": len(rows), "path": str(inst)})
PY

python3 scripts/t6a_score_instances.py --instances "${ROOT}/data/t10/instances_hhem.jsonl" \
  --outdir "${RAW}" --checker t6a_hhem
echo "t10 hhem node30 done $(date -Is)"
