#!/usr/bin/env bash
# Deprecated on HPC: V2a/V3 M1 scoring runs on node30 only.
set -euo pipefail
echo "run_t1_m1_rescore_cpu.sh is not used on HPC." >&2
echo "  HPC OpenRouter M1: jobs/run_t1_m1_rescore_openrouter.sh (V1+V4 → results/raw_m1/)" >&2
echo "  node30 V2/V3 M1:   jobs/run_t1_m1_score_node30.sh" >&2
exit 2
