#!/usr/bin/env python3
"""T7: FAIL/PASS rates — E1-unit vs E1-claim x2/x10 vs INV-unit, per verifier."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.append(str(ROOT / "scripts"))
from canonical_scores import reference_env_rows  # noqa: E402

from analyze import _c0_pass_bases  # noqa: E402

T7 = ROOT / "data/t7/instances_e1_unit.jsonl"
MAIN = ROOT / "data/v3/instances_main.jsonl"
EXPAND = ROOT / "data/expand/instances_cpu_early.jsonl"
RAW_T7 = ROOT / "results/raw/t7"
RAW_MAIN = ROOT / "results/raw"
OUT_MD = ROOT / "notes/t7_e1_unit_report.md"
OUT_JSON = ROOT / "notes/t7_e1_unit_report.json"

HPC_VERIFIERS = [
    "v1_medscore",
    "v4_ragas_nli",
    "v1b_medscore",
    "v5_ragas_nli",
    "v6_ragas_nli",
    "v1c_medscore",
    "v6_ragas_gpt4o_mini",
    "v6_ragas_haiku45",
    "v6_ragas_llama31_8b",
    "v6_ragas_mistral_small32",
]
T6A_MANIFEST = ROOT / "notes/t6a_eco_checkers.json"

SCORE_DIRS = [
    ROOT / "results/raw/e2_main",
    ROOT / "results/raw",
    ROOT / "results/raw/t6b/full",
    ROOT / "results/raw/t2_full",
    ROOT / "results/raw/t7",
    ROOT / "results/raw/t3",
]

CONDITIONAL_LLM = ("v1_medscore", "v4_ragas_nli", "v1b_medscore", "v5_ragas_nli")


def node30_verifiers() -> list[str]:
    base = ["v2a_minicheck", "v3_alignscore", "v2b_bespoke"]
    if T6A_MANIFEST.is_file():
        data = json.loads(T6A_MANIFEST.read_text())
        base.extend(c["id"] for c in data.get("checkers", []))
    return base


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def _score_path(raw_dir: Path, verifier: str) -> Path:
    llama = raw_dir / f"{verifier}.llama.jsonl"
    direct = raw_dir / f"{verifier}.jsonl"
    if llama.is_file():
        return llama
    if direct.is_file():
        return direct
    if verifier == "v2b_bespoke":
        alt = raw_dir / "t6_bespoke_minicheck.jsonl"
        if alt.is_file():
            return alt
    if T6A_MANIFEST.is_file():
        t6a = {c["id"]: c["jsonl"] for c in json.loads(T6A_MANIFEST.read_text()).get("checkers", [])}
        fname = t6a.get(verifier)
        if fname:
            cand = raw_dir / fname
            if cand.is_file():
                return cand
    return direct


def load_scores(raw_dir: Path, verifiers: list[str]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for v in verifiers:
        path = _score_path(raw_dir, v)
        m: dict[str, str] = {}
        for row in (reference_env_rows(path) if path and path.is_file() else []):
            iid = row.get("instance_id")
            if iid:
                m[iid] = row.get("verdict") or ""
        out[v] = m
    return out


def merged_scores(slug: str) -> dict[str, str]:
    """Merge score jsonls (main/C0 in t2_full → t7 overrides per instance_id)."""
    m: dict[str, str] = {}
    paths: list[Path] = []
    if T6A_MANIFEST.is_file():
        t6a = {c["id"]: c["jsonl"] for c in json.loads(T6A_MANIFEST.read_text()).get("checkers", [])}
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


def rate(ids: list[str], scores: dict[str, str], want: str) -> tuple[float | None, int, int]:
    hits = []
    for iid in ids:
        v = scores.get(iid)
        if v:
            hits.append(int(v == want))
    if not hits:
        return None, 0, len(ids)
    return sum(hits) / len(hits), len(hits), len(ids)


def main() -> None:
    t7_rows = read_jsonl(T7)
    t7_bases = {r["base_id"] for r in t7_rows}
    e1_unit_ids = [r["instance_id"] for r in t7_rows]
    claim_ids = [r["instance_id"] for r in t7_rows if r.get("condition") == "E1-unit-claim"]
    evid_ids = [r["instance_id"] for r in t7_rows if r.get("condition") == "E1-unit-evid"]
    iid_base = {r["instance_id"]: r["base_id"] for r in t7_rows}

    ref_rows = read_jsonl(MAIN) + read_jsonl(EXPAND)
    c0_ref = [r for r in ref_rows if r.get("valid", True) and r["base_id"] in t7_bases and r.get("condition") == "C0"]
    e1_claim_ids: list[str] = []
    inv_ids: list[str] = []
    for r in ref_rows:
        if not r.get("valid", True) or r["base_id"] not in t7_bases:
            continue
        if r["condition"] == "E1-claim" and r.get("magnitude") in ("x2", "x10"):
            e1_claim_ids.append(r["instance_id"])
        if r["condition"] == "INV-claim" and r.get("magnitude") == "unit_conversion":
            inv_ids.append(r["instance_id"])

    node_verifiers = node30_verifiers()
    scores_node_t7 = load_scores(RAW_T7, node_verifiers)

    def pick_scores(v: str) -> dict[str, str]:
        sc = merged_scores(v)
        if not sc and v in scores_node_t7:
            sc = scores_node_t7[v]
        elif v in scores_node_t7:
            sc = {**sc, **scores_node_t7[v]}
        return sc

    def c0_pass_bases_for(v: str) -> set[str]:
        sc = pick_scores(v)
        joined = []
        for r in c0_ref:
            iid = r["instance_id"]
            verdict = sc.get(iid)
            if not verdict:
                continue
            row = dict(r)
            row["verifier"] = v
            row["verdict"] = verdict
            joined.append(row)
        return _c0_pass_bases(joined)

    def rate_on_bases(ids: list[str], sc: dict[str, str], bases: set[str], want: str) -> tuple[float | None, int, int]:
        hits = []
        for iid in ids:
            if iid_base.get(iid) not in bases:
                continue
            verdict = sc.get(iid)
            if verdict and verdict != "PARSE_FAIL":
                hits.append(int(verdict == want))
        if not hits:
            return None, 0, len([i for i in ids if iid_base.get(i) in bases])
        return sum(hits) / len(hits), len(hits), len([i for i in ids if iid_base.get(i) in bases])

    all_v = sorted(set(HPC_VERIFIERS + node_verifiers))
    table = {}
    cond_table = {}
    for v in all_v:
        sc = pick_scores(v)
        fail_e1u, n_e1u, tot_e1u = rate(e1_unit_ids, sc, "FAIL")
        fail_e1c, n_e1c, tot_e1c = rate(e1_claim_ids, sc, "FAIL")
        pass_inv, n_inv, tot_inv = rate(inv_ids, sc, "PASS")
        table[v] = {
            "e1_unit_fail_rate": fail_e1u,
            "e1_unit_n_scored": n_e1u,
            "e1_unit_n_cohort": tot_e1u,
            "e1_claim_x2_x10_fail_rate": fail_e1c,
            "e1_claim_n_scored": n_e1c,
            "e1_claim_n_cohort": tot_e1c,
            "inv_unit_pass_rate": pass_inv,
            "inv_unit_n_scored": n_inv,
            "inv_unit_n_cohort": tot_inv,
        }
        c0b = c0_pass_bases_for(v)
        sc = pick_scores(v)
        fc, nc, tc = rate_on_bases(claim_ids, sc, c0b, "FAIL")
        fe, ne, te = rate_on_bases(evid_ids, sc, c0b, "FAIL")
        cond_table[v] = {
            "n_c0_pass_bases": len(c0b),
            "e1_claim_fail_rate_c0": fc,
            "e1_claim_n_c0": nc,
            "e1_claim_den_c0": tc,
            "e1_evid_fail_rate_c0": fe,
            "e1_evid_n_c0": ne,
            "e1_evid_den_c0": te,
        }

    payload = {
        "n_e1_unit_instances": len(e1_unit_ids),
        "n_e1_claim_ref": len(e1_claim_ids),
        "n_inv_unit_ref": len(inv_ids),
        "n_t7_bases": len(t7_bases),
        "verifiers": table,
        "conditional_c0_pass_t7_bases": cond_table,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# T7 E1-unit vs E1-claim vs INV-unit (per verifier)",
        "",
        f"- E1-unit cohort: **{len(e1_unit_ids)}** instances ({len(t7_bases)} bases)",
        f"- Reference E1-claim x2/x10 (same bases): **{len(e1_claim_ids)}**",
        f"- Reference INV-unit (same bases): **{len(inv_ids)}**",
        "",
        "| verifier | E1-unit FAIL rate | n | E1-claim x2/x10 FAIL rate | n | INV-unit PASS rate | n |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for v in all_v:
        cell = table[v]
        def fmt(x):
            return f"{x:.3f}" if x is not None else "—"

        lines.append(
            f"| {v} | {fmt(cell['e1_unit_fail_rate'])} | {cell['e1_unit_n_scored']}/{cell['e1_unit_n_cohort']} | "
            f"{fmt(cell['e1_claim_x2_x10_fail_rate'])} | {cell['e1_claim_n_scored']}/{cell['e1_claim_n_cohort']} | "
            f"{fmt(cell['inv_unit_pass_rate'])} | {cell['inv_unit_n_scored']}/{cell['inv_unit_n_cohort']} |"
        )
    lines.extend(
        [
            "",
            "## Conditional on C0 PASS (T7 bases only; each verifier's own C0 gate)",
            "",
            "| verifier | C0-pass bases | E1-unit-claim FAIL | E1-unit-evid FAIL |",
            "|---|---:|---:|---:|",
        ]
    )
    for v in all_v:
        c = cond_table.get(v, {})
        def fmt(x):
            return f"{x:.3f}" if x is not None else "—"
        lines.append(
            f"| {v} | {c.get('n_c0_pass_bases', 0)} | "
            f"{fmt(c.get('e1_claim_fail_rate_c0'))} ({c.get('e1_claim_n_c0', 0)}/{c.get('e1_claim_den_c0', 0)}) | "
            f"{fmt(c.get('e1_evid_fail_rate_c0'))} ({c.get('e1_evid_n_c0', 0)}/{c.get('e1_evid_den_c0', 0)}) |"
        )
    lines.extend(
        [
            "",
            "### LLM judges (|C0 PASS)",
            "",
            "| verifier | C0-pass bases | E1-unit-claim FAIL | E1-unit-evid FAIL |",
            "|---|---:|---:|---:|",
        ]
    )
    for v in CONDITIONAL_LLM:
        c = cond_table.get(v, {})
        def fmt_llm(x):
            return f"{x:.3f}" if x is not None else "—"
        lines.append(
            f"| {v} | {c.get('n_c0_pass_bases', 0)} | "
            f"{fmt_llm(c.get('e1_claim_fail_rate_c0'))} ({c.get('e1_claim_n_c0', 0)}/{c.get('e1_claim_den_c0', 0)}) | "
            f"{fmt_llm(c.get('e1_evid_fail_rate_c0'))} ({c.get('e1_evid_n_c0', 0)}/{c.get('e1_evid_den_c0', 0)}) |"
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
