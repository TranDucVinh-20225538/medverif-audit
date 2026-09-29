"""Human review gates for analysis (PI_ok, flip, unit naturalness)."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E1_POL = ROOT / "qc" / "e1_pol_review.csv"
INV_MANUAL = ROOT / "qc" / "inv_manual_review.csv"
UNIT_NAT = ROOT / "qc" / "unit_naturalness.csv"

POL_E1_CONDITIONS = frozenset({"E1-evid", "E1-claim", "E2"})


def _read_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def flip_pi_ok_bases() -> set[str]:
    return {r["base_id"] for r in _read_csv(E1_POL) if (r.get("PI_ok") or "").strip() == "Y"}


def flip_pi_ok_counts() -> dict[str, int]:
    rows = _read_csv(E1_POL)
    y = sum(1 for r in rows if r.get("PI_ok") == "Y")
    n = sum(1 for r in rows if r.get("PI_ok") == "N")
    return {"Y": y, "N": n, "total": len(rows)}


def inv_pi_ok_keys() -> set[tuple[str, str, str]]:
    """(base_id, type, mechanism) for INV manual review accepts."""
    out: set[tuple[str, str, str]] = set()
    for r in _read_csv(INV_MANUAL):
        if (r.get("PI_ok") or "").strip() == "Y":
            out.add((r["base_id"], r["type"], r.get("mechanism") or ""))
    return out


def unit_natural_y_bases() -> set[str]:
    return {r["base_id"] for r in _read_csv(UNIT_NAT) if (r.get("natural") or "").strip() == "Y"}


def unit_natural_labels() -> dict[str, str]:
    """base_id → human natural label (Y/N/empty)."""
    out: dict[str, str] = {}
    for r in _read_csv(UNIT_NAT):
        out[r["base_id"]] = (r.get("natural") or "").strip().upper()
    return out


def effective_unit_natural_y(base_id: str, rule_y: bool) -> bool:
    """Human unit_naturalness.csv overrides rule-based naturalness."""
    human = unit_natural_labels().get(base_id, "")
    if human == "Y":
        return True
    if human == "N":
        return False
    return rule_y


def inv_mechanism(row: dict) -> str:
    mag = row.get("magnitude") or ""
    if mag == "rephrase":
        return "template"
    if mag in ("paraphrase", "paraphrase_v3") or str(row.get("instance_id", "")).endswith("paraphrase_v3"):
        return "llm"
    if mag == "unit_conversion":
        return "unit"
    return mag or ""


def inv_row_pi_ok(row: dict, keys: set[tuple[str, str, str]] | None = None) -> bool:
    if row.get("condition") != "INV-claim":
        return True
    keys = keys if keys is not None else inv_pi_ok_keys()
    mech = inv_mechanism(row)
    if mech == "unit":
        return True
    return (row["base_id"], row["type"], mech) in keys


def analysis_keep_row(
    row: dict,
    *,
    flip_y: set[str] | None = None,
    inv_keys: set[tuple[str, str, str]] | None = None,
) -> bool:
    """Drop POL E1/E2 outside human flip_ok; drop INV outside PI_ok (except DOSE unit)."""
    flip_y = flip_y if flip_y is not None else flip_pi_ok_bases()
    if row.get("type") == "POLARITY" and row.get("condition") in POL_E1_CONDITIONS:
        return row["base_id"] in flip_y
    if row.get("condition") == "INV-claim":
        return inv_row_pi_ok(row, inv_keys)
    return True
