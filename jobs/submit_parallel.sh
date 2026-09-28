#!/bin/bash
# Parallel GPU wave: V1, label_v3b, gpu_early (V2a/V3); stage4 after V1 + gpu_early. V4 if Qwen complete.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
LOG="${ROOT}/jobs/logs"
mkdir -p "${LOG}"

scancel 61405 61406 2>/dev/null || true

V1=$(sbatch --parsable "${ROOT}/jobs/stage3_v1.sbatch")
V3B=$(sbatch --parsable "${ROOT}/jobs/label_v3b.sbatch")
GPU=$(sbatch --parsable "${ROOT}/jobs/gpu_early.sbatch")

V4=""
V4_SKIP=""
python3 - << 'PY' > "${LOG}/qwen_v4_gate.txt"
import json
from pathlib import Path
root = Path("/data2/hpcshared/medverif-audit/.cache/huggingface/hub")
folder = root / "models--Qwen--Qwen3-14B" / "snapshots" / "40c069824f4251a91eefaf281ebe4c544efd3e18"
incomplete = len(list((root / "models--Qwen--Qwen3-14B").glob("**/*.incomplete")))
bad = []
if folder.is_dir() and (folder / "model.safetensors.index.json").is_file():
    payload = json.loads((folder / "model.safetensors.index.json").read_text())
    for name in sorted(set(payload["weight_map"].values())):
        p = folder / name
        if not p.is_file():
            bad.append(name)
ready = folder.is_dir() and not bad and incomplete == 0
print(json.dumps({"ready": ready, "missing_shards": bad, "incomplete_blobs": incomplete}))
PY

if python3 -c "import json; d=json.load(open('${LOG}/qwen_v4_gate.txt')); exit(0 if d.get('ready') else 1)"; then
  V4=$(sbatch --parsable "${ROOT}/jobs/stage3_v4.sbatch")
else
  V4_SKIP=$(cat "${LOG}/qwen_v4_gate.txt")
fi

S4=$(sbatch --parsable --dependency=afterok:"${V1}:${GPU}" "${ROOT}/jobs/stage4.sbatch")

{
  echo "v1_job=${V1}"
  echo "v3b_job=${V3B}"
  echo "gpu_early_job=${GPU}"
  echo "stage4_job=${S4} afterok ${V1} ${GPU}"
  echo "v4_job=${V4:-SKIPPED}"
  echo "v4_gate=${V4_SKIP:-ready}"
} | tee "${LOG}/parallel.submit.txt"
