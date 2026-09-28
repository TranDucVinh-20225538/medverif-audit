#!/usr/bin/env bash
# Commit + push expand QC artifacts (idempotent via notes/expand_post_pushed).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
STAMP="${ROOT}/notes/expand_post_pushed"
YIELD="${ROOT}/data/expand/v3/prepare_stats.json"

cd "${ROOT}"
if [[ -f "${STAMP}" ]]; then
  echo "expand git push already done ($(cat "${STAMP}"))"
  exit 0
fi
if [[ ! -f "${YIELD}" ]]; then
  echo "missing ${YIELD}" >&2
  exit 2
fi

/usr/bin/git add \
  qc/expand_pol_flips.csv \
  qc/expand_dose_sample.csv \
  qc/expand_unit_natural.csv \
  data/expand/bases_main.jsonl \
  data/expand/instances_main.jsonl \
  data/expand/instances_cpu_early.jsonl \
  data/expand/instances_pending_node30.jsonl \
  data/expand/instances_pending_t6a.jsonl \
  data/expand/instances_score_pending.jsonl \
  data/expand/v3/prepare_stats.json \
  notes/expand_pol_flip_audit.json \
  notes/expand_node30_manifest.json \
  notes/expand_status.md \
  notes/score_pending_manifest.json \
  2>/dev/null || true

if /usr/bin/git diff --cached --quiet; then
  echo "nothing to commit for expand artifacts"
  exit 0
fi

/usr/bin/git commit -m "$(cat <<EOF
Expand Stage-1 post-QC: bases, review CSVs, node30/T6-A pending.

$(python3 -c "import json; d=json.load(open('${YIELD}')); print('yield', d.get('bases_main_by_type'), 'instances', d.get('instances_main_valid'))")
EOF
)"
/usr/bin/git push origin master
date -Is >"${STAMP}"
echo "pushed expand artifacts $(cat "${STAMP}")"
