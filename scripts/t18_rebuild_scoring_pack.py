#!/usr/bin/env python3
"""T18 scoring pack: base guards, value/unit errors, unit_spell; INV appendix only."""

from __future__ import annotations

import csv
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pack_span_guards import t18_base_exclusion  # noqa: E402
from perturb import _diff, _instance  # noqa: E402
from text_utils import (  # noqa: E402
    T18_METRIC_RE,
    format_decimal,
    highlight,
    parse_decimal,
    scale_metric_span,
    t18_metric_inv_conversion,
)

BASES = ROOT / "data/t18/bases_t18.jsonl"
OUT = ROOT / "data/t18/instances_t18.jsonl"
PI_CSV = ROOT / "qc/t18_PI_ok_labels.csv"
EXCLUDED_JSON = ROOT / "notes/t18_excluded_bases.json"
MANIFEST = ROOT / "notes/t18_scoring_manifest.json"

SPELL_PAIRS = (
    (re.compile(r"^(\d+(?:\.\d+)?)\s*km$", re.I), "kilometre", "kilometres"),
    (re.compile(r"^(\d+(?:\.\d+)?)\s*m$", re.I), "metre", "metres"),
    (re.compile(r"^(\d+(?:\.\d+)?)\s*cm$", re.I), "centimetre", "centimetres"),
    (re.compile(r"^(\d+(?:\.\d+)?)\s*kg$", re.I), "kilogram", "kilograms"),
    (re.compile(r"^(\d+(?:\.\d+)?)\s*g$", re.I), "gram", "grams"),
    (re.compile(r"^(\d+(?:\.\d+)?)\s*L$", re.I), "litre", "litres"),
    (re.compile(r"^(\d+(?:\.\d+)?)\s*mL$", re.I), "millilitre", "millilitres"),
    (re.compile(r"^(\d+(?:\.\d+)?)\s*kilometres?$", re.I), "km", "km"),
    (re.compile(r"^(\d+(?:\.\d+)?)\s*metres?$", re.I), "m", "m"),
    (re.compile(r"^(\d+(?:\.\d+)?)\s*centimetres?$", re.I), "cm", "cm"),
    (re.compile(r"^(\d+(?:\.\d+)?)\s*kilograms?$", re.I), "kg", "kg"),
    (re.compile(r"^(\d+(?:\.\d+)?)\s*grams?$", re.I), "g", "g"),
    (re.compile(r"^(\d+(?:\.\d+)?)\s*litres?$", re.I), "L", "L"),
    (re.compile(r"^(\d+(?:\.\d+)?)\s*millilitres?$", re.I), "mL", "mL"),
)

METRIC_SWAP = {
    "km": "m",
    "m": "km",
    "cm": "m",
    "kg": "g",
    "g": "kg",
    "L": "mL",
    "mL": "L",
    "l": "ml",
    "ml": "L",
    "kW": "W",
    "W": "kW",
}

def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_pi_inv_ok() -> set[str]:
    if not PI_CSV.is_file():
        return set()
    ok: set[str] = set()
    with PI_CSV.open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if (row.get("PI_ok") or "").strip().upper() == "Y":
                ok.add(row["instance_id"].strip())
    return ok


def spell_variant(span: str) -> str | None:
    s = span.strip()
    for pat, sing, plur in SPELL_PAIRS:
        m = pat.match(s)
        if not m:
            continue
        num = parse_decimal(m.group(1))
        if num == Decimal("1"):
            return f"1 {sing}"
        return f"{format_decimal(num)} {plur}"
    return None


def metric_unit_swap(span: str) -> tuple[str, str] | None:
    m = T18_METRIC_RE.match(span.strip())
    if not m or m.group(0) != span.strip():
        return None
    unit = m.group(2)
    key = unit if unit in METRIC_SWAP else unit.lower()
    if key == "ml":
        key = "mL"
    dst = METRIC_SWAP.get(key) or METRIC_SWAP.get(unit.lower())
    if not dst:
        return None
    return f"{m.group(1)} {dst}", f"{unit}→{dst}"


def add_value_leg(
    instances: list[dict],
    base: dict,
    claim0: str,
    evid0: str,
    c0: int,
    c1: int,
    e0: int,
    e1: int,
    cspan: str,
    espan: str,
    factor: Decimal,
    mag: str,
) -> None:
    new_span = scale_metric_span(espan, factor)
    evid_edit = _diff(evid0, evid0, e0, e1, new_span, "evidence")
    claim_edit = _diff(claim0, claim0, c0, c1, new_span, "claim")
    both = {
        "evidence": {k: evid_edit[k] for k in evid_edit if k != "text"},
        "claim": {k: claim_edit[k] for k in claim_edit if k != "text"},
    }
    instances.append(
        _instance(
            base,
            "E1-evid",
            mag,
            claim0,
            evid_edit["text"],
            "FAIL",
            {"evidence": both["evidence"], "claim_unchanged": True},
            cspan,
            new_span,
        )
    )
    instances.append(
        _instance(
            base,
            "E1-claim",
            mag,
            claim_edit["text"],
            evid0,
            "FAIL",
            {"claim": both["claim"], "evidence_unchanged": True},
            new_span,
            espan,
        )
    )
    instances.append(
        _instance(
            base,
            "E2",
            mag,
            claim_edit["text"],
            evid_edit["text"],
            "PASS",
            both,
            new_span,
            new_span,
        )
    )


def add_unit_swap(instances: list[dict], base: dict, claim0: str, evid0: str, c0: int, c1: int, espan: str) -> None:
    pair = metric_unit_swap(espan)
    if not pair:
        return
    new_span, tag = pair
    claim_edit = _diff(claim0, claim0, c0, c1, new_span, "claim")
    if not claim_edit["confined_to_span"]:
        return
    inst = _instance(
        base,
        "E1-unit",
        "unit_swap",
        claim_edit["text"],
        evid0,
        "FAIL",
        {"claim": {k: claim_edit[k] for k in claim_edit if k != "text"}, "unit_pair": tag, "evidence_unchanged": True},
        new_span,
        espan,
    )
    inst["t18_family"] = "unit_swap"
    instances.append(inst)


def add_unit_spell(instances: list[dict], base: dict, claim0: str, evid0: str, c0: int, c1: int, espan: str) -> None:
    spelled = spell_variant(espan)
    if not spelled or spelled.replace(" ", "") == espan.replace(" ", ""):
        return
    claim_edit = _diff(claim0, claim0, c0, c1, spelled, "claim")
    if not claim_edit["confined_to_span"]:
        return
    inst = _instance(
        base,
        "INV-claim",
        "unit_spell",
        claim_edit["text"],
        evid0,
        "PASS",
        {"claim": {k: claim_edit[k] for k in claim_edit if k != "text"}, "evidence_unchanged": True},
        spelled,
        espan,
    )
    inst["t18_family"] = "unit_spell"
    inst["condition"] = "T18-unit_spell"
    instances.append(inst)


def build_base(base: dict, inv_appendix_ids: set[str]) -> tuple[list[dict], str | None]:
    reason = t18_base_exclusion(base)
    if reason:
        return [], reason
    claim0 = base["claim"]
    evid0 = base["evidence"]
    c0, c1 = base["claim_span_start"], base["claim_span_end"]
    e0, e1 = base["evidence_span_start"], base["evidence_span_end"]
    cspan = claim0[c0:c1]
    espan = evid0[e0:e1]
    unchanged = {
        "where": "none",
        "span_before": cspan,
        "span_after": cspan,
        "edit_distance": 0,
        "confined_to_span": True,
        "highlight_before": highlight(claim0, c0, c1),
        "highlight_after": highlight(claim0, c0, c1),
        "evidence_highlight": highlight(evid0, e0, e1),
    }
    out: list[dict] = []
    out.append(_instance(base, "C0", "none", claim0, evid0, "PASS", unchanged, cspan, espan))
    for factor, mag in ((Decimal(2), "x2"), (Decimal("0.5"), "div2")):
        add_value_leg(out, base, claim0, evid0, c0, c1, e0, e1, cspan, espan, factor, mag)
    add_unit_swap(out, base, claim0, evid0, c0, c1, espan)
    add_unit_spell(out, base, claim0, evid0, c0, c1, espan)
    pair = t18_metric_inv_conversion(cspan, claim0)
    if pair:
        inv_span, src = pair
        inv_edit = _diff(claim0, claim0, c0, c1, inv_span, "claim")
        if inv_edit["confined_to_span"] and inv_edit["text"] != claim0:
            inst = _instance(
                base,
                "INV-claim",
                "unit_conversion",
                inv_edit["text"],
                evid0,
                "PASS",
                {
                    "claim": {k: inv_edit[k] for k in inv_edit if k != "text"},
                    "evidence_unchanged": True,
                    "unit_inv_source": src,
                },
                inv_span,
                espan,
            )
            inst["t18_family"] = "unit_conversion"
            iid = inst["instance_id"]
            if iid in inv_appendix_ids:
                inst["t18_inv_appendix"] = True
                inst["valid"] = True
            else:
                inst["valid"] = False
                inst["invalid_reason"] = "t18_inv_conversion_excluded"
            out.append(inst)
    for row in out:
        row.setdefault("valid", True)
        row["subset"] = "t18_wikipedia"
        if row.get("condition") == "INV-claim" and row.get("magnitude") == "unit_conversion":
            continue
        if row.get("magnitude") == "x10":
            row["valid"] = False
            row["invalid_reason"] = "t18_x10_excluded"
    return out, None


def appendix_inv_row(base: dict, inv_id: str) -> dict | None:
    claim0 = base["claim"]
    evid0 = base["evidence"]
    c0, c1 = base["claim_span_start"], base["claim_span_end"]
    espan = evid0[base["evidence_span_start"] : base["evidence_span_end"]]
    cspan = claim0[c0:c1]
    pair = t18_metric_inv_conversion(cspan, claim0)
    if not pair:
        return None
    inv_span, src = pair
    inv_edit = _diff(claim0, claim0, c0, c1, inv_span, "claim")
    if not inv_edit["confined_to_span"]:
        return None
    inst = _instance(
        base,
        "INV-claim",
        "unit_conversion",
        inv_edit["text"],
        evid0,
        "PASS",
        {
            "claim": {k: inv_edit[k] for k in inv_edit if k != "text"},
            "evidence_unchanged": True,
            "unit_inv_source": src,
        },
        inv_span,
        espan,
    )
    inst["instance_id"] = inv_id
    inst["t18_family"] = "unit_conversion"
    inst["t18_inv_appendix"] = True
    inst["valid"] = True
    inst["subset"] = "t18_wikipedia"
    return inst


def main() -> None:
    inv_ok = load_pi_inv_ok()
    bases = read_jsonl(BASES)
    by_id = {b["id"]: b for b in bases}
    excluded: list[dict] = []
    instances: list[dict] = []
    for base in bases:
        rows, reason = build_base(base, inv_ok)
        if reason:
            excluded.append({"base_id": base["id"], "reason": reason})
            continue
        instances.extend(rows)
    have_inv = {r["instance_id"] for r in instances if r.get("t18_inv_appendix")}
    appendix: list[dict] = []
    for iid in sorted(inv_ok):
        if iid in have_inv:
            continue
        bid = iid.split("__")[0]
        base = by_id.get(bid)
        if not base:
            continue
        row = appendix_inv_row(base, iid)
        if row:
            appendix.append(row)
    instances.extend(appendix)
    APPENDIX = ROOT / "data/t18/instances_t18_inv_appendix.jsonl"
    write_jsonl(APPENDIX, appendix)
    write_jsonl(OUT, instances)
    EXCLUDED_JSON.write_text(json.dumps({"excluded": excluded}, indent=2) + "\n")
    from collections import Counter

    scorable = [r for r in instances if r.get("valid", True) and not r.get("t18_inv_appendix")]
    fam = Counter(
        r.get("t18_family") or r.get("magnitude") or r.get("condition") for r in scorable
    )
    manifest = {
        "bases_total": len(bases),
        "bases_excluded": len(excluded),
        "instances_total": len(instances),
        "instances_scoring": len(scorable),
        "inv_appendix_only": sum(1 for r in instances if r.get("t18_inv_appendix")),
        "inv_appendix_path": str((ROOT / "data/t18/instances_t18_inv_appendix.jsonl").relative_to(ROOT)),
        "families_scoring": dict(fam),
        "excluded_path": str(EXCLUDED_JSON.relative_to(ROOT)),
        "instances_path": str(OUT.relative_to(ROOT)),
        "pi_inv_y": sorted(inv_ok),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
