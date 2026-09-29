"""Quantity Validity Card metrics: QI, NS, US (+ C0 pass, bootstrap CIs)."""

from __future__ import annotations

import json
import random
from collections import defaultdict
from typing import Callable

SEED = 42
N_BOOT = 1000


def _rate(num: int, den: int) -> float | None:
    return None if den == 0 else num / den


def _bootstrap_rate(values: list[int], seed: int = SEED) -> tuple[float | None, float | None, float | None]:
    if not values:
        return None, None, None
    rng = random.Random(seed)
    n = len(values)
    pts = []
    for _ in range(N_BOOT):
        samp = [values[rng.randrange(n)] for _ in range(n)]
        pts.append(sum(samp) / n)
    pts.sort()
    lo = pts[int(0.025 * len(pts))]
    hi = pts[int(0.975 * len(pts)) - 1]
    return sum(values) / n, lo, hi


def evaluate(
    items: list[dict],
    verifier_fn: Callable[[str, str], str],
    *,
    c0_pass_bases: set[str] | None = None,
) -> dict:
    """
    verifier_fn(claim, evidence) -> PASS|FAIL|PARSE_FAIL
    Items need: id, claim, evidence, condition, base_id, expected_verdict (optional).
    """
    c0_pass_bases = c0_pass_bases or {
        r["base_id"] for r in items if r.get("condition") == "C0" and verifier_fn(r["claim"], r["evidence"]) == "PASS"
    }
    by_family: dict[str, list[int]] = defaultdict(list)
    inv_hits: list[int] = []
    e1_fail: list[int] = []
    for row in items:
        v = verifier_fn(row["claim"], row["evidence"])
        if v == "PARSE_FAIL":
            continue
        bid = row["base_id"]
        cond = row.get("condition") or ""
        fam = row.get("family") or cond
        if cond == "INV-claim" and bid in c0_pass_bases:
            inv_hits.append(int(v == "PASS"))
            by_family[fam].append(int(v == "PASS"))
        if cond.startswith("E1") and bid in c0_pass_bases:
            e1_fail.append(int(v == "FAIL"))
    qi, qi_lo, qi_hi = _bootstrap_rate(inv_hits)
    ns, ns_lo, ns_hi = _bootstrap_rate(e1_fail)
    us = qi
    md = [
        "# Quantity Validity Card",
        "",
        f"- **QI** (INV-unit pass | C0): {_pct(qi)} [{_pct(qi_lo)}, {_pct(qi_hi)}] n={len(inv_hits)}",
        f"- **NS** (E1 FAIL | C0): {_pct(ns)} [{_pct(ns_lo)}, {_pct(ns_hi)}] n={len(e1_fail)}",
        f"- **US**: {_pct(us)}",
        "",
    ]
    for fam, vals in sorted(by_family.items()):
        md.append(f"- {fam}: {_pct(_rate(sum(vals), len(vals)))} (n={len(vals)})")
    payload = {
        "QI": qi,
        "QI_ci": [qi_lo, qi_hi],
        "NS": ns,
        "NS_ci": [ns_lo, ns_hi],
        "US": us,
        "n_inv": len(inv_hits),
        "n_e1": len(e1_fail),
        "by_family": {k: _rate(sum(v), len(v)) for k, v in by_family.items()},
    }
    return {"json": payload, "markdown": "\n".join(md) + "\n"}


def _pct(x: float | None) -> str:
    return "NA" if x is None else f"{100 * x:.1f}%"
