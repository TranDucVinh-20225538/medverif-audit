#!/usr/bin/env bash
# Regenerate every report table that reads local-checker scores (no API calls, no rescoring).
# Usage: jobs/regen_tables.sh [SNAPSHOT_DIR]  — optional copy of results/tables, notes, results/figures afterwards.
set -uo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
for s in t13_best_of_n_report t14_c0_conditional_report t14_t3_filter_report t17_ns_report \
         dose3_robustness_report t24b_report t3_family_report t4_eco_report t4c_eco_report \
         t7_e1_unit_report build_polarity_all_verifiers; do
  echo "=== ${s} $(date +%T)"
  timeout 1200 python3 "scripts/${s}.py" > "/tmp/regen_${s}.log" 2>&1
  echo "rc=$?"
done
echo "=== fig1 $(date +%T)"
python3 scripts/figures/fig1_qi_vs_us.py > /tmp/regen_fig1.log 2>&1
echo "rc=$?"
if [ -n "${1:-}" ]; then
  rm -rf "$1" && mkdir -p "$1" && cp -r results/tables notes results/figures "$1"/
fi
echo "REGEN_DONE $(date +%T)"
