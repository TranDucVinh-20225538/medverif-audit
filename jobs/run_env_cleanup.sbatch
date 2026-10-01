#!/bin/bash
#SBATCH --job-name=env_cleanup
#SBATCH --partition=defq
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/env_cleanup_%j.out
#SBATCH --error=/data2/hpcshared/medverif-audit/jobs/logs/env_cleanup_%j.err

# Oct 1 author decisions on non-reference-env files:
#  probes T3/T24b (rescore on mismatch), Granite M1 44 legacy rows -> cpuverif, MedScore 5 rows without API metadata
#  excluded, token-overlap on amendment-5 texts, regenerate paper_numbers_final.md, report, commit + push.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
export PYTHONUNBUFFERED=1 MPLBACKEND=Agg MEDVERIF_M1=0 NLTK_DATA="${ROOT}/.cache/nltk"
source /data2/shared/apps/conda/etc/profile.d/conda.sh
source "${ROOT}/jobs/lib/hf_env.sh"
medverif_hf_env
unset PYTHONPATH

GIT=/usr/bin/git
export GIT_AUTHOR_NAME="$("${GIT}" log -1 --format=%an)" GIT_AUTHOR_EMAIL="$("${GIT}" log -1 --format=%ae)"
export GIT_COMMITTER_NAME="${GIT_AUTHOR_NAME}" GIT_COMMITTER_EMAIL="${GIT_AUTHOR_EMAIL}"
# report/analysis python (matplotlib, quantulum3, pint); scoring pythons below
PY=/data2/cmdir/home/toandq/.conda/envs/vllm/bin/python
cpu_py="$(env -u PYTHONPATH conda run -n cpuverif python -c 'import sys; print(sys.executable)')"
legacy_py="$(env -u PYTHONPATH conda run -n cpuverif_legacy python -c 'import sys; print(sys.executable)')"
SRC_PATH="${ROOT}/.cache/src/MiniCheck:${ROOT}/src:${ROOT}/analysis:${ROOT}/scripts:${ROOT}/.cache/src/AlignScore/src"
H="scripts/env_probe_cpuverif.py"
W="${ROOT}/results/diagnostics/env_cleanup_oct1/work_${SLURM_JOB_ID:-local}"
SNAP="${ROOT}/results/diagnostics/env_cleanup_oct1"
mkdir -p "${W}" "${SNAP}"
rm -f notes/env_probe_cpuverif.json
echo "env cleanup start $(date -Is) job=${SLURM_JOB_ID:-local}"

pyr() { env PYTHONNOUSERSITE=1 "${PY}" "$@"; }

score() {  # score CHECKER INSTANCES OUTDIR -> OUTDIR/<file>
  local cid="$1" inst="$2" out="$3"
  mkdir -p "${out}"
  case "${cid}" in
    t6a_summac_zs)
      PYTHONPATH="${ROOT}/src:${ROOT}/analysis:${ROOT}/scripts" MEDVERIF_LANE_B_ENV_PROFILE=legacy \
        "${legacy_py}" scripts/t6a_score_instances.py --instances "${inst}" --outdir "${out}" --checker "${cid}" ;;
    t6a_*)
      PYTHONPATH="${SRC_PATH}" MEDVERIF_LANE_B_ENV_PROFILE=cpuverif \
        "${cpu_py}" scripts/t6a_score_instances.py --instances "${inst}" --outdir "${out}" --checker "${cid}" ;;
    *)
      PYTHONPATH="${SRC_PATH}" MEDVERIF_LANE_B_ENV_PROFILE=cpuverif \
        "${cpu_py}" src/score_jsonl.py --verifier "${cid}" --instances "${inst}" --out "${out}/${cid}.jsonl" ;;
  esac
}

probe() {  # probe CHECKER SCOREFILE REFENV INSTANCES...
  local cid="$1" f="$2" env="$3"; shift 3
  local tag; tag="$(echo "${f}" | tr '/' '_')"
  local d="${W}/${tag}" name; name="$(basename "${f}")"
  echo "=== probe ${f} (${env}) $(date -Is)"
  pyr "${H}" sample --file "${f}" --instances "$@" --out "${d}.subset.jsonl" --n 30
  score "${cid}" "${d}.subset.jsonl" "${d}"
  if pyr "${H}" compare --file "${f}" --probe "${d}/${name}" --label "${cid}" --env "${env}" --exit-code; then
    echo "CHECKED ${f}"
  else
    echo "MISMATCH ${f}: full rescore in ${env}"
    pyr "${H}" sample --file "${f}" --instances "$@" --out "${d}.all.jsonl" --n 0
    score "${cid}" "${d}.all.jsonl" "${d}"
    pyr "${H}" replace --file "${f}" --new "${d}/${name}" --env "${env}" --reason "probe mismatch (Oct 1 decision 2)"
  fi
}

regen_all() {
  for s in t13_best_of_n_report t14_c0_conditional_report t14_t3_filter_report t17_ns_report dose3_robustness_report \
           t24b_report t3_family_report t4_eco_report t4c_eco_report t7_e1_unit_report build_polarity_all_verifiers; do
    pyr "scripts/${s}.py" > "${W}/regen_${s}.log" 2>&1 || { echo "REGEN FAILED ${s}"; tail -20 "${W}/regen_${s}.log"; exit 5; }
  done
  pyr scripts/m1_strong_run.py --final --amend5 --dump-rows > "${W}/m1_strong_run.log" 2>&1
  pyr scripts/m1_e1_unit_repair_report.py > /dev/null
  pyr scripts/figures/fig1_qi_vs_us.py > "${W}/fig1.log"
  pyr scripts/paper_numbers_final.py > "${W}/paper_numbers.log"
}

"${GIT}" show HEAD:notes/paper_numbers_final.json > "${SNAP}/pn_head.json"
cp results/tables/m1_strong_final_amend5.md "${SNAP}/a5_before.md"

# --- 2. T3 / T24b probes
T3_INST="data/t3/instances_inv_families.jsonl data/v3/instances_main.jsonl data/v3/instances_cpu_early.jsonl"
probe t6a_minicheck_roberta results/raw/t3/t6_minicheck_roberta.jsonl cpuverif ${T3_INST}
probe t6a_alignscore_base   results/raw/t3/t6_alignscore_base.jsonl   cpuverif ${T3_INST}
probe t6a_summac_zs         results/raw/t3/t6_summac_zs.jsonl         cpuverif_legacy ${T3_INST}
probe t6a_granite_guardian  results/raw/t3/t6_granite_guardian.jsonl  cpuverif ${T3_INST}
probe v2a_minicheck         results/raw/t24b/v2a_minicheck.jsonl      cpuverif data/t24/instances_t24b.jsonl
probe v3_alignscore         results/raw/t24b/v3_alignscore.jsonl      cpuverif data/t24/instances_t24b.jsonl

# --- 4. Granite M1 US_up: legacy rows -> cpuverif (5 cpuverif control rows must reproduce)
GF=results/raw/lane_b/m1_t7_e1_unit/t6_granite_guardian.jsonl
echo "=== granite legacy rescore $(date -Is)"
pyr "${H}" sample --file "${GF}" --instances data/lane_b/m1_t7_e1_unit.jsonl --ids-from-env legacy --controls 5 --out "${W}/granite.subset.jsonl"
score t6a_granite_guardian "${W}/granite.subset.jsonl" "${W}/granite"
if pyr "${H}" controls --file "${GF}" --new "${W}/granite/t6_granite_guardian.jsonl"; then
  pyr "${H}" replace --file "${GF}" --new "${W}/granite/t6_granite_guardian.jsonl" --env cpuverif \
    --reason "legacy rows rescored in cpuverif (Oct 1 decision 4)" --only-ids-from targets
else
  echo "GRANITE CONTROLS FAILED: rows not replaced" >&2
fi

echo "=== regen after steps 2+4 $(date -Is)"
regen_all
cp notes/paper_numbers_final.json "${SNAP}/pn_mid.json"
cp results/tables/m1_strong_final_amend5.md "${SNAP}/a5_after_granite.md"

# --- 5. MedScore rows without API metadata
echo "=== medscore exclusion $(date -Is)"
pyr - "${SNAP}/medscore_removed.json" <<'EOF'
import json, sys
p = "results/raw/v1_medscore.jsonl"
rows = [json.loads(l) for l in open(p) if l.strip()]
bad = [r for r in rows if not (r.get("api_model") or r.get("api_provider") or r.get("openrouter_model"))]
backup = "results/raw/v1_medscore.no_api_meta.quarantined.jsonl"
with open(backup, "w") as f:
    f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in bad)
with open(p, "w") as f:
    f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows if r not in bad)
a = "notes/allow_data_shrink.json"
d = json.load(open(a))
d["paths"][p] = f"Oct 1 decision 5: exclude {len(bad)} rows without API metadata (moved to {backup})"
open(a, "w").write(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
json.dump({"ids": [r["instance_id"] for r in bad], "backup": backup}, open(sys.argv[1], "w"), indent=1)
print(len(bad), "rows removed")
EOF
regen_all

# --- 7. token overlap on amendment-5 texts
echo "=== token overlap amend5 $(date -Is)"
HF_HUB_OFFLINE=1 pyr scripts/m1_token_overlap_exploratory.py --amend5 > "${W}/token_overlap.log" 2>&1

# --- 8. report + status + commit
pyr scripts/m1_amend5_side_by_side.py > /dev/null
pyr scripts/env_cleanup_report.py "${SNAP}"
pyr - "${SLURM_JOB_ID:-local}" <<'EOF'
import json, sys, datetime
from collections import Counter
pn = json.load(open("notes/paper_numbers_final.json"))
st = Counter(r["status"] for r in pn)
line = (f"- **Env cleanup job {sys.argv[1]} done {datetime.datetime.now().strftime('%b %d %H:%M')}:** decisions 1–8 applied; "
        f"`paper_numbers_final.md` {len(pn)} numbers (" + ", ".join(f"{k} {v}" for k, v in st.most_common()) +
        "); report `notes/env_cleanup_oct1.md`.\n")
p = "notes/batch_oct_status.md"
s = open(p).read()
i = s.find("## Oct 1 decisions (author)")
j = s.find("\n\n", i) + 2 if i >= 0 else 0
open(p, "w").write(s[:j] + line + s[j:])
print(line)
EOF
rm -rf "${W}"/*.subset.jsonl "${W}"/*.all.jsonl
"${GIT}" add -- results/raw results/raw_m1 notes results/tables results/figures results/diagnostics/env_cleanup_oct1 \
  scripts src paper_numbers_final.md jobs/run_env_cleanup.sbatch
if "${GIT}" diff --cached --name-only | grep -E -i '(iaa_key|iaa_answer_key|\.env$|openrouter\.env|secret|credential)'; then
  echo "ABORT: forbidden file staged" >&2; "${GIT}" reset -q; exit 4
fi
"${GIT}" commit -q -m "Env cleanup (job ${SLURM_JOB_ID:-local}): Bespoke=vllm and T9=nemo by design; T3/T24b probes; Granite M1 legacy rows -> cpuverif; MedScore no-API rows excluded; token overlap amend5; paper_numbers_final regenerated"
for i in 1 2 3; do
  "${GIT}" push -q origin HEAD:master && { echo "PUSHED $("${GIT}" log --oneline -1)"; break; }
  "${GIT}" fetch -q origin
  [ "$("${GIT}" rev-parse HEAD)" = "$("${GIT}" rev-parse origin/master)" ] && { echo "PUSHED (remote already at HEAD)"; break; }
  echo "push attempt ${i} failed" >&2; sleep 30
done
echo "=== DONE $(date -Is)"
