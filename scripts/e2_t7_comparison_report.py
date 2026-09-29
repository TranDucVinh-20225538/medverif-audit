#!/usr/bin/env python3
"""E2|C0 PASS vs T7 E1-unit-claim/evid FAIL rates per verifier."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))

from analyze import _c0_pass_bases, _parsed, read_jsonl  # noqa: E402

MAIN = ROOT / "data/v3/instances_main.jsonl"
EXPAND = ROOT / "data/expand/instances_cpu_early.jsonl"
E2_INST = ROOT / "data/e2/instances_main_x2.jsonl"
T7 = ROOT / "data/t7/instances_e1_unit.jsonl"
T6A = ROOT / "notes/t6a_eco_checkers.json"
OUT = ROOT / "notes/e2_t7_verifier_comparison.md"
OUT_JSON = ROOT / "notes/e2_t7_verifier_comparison.json"

SCORE_DIRS = [
    ROOT / "results/raw/e2_main",
    ROOT / "results/raw",
    ROOT / "results/raw/t6b/full",
    ROOT / "results/raw/t2_full",
    ROOT / "results/raw/t7",
    ROOT / "results/raw/t3",
    ROOT / "results/raw/t4c_eco",
]


def _verifier_slug(path: Path) -> str | None:
    name = path.name
    if "quarantine" in name or ".legacy." in name:
        return None
    if name.endswith(".llama.jsonl"):
        return name[: -len(".llama.jsonl")]
    if name.endswith(".jsonl"):
        return name[: -len(".jsonl")]
    return None


def all_verifier_slugs() -> list[str]:
    slugs: set[str] = set()
    for d in SCORE_DIRS:
        if d.is_dir():
            for p in d.glob("*.jsonl"):
                slug = _verifier_slug(p)
                if slug:
                    slugs.add(slug)
    if T6A.is_file():
        for c in json.loads(T6A.read_text()).get("checkers", []):
            slugs.add(c["id"])
    if any((d / "t6_bespoke_minicheck.jsonl").is_file() for d in SCORE_DIRS):
        slugs.add("v2b_bespoke")
    return sorted(slugs)


def merged_scores(slug: str) -> dict[str, str]:
    """Merge e2_main → raw/t7 → other dirs (later paths override)."""
    m: dict[str, str] = {}
    paths: list[Path] = []
    if T6A.is_file():
        t6a = {c["id"]: c["jsonl"] for c in json.loads(T6A.read_text()).get("checkers", [])}
        if slug in t6a:
            for d in SCORE_DIRS:
                cand = d / t6a[slug]
                if cand.is_file():
                    paths.append(cand)
    if slug == "v2b_bespoke":
        for name in ("t6_bespoke_minicheck.jsonl", "v2b_bespoke.jsonl"):
            for d in SCORE_DIRS:
                cand = d / name
                if cand.is_file():
                    paths.append(cand)
    for d in SCORE_DIRS:
        llama = d / f"{slug}.llama.jsonl"
        plain = d / f"{slug}.jsonl"
        if llama.is_file():
            paths.append(llama)
        elif plain.is_file():
            paths.append(plain)
    seen: set[Path] = set()
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        for row in read_jsonl(path):
            iid = row.get("instance_id")
            if iid:
                m[iid] = row.get("verdict") or ""
    return m


def join(inst_map: dict, scores: dict[str, str], verifier: str) -> list[dict]:
    rows = []
    for iid, v in scores.items():
        inst = inst_map.get(iid)
        if not inst:
            continue
        row = dict(inst)
        row["verifier"] = verifier
        row["verdict"] = v
        rows.append(row)
    return rows


def rate(ids: list[str], scores: dict[str, str], want: str) -> tuple[float | None, int, int]:
    hits = []
    for iid in ids:
        verdict = scores.get(iid)
        if verdict:
            hits.append(int(verdict == want))
    if not hits:
        return None, 0, len(ids)
    return sum(hits) / len(hits), len(hits), len(ids)


def e2_pass_cond(joined: list[dict]) -> tuple[float | None, int, int]:
    c0 = _c0_pass_bases(joined)
    e2 = [r for r in joined if r["condition"] == "E2" and r["base_id"] in c0 and _parsed(r)]
    if not e2:
        return None, 0, 0
    np = sum(r["verdict"] == "PASS" for r in e2)
    return np / len(e2), np, len(e2)


def main() -> None:
    inst_map = {
        r["instance_id"]: r
        for r in read_jsonl(MAIN) + read_jsonl(EXPAND)
        if r.get("valid", True)
    }
    t7_rows = read_jsonl(T7)
    t7_bases = {r["base_id"] for r in t7_rows}
    claim_ids = [r["instance_id"] for r in t7_rows if r.get("condition") == "E1-unit-claim"]
    evid_ids = [r["instance_id"] for r in t7_rows if r.get("condition") == "E1-unit-evid"]

    table = {}
    for verifier in all_verifier_slugs():
        scores = merged_scores(verifier)
        if not scores:
            continue
        joined = join(inst_map, scores, verifier)
        e2_rate, e2_np, e2_n = e2_pass_cond(joined)
        fail_claim, n_c, tot_c = rate(claim_ids, scores, "FAIL")
        fail_evid, n_e, tot_e = rate(evid_ids, scores, "FAIL")
        if e2_n == 0 and n_c == 0 and n_e == 0:
            continue
        table[verifier] = {
            "e2_pass_rate": e2_rate,
            "e2_n": e2_n,
            "e2_pass": e2_np,
            "e1_claim_fail_rate": fail_claim,
            "e1_claim_n": n_c,
            "e1_evid_fail_rate": fail_evid,
            "e1_evid_n": n_e,
        }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(table, indent=2) + "\n")

    def fmt(x):
        return f"{x:.3f}" if x is not None else "—"

    lines = [
        "# E2 | C0 vs T7 E1-unit (per verifier)",
        "",
        f"- E2 cohort: **main x2** (`{E2_INST.name}`); conditional on each verifier's C0 PASS.",
        f"- T7 E1-unit: **{len(claim_ids)}** claim + **{len(evid_ids)}** evid instances ({len(t7_bases)} bases).",
        "",
        "| verifier | E2 PASS (|C0) | E1-unit-claim FAIL | E1-unit-evid FAIL |",
        "|---|---:|---:|---:|",
    ]
    for v, cell in sorted(table.items()):
        e2s = fmt(cell["e2_pass_rate"])
        if cell["e2_n"]:
            e2s += f" ({cell['e2_pass']}/{cell['e2_n']})"
        lines.append(
            f"| {v} | {e2s} | {fmt(cell['e1_claim_fail_rate'])} ({cell['e1_claim_n']}/{len(claim_ids)}) | "
            f"{fmt(cell['e1_evid_fail_rate'])} ({cell['e1_evid_n']}/{len(evid_ids)}) |"
        )
    lines.append("")
    OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
