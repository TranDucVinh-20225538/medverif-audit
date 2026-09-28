#!/usr/bin/env python3
"""T8b false-alarm (FAIL) rates with bootstrap CIs; T8 INV/E1 split; BAcc reference."""

from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INST_T8B = ROOT / "data/t8/instances_aggrefact_t8b.jsonl"
INST_T8 = ROOT / "data/t8/instances_aggrefact_inv.jsonl"
RAW = ROOT / "results/raw/t8"
OUT_JSON = ROOT / "notes/t8b_false_alarm_report.json"
OUT_MD = ROOT / "notes/t8b_false_alarm_report.md"
N_BOOT = 2000
SEED = 2026


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open() if line.strip()]


def verifier_list() -> list[str]:
    checkers = json.loads((ROOT / "notes/t6a_eco_checkers.json").read_text()).get("checkers", [])
    return ["v1b_medscore", "v2a_minicheck", "v3_alignscore"] + [c["id"] for c in checkers]


def load_scores(v: str, *, t8b_only: bool = False) -> dict[str, str]:
    names = [f"{v}_t8b.jsonl"] if t8b_only else [f"{v}_t8b.jsonl", f"{v}.jsonl"]
    out: dict[str, str] = {}
    for name in names:
        path = RAW / name
        if not path.is_file():
            continue
        for row in read_jsonl(path):
            iid = row.get("instance_id")
            if iid and iid not in out:
                out[iid] = row.get("verdict")
    return out


def bootstrap_ci(values: list[int], n_boot: int = N_BOOT, seed: int = SEED) -> tuple[float, float, float]:
    if not values:
        return float("nan"), float("nan"), float("nan")
    n = len(values)
    mean = sum(values) / n
    rng = random.Random(seed)
    boots = []
    for _ in range(n_boot):
        s = sum(values[rng.randrange(n)] for _ in range(n)) / n
        boots.append(s)
    boots.sort()
    lo = boots[int(0.025 * n_boot)]
    hi = boots[int(0.975 * n_boot)]
    return mean, lo, hi


def bacc_supported(scored_verdicts: list[str]) -> float | None:
    """All instances expected PASS (supported): balanced acc = pass rate."""
    if not scored_verdicts:
        return None
    tp = sum(1 for v in scored_verdicts if v == "PASS")
    return tp / len(scored_verdicts)


def main() -> None:
    verifiers = verifier_list()
    t8b_rows = read_jsonl(INST_T8B) if INST_T8B.is_file() else []
    t8_rows = read_jsonl(INST_T8) if INST_T8.is_file() else []

    report: dict = {
        "t8b": {"verifiers": {}, "groups": ["format_mismatch", "qty_match"]},
        "t8_unit_sample": {"verifiers": {}},
    }

    by_group: dict[str, list[str]] = {"format_mismatch": [], "qty_match": []}
    for row in t8b_rows:
        g = row.get("t8b_group")
        if g in by_group:
            by_group[g].append(row["instance_id"])

    for v in verifiers:
        sc_t8b = load_scores(v, t8b_only=True)
        sc_t8 = load_scores(v, t8b_only=False)
        t8b_block: dict = {"false_alarm_fail_rate": {}, "bacc_supported_sample": None}
        all_scored: list[str] = []
        for group in ("format_mismatch", "qty_match"):
            ids = by_group[group]
            verdicts = [sc_t8b[i] for i in ids if sc_t8b.get(i)]
            fails = [1 if x == "FAIL" else 0 for x in verdicts]
            m, lo, hi = bootstrap_ci(fails)
            t8b_block["false_alarm_fail_rate"][group] = {
                "n_scored": len(verdicts),
                "fail_rate": m if verdicts else None,
                "ci95": [lo, hi] if verdicts else None,
            }
            all_scored.extend(verdicts)
        bacc = bacc_supported(all_scored)
        t8b_block["bacc_supported_sample"] = bacc
        qm = t8b_block["false_alarm_fail_rate"].get("qty_match", {})
        fr = qm.get("fail_rate")
        t8b_block["qty_match_pass_rate_c0_sanity"] = (1.0 - fr) if fr is not None else None
        report["t8b"]["verifiers"][v] = t8b_block

        inv_ids = [r["instance_id"] for r in t8_rows if r.get("condition") == "T8-aggrefact-inv"]
        e1_ids = [r["instance_id"] for r in t8_rows if r.get("condition") == "T8-aggrefact-e1-unit"]
        inv_v = [sc_t8[i] for i in inv_ids if sc_t8.get(i)]
        e1_v = [sc_t8[i] for i in e1_ids if sc_t8.get(i)]
        inv_pass = [1 if x == "PASS" else 0 for x in inv_v]
        e1_fail = [1 if x == "FAIL" else 0 for x in e1_v]
        ip, ilo, ihi = bootstrap_ci(inv_pass)
        ef, elo, ehi = bootstrap_ci(e1_fail)
        report["t8_unit_sample"]["verifiers"][v] = {
            "inv_pass_rate": {"n": len(inv_v), "rate": ip if inv_v else None, "ci95": [ilo, ihi] if inv_v else None},
            "e1_unit_fail_rate": {"n": len(e1_v), "rate": ef if e1_v else None, "ci95": [elo, ehi] if e1_v else None},
        }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# T8b supported-pair false-alarm report",
        "",
        "Expected verdict: **PASS** (original label = supported). False alarm = verifier **FAIL**.",
        "",
        "## T8b per group (FAIL rate = false alarm)",
        "",
        "| verifier | group | n | FAIL rate | 95% CI |",
        "|---|---|---:|---:|---|",
    ]
    for v, block in report["t8b"]["verifiers"].items():
        for g, cell in block["false_alarm_fail_rate"].items():
            ci = cell.get("ci95")
            ci_s = f"[{ci[0]:.3f}, {ci[1]:.3f}]" if ci else "—"
            rate = cell.get("fail_rate")
            rate_s = f"{rate:.3f}" if rate is not None else "—"
            lines.append(f"| {v} | {g} | {cell['n_scored']} | {rate_s} | {ci_s} |")
    lines += [
        "",
        "## BAcc reference (supported sample = groups i+ii, expected PASS)",
        "",
        "| verifier | BAcc |",
        "|---|---:|",
    ]
    for v, block in report["t8b"]["verifiers"].items():
        b = block.get("bacc_supported_sample")
        lines.append(f"| {v} | {b:.3f} |" if b is not None else f"| {v} | — |")
    lines += ["", "## T8 unit sample split", "", "| verifier | INV pass rate | E1-unit fail rate |", "|---|---:|---:|"]
    for v, block in report["t8_unit_sample"]["verifiers"].items():
        ip = block["inv_pass_rate"]
        ef = block["e1_unit_fail_rate"]
        lines.append(
            f"| {v} | {ip['rate']:.3f} (n={ip['n']}) | {ef['rate']:.3f} (n={ef['n']}) |"
            if ip.get("rate") is not None and ef.get("rate") is not None
            else f"| {v} | — | — |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(json.dumps({"wrote": str(OUT_JSON)}, indent=2))


if __name__ == "__main__":
    main()
