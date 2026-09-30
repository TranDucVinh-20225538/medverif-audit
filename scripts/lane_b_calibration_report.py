#!/usr/bin/env python3
"""Compare Lane B HPC calibration scores vs node30 (verdict agreement + |Δscore|)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from lane_b_checker_routing import cpuverif_checkers, legacy_checkers  # noqa: E402
from verifiers.io_utils import read_jsonl  # noqa: E402

CAL = ROOT / "data/lane_b/calibration_200.jsonl"
HPC_DIR = ROOT / "results/raw/lane_b/calibration_200"
NODE30 = ROOT / "results/raw_node30"

ALL_CHECKERS = (
    ("t6a_minicheck_roberta", "t6_minicheck_roberta.jsonl"),
    ("t6a_minicheck_deberta", "t6_minicheck_deberta.jsonl"),
    ("t6a_alignscore_base", "t6_alignscore_base.jsonl"),
    ("t6a_summac_zs", "t6_summac_zs.jsonl"),
    ("t6a_summac_conv", "t6_summac_conv.jsonl"),
    ("t6a_hhem", "t6_hhem.jsonl"),
    ("t6a_granite_guardian", "t6_granite_guardian.jsonl"),
)


def by_id(path: Path) -> dict[str, dict]:
    if not path.is_file():
        return {}
    return {r["instance_id"]: r for r in read_jsonl(path)}


def compare(ref: dict[str, dict], hpc: dict[str, dict], ids: set[str]) -> dict:
    n = agree = 0
    diffs: list[float] = []
    env_ids: set[str] = set()
    for iid in ids:
        a, b = ref.get(iid), hpc.get(iid)
        if not b:
            continue
        if b.get("lane_b_env_id"):
            env_ids.add(str(b["lane_b_env_id"]))
        if not a:
            continue
        va, vb = a.get("verdict"), b.get("verdict")
        if va not in ("PASS", "FAIL") or vb not in ("PASS", "FAIL"):
            continue
        n += 1
        agree += int(va == vb)
        sa, sb = a.get("score"), b.get("score")
        if sa is not None and sb is not None:
            diffs.append(abs(float(sa) - float(sb)))
    rate = agree / n if n else None
    mean_diff = sum(diffs) / len(diffs) if diffs else None
    return {
        "n": n,
        "agreement": rate,
        "mean_abs_score_diff": mean_diff,
        "hpc_lane_b_env_ids": sorted(env_ids),
    }


def run_report(*, legacy: bool) -> None:
    if legacy:
        checker_ids = set(legacy_checkers())
        env_json = ROOT / "notes/lane_b_env_legacy.json"
        out_json = ROOT / "notes/lane_b_calibration_agreement_legacy.json"
        out_md = ROOT / "notes/lane_b_calibration_agreement_legacy.md"
        title = "# Lane B legacy calibration vs node30"
    else:
        checker_ids = set(cpuverif_checkers())
        env_json = ROOT / "notes/lane_b_env.json"
        out_json = ROOT / "notes/lane_b_calibration_agreement.json"
        out_md = ROOT / "notes/lane_b_calibration_agreement.md"
        title = "# Lane B cpuverif calibration vs node30"

    cal_ids = {r["instance_id"] for r in read_jsonl(CAL)}
    env_id = None
    if env_json.is_file():
        try:
            env_id = json.loads(env_json.read_text()).get("env_id")
        except json.JSONDecodeError:
            pass
    rows = []
    lines = [
        title,
        "",
        f"Calibration ids: {len(cal_ids)}",
        f"HPC dir: `{HPC_DIR.relative_to(ROOT)}`",
        f"lane_b_env_id: `{env_id or 'unknown'}`",
        "",
        "| Checker | n | agreement | mean |Δscore| | env_ids |",
        "|---|---:|---:|---:|---|",
    ]
    for cid, fname in ALL_CHECKERS:
        if cid not in checker_ids:
            continue
        ref = by_id(NODE30 / fname)
        hpc = by_id(HPC_DIR / fname)
        stat = compare(ref, hpc, cal_ids)
        stat["checker"] = cid
        stat["node30_file"] = fname
        stat["hpc_file"] = str((HPC_DIR / fname).relative_to(ROOT))
        rows.append(stat)
        ag = stat["agreement"]
        mdiff = stat["mean_abs_score_diff"]
        eids = ",".join(stat.get("hpc_lane_b_env_ids") or []) or "—"
        ag_s = f"{100 * ag:.1f}%" if ag is not None else "NA"
        mdiff_s = f"{mdiff:.4f}" if mdiff is not None else "NA"
        lines.append(f"| {cid} | {stat['n']} | {ag_s} | {mdiff_s} | {eids} |")

    blocked = [r["checker"] for r in rows if r.get("agreement") is not None and r["agreement"] < 0.97]
    doc = {
        "lane_b_env_id": env_id,
        "profile": "legacy" if legacy else "cpuverif",
        "threshold_agreement": 0.97,
        "blocked_checkers": blocked,
        "checkers": rows,
    }
    out_json.write_text(json.dumps(doc, indent=2) + "\n")
    if blocked:
        lines.extend(["", f"**Excluded from Lane B packs** (agreement < 97%): {', '.join(blocked)}"])
    out_md.write_text("\n".join(lines) + "\n")
    print(out_json.read_text())


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--legacy", action="store_true")
    args = p.parse_args()
    run_report(legacy=args.legacy)


if __name__ == "__main__":
    main()
