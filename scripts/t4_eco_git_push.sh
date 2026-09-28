#!/usr/bin/env bash
# Push T4 eco artifacts for node30 (V2/V3) + QC review.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"

/usr/bin/git add \
  qc/eco_sample.csv \
  qc/eco_PI_ok_labels.csv \
  qc/eco_review2.csv \
  data/t4/eco_classified.jsonl \
  data/t4/eco_instances.jsonl \
  data/t4/instances_eco_verify.jsonl \
  notes/t4_eco_manifest.json \
  notes/t6a_eco_checkers.json \
  notes/t4_eco_report.md \
  notes/t4_eco_report.json \
  scripts/t4_eco_qc_review2.py \
  scripts/t4_eco_report.py \
  scripts/t4_eco_score_node30.py \
  scripts/t6a_score_instances.py \
  jobs/run_t4_eco_node30.sh \
  src/t4_eco_compare.py \
  src/verifiers/t6a_*.py 2>/dev/null || true

if /usr/bin/git diff --cached --quiet; then
  echo "t4_eco_git_push: nothing staged"
  exit 0
fi

/usr/bin/git commit -m "$(cat <<'EOF'
T4 eco: classified answers, QC sample, verifier instances.

EOF
)"
/usr/bin/git push origin HEAD
