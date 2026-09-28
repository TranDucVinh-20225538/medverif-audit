#!/usr/bin/env python3
"""T1: cost vs validity table + invariance/sensitivity with/without M1 (+ M2 hybrid)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from analyze import load_joined_from_records, read_jsonl, sensitivity_invariance  # noqa: E402
from quantity_consistency import m2_verdict  # noqa: E402
from verifiers.preprocess import verifier_inputs  # noqa: E402
from verifier_types import verifier_type  # noqa: E402

INST = ROOT / "data" / "v3" / "instances_cpu_early.jsonl"
RAW_BASE = ROOT / "results" / "raw"
RAW_M1 = ROOT / "results" / "raw_m1"
SOURCES = ROOT / "notes" / "cost_validity_sources.json"
OUT = ROOT / "results" / "tables" / "cost_vs_validity.md"

VERIFIERS_MAIN = (
    ("v1_medscore", "V1 (Mistral OR)"),
    ("v4_ragas_nli", "V4 (Llama OR)"),
    ("v2a_minicheck", "V2a (MiniCheck, node30)"),
    ("v3_alignscore", "V3 (AlignScore, node30)"),
)


def apply_m2_hybrid(rows: list[dict]) -> list[dict]:
    out = []
    for row in rows:
        r = dict(row)
        if r["verdict"] not in ("PASS", "FAIL"):
            out.append(r)
            continue
        claim, evidence = verifier_inputs({**r, "claim": r.get("claim"), "evidence": r.get("evidence")})
        r["verdict"] = m2_verdict(r["verdict"], claim, evidence)
        out.append(r)
    return out


def dose_macro(rows: list[dict], verifier: str) -> tuple[float | None, float | None]:
    pts = [p for p in sensitivity_invariance(rows) if p["verifier"] == verifier and p["type"] == "DOSE"]
    if not pts:
        return None, None
    p = pts[0]
    return p.get("invariance"), p.get("sensitivity_e1_evid")


def cost_per_1k(verifier: str, raw_dir: Path) -> float | None:
    path = raw_dir / f"{verifier}.jsonl"
    if not path.is_file():
        return None
    n = 0
    cost = 0.0
    for line in path.open():
        if not line.strip():
            continue
        row = json.loads(line)
        n += 1
        cost += float(row.get("api_cost_usd") or 0)
    if n == 0:
        return None
    return (cost / n) * 1000.0


def join_verifier(instances: list[dict], verifier: str, raw_dir: Path) -> list[dict]:
    return load_joined_from_records(instances, raw_dir)


def main() -> None:
    instances = [r for r in read_jsonl(INST) if r.get("valid", True)]
    sources = json.loads(SOURCES.read_text()) if SOURCES.is_file() else {}
    vsrc = sources.get("verifiers") or {}

    lines = [
        "# Cost vs validity (T1)",
        "",
        f"Instances: `{INST.relative_to(ROOT)}` (n={len(instances)}).",
        "",
        "**Metrics (DOSE, conditional on C0 PASS):** invariance = INV-claim PASS rate; "
        "sensitivity = E1-evid FAIL rate (higher = better). PARSE_FAIL excluded.",
        "",
        "| Verifier | Verifier type | $/1k claims | Paper BAcc (AggreFact) | Source | "
        "Inv (raw) | Sens (raw) | Inv (M1 infer)* | Sens (M1 infer)* | Inv (M1+M2†) | Sens (M1+M2†) |",
        "| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]

    for vkey, label in VERIFIERS_MAIN:
        raw_rows = join_verifier(instances, vkey, RAW_BASE)
        m1_rows = join_verifier(instances, vkey, RAW_M1) if RAW_M1.is_dir() else []
        m2_rows = apply_m2_hybrid(raw_rows)

        inv0, sen0 = dose_macro(raw_rows, vkey)
        inv1, sen1 = dose_macro(m1_rows, vkey) if m1_rows else (None, None)
        inv2, sen2 = dose_macro(m2_rows, vkey)

        meta = vsrc.get(vkey) or {}
        bacc = meta.get("paper_bacc")
        bacc_s = f"{bacc:.2f}" if isinstance(bacc, (int, float)) else "—"
        src = meta.get("source") or "—"
        vtype = meta.get("verifier_type") or verifier_type(vkey)
        c1k = cost_per_1k(vkey, RAW_BASE)
        c1k_s = f"${c1k:.2f}" if c1k is not None else "—"

        def f(x: float | None) -> str:
            return f"{x:.3f}" if x is not None else "—"

        lines.append(
            f"| {label} | {vtype} | {c1k_s} | {bacc_s} | {src} | {f(inv0)} | {f(sen0)} | {f(inv1)} | {f(sen1)} | {f(inv2)} | {f(sen2)} |"
        )

    lines += [
        "",
        "\\* **M1 infer:** scores from `results/raw_m1/` with `MEDVERIF_M1=1` at inference (job `t1_m1_rescore`). "
        "Em dash until re-score completes.",
        "",
        "† **M1+M2 hybrid:** post-hoc M2 quantity veto on M1-normalized claim/evidence (no extra LLM calls).",
        "",
        "Paper BAcc notes:",
    ]
    for vkey, _ in VERIFIERS_MAIN:
        meta = vsrc.get(vkey) or {}
        if meta.get("paper_bacc_note"):
            lines.append(f"- **{vkey}:** {meta['paper_bacc_note']}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
