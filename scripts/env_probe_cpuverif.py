#!/usr/bin/env python3
"""Reference-env agreement probes and row replacement for score files.

  sample  --file F --instances I [I ...] --out SUBSET [--n 30] [--ids-from-env PROFILE] [--controls K]
  compare --file F --probe P --label L [--env cpuverif]      -> notes/env_probe_cpuverif.json[F]
  replace --file F --new N --env cpuverif --reason R          -> F rows replaced by id; backup F.pre_<env>.quarantined.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "notes/env_probe_cpuverif.json"
SEED = 42


def read(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.open() if l.strip()]


def rel(p: Path) -> str:
    return str(p.resolve().relative_to(ROOT))


def log_update(key: str, entry: dict) -> None:
    d = json.loads(LOG.read_text()) if LOG.is_file() else {}
    d[key] = {**d.get(key, {}), **entry, "updated": datetime.now(timezone.utc).isoformat()}
    LOG.write_text(json.dumps(d, indent=1, ensure_ascii=False) + "\n")


def cmd_sample(a) -> None:
    rows = read(Path(a.file))
    inst = {r["instance_id"]: r for f in a.instances for r in read(Path(f))}
    if a.ids_from_env:
        target = [r["instance_id"] for r in rows if r.get("lane_b_env_profile") == a.ids_from_env and r["instance_id"] in inst]
        others = sorted(r["instance_id"] for r in rows if r.get("lane_b_env_profile") != a.ids_from_env and r["instance_id"] in inst)
        controls = random.Random(SEED).sample(others, min(a.controls, len(others))) if a.controls else []
        ids = target + controls
        log_update(rel(Path(a.file)), {"targets": target, "controls": controls})
    elif a.n <= 0:
        ids = [r["instance_id"] for r in rows if r["instance_id"] in inst]
    else:
        pool = sorted(r["instance_id"] for r in rows if r["instance_id"] in inst and r.get("verdict") in ("PASS", "FAIL"))
        ids = random.Random(SEED).sample(pool, min(a.n, len(pool)))
    missing = [r["instance_id"] for r in rows if r["instance_id"] not in inst]
    with open(a.out, "w") as f:
        for i in ids:
            f.write(json.dumps(inst[i], ensure_ascii=False) + "\n")
    print(json.dumps({"file": a.file, "sampled": len(ids), "rows_in_file": len(rows), "rows_without_instance": len(missing)}))


def cmd_compare(a) -> None:
    old = {r["instance_id"]: r for r in read(Path(a.file))}
    new = {r["instance_id"]: r for r in read(Path(a.probe))}
    common = sorted(set(old) & set(new))
    disagree = [i for i in common if old[i].get("verdict") != new[i].get("verdict")]
    diffs = [abs(float(old[i]["score"]) - float(new[i]["score"])) for i in common
             if old[i].get("score") not in (None, "None") and new[i].get("score") not in (None, "None")]
    entry = {"label": a.label, "reference_env": a.env, "n_compared": len(common), "verdict_agree": len(common) - len(disagree),
             "disagree": disagree, "max_abs_score_diff": max(diffs) if diffs else None,
             "pass": bool(common) and not disagree and len(common) >= a.min_n}
    log_update(rel(Path(a.file)), entry)
    print(json.dumps({k: v for k, v in entry.items() if k != "disagree"} | {"n_disagree": len(disagree)}))
    if a.exit_code:
        raise SystemExit(0 if entry["pass"] else 1)


def cmd_controls(a) -> None:
    """Exit 0 only if every control row (already in the reference env) is reproduced by the rescoring path."""
    path = Path(a.file)
    ctl = json.loads(LOG.read_text())[rel(path)]["controls"]
    old = {r["instance_id"]: r for r in read(path)}
    new = {r["instance_id"]: r for r in read(Path(a.new))}
    agree = sum(1 for i in ctl if i in new and new[i].get("verdict") == old[i].get("verdict"))
    diffs = [abs(float(new[i]["score"]) - float(old[i]["score"])) for i in ctl if i in new]
    ok = agree == len(ctl) and len(diffs) == len(ctl) and max(diffs, default=1.0) < a.tol
    log_update(rel(path), {"control_agree": agree, "control_max_abs_score_diff": max(diffs) if diffs else None, "control_pass": ok})
    print(json.dumps({"controls": len(ctl), "agree": agree, "max_abs_score_diff": max(diffs) if diffs else None, "pass": ok}))
    raise SystemExit(0 if ok else 1)


def cmd_replace(a) -> None:
    path = Path(a.file)
    rows = read(path)
    new = {r["instance_id"]: r for r in read(Path(a.new))}
    if a.only_ids_from:
        keep = set(json.loads(LOG.read_text())[rel(path)][a.only_ids_from])
        new = {k: v for k, v in new.items() if k in keep}
    backup = path.with_name(path.name.replace(".jsonl", f".pre_{a.env}.quarantined.jsonl"))
    if not backup.exists():
        backup.write_text(path.read_text())
    out, n = [], 0
    for r in rows:
        nr = new.get(r["instance_id"])
        if nr is not None:
            nr = {**nr, "lane_b_env_profile": nr.get("lane_b_env_profile") or a.env}
            for k in ("verifier", "model"):
                if k in r and k not in nr:
                    nr[k] = r[k]
            out.append(nr)
            n += 1
        else:
            out.append(r)
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in out))
    flips = sum(1 for r, o in zip(out, rows) if r.get("verdict") != o.get("verdict"))
    log_update(rel(path), {"replaced_rows": n, "replaced_env": a.env, "replace_reason": a.reason,
                           "replace_verdict_flips": flips, "backup": rel(backup)})
    print(json.dumps({"file": a.file, "replaced": n, "verdict_flips": flips, "backup": rel(backup)}))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sample")
    s.add_argument("--file", required=True)
    s.add_argument("--instances", required=True, nargs="+")
    s.add_argument("--out", required=True)
    s.add_argument("--n", type=int, default=30)
    s.add_argument("--ids-from-env")
    s.add_argument("--controls", type=int, default=0)
    c = sub.add_parser("compare")
    c.add_argument("--file", required=True)
    c.add_argument("--probe", required=True)
    c.add_argument("--label", required=True)
    c.add_argument("--env", default="cpuverif")
    c.add_argument("--min-n", type=int, default=30)
    c.add_argument("--exit-code", action="store_true")
    r = sub.add_parser("replace")
    r.add_argument("--file", required=True)
    r.add_argument("--new", required=True)
    r.add_argument("--env", default="cpuverif")
    r.add_argument("--reason", required=True)
    r.add_argument("--only-ids-from")
    k = sub.add_parser("controls")
    k.add_argument("--file", required=True)
    k.add_argument("--new", required=True)
    k.add_argument("--tol", type=float, default=1e-3)
    a = ap.parse_args()
    {"sample": cmd_sample, "compare": cmd_compare, "replace": cmd_replace, "controls": cmd_controls}[a.cmd](a)


if __name__ == "__main__":
    main()
