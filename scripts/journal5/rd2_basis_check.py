#!/usr/bin/env python3
"""(RD2-5a) Run the FROZEN dose-basis check (scripts/journal4/basis_check.py, rule basis-check-1, commit fdb95de) on RD2.

Refuses to run unless basis_check.py is byte-identical to its version at the freeze commit (git blob comparison; plus
`git diff fdb95de -- scripts/journal4/basis_check.py` empty).  Inputs: claim (answer) + evidence (label excerpt) of
results/journal5/rd2/real_dose/instances.jsonl only -- never the gold target span.  CPU, deterministic, stdlib.
Output: results/journal5/rd2/basis_check/per_item.jsonl (one row per instance: status/flag/flag_type for the full and
strict variants + per-dose detail).  Metrics (recall / false alarm vs pharmacist adjudication) are computed by
scripts/journal5/rd2_report.py.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rd2_common import INSTANCES, RD2_DIR, ROOT, git, log, read_jsonl, sha256_file, write_jsonl  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts" / "journal4"))
FREEZE_COMMIT = "fdb95de68b376340946f2e251040d3006c20072e"
RULE = "scripts/journal4/basis_check.py"
OUT = RD2_DIR / "basis_check" / "per_item.jsonl"


def frozen_ok() -> tuple:
    cur = sha256_file(ROOT / RULE)
    try:
        import subprocess
        blob = subprocess.run(["git", "show", "%s:%s" % (FREEZE_COMMIT, RULE)], cwd=str(ROOT), stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=60).stdout
    except Exception:  # noqa: BLE001
        blob = b""
    frz = hashlib.sha256(blob).hexdigest() if blob else ""
    return (bool(frz) and cur == frz and not git("diff", "--name-only", FREEZE_COMMIT, "--", RULE)), cur, frz


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", default=str(INSTANCES))
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    ok, cur, frz = frozen_ok()
    if not ok:
        raise SystemExit("basis_check.py differs from the freeze commit %s (current %s, frozen %s) -- refusing" % (
            FREEZE_COMMIT[:7], cur[:12], (frz or "unavailable")[:12]))
    import basis_check as B  # noqa: E402
    rows = read_jsonl(args.instances)
    if not rows:
        raise SystemExit("no instances in %s" % args.instances)
    out = []
    for r in rows:
        res = B.check_pair(r["claim"], r["evidence"])
        out.append(dict(res, instance_id=r["instance_id"], drug=r["drug"], generator=r["generator"],
                        answer_condition=r["answer_condition"], auto_class=r["auto_class"], stratum=r.get("stratum"),
                        rule_sha256=cur, freeze_commit=FREEZE_COMMIT))
    write_jsonl(args.out, out)
    log("RD2_basis_check", rows=len(out), flag_full=sum(o["flag_full"] for o in out),
        flag_strict=sum(o["flag_strict"] for o in out), rule_sha256=cur[:12], out=args.out)


if __name__ == "__main__":
    main()
