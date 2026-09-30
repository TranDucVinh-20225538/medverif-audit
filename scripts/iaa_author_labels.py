"""Author reference labels for IAA q2 (natural / PI_ok / nat3)."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

POL_E1 = frozenset({"E1-evid", "E1-claim", "E2"})


def _read(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _inv_mechanism(row: dict) -> str:
    mag = row.get("magnitude") or ""
    if mag == "rephrase":
        return "template"
    if mag in ("paraphrase", "paraphrase_v3") or str(row.get("instance_id", "")).endswith(
        "paraphrase_v3"
    ):
        return "llm"
    if mag == "unit_conversion":
        return "unit"
    return mag or ""


def load_author_label_tables() -> dict:
    nat3 = {r["base_id"]: (r.get("natural") or "").strip().upper() for r in _read(ROOT / "qc/nat3_labels.csv")}
    inv_inst = {
        r["instance_id"]: (r.get("PI_ok") or "").strip().upper()
        for r in _read(ROOT / "qc/inv_claim_PI_ok_labels.csv")
    }
    inv_manual: dict[tuple[str, str, str], str] = {}
    for r in _read(ROOT / "qc/inv_manual_review.csv"):
        pi = (r.get("PI_ok") or "").strip().upper()
        if pi in ("Y", "N"):
            inv_manual[(r["base_id"], r["type"], r.get("mechanism") or "")] = pi
    flip_pi = {
        r["base_id"]: (r.get("PI_ok") or "").strip().upper()
        for r in _read(ROOT / "qc/e1_pol_review.csv")
    }
    dose3: dict[str, dict[str, str]] = {}
    for r in _read(ROOT / "qc/dose3_labels.csv"):
        dose3[r["base_id"]] = {
            k: (r.get(k) or "").strip().upper()
            for k in ("C0_ok", "E1x2_ok", "E1x10_ok", "PI_ok")
        }
    dose_pi = {
        r["base_id"]: (r.get("PI_ok") or "").strip().upper()
        for r in _read(ROOT / "qc/dose_PI_ok_labels.csv")
    }
    dose_audit = {
        r["base_id"]: (r.get("PI_ok") or "").strip().upper()
        for r in _read(ROOT / "qc/main_dose_audit.csv")
    }
    return {
        "nat3": nat3,
        "inv_inst": inv_inst,
        "inv_manual": inv_manual,
        "flip_pi": flip_pi,
        "dose3": dose3,
        "dose_pi": dose_pi,
        "dose_audit": dose_audit,
    }


def author_q2_label(inst: dict, tables: dict | None = None) -> tuple[str | None, str]:
    """Return (Y/N or None if no author label, source tag)."""
    tables = tables or load_author_label_tables()
    bid = inst.get("base_id") or ""
    cond = inst.get("condition")
    mag = inst.get("magnitude") or ""
    typ = inst.get("type")
    iid = inst.get("instance_id") or ""

    if cond == "INV-claim" and mag == "unit_conversion":
        v = tables["nat3"].get(bid)
        if v in ("Y", "N"):
            return v, "nat3"

    if cond == "INV-claim":
        v = tables["inv_inst"].get(iid)
        if v in ("Y", "N"):
            return v, "inv_claim_PI_ok"
        mech = _inv_mechanism(inst)
        if mech != "unit":
            v = tables["inv_manual"].get((bid, typ or "", mech))
            if v in ("Y", "N"):
                return v, "inv_manual_PI_ok"

    if typ == "POLARITY" and cond in POL_E1:
        v = tables["flip_pi"].get(bid)
        if v in ("Y", "N"):
            return v, "flip_PI_ok"

    if typ == "DOSE":
        d3 = tables["dose3"].get(bid, {})
        if cond == "C0":
            v = d3.get("C0_ok") or d3.get("PI_ok")
        elif mag == "x2":
            v = d3.get("E1x2_ok") or d3.get("PI_ok")
        elif mag == "x10":
            v = d3.get("E1x10_ok") or d3.get("PI_ok")
        else:
            v = d3.get("PI_ok")
        if v in ("Y", "N"):
            return v, "dose3"
        for src, tab in (("dose_PI_ok", tables["dose_pi"]), ("main_dose_audit", tables["dose_audit"])):
            v = tab.get(bid)
            if v in ("Y", "N"):
                return v, src

    return None, "missing"


def expected_q1_label(inst: dict) -> str | None:
    v = (inst.get("expected_verdict") or "").strip().upper()
    if v == "PASS":
        return "Y"
    if v == "FAIL":
        return "N"
    return None
