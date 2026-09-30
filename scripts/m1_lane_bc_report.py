#!/usr/bin/env python3
"""Reviewer M1 report: Lane B + Lane C packs, before→after QI/NS/US + coverage."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from analyze import _c0_pass_bases, _parsed, bootstrap_rate, read_jsonl  # noqa: E402
from review_filters import analysis_keep_row  # noqa: E402
from m1_coverage_audit import audit_pack_instances  # noqa: E402
from verifier_labels import DISPLAY_NAME  # noqa: E402

OUT_MD = ROOT / "notes/m1_lane_bc_report.md"
OUT_JSON = ROOT / "notes/m1_lane_bc_report.json"

V4_LLAMA = "v4_ragas_nli.llama.jsonl"


def load_instances(rel: str) -> list[dict]:
    rows = []
    for r in read_jsonl(ROOT / rel):
        if not r.get("valid", True):
            continue
        if not analysis_keep_row(r):
            continue
        rows.append(r)
    return rows


def score_path(score_dir: Path, verifier: str) -> Path | None:
    if verifier == "v4_ragas_nli":
        for name in (V4_LLAMA, "v4_ragas_nli.jsonl"):
            p = score_dir / name
            if p.is_file():
                return p
        return None
    if verifier == "v2b_bespoke":
        for name in ("v2b_bespoke.jsonl", "t6_bespoke_minicheck.jsonl"):
            p = score_dir / name
            if p.is_file():
                return p
        return None
    p = score_dir / f"{verifier}.jsonl"
    return p if p.is_file() else None


def load_scores(score_dir: Path, verifier: str) -> dict[str, dict]:
    path = score_path(score_dir, verifier)
    if not path:
        return {}
    out: dict[str, dict] = {}
    for line in path.open():
        if not line.strip():
            continue
        row = json.loads(line)
        iid = row.get("instance_id")
        if iid:
            out[iid] = row
    return out


def c0_pass_bases_for_pack(inst_rows: list[dict], score_dir: Path, verifier: str) -> set[str]:
    """C0 PASS bases for pack base_ids (C0 rows may live outside the pack JSONL)."""
    base_ids = {r["base_id"] for r in inst_rows}
    c0_rows = []
    for rel in ("data/v3/instances_main.jsonl", "data/lane_c/m1_h2_main.jsonl"):
        for r in load_instances(rel):
            if r["base_id"] not in base_ids or r.get("condition") != "C0":
                continue
            c0_rows.append(r)
    if not c0_rows:
        return _c0_pass_bases(join(inst_rows, load_scores(score_dir, verifier), verifier))
    sc = load_scores(score_dir, verifier)
    jc0 = join(c0_rows, sc, verifier)
    return _c0_pass_bases(jc0) if jc0 else set()


def join(inst_rows: list[dict], scores: dict[str, dict], verifier: str) -> list[dict]:
    joined = []
    for inst in inst_rows:
        sc = scores.get(inst["instance_id"])
        if not sc:
            continue
        row = dict(inst)
        row["verifier"] = verifier
        row["verdict"] = sc.get("verdict")
        row["raw_output"] = sc.get("raw_output") or sc.get("explanation") or ""
        joined.append(row)
    return joined


def rate_for(
    block: list[dict],
    *,
    condition: str | tuple[str, ...],
    want: str = "PASS",
    cond_bases: set[str] | None = None,
) -> dict:
    """Base-level bootstrap; QI uses PASS on INV, NS/US use FAIL on E1."""
    if isinstance(condition, str):
        conds = (condition,)
    else:
        conds = condition
    cond_bases = cond_bases if cond_bases is not None else _c0_pass_bases(block)
    by_base: dict[str, list[dict]] = defaultdict(list)
    for r in block:
        if r["base_id"] not in cond_bases:
            continue
        if r.get("condition") not in conds:
            continue
        if not _parsed(r):
            continue
        by_base[r["base_id"]].append(r)
    groups: list[tuple[int, int]] = []
    for g in by_base.values():
        if want == "PASS":
            groups.append((sum(1 for x in g if x["verdict"] == "PASS"), len(g)))
        else:
            groups.append((sum(1 for x in g if x["verdict"] == "FAIL"), len(g)))
    return bootstrap_rate(groups)


def fmt_stat(st: dict) -> str:
    if not st or st.get("rate") is None:
        return "NA"
    lo, hi = st.get("lo"), st.get("hi")
    ci = f" [{lo:.3f},{hi:.3f}]" if lo is not None and hi is not None else ""
    return f"{st['rate']:.3f}{ci} ({st['num']}/{st['den']})"


def discover_verifiers(*dirs: Path) -> list[str]:
    slugs: set[str] = set()
    for d in dirs:
        if not d.is_dir():
            continue
        for p in d.glob("*.jsonl"):
            name = p.name
            if name == V4_LLAMA:
                slugs.add("v4_ragas_nli")
            elif name == "t6_bespoke_minicheck.jsonl":
                slugs.add("v2b_bespoke")
            elif name.endswith(".jsonl"):
                slugs.add(name[:-6])
    return sorted(slugs)


def e1_unit_repairs(
    before: list[dict],
    after: list[dict],
    verifier: str,
) -> tuple[int, int, list[str]]:
    """FAIL→PASS on E1-unit-evid, paired by instance_id."""
    b = {r["instance_id"]: r for r in before if r["verifier"] == verifier}
    a = {r["instance_id"]: r for r in after if r["verifier"] == verifier}
    repairs = 0
    total_evid = 0
    expl: list[str] = []
    for iid, rb in b.items():
        if rb.get("condition") != "E1-unit-evid":
            continue
        ra = a.get(iid)
        if not ra or not _parsed(rb) or not _parsed(ra):
            continue
        total_evid += 1
        if rb["verdict"] == "FAIL" and ra["verdict"] == "PASS":
            repairs += 1
            if len(expl) < 5:
                txt = (ra.get("raw_output") or ra.get("explanation") or "").strip().replace("\n", " ")
                if txt and not txt.replace(".", "").replace("-", "").isdigit():
                    expl.append(f"`{iid}`: {txt[:400]}")
    return repairs, total_evid, expl


PACK_SPECS = [
    {
        "id": "lane_b_m1_t7",
        "label": "Lane B · m1_t7_e1_unit",
        "instances": "data/lane_b/m1_t7_e1_unit.jsonl",
        "before_dir": ROOT / "results/raw/t7",
        "after_dir": ROOT / "results/raw/lane_b/m1_t7_e1_unit",
    },
    {
        "id": "lane_b_m1_main",
        "label": "Lane B · m1_main_inv_e1_c0",
        "instances": "data/lane_b/m1_main_inv_e1_c0.jsonl",
        "before_dir": ROOT / "results/raw",
        "after_dir": ROOT / "results/raw/lane_b/m1_main_inv_e1_c0",
    },
    {
        "id": "lane_c_m1_h2",
        "label": "Lane C · m1_h2_main",
        "instances": "data/lane_c/m1_h2_main.jsonl",
        "before_dir": ROOT / "results/raw",
        "after_dir": ROOT / "results/raw_m1/lane_c",
    },
]


def main() -> None:
    payload: dict = {"packs": []}
    lines = [
        "# M1 report — Lane B + Lane C packs",
        "",
        "Before = scores on **original** text (`results/raw`…); after = **M1** "
        "(pre-applied T7 pack and/or `MEDVERIF_M1=1` / `raw_m1/lane_c`). "
        "Bootstrap **1000** resamples by `base_id`, seed **42**. QI = INV-claim **PASS** | C0; "
        "NS/US = E1 **FAIL** | C0.",
        "",
    ]

    for spec in PACK_SPECS:
        inst = load_instances(spec["instances"])
        cov = audit_pack_instances(inst)
        verifiers = discover_verifiers(spec["before_dir"], spec["after_dir"])
        pack_out = {"id": spec["id"], "n_instances": len(inst), "coverage": cov, "verifiers": {}}
        lines.extend(
            [
                f"## {spec['label']}",
                "",
                f"- Instances (analysis keep): **{len(inst)}**",
                f"- M1 dose-span coverage: **{cov['m1_parsable']}/{cov['dose_spans']}** "
                f"({cov['coverage_pct']:.1f}%)" if cov["dose_spans"] else "- M1 dose-span coverage: **0 spans**",
                "",
                "### Normalizer failure categories (non-ok spans)",
                "",
            ]
        )
        if cov["failure_counts"]:
            for cat, cnt in sorted(cov["failure_counts"].items(), key=lambda x: -x[1]):
                ex = cov["failure_examples"].get(cat, "")
                lines.append(f"- **{cat}**: {cnt} — e.g. _{ex[:140]}_")
        else:
            lines.append("- _(none)_")
        lines.extend(["", "### Before → after metrics", ""])
        lines.append(
            "| Verifier | QI | NS claim | NS evid | US claim | US evid |"
        )
        lines.append("| --- | --- | --- | --- | --- | --- |")

        for v in verifiers:
            sb = load_scores(spec["before_dir"], v)
            sa = load_scores(spec["after_dir"], v)
            if not sb and not sa:
                continue
            jb = join(inst, sb, v)
            ja = join(inst, sa, v)
            if not jb and not ja:
                continue
            label = DISPLAY_NAME.get(v, v)
            c0_before = c0_pass_bases_for_pack(inst, spec["before_dir"], v)
            c0_after = c0_pass_bases_for_pack(inst, spec["after_dir"], v)
            metrics = {
                "QI": (
                    rate_for(jb, condition="INV-claim", want="PASS", cond_bases=c0_before),
                    rate_for(ja, condition="INV-claim", want="PASS", cond_bases=c0_after),
                ),
                "NS_claim": (
                    rate_for(jb, condition="E1-claim", want="FAIL", cond_bases=c0_before),
                    rate_for(ja, condition="E1-claim", want="FAIL", cond_bases=c0_after),
                ),
                "NS_evid": (
                    rate_for(jb, condition="E1-evid", want="FAIL", cond_bases=c0_before),
                    rate_for(ja, condition="E1-evid", want="FAIL", cond_bases=c0_after),
                ),
                "US_claim": (
                    rate_for(jb, condition="E1-unit-claim", want="FAIL", cond_bases=c0_before),
                    rate_for(ja, condition="E1-unit-claim", want="FAIL", cond_bases=c0_after),
                ),
                "US_evid": (
                    rate_for(jb, condition="E1-unit-evid", want="FAIL", cond_bases=c0_before),
                    rate_for(ja, condition="E1-unit-evid", want="FAIL", cond_bases=c0_after),
                ),
            }
            rep_b, rep_n, rep_ex = e1_unit_repairs(jb, ja, v)
            pack_out["verifiers"][v] = {
                "metrics": {k: {"before": b, "after": a} for k, (b, a) in metrics.items()},
                "e1_unit_evid_repair": {"before_pass_after": rep_b, "n": rep_n, "examples": rep_ex},
            }
            def cell(key: str) -> str:
                b, a = metrics[key]
                return f"{fmt_stat(b)} → {fmt_stat(a)}"

            lines.append(
                f"| {label} | {cell('QI')} | {cell('NS_claim')} | {cell('NS_evid')} | "
                f"{cell('US_claim')} | {cell('US_evid')} |"
            )
            if rep_n and rep_b:
                lines.append("")
                lines.append(f"**{label}** E1-unit-evid M1 repairs: **{rep_b}/{rep_n}** FAIL→PASS.")
                for ex in rep_ex:
                    lines.append(f"- {ex}")
                lines.append("")

        lines.append("")
        payload["packs"].append(pack_out)

    OUT_MD.write_text("\n".join(lines) + "\n")
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"wrote": str(OUT_MD), "packs": len(payload["packs"])}, indent=2))


if __name__ == "__main__":
    main()
