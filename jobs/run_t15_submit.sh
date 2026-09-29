#!/usr/bin/env bash
# Submit T15 GPU train+eval if no duplicate t15-* job is queued/running.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
USER="${USER:-$(whoami)}"

if squeue -u "${USER}" -h -o "%j" 2>/dev/null | rg -q '^t15-'; then
  echo "t15: job already in squeue; not submitting duplicate"
  exit 0
fi

if [[ ! -f "${ROOT}/data/t15/train.jsonl" ]]; then
  echo "t15: missing data/t15/train.jsonl (expected commit 153429c)" >&2
  exit 1
fi

overlap="$(python3 -c "import json; print(json.load(open('${ROOT}/data/t15/disjointness_check.json'))['overlap_total'])")"
if [[ "${overlap}" != "0" ]]; then
  echo "t15: disjointness_check overlap_total=${overlap}" >&2
  exit 1
fi

sbatch "${ROOT}/jobs/run_t15_train.sbatch"
