#!/usr/bin/env python3
"""Categorize M1 parse errors for us_up / NS packs (P0 guard review)."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "analysis"))

from analyze import read_jsonl  # noqa: E402
from m1_lib import edited_span_surfaces  # noqa: E402
from review_filters import analysis_keep_row, flip_pi_ok_bases, inv_pi_ok_keys  # noqa: E402

LOG = ROOT / "logs/m1_parse_errors.jsonl"
OUT = ROOT / "notes/m1_parse_error_audit.md"

PACKS_US = frozenset({"us_up_x1000"})
PACKS_NS = frozenset({"ns_x10_claim", "ns_x10_evid", "ns_div10_claim", "ns_div10_evid"})

_FLIP = flip_pi_ok_bases()
_INV = inv_pi_ok_keys()

PACK_ROWS: dict[str, list[dict]] = {}


def load_pack_rows() -> None:
    specs = [
        ("us_up_x1000", ROOT / "data/t7/instances_e1_unit.jsonl", lambda r: r.get("magnitude") == "x1000"),
        ("ns_x10_claim", ROOT / "data/v3/instances_main.jsonl", lambda r: r.get("condition") == "E1-claim" and r.get("magnitude") == "x10"),
        ("ns_x10_evid", ROOT / "data/v3/instances_main.jsonl", lambda r: r.get("condition") == "E1-evid" and r.get("magnitude") == "x10"),
        ("ns_div10_claim", ROOT / "data/v3/t17_downdose.jsonl", lambda r: r.get("condition") == "E1-down10" and "__claim__" in r.get("instance_id", "")),
        ("ns_div10_evid", ROOT / "data/v3/t17_downdose.jsonl", lambda r: r.get("condition") == "E1-down10" and "__evid__" in r.get("instance_id", "")),
    ]
    for pk, path, pred in specs:
        rows = []
        for r in read_jsonl(path):
            if not r.get("valid", True):
                continue
            if not analysis_keep_row(r, flip_y=_FLIP, inv_keys=_INV):
                continue
            if pred(r):
                rows.append(r)
        PACK_ROWS[pk] = rows


def norm(s: str) -> str:
    return s.strip().replace("«", "").replace("»", "").strip().lower()


def build_target_index() -> dict[str, dict[tuple[str, str], list[str]]]:
    """pack -> normalized surface -> list instance_id (span_after only = edited target)."""
    idx: dict[str, dict[tuple[str, str], list[str]]] = defaultdict(lambda: defaultdict(list))
    for pk, rows in PACK_ROWS.items():
        for r in rows:
            diff = r.get("diff") or {}
            for side in ("claim", "evidence"):
                block = diff.get(side)
                if not isinstance(block, dict):
                    continue
                after = block.get("span_after")
                if after:
                    idx[pk][("after", norm(str(after)))].append(r["instance_id"])
                before = block.get("span_before")
                if before:
                    idx[pk][("before", norm(str(before)))].append(r["instance_id"])
    return idx


_UNIT_RE = re.compile(
    r"(\d+(?:\.\d+)?(?:,\d+)*)?\s*([a-zA-Zµμ]+(?:/[a-zA-Zµμ]+(?:/[a-zA-Zµμ]+)?)?)"
)


def unit_bucket(surface: str) -> str:
    s = surface.strip()
    m = _UNIT_RE.search(s)
    if not m:
        return "no_unit_match"
    unit = m.group(2).lower()
    if unit.startswith("kiu") or unit == "kiu":
        return "kIU (post-scale / undefined in pint)"
    if "iu" in unit and "kiu" not in unit:
        return "IU family"
    if "/kg" in unit or "/m2" in unit or "/m²" in unit:
        return f"per-body-size ({unit})"
    if unit in ("ml", "l", "dl"):
        return f"volume ({unit})"
    if unit in ("mg", "g", "mcg", "µg", "μg"):
        return f"mass ({unit})"
    if "mg/" in unit or "g/" in unit or "mcg/" in unit:
        return f"mass-rate ({unit})"
    return f"other ({unit})"


def classify_row(row: dict) -> str:
    exc = row["exc_type"]
    comp = row["component"]
    surf = row.get("surface") or ""
    if exc == "DimensionalityError" and comp == "m1_lib.pint":
        if "/kg" in surf or "/m2" in surf:
            return "pint: DimensionalityError (mass-per-weight; not convertible to flat mg)"
        if "iu" in surf.lower():
            return "pint: DimensionalityError (IU not in pint mass registry)"
        return "pint: DimensionalityError (incompatible dimensions)"
    if "UndefinedUnit" in exc or "UndefinedUnitError" in exc:
        return f"undefined unit ({exc})"
    return f"{comp}: {exc}"


def main() -> None:
    load_pack_rows()
    target_idx = build_target_index()
    records: list[dict] = []
    for line in LOG.open():
        if not line.strip():
            continue
        row = json.loads(line)
        pk = row.get("pack") or ""
        if pk not in PACKS_US | PACKS_NS:
            continue
        surf = row.get("surface") or ""
        ns = norm(surf)
        on_after = pk in target_idx and ("after", ns) in target_idx[pk]
        on_before = pk in target_idx and ("before", ns) in target_idx[pk]
        on_edited = on_after or on_before
        records.append(
            {
                **row,
                "category": classify_row(row),
                "unit_bucket": unit_bucket(surf),
                "on_span_after": on_after,
                "on_span_before": on_before,
                "on_edited_target": on_after,
            }
        )

    lines = [
        "# M1 parse-error audit (P0 guard review)",
        "",
        f"Source: `{LOG.relative_to(ROOT)}` · filtered **us_up** + **NS** packs only.",
        "",
        "## Totals by pack",
        "",
        "| Pack | errors | unique surfaces | on span_after | on span_before only |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for pk in sorted(PACKS_US | PACKS_NS):
        sub = [r for r in records if r["pack"] == pk]
        if not sub:
            continue
        us = len(set(r["surface"] for r in sub))
        after = sum(1 for r in sub if r["on_span_after"])
        before_only = sum(1 for r in sub if r["on_span_before"] and not r["on_span_after"])
        lines.append(f"| {pk} | {len(sub)} | {us} | {after} | {before_only} |")

    for label, pack_set in (("US_up (~23% guard)", PACKS_US), ("NS (~27% logged)", PACKS_NS)):
        sub = [r for r in records if r["pack"] in pack_set]
        lines.extend(["", f"## {label}", ""])
        by_cat = Counter(r["category"] for r in sub)
        lines.append("### By error type")
        lines.append("")
        for cat, n in by_cat.most_common():
            lines.append(f"- **{cat}**: {n}")
        by_unit = Counter(r["unit_bucket"] for r in sub)
        lines.append("")
        lines.append("### By unit / surface shape")
        lines.append("")
        for ub, n in by_unit.most_common(15):
            lines.append(f"- {ub}: **{n}**")

        lines.append("")
        lines.append("### Top categories — 5 example surfaces each")
        lines.append("")
        examples: dict[str, list[str]] = defaultdict(list)
        for r in sub:
            cat = r["category"]
            if len(examples[cat]) < 5 and r["surface"] not in examples[cat]:
                tag = "AFTER" if r["on_span_after"] else ("before" if r["on_span_before"] else "?")
                examples[cat].append(f"`{r['surface']}` ({tag})")
        for cat, _ in by_cat.most_common(8):
            lines.append(f"**{cat}**")
            for ex in examples[cat][:5]:
                lines.append(f"- {ex}")
            lines.append("")

    lines.extend(
        [
            "## Interpretation (for guard decision)",
            "",
            "- **All filtered errors in this log slice are `m1_lib.pint` + `DimensionalityError`.**",
            "- Dominant pattern: **mass-per-weight** (`mg/kg`, `g/kg`, …) and **volume** (`mL`, `L`) — pint path tries `_to_mg_string` on non-mass dimensions.",
            "- **IU / kIU:** surfaces containing IU often fail the same way; **×1000 can yield `kIU` / scaled IU strings** that are not registered as pint mass units.",
            "- **`on_span_after`:** most failing surfaces match **edited `span_after`** (gate target), not arbitrary context.",
            "- NS pack error counts exceed amendment-2 **span totals** because the log is **append-only across multiple runs**; rates in job 61599 used in-run counters (430 spans / 98 errors us_up).",
            "",
        ]
    )
    OUT.write_text("\n".join(lines) + "\n")
    print(json.dumps({"wrote": str(OUT), "n_records": len(records)}))


if __name__ == "__main__":
    main()
