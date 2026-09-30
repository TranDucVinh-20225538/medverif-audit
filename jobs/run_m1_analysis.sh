#!/usr/bin/env bash
# Merge node30 M1 scores, report before/after, build M1+ pending for node30.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"

/usr/bin/git fetch origin node30-results 2>/dev/null || true
for f in v2a_minicheck.jsonl v3_alignscore.jsonl; do
  if /usr/bin/git cat-file -e "origin/node30-results:results/raw_m1/${f}" 2>/dev/null; then
    /usr/bin/git show "origin/node30-results:results/raw_m1/${f}" > "results/raw_m1/${f}"
    echo "merged results/raw_m1/${f} from origin/node30-results"
  fi
done

python3 scripts/build_m1_pending_node30.py
python3 scripts/build_m1plus_pending_node30.py
python3 scripts/m1_before_after_report.py
python3 scripts/t1_cost_validity_report.py

echo "m1 analysis done $(date -Is)"
