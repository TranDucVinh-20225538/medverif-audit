#!/usr/bin/env bash
# Write notes/scoring_milestones.md when V1 completes main+thr union or V4 hits 1000.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
OUT="${ROOT}/notes/scoring_milestones.md"
TARGET=$(wc -l < "${ROOT}/data/v3/instances_cpu_early.jsonl")
V1_MAIN_THR=$(($(wc -l < "${ROOT}/data/v3/instances_cpu_main.jsonl") + $(wc -l < "${ROOT}/data/v3/instances_cpu_threshold.jsonl")))
v1_done=0
v4_1k=0
while true; do
  v1=$(wc -l < "${ROOT}/results/raw/v1_medscore.jsonl" 2>/dev/null || echo 0)
  v4=$(wc -l < "${ROOT}/results/raw/v4_ragas_nli.jsonl" 2>/dev/null || echo 0)
  ts=$(date -Is)
  {
    echo "# Scoring milestones"
    echo ""
    echo "Updated: ${ts}"
    echo ""
    echo "- cpu_early target (reference): **${TARGET}**"
    echo "- V1 main+threshold rows: **${V1_MAIN_THR}**"
    echo "- V1 scored (main raw): **${v1}**"
    echo "- V4 scored (main raw): **${v4}**"
    echo ""
  } > "${OUT}.tmp"
  if [[ "${v1_done}" -eq 0 ]] && [[ "${v1}" -ge "${V1_MAIN_THR}" ]]; then
    echo "**MILESTONE: V1 main scoring complete** (${v1} lines in raw/v1_medscore.jsonl)" >> "${OUT}.tmp"
    v1_done=1
  fi
  if [[ "${v4_1k}" -eq 0 ]] && [[ "${v4}" -ge 1000 ]]; then
    echo "**MILESTONE: V4 passed 1000** (${v4} lines)" >> "${OUT}.tmp"
    v4_1k=1
  fi
  mv "${OUT}.tmp" "${OUT}"
  if [[ "${v1_done}" -eq 1 ]] && [[ "${v4_1k}" -eq 1 ]]; then
    echo "milestones complete $(date -Is)" >> "${ROOT}/jobs/logs/watch_milestones.log"
    exit 0
  fi
  sleep 60
done
