#!/usr/bin/env bash
# Read notes/v4_openrouter_probe.json; if /no_think passes use Qwen3, else Llama 3.3 70B.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
PROBE="${ROOT}/notes/v4_openrouter_probe.json"
if [[ ! -f "${PROBE}" ]]; then
  echo "missing ${PROBE}; run jobs/run_v4_probe.sh first" >&2
  exit 1
fi

winner="$(python3 - <<'PY'
import json, pathlib
p = pathlib.Path("/data2/hpcshared/medverif-audit/notes/v4_openrouter_probe.json")
d = json.loads(p.read_text())
w = d.get("winner")
print(w["config"] if w else "")
PY
)"

export MEDVERIF_USE_OPENROUTER=1
if [[ "${winner}" == "no_think_suffix_deepinfra" ]]; then
  export MEDVERIF_V4_OPENROUTER_MODEL=qwen/qwen3-14b
  export MEDVERIF_V4_PROVIDER=DeepInfra
  export MEDVERIF_V4_PROMPT_SUFFIX=" /no_think"
  export MEDVERIF_V4_REASONING_JSON='{"reasoning":{"enabled":false}}'
  echo "V4 path: Qwen3-14B + /no_think (probe winner)"
else
  export MEDVERIF_V4_OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct
  export MEDVERIF_V4_PROVIDER="${MEDVERIF_V4_PROVIDER:-DeepInfra}"
  unset MEDVERIF_V4_PROMPT_SUFFIX MEDVERIF_V4_REASONING_JSON
  echo "V4 path: Llama-3.3-70B (Qwen3 probe did not pass gate; winner=${winner:-none})"
fi

cd "${ROOT}"
set -a && source ~/kkk/openrouter.env && set +a
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
export PYTHONPATH="${ROOT}/src"
export HF_HOME="${ROOT}/.cache/huggingface"
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"

LOG="${ROOT}/jobs/logs/v4_smoke_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "v4 smoke start $(date -Is)"
python3 scripts/v4_smoke_and_examples.py
echo "v4 smoke done $(date -Is); launching full"
bash "${ROOT}/jobs/run_v4_openrouter_full.sh"
