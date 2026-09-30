#!/usr/bin/env python3
"""T14: P(PASS) per family conditional on C0 PASS, vs INV-unit natural QI (existing scores)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))

from review_filters import effective_unit_natural_y  # noqa: E402
from text_utils import rule_natural_unit_conversion_label  # noqa: E402
from verifier_labels import (  # noqa: E402
    CANONICAL_VERIFIERS,
    FAMILY_ORDER,
    verifier_display_name,
    verifier_family,
)

import t13_best_of_n_report as t13  # noqa: E402
from t13_best_of_n_report import MAIN, inv_span_before, merged_score_rows, score_from_row  # noqa: E402
from t14_t3_filter_report import is_pass  # noqa: E402

from t14_repr import MAG_SPACING, MAG_SYMBOL, MAG_UNIT  # noqa: E402

INST = ROOT / "data/t14/instances_t14.jsonl"
MANIFEST = ROOT / "data/t14/manifest_t14.json"
OUT_MD = ROOT / "results/tables/t14_c0_conditional_pass.md"
OUT_JSON = ROOT / "notes/t14_c0_conditional_pass.json"

T14_FAMILIES = (
    (MAG_UNIT, "unit spell-out"),
    (MAG_SPACING, "spacing"),
    (MAG_SYMBOL, "symbol (mcg/µg/μg)"),
)


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def c0_and_inv_maps() -> tuple[dict[str, str], dict[str, str]]:
    c0: dict[str, str] = {}
    inv_nat: dict[str, str] = {}
    for r in read_jsonl(MAIN):
        if not r.get("valid", True) or r.get("type") != "DOSE" or r.get("subset") != "main":
            continue
        bid = r["base_id"]
        if r.get("condition") == "C0":
            c0[bid] = r["instance_id"]
        elif r.get("condition") == "INV-claim" and r.get("magnitude") == "unit_conversion":
            orig = inv_span_before(r)
            if effective_unit_natural_y(bid, bool(rule_natural_unit_conversion_label(orig))):
                inv_nat[bid] = r["instance_id"]
    return c0, inv_nat


def t14_by_family() -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {k: [] for k, _ in T14_FAMILIES}
    for row in read_jsonl(INST):
        mag = row.get("magnitude")
        if mag in out:
            out[mag].append(row)
    return out


def conditional_pass(
    slug: str,
    scores: dict[str, dict],
    target_iids: list[tuple[str, str]],
) -> tuple[float | None, int, int]:
    """target_iids: list of (base_id, instance_id). Returns rate, n_cond, n_c0_pass."""
    passes = 0
    n = 0
    n_c0 = 0
    for _bid, iid in target_iids:
        row = scores.get(iid)
        if not row:
            continue
        p = is_pass(slug, row)
        if p is None:
            continue
        n += 1
        passes += int(p)
    return (passes / n if n else None), n, n_c0


def main() -> None:
    c0_map, inv_map = c0_and_inv_maps()
    t14 = t14_by_family()
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.is_file() else {}

    c0_targets = [(bid, iid) for bid, iid in c0_map.items()]
    inv_targets = [(bid, inv_map[bid]) for bid in inv_map if bid in c0_map]
    family_targets: dict[str, list[tuple[str, str]]] = {}
    for mag, _ in T14_FAMILIES:
        family_targets[mag] = [(r["base_id"], r["instance_id"]) for r in t14.get(mag, [])]

    by_verifier: dict[str, dict] = {}
    for slug in CANONICAL_VERIFIERS:
        scores = merged_score_rows(slug)
        # Also merge T14 raw scores (same slug filenames under results/raw/t14)
        t14_dir = ROOT / "results/raw/t14"
        if t14_dir.is_dir():
            names = [f"{slug}.jsonl", f"{slug}.llama.jsonl"]
            if slug.startswith("t6a_"):
                names.append(f"t6_{slug[4:]}.jsonl")
            for name in names:
                path = t14_dir / name
                if path.is_file():
                    for row in read_jsonl(path):
                        iid = row.get("instance_id")
                        if iid:
                            scores[iid] = row

        c0_rate, n_c0_scored, _ = conditional_pass(slug, scores, c0_targets)
        n_c0_pass = 0
        for bid, iid in c0_targets:
            row = scores.get(iid)
            if row and is_pass(slug, row):
                n_c0_pass += 1

        inv_rate, n_inv, _ = conditional_pass(
            slug,
            scores,
            [(bid, iid) for bid, iid in inv_targets if bid in c0_map],
        )
        inv_cond: list[int] = []
        for bid, iid in inv_targets:
            c0_row = scores.get(c0_map[bid])
            if not c0_row or not is_pass(slug, c0_row):
                continue
            row = scores.get(iid)
            if not row:
                continue
            p = is_pass(slug, row)
            if p is None:
                continue
            inv_cond.append(int(p))
        qi = sum(inv_cond) / len(inv_cond) if inv_cond else None

        fam_cells: dict[str, dict] = {}
        for mag, label in T14_FAMILIES:
            cond_pass: list[int] = []
            for bid, iid in family_targets.get(mag, []):
                c0_row = scores.get(c0_map.get(bid, ""))
                if not c0_row or not is_pass(slug, c0_row):
                    continue
                row = scores.get(iid)
                if not row:
                    continue
                p = is_pass(slug, row)
                if p is None:
                    continue
                cond_pass.append(int(p))
            fam_cells[mag] = {
                "label": label,
                "p_pass_given_c0": sum(cond_pass) / len(cond_pass) if cond_pass else None,
                "n_given_c0": len(cond_pass),
            }

        by_verifier[slug] = {
            "display_name": verifier_display_name(slug),
            "family": verifier_family(slug),
            "c0_pass_rate": c0_rate,
            "n_c0_scored": n_c0_scored,
            "n_c0_pass": n_c0_pass,
            "qi_inv_natural_given_c0": qi,
            "n_qi_given_c0": len(inv_cond),
            "families": fam_cells,
        }

    payload = {
        "design": "P(PASS | instance) among bases with C0 PASS for T14 and INV natural QI",
        "t14_instances": {mag: len(rows) for mag, rows in t14.items()},
        "appendix": manifest.get("appendix", {}),
        "by_verifier": by_verifier,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")

    def fmt_rate(x: float | None, n: int) -> str:
        if x is None or x != x:
            return f"— (n={n})"
        return f"{x:.3f} (n={n})"

    lines = [
        "# T14 — pass rates conditional on C0 PASS",
        "",
        "Among **main DOSE** bases where the verifier **PASS**es **C0**, "
        "report **P(PASS)** on each T14 claim-side family (expected PASS). "
        "**QI** column: same conditioning for **INV-unit natural** (conversion) — higher is better.",
        "",
        f"- T14 pack sizes: unit_spell **{len(t14.get(MAG_UNIT, []))}**, "
        f"spacing **{len(t14.get(MAG_SPACING, []))}**, symbol **{len(t14.get(MAG_SYMBOL, []))}**.",
    ]
    app = manifest.get("appendix") or {}
    if app.get("thousands_sep"):
        lines.append(f"- Appendix: {app['thousands_sep']}")
    lines.extend(["", "| model | family | C0 pass rate | n C0 | QI (INV nat | C0) | unit spell | spacing | symbol |", "|---|---|---:|---:|---:|---:|---:|---:|"])

    for slug, d in sorted(
        by_verifier.items(),
        key=lambda t: (FAMILY_ORDER.get(t[1]["family"], 9), t[0]),
    ):
        fu = d["families"][MAG_UNIT]
        fs = d["families"][MAG_SPACING]
        fy = d["families"][MAG_SYMBOL]
        lines.append(
            f"| {d['display_name']} | {d['family']} | "
            f"{fmt_rate(d['c0_pass_rate'], d['n_c0_scored'])} | {d['n_c0_pass']} | "
            f"{fmt_rate(d['qi_inv_natural_given_c0'], d['n_qi_given_c0'])} | "
            f"{fmt_rate(fu['p_pass_given_c0'], fu['n_given_c0'])} | "
            f"{fmt_rate(fs['p_pass_given_c0'], fs['n_given_c0'])} | "
            f"{fmt_rate(fy['p_pass_given_c0'], fy['n_given_c0'])} |"
        )

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
