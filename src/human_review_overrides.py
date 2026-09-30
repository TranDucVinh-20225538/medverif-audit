"""Apply PI_ok labels from qc/*.csv to instance validity (post QC rules)."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path("/data2/hpcshared/medverif-audit")
E1_POL = ROOT / "qc" / "e1_pol_review.csv"
INV_MANUAL = ROOT / "qc" / "inv_manual_review.csv"

POL_E1 = frozenset({"E1-evid", "E1-claim", "E2"})


def _read_csv(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def flip_pi_by_base() -> dict[str, str]:
    return {
        r["base_id"]: r["PI_ok"].strip()
        for r in _read_csv(E1_POL)
        if (r.get("PI_ok") or "").strip() in {"Y", "N"}
    }


def inv_pi_yes_keys() -> set[tuple[str, str, str]]:
    out: set[tuple[str, str, str]] = set()
    for r in _read_csv(INV_MANUAL):
        if (r.get("PI_ok") or "").strip() == "Y":
            out.add((r["base_id"], r["type"], r.get("mechanism") or ""))
    return out


def inv_pi_no_keys() -> set[tuple[str, str, str]]:
    out: set[tuple[str, str, str]] = set()
    for r in _read_csv(INV_MANUAL):
        if (r.get("PI_ok") or "").strip() == "N":
            out.add((r["base_id"], r["type"], r.get("mechanism") or ""))
    return out


def inv_mechanism(inst: dict) -> str:
    mag = inst.get("magnitude") or ""
    if mag == "rephrase":
        return "template"
    if mag in ("paraphrase", "paraphrase_v3") or str(inst.get("instance_id", "")).endswith(
        "paraphrase_v3"
    ):
        return "llm"
    if mag == "unit_conversion":
        return "unit"
    return mag or ""


def apply_human_overrides(inst: dict) -> None:
    """Mutate inst valid/invalid_reason/override from human CSVs."""
    bid = inst.get("base_id") or ""
    flip_pi = flip_pi_by_base()
    inv_y = inv_pi_yes_keys()
    inv_n = inv_pi_no_keys()

    if inst.get("type") == "POLARITY" and inst.get("condition") in POL_E1:
        pi = flip_pi.get(bid)
        if pi == "Y":
            inst["valid"] = True
            inst["invalid_reason"] = None
            inst["override"] = "human"
        elif pi == "N":
            inst["valid"] = False
            inst["invalid_reason"] = "human_reject"
            inst.pop("override", None)
        return

    if inst.get("condition") != "INV-claim":
        return

    mech = inv_mechanism(inst)
    if mech == "unit" and inst.get("type") == "DOSE":
        return

    key = (bid, inst.get("type") or "", mech)
    if key in inv_y:
        inst["valid"] = True
        inst["invalid_reason"] = None
        inst["override"] = "human"
    elif key in inv_n:
        inst["valid"] = False
        inst["invalid_reason"] = "human_reject"
        inst.pop("override", None)
