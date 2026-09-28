#!/usr/bin/env python3
"""T6-D: invariance/sensitivity vs cost for V1–V5 + zoo (+ scale curves)."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from analyze import (  # noqa: E402
    _c0_pass_bases,
    _parsed,
    bootstrap_rate,
    load_joined_from_records,
    read_jsonl,
    sensitivity_invariance,
)
from text_utils import rule_natural_unit_conversion_label  # noqa: E402
from review_filters import effective_unit_natural_y, inv_mechanism  # noqa: E402
from verifier_types import verifier_type  # noqa: E402

SCOPE = ROOT / "data" / "v3" / "instances_t6_scope.jsonl"
SOURCES = ROOT / "notes" / "cost_validity_sources.json"
T6_MODELS = ROOT / "notes" / "t6_models.json"
OUT_TABLE = ROOT / "results" / "tables" / "t6d_cost_validity.md"
FIG_DIR = ROOT / "results" / "figures" / "t6d"

# score paths: (label, verdicts_dir, filename_stem)
SCORE_SPECS: list[tuple[str, Path, str]] = [
    ("v1_medscore", ROOT / "results/raw", "v1_medscore"),
    ("v4_ragas_nli", ROOT / "results/raw", "v4_ragas_nli"),
    ("v2a_minicheck", ROOT / "results/raw", "v2a_minicheck"),
    ("v3_alignscore", ROOT / "results/raw", "v3_alignscore"),
    ("v1b_medscore", ROOT / "results/raw/t2_full", "v1b_medscore"),
    ("v5_ragas_nli", ROOT / "results/raw/t2_full", "v5_ragas_nli"),
]

GPU_USD_PER_1K = {
    "v2a_minicheck": 0.0,
    "v3_alignscore": 0.0,
}

SCALE_FAMILIES = {
    "llama_nli": ["v6_ragas_llama31_8b", "v4_ragas_nli"],
    "openai_nli": ["v6_ragas_gpt4o_mini", "v5_ragas_nli"],
    "openai_medscore": ["v1c_medscore", "v1b_medscore"],
    "anthropic_nli": ["v6_ragas_haiku45", "v5_ragas_nli"],
}


def inv_span_before(row: dict) -> str:
    diff = row.get("diff") or {}
    claim = diff.get("claim") or {}
    return str(claim.get("span_before") or row.get("claim_span") or "")


def metric_slice(rows: list[dict], verifier: str, predicate) -> float | None:
    block = [r for r in rows if r["verifier"] == verifier and predicate(r)]
    groups = []
    by: dict[str, list[int]] = {}
    for row in block:
        if not _parsed(row):
            continue
        num, den = by.setdefault(row["base_id"], [0, 0])
        den += 1
        if row["verdict"] == "PASS":
            num += 1
        by[row["base_id"]] = [num, den]
    groups = [(n, d) for n, d in by.values()]
    stat = bootstrap_rate(groups)
    return stat["rate"]


def e1_sensitivity(rows: list[dict], verifier: str, mag: str) -> float | None:
    block = [r for r in rows if r["verifier"] == verifier and r["type"] == "DOSE"]
    cond = _c0_pass_bases(block)
    by: dict[str, list[int]] = {}
    for row in block:
        if row["base_id"] not in cond or row["condition"] != "E1-claim":
            continue
        if row.get("magnitude") != mag or not _parsed(row):
            continue
        num, den = by.setdefault(row["base_id"], [0, 0])
        den += 1
        if row["verdict"] == "FAIL":
            num += 1
        by[row["base_id"]] = [num, den]
    return bootstrap_rate([(n, d) for n, d in by.values()])["rate"]


def cost_per_1k(raw_dir: Path, stem: str) -> float:
    path = raw_dir / f"{stem}.jsonl"
    if not path.is_file():
        return float("nan")
    n = cost = 0.0
    for line in path.open():
        if line.strip():
            row = json.loads(line)
            n += 1
            cost += float(row.get("api_cost_usd") or 0)
    if n == 0:
        return float("nan")
    return (cost / n) * 1000.0


def load_zoo_specs() -> list[tuple[str, Path, str]]:
    specs = list(SCORE_SPECS)
    pilot = ROOT / "results/raw/t6b/pilot"
    full = ROOT / "results/raw/t6b/full"
    if T6_MODELS.is_file():
        for m in json.loads(T6_MODELS.read_text()).get("t6b_openrouter", []):
            slug = m["slug"]
            if (full / f"{slug}.jsonl").is_file():
                specs.append((slug, full, slug))
            elif (pilot / f"{slug}.jsonl").is_file():
                specs.append((slug, pilot, slug))
    return specs


def rows_from_scorefile(instances: list[dict], label: str, path: Path) -> list[dict]:
    inst_by = {i["instance_id"]: i for i in instances}
    out: list[dict] = []
    if not path.is_file():
        return out
    for rec in read_jsonl(path):
        inst = inst_by.get(rec["instance_id"])
        if not inst:
            continue
        row = dict(inst)
        row["verifier"] = label
        row["verdict"] = rec.get("verdict")
        row["score"] = rec.get("score")
        out.append(row)
    return out


def join_all(instances: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    joined_main = load_joined_from_records(instances, ROOT / "results/raw")
    for v in ("v1_medscore", "v2a_minicheck", "v3_alignscore", "v4_ragas_nli"):
        out[v] = [r for r in joined_main if r["verifier"] == v]
    for label, raw_dir, stem in load_zoo_specs():
        if label in out and out[label]:
            continue
        rows = rows_from_scorefile(instances, label, raw_dir / f"{stem}.jsonl")
        if rows:
            out[label] = rows
    for stem, label in (("v1b_medscore", "v1b_medscore"), ("v5_ragas_nli", "v5_ragas_nli")):
        rows = rows_from_scorefile(
            instances, label, ROOT / "results/raw/t2_full" / f"{stem}.jsonl"
        )
        if rows:
            out[label] = rows
        rows_p = rows_from_scorefile(
            instances, label, ROOT / "results/raw/t2_pilot" / f"{stem}.jsonl"
        )
        if rows_p and label not in out:
            out[label] = rows_p
    return out


def main() -> None:
    instances = read_jsonl(SCOPE)
    by_verifier = join_all(instances)
    sources = json.loads(SOURCES.read_text()) if SOURCES.is_file() else {}
    vsrc = sources.get("verifiers") or {}

    lines = ["# T6-D cost vs validity", "", f"Scope n={len(instances)} (`instances_t6_scope.jsonl`).", ""]
    lines.append(
        "| Verifier | Verifier type | $/1k | Paper BAcc | Inv DOSE | Sens E1 x2 | Sens E1 x10 | "
        "INV-unit all | INV-unit nat | POL INV tmpl |"
    )
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")

    scatter_x: list[float] = []
    scatter_y: list[float] = []
    scatter_s: list[float] = []
    scatter_l: list[str] = []

    for label, rows in sorted(by_verifier.items()):
        if not rows:
            continue
        inv_dose = next(
            (p["invariance"] for p in sensitivity_invariance(rows) if p["type"] == "DOSE"),
            None,
        )
        sens = next(
            (p["sensitivity_e1_evid"] for p in sensitivity_invariance(rows) if p["type"] == "DOSE"),
            None,
        )
        inv_all = metric_slice(
            rows,
            label,
            lambda r: r["condition"] == "INV-claim"
            and r["type"] == "DOSE"
            and r.get("magnitude") == "unit_conversion",
        )
        inv_nat = metric_slice(
            rows,
            label,
            lambda r: r["condition"] == "INV-claim"
            and r["type"] == "DOSE"
            and r.get("magnitude") == "unit_conversion"
            and effective_unit_natural_y(
                r["base_id"], bool(rule_natural_unit_conversion_label(inv_span_before(r)))
            ),
        )
        pol_inv = metric_slice(
            rows,
            label,
            lambda r: r["condition"] == "INV-claim"
            and r["type"] == "POLARITY"
            and inv_mechanism(r) == "template",
        )
        sx2 = e1_sensitivity(rows, label, "x2")
        sx10 = e1_sensitivity(rows, label, "x10")
        raw_dir = ROOT / "results/raw"
        c1k = cost_per_1k(raw_dir, label)
        if c1k != c1k:
            c1k = cost_per_1k(ROOT / "results/raw/t2_full", label)
        if c1k != c1k:
            c1k = cost_per_1k(ROOT / "results/raw/t6b/pilot", label)
        meta = vsrc.get(label) or {}
        bacc = meta.get("paper_bacc")
        bacc_s = f"{bacc:.2f}" if isinstance(bacc, (int, float)) else "—"

        def f(v: float | None) -> str:
            return f"{v:.3f}" if v is not None else "—"

        vtype = (vsrc.get(label) or {}).get("verifier_type") or verifier_type(label)
        lines.append(
            f"| {label} | {vtype} | {f(c1k) if c1k == c1k else '—'} | {bacc_s} | {f(inv_dose)} | {f(sx2)} | {f(sx10)} | "
            f"{f(inv_all)} | {f(inv_nat)} | {f(pol_inv)} |"
        )
        if inv_dose is not None and sens is not None and c1k == c1k:
            scatter_x.append(inv_dose)
            scatter_y.append(sens)
            scatter_s.append(max(c1k, 0.01))
            scatter_l.append(label)

    OUT_TABLE.parent.mkdir(parents=True, exist_ok=True)
    OUT_TABLE.write_text("\n".join(lines) + "\n")

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        plt = None
    if scatter_x and plt is not None:
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.scatter(scatter_x, scatter_y, s=[v * 80 for v in scatter_s], alpha=0.7)
        for x, y, lab in zip(scatter_x, scatter_y, scatter_l):
            ax.annotate(lab, (x, y), fontsize=6, alpha=0.8)
        ax.set_xlabel("invariance (DOSE INV, C0-pass)")
        ax.set_ylabel("sensitivity (E1-evid FAIL, C0-pass)")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_title("T6-D: invariance vs sensitivity (marker size ∝ $/1k)")
        fig.tight_layout()
        fig.savefig(FIG_DIR / "invariance_vs_sensitivity_cost.png", dpi=120)
        plt.close(fig)

    if plt is None:
        print("matplotlib missing; tables only", file=sys.stderr)
        print(OUT_TABLE)
        return

    # scale curves within families
    for fam, members in SCALE_FAMILIES.items():
        ys = []
        xs = list(range(len(members)))
        for m in members:
            rows = by_verifier.get(m, [])
            if not rows:
                ys.append(float("nan"))
                continue
            pt = next((p for p in sensitivity_invariance(rows) if p["type"] == "DOSE"), {})
            ys.append(pt.get("invariance") if pt else float("nan"))
        if all(y != y for y in ys):
            continue
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.plot(xs, ys, marker="o")
        ax.set_xticks(xs, members, rotation=25, ha="right")
        ax.set_ylabel("DOSE invariance")
        ax.set_ylim(0, 1)
        ax.set_title(f"T6-D scale curve: {fam}")
        fig.tight_layout()
        fig.savefig(FIG_DIR / f"scale_{fam}.png", dpi=120)
        plt.close(fig)

    print(OUT_TABLE)


if __name__ == "__main__":
    main()
