#!/usr/bin/env python3
"""CPU-only: unit naturalness CSV, INV breakdown (68 scored rows), prelim v2/v3 table."""

from __future__ import annotations

import csv
import json
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "analysis"))

from analyze import (  # noqa: E402
    N_BOOT,
    SEED,
    _c0_pass_bases,
    _parsed,
    _percentile,
    auroc,
    load_joined,
    read_jsonl,
)
from text_utils import natural_unit_conversion  # noqa: E402

V2_BASES = ROOT / "data" / "v2" / "bases_main.jsonl"
V2_INST = ROOT / "data" / "v2" / "instances_main.jsonl"
INSTANCES = ROOT / "data" / "v3" / "instances_cpu_early.jsonl"
VERDICTS = ROOT / "results" / "raw"
OUT_CSV = ROOT / "qc" / "unit_naturalness.csv"
OUT_BREAKDOWN = ROOT / "qc" / "inv_unit_breakdown.md"
OUT_PRELIM = ROOT / "results" / "tables" / "prelim_v2v3.md"

DEFAULT_T = 0.5
VERIFIERS = ("v2a_minicheck", "v3_alignscore")

CONDITION_ROWS = (
    ("C0", lambda r: r["condition"] == "C0"),
    ("E1-evid", lambda r: r["condition"] == "E1-evid"),
    ("E1-claim", lambda r: r["condition"] == "E1-claim"),
    ("E2", lambda r: r["condition"] == "E2"),
    (
        "INV-unit",
        lambda r: r["condition"] == "INV-claim"
        and r["type"] == "DOSE"
        and r["magnitude"] == "unit_conversion",
    ),
    (
        "INV-polarity",
        lambda r: r["condition"] == "INV-claim"
        and r["type"] == "POLARITY"
        and r["magnitude"] == "rephrase",
    ),
)

INV_SLICES = (
    (
        "DOSE / unit_conversion",
        lambda r: r["type"] == "DOSE" and r["magnitude"] == "unit_conversion",
    ),
    (
        "POLARITY / rephrase (template)",
        lambda r: r["type"] == "POLARITY" and r["magnitude"] == "rephrase",
    ),
)


def bootstrap_auroc_pairs(
    pairs: list[tuple[float, float]],
    seed: int = SEED,
) -> dict:
    if not pairs:
        return {"auroc": None, "lo": None, "hi": None, "n": 0}
    pos = [a for a, _ in pairs]
    neg = [b for _, b in pairs]
    point = auroc(pos, neg)
    if point is None or len(pairs) < 2:
        return {"auroc": point, "lo": None, "hi": None, "n": len(pairs)}
    rng = random.Random(seed)
    stats: list[float] = []
    m = len(pairs)
    for _ in range(N_BOOT):
        sample = [pairs[rng.randrange(m)] for _ in range(m)]
        v = auroc([a for a, _ in sample], [b for _, b in sample])
        if v is not None:
            stats.append(v)
    stats.sort()
    return {
        "auroc": point,
        "lo": _percentile(stats, 0.025) if stats else None,
        "hi": _percentile(stats, 0.975) if stats else None,
        "n": m,
    }


def bootstrap_auroc_scores(
    pos: list[float],
    neg: list[float],
    seed: int = SEED,
) -> dict:
    if not pos or not neg:
        return {"auroc": None, "lo": None, "hi": None, "n_pos": len(pos), "n_neg": len(neg)}
    point = auroc(pos, neg)
    if point is None:
        return {"auroc": None, "lo": None, "hi": None, "n_pos": len(pos), "n_neg": len(neg)}
    pairs = [(p, n) for p in pos for n in neg]
    if len(pairs) < 2:
        return {"auroc": point, "lo": None, "hi": None, "n_pos": len(pos), "n_neg": len(neg)}
    rng = random.Random(seed)
    stats: list[float] = []
    for _ in range(N_BOOT):
        sp = [pos[rng.randrange(len(pos))] for _ in range(len(pos))]
        sn = [neg[rng.randrange(len(neg))] for _ in range(len(neg))]
        v = auroc(sp, sn)
        if v is not None:
            stats.append(v)
    stats.sort()
    return {
        "auroc": point,
        "lo": _percentile(stats, 0.025) if stats else None,
        "hi": _percentile(stats, 0.975) if stats else None,
        "n_pos": len(pos),
        "n_neg": len(neg),
    }


def pass_at_threshold(score: float, t: float) -> bool:
    return score > t


def f1_at_threshold(rows: list[tuple[float, bool]], t: float) -> float:
    """Gold True = expected PASS (C0); False = expected FAIL (E1). Pred PASS if score > t."""
    tp = fp = fn = 0
    for score, gold_pass in rows:
        pred = pass_at_threshold(score, t)
        if gold_pass and pred:
            tp += 1
        elif not gold_pass and pred:
            fp += 1
        elif gold_pass and not pred:
            fn += 1
    if tp == 0:
        return 0.0
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    if prec + rec == 0:
        return 0.0
    return 2 * prec * rec / (prec + rec)


def bootstrap_median(values: list[float], seed: int = SEED) -> dict:
    if not values:
        return {"median": None, "lo": None, "hi": None, "n": 0}
    point = statistics.median(values)
    if len(values) < 2:
        return {"median": point, "lo": None, "hi": None, "n": len(values)}
    rng = random.Random(seed)
    stats: list[float] = []
    m = len(values)
    for _ in range(N_BOOT):
        sample = [values[rng.randrange(m)] for _ in range(m)]
        stats.append(statistics.median(sample))
    stats.sort()
    return {
        "median": point,
        "lo": _percentile(stats, 0.025),
        "hi": _percentile(stats, 0.975),
        "n": m,
    }


def dose_paired_drops(block: list[dict]) -> dict[str, list[float]]:
    """Per-base score drop from C0 (C0 − condition), C0-conditional DOSE bases."""
    cond = _c0_pass_bases(block)
    by: dict[str, dict[str, float]] = {}
    for row in block:
        if row["type"] != "DOSE" or row["base_id"] not in cond or not _parsed(row):
            continue
        score = row.get("score")
        if not isinstance(score, (int, float)):
            continue
        slot = by.setdefault(row["base_id"], {})
        if row["condition"] == "C0":
            slot["c0"] = float(score)
        elif row["condition"] == "INV-claim" and row["magnitude"] == "unit_conversion":
            slot["inv"] = float(score)
        elif row["condition"] == "E1-claim" and row["magnitude"] == "x2":
            slot["e1_x2"] = float(score)
        elif row["condition"] == "E1-claim" and row["magnitude"] == "x10":
            slot["e1_x10"] = float(score)
    out: dict[str, list[float]] = {"inv": [], "e1_x2": [], "e1_x10": []}
    for slot in by.values():
        if "c0" not in slot:
            continue
        c0 = slot["c0"]
        for key, out_key in (("inv", "inv"), ("e1_x2", "e1_x2"), ("e1_x10", "e1_x10")):
            if key in slot:
                out[out_key].append(c0 - slot[key])
    return out


def max_min_inv_e1_sensitivity(block: list[dict]) -> dict:
    """max_τ min(INV-unit pass, E1 fail rate) on DOSE, C0-conditional, τ ∈ [0,1] step 0.01."""
    cond = _c0_pass_bases(block)
    inv_scores = [
        float(r["score"])
        for r in block
        if r["type"] == "DOSE"
        and r["base_id"] in cond
        and r["condition"] == "INV-claim"
        and r["magnitude"] == "unit_conversion"
        and _parsed(r)
        and isinstance(r.get("score"), (int, float))
    ]
    e1_scores = [
        float(r["score"])
        for r in block
        if r["type"] == "DOSE"
        and r["base_id"] in cond
        and r["condition"] in ("E1-evid", "E1-claim")
        and _parsed(r)
        and isinstance(r.get("score"), (int, float))
    ]
    if not inv_scores or not e1_scores:
        return {"tau": None, "objective": None, "inv_pass": None, "e1_fail": None}
    best = {"tau": 0.0, "objective": -1.0, "inv_pass": 0.0, "e1_fail": 0.0}
    for step in range(101):
        tau = step / 100
        inv_pass = sum(s > tau for s in inv_scores) / len(inv_scores)
        e1_fail = sum(s <= tau for s in e1_scores) / len(e1_scores)
        obj = min(inv_pass, e1_fail)
        if obj > best["objective"] or (
            obj == best["objective"] and abs(tau - DEFAULT_T) < abs(best["tau"] - DEFAULT_T)
        ):
            best = {
                "tau": tau,
                "objective": obj,
                "inv_pass": inv_pass,
                "e1_fail": e1_fail,
            }
    return best


def best_f1_threshold(rows: list[tuple[float, bool]]) -> tuple[float, float]:
    if not rows:
        return DEFAULT_T, 0.0
    scores = sorted({s for s, _ in rows})
    grid = scores + [max(0.0, scores[0] - 1e-6)] if scores else []
    for step in range(101):
        grid.append(step / 100)
    best_t = DEFAULT_T
    best_f1 = -1.0
    seen = set()
    for t in grid:
        key = round(t, 6)
        if key in seen:
            continue
        seen.add(key)
        f1 = f1_at_threshold(rows, t)
        if f1 > best_f1 or (f1 == best_f1 and abs(t - DEFAULT_T) < abs(best_t - DEFAULT_T)):
            best_f1 = f1
            best_t = t
    return best_t, best_f1


def unit_naturalness_rows() -> list[dict]:
    bases = {r["id"]: r for r in read_jsonl(V2_BASES) if r.get("type") == "DOSE"}
    unit_bases = sorted(
        {
            r["base_id"]
            for r in read_jsonl(V2_INST)
            if r.get("magnitude") == "unit_conversion"
        }
    )
    rows = []
    for base_id in unit_bases:
        base = bases[base_id]
        span = base.get("target_span_claim") or ""
        converted = natural_unit_conversion(span) or ""
        rows.append(
            {
                "base_id": base_id,
                "dose_kind": base.get("dose_kind") or "",
                "claim_span": span,
                "converted_span": converted,
                "natural": "",
            }
        )
    return rows


def write_unit_naturalness(rows: list[dict]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = ["base_id", "dose_kind", "claim_span", "converted_span", "natural"]
    with OUT_CSV.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def inv_pass_table(joined: list[dict], verifier: str, c0_only: bool) -> list[tuple[str, int, int]]:
    block = [r for r in joined if r["verifier"] == verifier]
    cond = _c0_pass_bases(block) if c0_only else None
    out = []
    for label, pred in INV_SLICES:
        parsed = [
            r
            for r in block
            if pred(r)
            and _parsed(r)
            and (cond is None or r["base_id"] in cond)
        ]
        n_pass = sum(r["verdict"] == "PASS" for r in parsed)
        out.append((label, n_pass, len(parsed)))
    return out


def write_inv_breakdown(joined: list[dict]) -> None:
    early = read_jsonl(INSTANCES)
    inv_early = [r for r in early if r.get("condition") == "INV-claim" and r.get("valid", True)]
    n_unit = sum(1 for r in inv_early if r["type"] == "DOSE" and r["magnitude"] == "unit_conversion")
    n_pol = sum(1 for r in inv_early if r["type"] == "POLARITY" and r["magnitude"] == "rephrase")
    lines = [
        "# INV-claim rows in cpu_early",
        "",
        f"Matrix: `{INSTANCES.relative_to(ROOT)}` — **{len(inv_early)}** valid INV-claim rows: "
        f"**{n_unit}** DOSE `unit_conversion`, **{n_pol}** POLARITY template `rephrase`.",
        "",
        "V2/V3 node30 scores (first tranche, n=1216) cover **DOSE unit_conversion only** "
        "(8/68 and 19/68 PASS @ 0.5). POLARITY `rephrase` rows are in "
        "`data/v3/instances_score_pending_node30.jsonl` (awaiting node30).",
        "",
        "Pass counts below use logged `verdict` (score > 0.5; `notes/environment_node30.md`).",
        "",
        "## Pass rate by INV kind (scored rows only)",
        "",
        "| Verifier | Slice | All scored | Conditional on C0 PASS |",
        "| --- | --- | --- | --- |",
    ]
    for verifier in VERIFIERS:
        all_rows = inv_pass_table(joined, verifier, c0_only=False)
        cond_rows = inv_pass_table(joined, verifier, c0_only=True)
        for (label, np_a, den_a), (_, np_c, den_c) in zip(all_rows, cond_rows):
            all_s = f"{np_a}/{den_a}" if den_a else "—"
            cond_s = f"{np_c}/{den_c}" if den_c else "—"
            lines.append(f"| {verifier} | {label} | {all_s} | {cond_s} |")
    OUT_BREAKDOWN.write_text("\n".join(lines) + "\n")


def filtered_block(joined: list[dict], verifier: str, c0_cond: bool) -> list[dict]:
    block = [r for r in joined if r["verifier"] == verifier]
    if not c0_cond:
        return block
    cond = _c0_pass_bases(block)
    return [r for r in block if r["base_id"] in cond]


def pass_rate_default(block: list[dict], pred) -> tuple[int, int]:
    parsed = [r for r in block if pred(r) and _parsed(r)]
    if not parsed:
        return 0, 0
    return sum(r["verdict"] == "PASS" for r in parsed), len(parsed)


def median_score(block: list[dict], pred) -> float | None:
    scores = [
        float(r["score"])
        for r in block
        if pred(r) and _parsed(r) and isinstance(r.get("score"), (int, float))
    ]
    if not scores:
        return None
    return statistics.median(scores)


def c0_e1_calibration_rows(block: list[dict]) -> list[tuple[float, bool]]:
    out = []
    for row in block:
        if not _parsed(row) or not isinstance(row.get("score"), (int, float)):
            continue
        if row["condition"] == "C0":
            out.append((float(row["score"]), True))
        elif row["condition"] in ("E1-evid", "E1-claim"):
            out.append((float(row["score"]), False))
    return out


def write_prelim(joined: list[dict]) -> None:
    OUT_PRELIM.parent.mkdir(parents=True, exist_ok=True)
    n_early = len(read_jsonl(INSTANCES))
    lines = [
        "# Preliminary V2 / V3 (cpu_early)",
        "",
        f"Instances: `{INSTANCES.relative_to(ROOT)}` ({n_early} rows).",
        f"Scores (first tranche): `{VERDICTS.relative_to(ROOT)}/v2a_minicheck.jsonl`, "
        "`v3_alignscore.jsonl` (1216 instance_ids; DOSE unit INV **68/68** scored).",
        "",
        "Default binarization: **score > 0.5 → PASS** (repo default for V2a and V3).",
        "Conditional slices: only bases whose **C0** verdict is PASS for that verifier.",
        "",
        "## Interpretation: ranking failure, not calibration",
        "",
        "AUROC(**C0** vs **INV-unit**) ≈ **0.97** — verifiers assign *much* lower scores to "
        "unit-equivalent claims than to the original C0 wording (they treat INV like a large "
        "claim change, not an invariant rewrite).",
        "",
        "Threshold tuning does **not** rescue invariance without sacrificing E1 sensitivity: "
        "the best-F1 τ on C0+E1 is **above** 0.5, and raising τ **lowers** INV-unit pass "
        "while E1 fail rate is already high at default. There is no τ that simultaneously "
        "passes most INV-unit rows and fails most E1 rows — a **ranking** problem, not a "
        "fixed-offset calibration problem.",
        "",
        "## INV-claim pass (68 scored DOSE unit rows; 78 POL rephrase pending node30)",
        "",
        "| Verifier | INV-unit (all) | INV-unit (C0-cond) | INV-polarity scored |",
        "| --- | --- | --- | --- |",
    ]
    for verifier in VERIFIERS:
        all_u = inv_pass_table(joined, verifier, False)[0]
        cond_u = inv_pass_table(joined, verifier, True)[0]
        pol = inv_pass_table(joined, verifier, False)[1]
        lines.append(
            f"| {verifier} | {all_u[1]}/{all_u[2]} | {cond_u[1]}/{cond_u[2]} | "
            f"{pol[1]}/{pol[2]} |"
        )

    lines += [
        "",
        "## Pass @ default threshold (0.5), conditional on C0 PASS",
        "",
        "| Verifier | Condition | PASS | Median score |",
        "| --- | --- | --- | --- |",
    ]
    for verifier in VERIFIERS:
        block = filtered_block(joined, verifier, c0_cond=True)
        for name, pred in CONDITION_ROWS:
            n_pass, den = pass_rate_default(block, pred)
            med = median_score(block, pred)
            med_s = f"{med:.4f}" if med is not None else "—"
            rate = f"{n_pass}/{den}" if den else "—"
            lines.append(f"| {verifier} | {name} | {rate} | {med_s} |")

    lines += [
        "",
        "## AUROC",
        "",
        "### C0 vs INV-unit (DOSE `unit_conversion`)",
        "",
        "Positive class: **C0** scores; negative: **INV-unit** scores (C0-conditional bases). "
        "Ideal invariance: AUROC ≈ **0.5** (no separation). Observed ≈ **0.97** → strong "
        " erroneous separation.",
        "",
        "| Verifier | AUROC | 95% CI | n(C0) | n(INV-unit) |",
        "| --- | --- | --- | --- | --- |",
    ]
    for verifier in VERIFIERS:
        block = filtered_block(joined, verifier, c0_cond=True)
        pos = [
            float(r["score"])
            for r in block
            if r["condition"] == "C0"
            and _parsed(r)
            and isinstance(r.get("score"), (int, float))
        ]
        neg = [
            float(r["score"])
            for r in block
            if r["condition"] == "INV-claim"
            and r["magnitude"] == "unit_conversion"
            and _parsed(r)
            and isinstance(r.get("score"), (int, float))
        ]
        stat = bootstrap_auroc_scores(pos, neg)
        ci = (
            f"[{stat['lo']:.4f}, {stat['hi']:.4f}]"
            if stat["lo"] is not None
            else "—"
        )
        val = f"{stat['auroc']:.4f}" if stat["auroc"] is not None else "NA"
        lines.append(
            f"| {verifier} | {val} | {ci} | {stat['n_pos']} | {stat['n_neg']} |"
        )

    lines += [
        "",
        "### INV-unit vs E1-claim (DOSE; detects dose change vs invariance)",
        "",
        "Positive: **INV-unit**; negative: **E1-claim** (mean of x2/x10 per base when both exist). "
        f"Bootstrap: {N_BOOT} resamples, seed {SEED}.",
        "",
        "| Verifier | AUROC | 95% CI | Paired bases |",
        "| --- | --- | --- | --- |",
    ]
    for verifier in VERIFIERS:
        block = [r for r in joined if r["verifier"] == verifier and r["type"] == "DOSE"]
        cond = _c0_pass_bases(block)
        by_base: dict[str, dict] = {}
        for row in block:
            if row["base_id"] not in cond or not _parsed(row):
                continue
            score = row.get("score")
            if not isinstance(score, (int, float)):
                continue
            if row["condition"] == "INV-claim" and row["magnitude"] == "unit_conversion":
                by_base.setdefault(row["base_id"], {})["inv"] = float(score)
            elif row["condition"] == "E1-claim":
                by_base.setdefault(row["base_id"], {}).setdefault("e1", []).append(float(score))
        pairs = [
            (v["inv"], sum(v["e1"]) / len(v["e1"]))
            for v in by_base.values()
            if "inv" in v and "e1" in v
        ]
        stat = bootstrap_auroc_pairs(pairs)
        ci = (
            f"[{stat['lo']:.4f}, {stat['hi']:.4f}]"
            if stat.get("lo") is not None
            else "—"
        )
        val = f"{stat['auroc']:.4f}" if stat.get("auroc") is not None else "NA"
        lines.append(f"| {verifier} | {val} | {ci} | {stat.get('n', 0)} |")

    lines += [
        "",
        "## Score drop from C0 (DOSE, paired by base, C0-conditional)",
        "",
        "Drop = score(C0) − score(condition). Bootstrap **median** drop across bases "
        f"({N_BOOT} resamples, seed {SEED}).",
        "",
        "| Verifier | INV-unit median drop [CI] | E1-claim x2 | E1-claim x10 |",
        "| --- | --- | --- | --- |",
    ]
    headline_bits = []
    for verifier in VERIFIERS:
        block = [r for r in joined if r["verifier"] == verifier and r["type"] == "DOSE"]
        drops = dose_paired_drops(block)
        parts = []
        for key in ("inv", "e1_x2", "e1_x10"):
            stat = bootstrap_median(drops[key])
            if stat["median"] is None:
                parts.append("—")
            elif stat["lo"] is None:
                parts.append(f"{stat['median']:.4f}")
            else:
                parts.append(f"{stat['median']:.4f} [{stat['lo']:.4f}, {stat['hi']:.4f}]")
        lines.append(f"| {verifier} | {parts[0]} | {parts[1]} | {parts[2]} |")
        if drops["inv"] and drops["e1_x2"]:
            headline_bits.append(
                f"{verifier}: median drop INV-unit {statistics.median(drops['inv']):.3f} "
                f"vs E1 x2 {statistics.median(drops['e1_x2']):.3f}"
            )
    if headline_bits:
        lines += [
            "",
            "**Headline (median score drop from C0):** rewriting a dose in equivalent units "
            "(e.g. 500 mg → 0.5 g) costs **comparable** verifier score to a **2× dose error** "
            f"— e.g. {headline_bits[0]}; V3 is closer but same pattern.",
            "",
        ]

    lines += [
        "## Threshold analysis",
        "",
        "### Best F1 on C0 + E1 (C0-conditional DOSE)",
        "",
        "Gold: C0 → PASS; E1-evid / E1-claim → FAIL. Higher τ **reduces** INV pass — no calibration fix.",
        "",
        "| Verifier | Best-F1 τ | F1 | INV-unit pass @ τ | INV-unit pass @ 0.5 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for verifier in VERIFIERS:
        block = filtered_block(joined, verifier, c0_cond=True)
        cal = c0_e1_calibration_rows(block)
        best_t, best_f1 = best_f1_threshold(cal)
        inv_rows = [
            r
            for r in block
            if r["type"] == "DOSE"
            and r["condition"] == "INV-claim"
            and r["magnitude"] == "unit_conversion"
            and _parsed(r)
            and isinstance(r.get("score"), (int, float))
        ]
        at_t = sum(pass_at_threshold(float(r["score"]), best_t) for r in inv_rows)
        at_default = sum(r["verdict"] == "PASS" for r in inv_rows)
        lines.append(
            f"| {verifier} | {best_t:.4f} | {best_f1:.4f} | {at_t}/{len(inv_rows)} | "
            f"{at_default}/{len(inv_rows)} |"
        )

    lines += [
        "",
        "### max_τ min(INV-unit pass, E1 fail) — no joint operating point",
        "",
        "τ ∈ [0, 1] step 0.01; DOSE; C0-conditional. E1 = E1-evid + E1-claim.",
        "",
        "| Verifier | Best τ | min(pass INV, fail E1) | INV pass @ τ | E1 fail @ τ |",
        "| --- | --- | --- | --- | --- |",
    ]
    for verifier in VERIFIERS:
        block = filtered_block(joined, verifier, c0_cond=True)
        mm = max_min_inv_e1_sensitivity(block)
        if mm["tau"] is None:
            lines.append(f"| {verifier} | — | — | — | — |")
        else:
            lines.append(
                f"| {verifier} | {mm['tau']:.2f} | {mm['objective']:.3f} | "
                f"{100 * mm['inv_pass']:.1f}% | {100 * mm['e1_fail']:.1f}% |"
            )
    lines += [
        "",
        "At the best joint τ, **min(INV pass, E1 fail)** stays far below what we would need "
        "for a usable verifier — consistent with a ranking failure, not a single wrong threshold.",
        "",
    ]

    OUT_PRELIM.write_text("\n".join(lines) + "\n")


def main() -> None:
    nat = unit_naturalness_rows()
    write_unit_naturalness(nat)
    joined = load_joined(INSTANCES, VERDICTS)
    if not joined:
        raise SystemExit("no joined rows — check v2a/v3 score files")
    write_inv_breakdown(joined)
    write_prelim(joined)
    print(
        json.dumps(
            {
                "unit_naturalness": str(OUT_CSV),
                "n_unit_naturalness": len(nat),
                "inv_breakdown": str(OUT_BREAKDOWN),
                "prelim": str(OUT_PRELIM),
                "n_joined": len(joined),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
