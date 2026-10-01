#!/bin/bash
#SBATCH --job-name=final_chain
#SBATCH --partition=defq
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=01:30:00
#SBATCH --output=/data2/hpcshared/medverif-audit/jobs/logs/final_chain_%j.out
#SBATCH --error=/data2/hpcshared/medverif-audit/jobs/logs/final_chain_%j.err

# Figure 1 final -> paper_numbers_final.md (amendment 5) -> audit zip v3 (with AggreFact) -> commit + push.
set -euo pipefail
ROOT=/data2/hpcshared/medverif-audit
cd "${ROOT}"
export PYTHONUNBUFFERED=1 MPLBACKEND=Agg PYTHONNOUSERSITE=1
unset PYTHONPATH
# compute-node /usr/bin/python3 (3.12) lacks matplotlib/quantulum3/pint; the vllm env has all three
PY=/data2/cmdir/home/toandq/.conda/envs/vllm/bin/python
GIT=/usr/bin/git
# compute nodes cannot auto-detect a committer email; reuse the identity of the last commit
export GIT_AUTHOR_NAME="$("${GIT}" log -1 --format=%an)" GIT_AUTHOR_EMAIL="$("${GIT}" log -1 --format=%ae)"
export GIT_COMMITTER_NAME="${GIT_AUTHOR_NAME}" GIT_COMMITTER_EMAIL="${GIT_AUTHOR_EMAIL}"
ZIP_COMMIT_MAX_MB=95

echo "=== [1/4] Figure 1 $(date -Is)"
"${PY}" scripts/figures/fig1_qi_vs_us.py

echo "=== [2/4] repair report + paper_numbers_final $(date -Is)"
"${PY}" scripts/m1_e1_unit_repair_report.py > /dev/null
"${PY}" scripts/paper_numbers_final.py

echo "=== [3/4] audit zip v3 $(date -Is)"
"${PY}" scripts/build_audit_zip_v3.py

echo "=== [4/4] commit + push $(date -Is)"
ZIP_MB=$(( $(stat -c %s release/audit_snapshot_v3.zip) / 1048576 ))
"${PY}" - "${SLURM_JOB_ID:-local}" "${ZIP_MB}" "${ZIP_COMMIT_MAX_MB}" <<'EOF'
import json, sys, datetime
job, zmb, zmax = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
pn = json.load(open("notes/paper_numbers_final.json"))
from collections import Counter
st = Counter(r["status"] for r in pn)
fig = json.load(open("results/figures/fig1_qi_vs_us.json"))
man = json.load(open("release/audit_snapshot_v3_manifest.json"))
in_git = "committed" if zmb < zmax else f"NOT committed (>{zmax} MB; on disk at release/audit_snapshot_v3.zip, sha256 in manifest)"
line = (f"- **Final chain job {job} done {datetime.datetime.now().strftime('%b %d %H:%M')}:** Figure 1 final "
        f"({len(fig)} points, HHEM/SummaC-Conv excluded); `paper_numbers_final.md` from amendment 5 "
        f"({len(pn)} numbers: " + ", ".join(f"{k} {v}" for k, v in st.most_common()) + "); "
        f"audit zip v3 {man['n_files']} files, {zmb} MB, {in_git}.\n")
p = "notes/batch_oct_status.md"
s = open(p).read()
anchor = "- **Final chain (one sbatch):**"
i = s.find(anchor)
j = s.find("\n", i) + 1 if i >= 0 else 0
s = s[:j] + line + s[j:]
open(p, "w").write(s)
print(line)
EOF

"${GIT}" add scripts/figures/fig1_qi_vs_us.py results/figures/fig1_qi_vs_us.pdf results/figures/fig1_qi_vs_us.png \
  results/figures/fig1_qi_vs_us.json scripts/paper_numbers_final.py paper_numbers_final.md notes/paper_numbers_final.json \
  scripts/m1_e1_unit_repair_report.py notes/m1_e1_unit_repair_report.json scripts/build_audit_zip_v3.py \
  release/audit_snapshot_v3_manifest.json jobs/run_final_chain.sbatch notes/batch_oct_status.md
[ -f notes/m1_e1_unit_repair_report.md ] && "${GIT}" add notes/m1_e1_unit_repair_report.md
if [ "${ZIP_MB}" -lt "${ZIP_COMMIT_MAX_MB}" ]; then
  "${GIT}" add -f release/audit_snapshot_v3.zip
fi
if "${GIT}" diff --cached --name-only | grep -E -i '(iaa_key|iaa_answer_key|\.env$|openrouter\.env|secret|credential)'; then
  echo "ABORT: forbidden file staged" >&2
  "${GIT}" reset -q
  exit 4
fi
"${GIT}" commit -q -m "Final chain (job ${SLURM_JOB_ID:-local}): Figure 1 final, paper_numbers_final.md from amendment 5, audit zip v3 with AggreFact"
for i in 1 2 3; do
  if "${GIT}" push -q origin HEAD:master; then
    echo "PUSHED $("${GIT}" log --oneline -1)"
    break
  fi
  echo "push attempt ${i} failed; retrying" >&2
  sleep 30
done
echo "=== DONE $(date -Is)"
