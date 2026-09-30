"""Classify textbook vs label dose span surface differences (M1-matched pairs)."""

from __future__ import annotations

import re
from decimal import Decimal

from quantity_norm import _MASS_TO_MG, _split_unit  # noqa: PLC2701
from text_utils import DOSE_RE, format_decimal, parse_decimal

_SYMBOL_MASS = (
    frozenset({"mcg", "µg", "μg", "ug"}),
)
_SPELL_MASS = (
    (frozenset({"g", "grams"}), "spelling"),
    (frozenset({"mg", "milligrams"}), "spelling"),
    (frozenset({"mcg", "micrograms", "µg", "μg"}), "spelling"),
)


def parse_span(span: str) -> tuple[Decimal, str] | None:
    m = DOSE_RE.search(span.strip())
    if not m:
        return None
    return parse_decimal(m.group(1)), m.group(2)


def mass_mg(n: Decimal, unit: str) -> Decimal | None:
    base, _ = _split_unit(unit)
    if base in _MASS_TO_MG:
        return n * _MASS_TO_MG[base]
    return None


def categorize_surface_diff(textbook_span: str, label_span: str) -> str:
    pt = parse_span(textbook_span)
    pl = parse_span(label_span)
    if not pt or not pl:
        return "other"
    nt, ut = pt
    nl, ul = pl
    mt, ml = mass_mg(nt, ut), mass_mg(nl, ul)
    if mt is not None and ml is not None and mt == ml:
        if nt == nl and ut.replace(" ", "").lower() == ul.replace(" ", "").lower():
            if textbook_span.strip() != label_span.strip():
                return "formatting"
            return "other"
        if nt == nl:
            u_norm = {ut.lower(), ul.lower()}
            for group in _SYMBOL_MASS:
                if u_norm <= group:
                    return "symbol"
            for group, cat in _SPELL_MASS:
                if u_norm <= group:
                    return cat
            if ut != ul:
                return "spelling"
        if nt != nl:
            return "scale_conversion"
    if format_decimal(nt) == format_decimal(nl) and ut == ul:
        if str(nt) != str(nl) or textbook_span.strip() != label_span.strip():
            return "formatting"
    tb_compact = re.sub(r"\s+", "", textbook_span.lower())
    lb_compact = re.sub(r"\s+", "", label_span.lower())
    if tb_compact != lb_compact:
        if nt == nl:
            return "formatting" if ut == ul else "spelling"
        return "scale_conversion"
    return "other"


def pair_key(drug: str, tb_sent: str, lb_sent: str, tb_span: str, lb_span: str) -> tuple:
    return (
        drug.strip().lower(),
        tb_sent.strip(),
        lb_sent.strip(),
        tb_span.strip(),
        lb_span.strip(),
    )


def pair_key_from_row(row: dict) -> tuple:
    return pair_key(
        row["drug"],
        row.get("textbook_sentence") or "",
        row.get("label_sentence") or "",
        row.get("textbook_span") or row.get("textbook_dose") or "",
        row.get("label_span") or row.get("label_dose") or "",
    )
