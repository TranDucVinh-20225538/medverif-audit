#!/usr/bin/env bash
# Push node30/HPC pending packs + jobs (no score jsonl).
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"

python3 scripts/build_m1_t7_node30.py
python3 scripts/build_pol_flip_pending_node30.py
python3 scripts/build_m1plus_pending_node30.py
python3 scripts/build_t3_bespoke_pending_node30.py
python3 scripts/t14_build_instances.py
python3 scripts/build_t14_score_pending.py
python3 scripts/build_score_pending.py

/usr/bin/git add \
  scripts/build_m1_t7_node30.py \
  scripts/build_t7_m1_pending.py \
  scripts/t7_score_pending_m1.py \
  scripts/t7_m1_mcnemar_report.py \
  scripts/build_pol_flip_pending_node30.py \
  scripts/build_polarity_all_verifiers.py \
  scripts/t1_score_pending_m1plus.py \
  scripts/t3_family_report.py \
  scripts/build_score_pending.py \
  scripts/node30_batch_git_push.sh \
  jobs/run_t7_m1_node30.sh \
  jobs/run_t7_m1_hpc.sh \
  jobs/run_t1_m1plus_score_node30.sh \
  jobs/run_node30_score_pending.sh \
  data/t7/instances_e1_unit_m1_pending.jsonl \
  data/v3/instances_m1_t7_node30.jsonl \
  data/v3/instances_pol_flip_pending_node30.jsonl \
  data/v3/instances_m1plus_pending_node30.jsonl \
  data/v3/instances_m1plus_score_pending_node30.jsonl \
  data/v3/instances_t3_bespoke_pending_node30.jsonl \
  data/v3/instances_t14_pending_node30.jsonl \
  data/t14/instances_t14.jsonl \
  data/t14/instances_t14_pending_openrouter.jsonl \
  data/v3/instances_t14.jsonl \
  qc/t14_sample.csv \
  data/t14/manifest_t14.json \
  notes/t14_score_pending_manifest.json \
  scripts/t14_build_instances.py \
  scripts/build_t14_score_pending.py \
  jobs/run_t14_score_node30.sh \
  jobs/run_t14_score_openrouter.sh \
  scripts/build_t3_bespoke_pending_node30.py \
  notes/m1plus_pending_node30.md \
  notes/t3_bespoke_pending_node30_manifest.json \
  results/tables/t3_family_pass.md \
  notes/t3_family_pass.json \
  notes/e2_t7_verifier_comparison.md \
  notes/e2_t7_verifier_comparison.json \
  qc/e1_pol_review.csv \
  data/v3/instances_score_pending_node30.jsonl \
  data/v3/instances_score_pending_t3_inv.jsonl \
  notes/t7_m1_pending_manifest.json \
  notes/m1_t7_node30_manifest.json \
  notes/pol_flip_pending_node30_manifest.json \
  notes/m1plus_pending_node30_manifest.json \
  notes/score_pending_manifest.json \
  notes/node30_score_pending.md 2>/dev/null || true

if /usr/bin/git diff --cached --quiet; then
  echo "node30_batch_git_push: nothing staged"
  exit 0
fi

/usr/bin/git commit -m "$(cat <<'EOF'
T7 M1, POL flip pending, M1+/T3 node30 score packs.

EOF
)"
/usr/bin/git push origin HEAD
