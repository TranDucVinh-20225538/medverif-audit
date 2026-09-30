#!/usr/bin/env bash
# After GPU cal ≥97% on 200 rows: archive CPU partials, launch full GPU base+ft legs.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
CAL="${ROOT}/notes/t15_aggrefact_gpu_calibration.json"
if [[ ! -f "${CAL}" ]] || ! python3 -c "import json,sys; d=json.load(open('${CAL}')); sys.exit(0 if d.get('pass') and d.get('path')=='minicheck_library_gpu' else 1)"; then
  echo "FATAL: MiniCheck library GPU calibration did not pass — see ${CAL}"
  exit 1
fi
scancel -u "${USER}" -n t15_aggrefac -n t15_agg_ft 2>/dev/null || true
ARCH="${ROOT}/results/raw/t15/_archive_cpu_partial_$(date +%Y%m%dT%H%M%S)"
mkdir -p "${ARCH}"
for f in base_aggrefact_test.jsonl ft_aggrefact_test.jsonl; do
  [[ -f "${ROOT}/results/raw/t15/${f}" ]] && mv "${ROOT}/results/raw/t15/${f}" "${ARCH}/"
done
echo "archived CPU partials to ${ARCH}"
sbatch --export=ALL,LEG=base "${ROOT}/jobs/run_t15_aggrefact_gpu_leg.sbatch"
sbatch --export=ALL,LEG=ft "${ROOT}/jobs/run_t15_aggrefact_gpu_leg.sbatch"
