#!/usr/bin/env bash
# T18: download 2 Wikipedia parquet shards + build ~100 bases (local filter, no HF streaming).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
LOG="${ROOT}/jobs/logs/t18_overnight_$(date +%Y%m%dT%H%M).log"
exec >>"${LOG}" 2>&1
echo "T18 overnight start $(date -Is)"

bash "${ROOT}/jobs/run_t18_parquet_download.sh"

export PYTHONPATH="${ROOT}/src"
python3 scripts/build_t18_wikipedia_pack.py --max-bases 100 --parquet-shards 2

echo "T18 overnight done $(date -Is) — review qc/t18_sample.csv"

/usr/bin/git -C "${ROOT}" add data/t18 qc/t18_sample.csv notes/t18_manifest.json notes/t18_perturb_failures.json 2>/dev/null || true
if /usr/bin/git -C "${ROOT}" diff --cached --quiet; then
  echo "T18: nothing to commit"
else
  MSG=$(mktemp)
  printf '%s\n\n%s\n' 'feat(t18): Wikipedia parquet pack (~100 bases)' 'Local shard filter; qc/t18_sample.csv for morning review.' >"${MSG}"
  /usr/bin/git -C "${ROOT}" commit -F "${MSG}"
  rm -f "${MSG}"
  /usr/bin/git -C "${ROOT}" push origin master || true
fi
