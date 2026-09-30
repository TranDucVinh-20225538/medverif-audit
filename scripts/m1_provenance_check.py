#!/usr/bin/env python3
"""M1 text provenance + amendment-4 spec check for every after-M1 text scored in m1_strong_final.

(a) Reproduce each M1 pack byte-for-byte from its build-time source under each candidate
    normalizer: `node30` (quantity_norm.M1_DOSE_RE_NODE30) and `head_8939e6c`
    (text_utils.DOSE_RE, the regex quantity_norm used at 8939e6c).
(b) Scored text = pack text, re-normalized when the pack was scored with MEDVERIF_M1=1.
    Off-spec = scored text != spec normalizer (quantity_norm.M1_DOSE_RE_SPEC) applied to source.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from quantity_norm import M1_DOSE_RE_NODE30, M1_DOSE_RE_SPEC, apply_m1_pair  # noqa: E402
from text_utils import DOSE_RE as DOSE_RE_HEAD  # noqa: E402

FINAL_COMMIT = "8939e6c"
OUT_JSON = ROOT / "notes/m1_provenance.json"
OUT_MD = ROOT / "notes/m1_provenance.md"

NORMALIZERS = {"node30": M1_DOSE_RE_NODE30, "head_8939e6c": DOSE_RE_HEAD}


def git_jsonl(path: str, commit: str) -> list[dict]:
    out = subprocess.run(
        ["/usr/bin/git", "-C", str(ROOT), "show", f"{commit}:{path}"], capture_output=True, text=True
    )
    if out.returncode:
        return []
    return [json.loads(line) for line in out.stdout.splitlines() if line.strip()]


def disk_jsonl(path: str) -> list[dict]:
    return [json.loads(line) for line in (ROOT / path).open() if line.strip()]


def t7_c0_sources(commit: str, bases: set[str]) -> dict[str, dict]:
    """build_t7_m1_pending.py: C0 from MAIN then EXPAND (last wins, valid only)."""
    c0: dict[str, dict] = {}
    for path in ("data/v3/instances_main.jsonl", "data/expand/instances_cpu_early.jsonl"):
        for row in git_jsonl(path, commit):
            if row.get("valid", True) and row["base_id"] in bases and row.get("condition") == "C0":
                c0[row["instance_id"]] = row
    return c0


def sources_for(pack: str) -> dict[str, dict]:
    if pack == "us_up_local":
        return {r["instance_id"]: r for r in git_jsonl("data/t7/instances_e1_unit.jsonl", FINAL_COMMIT)}
    if pack == "us_down":
        return {r["instance_id"]: r for r in git_jsonl("data/v3/t17_downdose.jsonl", FINAL_COMMIT)}
    if pack == "us_up_api":
        build = "f716016"
        t7 = {r["instance_id"]: r for r in git_jsonl("data/t7/instances_e1_unit.jsonl", build)}
        t7.update(t7_c0_sources(build, {r["base_id"] for r in t7.values()}))
        return t7
    raise KeyError(pack)


PACKS = {
    # name: (pack path at FINAL_COMMIT, scored with MEDVERIF_M1, checkers using it in m1_strong_final)
    "us_up_local": ("data/lane_b/m1_t7_e1_unit.jsonl", "1", "all local checkers + Bespoke/Granite"),
    "us_up_api": ("data/t7/instances_e1_unit_m1_pending.jsonl", "0", "v1_medscore, v4/v5_ragas_nli"),
    "us_down": ("data/lane_b/m1_t17_unit_down.jsonl", "unset", "all checkers"),
}
M1_CONDITIONS = ("E1-unit-claim", "E1-unit-evid", "E1-unit-down")


def main() -> None:
    report: dict = {"final_commit": FINAL_COMMIT, "packs": {}}
    for name, (path, m1_flag, users) in PACKS.items():
        pack = git_jsonl(path, FINAL_COMMIT)
        src = sources_for(name)
        repro = {}
        for label, rx in NORMALIZERS.items():
            bad = [
                r["instance_id"]
                for r in pack
                if r["instance_id"] not in src
                or apply_m1_pair(src[r["instance_id"]]["claim"], src[r["instance_id"]]["evidence"], rx)
                != (r["claim"], r["evidence"])
            ]
            repro[label] = {"matched": len(pack) - len(bad), "total": len(pack), "mismatch": bad}
        scored_rows = [r for r in pack if r.get("condition") in M1_CONDITIONS]
        off_spec, rescale_diff = [], []
        for r in scored_rows:
            text = (r["claim"], r["evidence"])
            if m1_flag != "0":
                again = apply_m1_pair(*text, DOSE_RE_HEAD)
                if again != text:
                    rescale_diff.append(r["instance_id"])
                if m1_flag == "1":
                    text = again
            s = src[r["instance_id"]]
            if apply_m1_pair(s["claim"], s["evidence"], M1_DOSE_RE_SPEC) != text:
                off_spec.append(r["instance_id"])
        report["packs"][name] = {
            "path": path,
            "scored_with_MEDVERIF_M1": m1_flag,
            "used_by": users,
            "reproduction": repro,
            "m1_rows_scored": len(scored_rows),
            "rescoring_normalizer_changes_text": rescale_diff,
            "off_spec": off_spec,
            "off_spec_bases": sorted({i.split("__")[0] for i in off_spec}),
        }
    ns = disk_jsonl("data/lane_b/m1_strong_ns.jsonl")
    report["ns_rows_changed_by_spec_m1"] = [
        r["instance_id"]
        for r in ns
        if apply_m1_pair(r["claim"], r["evidence"], M1_DOSE_RE_SPEC) != (r["claim"], r["evidence"])
    ]
    report["ns_rows_total"] = len(ns)
    OUT_JSON.write_text(json.dumps(report, indent=1) + "\n")

    lines = [
        "# M1 text provenance and amendment-4 spec check",
        "",
        f"Texts behind `m1_strong_final` (`{FINAL_COMMIT}`). Script: `scripts/m1_provenance_check.py`.",
        "",
        "| Pack | used by | node30 repro | head_8939e6c repro | M1 rows scored | off-spec rows (bases) |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for name, p in report["packs"].items():
        r = p["reproduction"]
        lines.append(
            f"| {name} | {p['used_by']} | {r['node30']['matched']}/{r['node30']['total']} | "
            f"{r['head_8939e6c']['matched']}/{r['head_8939e6c']['total']} | {p['m1_rows_scored']} | "
            f"{len(p['off_spec'])} ({len(p['off_spec_bases'])}) |"
        )
    lines += [
        "",
        f"NS packs (no M1 by design): {len(report['ns_rows_changed_by_spec_m1'])}/{report['ns_rows_total']} "
        "rows would change under spec M1.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
