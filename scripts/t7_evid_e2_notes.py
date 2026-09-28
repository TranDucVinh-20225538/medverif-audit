#!/usr/bin/env python3
"""E1-unit-evid V1b examples + E2 PASS rates (conditional on C0), all verifiers."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from analyze import _c0_pass_bases, _parsed, read_jsonl  # noqa: E402

T7 = ROOT / "data/t7/instances_e1_unit.jsonl"
MAIN = ROOT / "data/v3/instances_main.jsonl"
EXPAND = ROOT / "data/expand/instances_cpu_early.jsonl"
OUT = ROOT / "notes/t7_evid_llm_examples.md"
T6A = ROOT / "notes/t6a_eco_checkers.json"

SCORE_DIRS = [
    ROOT / "results/raw",
    ROOT / "results/raw/t6b/full",
    ROOT / "results/raw/t7",
    ROOT / "results/raw/t3",
]


def score_paths() -> dict[str, Path]:
    out: dict[str, Path] = {}
    for d in SCORE_DIRS:
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.jsonl")):
            out.setdefault(p.stem, p)
    if T6A.is_file():
        for c in json.loads(T6A.read_text()).get("checkers", []):
            cid, fname = c["id"], c["jsonl"]
            for d in SCORE_DIRS:
                cand = d / fname
                if cand.is_file():
                    out[cid] = cand
                    break
    bespoke = ROOT / "results/raw/t7/t6_bespoke_minicheck.jsonl"
    if bespoke.is_file():
        out["v2b_bespoke"] = bespoke
        out["t6_bespoke_minicheck"] = bespoke
    return out


def load_verdicts(path: Path) -> dict[str, dict]:
    m: dict[str, dict] = {}
    for row in read_jsonl(path):
        iid = row.get("instance_id")
        if iid:
            m[iid] = row
    return m


def inst_by_id() -> dict[str, dict]:
    rows = read_jsonl(MAIN) + read_jsonl(EXPAND)
    return {r["instance_id"]: r for r in rows if r.get("valid", True)}


def join_verifier(verifier: str, scores: dict[str, dict], instances: dict[str, dict]) -> list[dict]:
    joined = []
    for iid, rec in scores.items():
        inst = instances.get(iid)
        if not inst:
            continue
        row = dict(inst)
        row["verifier"] = verifier
        row["verdict"] = rec.get("verdict")
        row["raw_output"] = rec.get("raw_output")
        joined.append(row)
    return joined


def e2_pass_cond_c0(joined: list[dict]) -> tuple[float | None, int, int, int]:
    c0 = _c0_pass_bases(joined)
    e2 = [
        r
        for r in joined
        if r["condition"] == "E2" and r["base_id"] in c0 and _parsed(r)
    ]
    if not e2:
        return None, 0, 0, len(c0)
    n_pass = sum(r["verdict"] == "PASS" for r in e2)
    return n_pass / len(e2), n_pass, len(e2), len(c0)


def main() -> None:
    t7_rows = read_jsonl(T7)
    evid = [r for r in t7_rows if r.get("condition") == "E1-unit-evid"]
    paths = score_paths()
    v1b = load_verdicts(paths["v1b_medscore"])

    pass_rows = []
    for inst in evid:
        rec = v1b.get(inst["instance_id"])
        if rec and rec.get("verdict") == "PASS":
            pass_rows.append((inst, rec))
    pass_rows.sort(key=lambda x: x[0]["base_id"])

    lines = [
        "# T7 E1-unit-evid: V1b PASS examples (LLM plausibility vs faithfulness)",
        "",
        "Cohort: **E1-unit-evid** (wrong unit in **evidence** only; claim matches C0). "
        "Expected verifier verdict: **FAIL**. V1b (gpt-4o MedScore) **PASS** = accepts implausible unit in evidence.",
        "",
        f"- E1-unit-evid instances: **{len(evid)}**",
        f"- V1b PASS (false negative on unit error): **{len(pass_rows)}**",
        "",
        "## Ten V1b PASS examples",
        "",
    ]
    for i, (inst, rec) in enumerate(pass_rows[:10], 1):
        lines.extend(
            [
                f"### {i}. `{inst['instance_id']}` (base `{inst['base_id']}`, unit {inst.get('unit_pair', '?')})",
                "",
                f"- **claim_span (C0-aligned claim):** `{inst.get('claim_span', '')}`",
                f"- **evidence_span (implausible unit):** `{inst.get('evidence_span', '')}`",
                f"- **expected_verdict:** {inst.get('expected_verdict')}",
                f"- **V1b verdict:** {rec.get('verdict')}",
                "",
                "**Claim:**",
                "",
                f"> {inst.get('claim', '')}",
                "",
                "**Evidence:**",
                "",
                f"> {inst.get('evidence', '')}",
                "",
                "**raw_output:**",
                "",
                "```",
                (rec.get("raw_output") or "").strip(),
                "```",
                "",
            ]
        )

    instances = inst_by_id()
    e2_table = []
    t6a_ids = set()
    if T6A.is_file():
        t6a_ids = {c["id"] for c in json.loads(T6A.read_text()).get("checkers", [])}
    for verifier, path in sorted(paths.items()):
        if verifier.startswith("t6_") and verifier not in t6a_ids:
            continue
        if path.stem != verifier and verifier not in t6a_ids and verifier not in {
            "v2b_bespoke",
            "t6_bespoke_minicheck",
        }:
            if (ROOT / "results/raw/t7" / f"{verifier}.jsonl").is_file():
                continue
        scores = load_verdicts(path)
        joined = join_verifier(verifier, scores, instances)
        if not joined:
            continue
        rate, n_pass, n_e2, n_c0 = e2_pass_cond_c0(joined)
        e2_table.append((verifier, rate, n_pass, n_e2, n_c0))

    lines.extend(
        [
            "## E2 (faithful-but-wrong magnitude) PASS rate, conditional on C0 PASS",
            "",
            "E2 edits **both** claim and evidence with the same wrong dose (expected **PASS**). "
            "Rates below use **each verifier's own** C0 PASS bases (standard conditional metric).",
            "",
            "| verifier | E2 PASS rate | n_PASS/n_E2 | C0-pass bases |",
            "|---|---:|---:|---:|",
        ]
    )
    for verifier, rate, n_pass, n_e2, n_c0 in e2_table:
        rate_s = f"{rate:.3f}" if rate is not None else "—"
        lines.append(f"| {verifier} | {rate_s} | {n_pass}/{n_e2} | {n_c0} |")

    lines.extend(
        [
            "",
            "**Reading:** If LLM judges show **lower** E2 PASS than encoders while encoders PASS, "
            "that supports LLM judges reacting to **plausibility** rather than strict claim–evidence match.",
            "",
        ]
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT} ({len(pass_rows)} V1b PASS on evid)")


if __name__ == "__main__":
    main()
