#!/usr/bin/env python3
"""Amendment 5 gate check: M1 (spec) vs independent M1-lib (quantulum3 + pint) on edited target spans.

Per pack: spans where both give the same canonical quantity / differ / M1-lib fails / M1 fails,
with examples; then the instance gate (all target spans agree) and the base cohort vs the
amendment-4 gate cache used by m1_strong_final.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from m1_lib_indep import UREG, parse_surface, same_quantity  # noqa: E402
from m1_strong_run import MAIN, T7, T17, load_rows  # noqa: E402
from quantity_norm import M1_DOSE_RE_SPEC, canonicalize_dose_span  # noqa: E402

OLD_CACHE = ROOT / "results/cache/m1_strong_gate.json"
OUT_JSON = ROOT / "notes/m1_gate_independent.json"
OUT_MD = ROOT / "notes/m1_gate_independent.md"
N_EXAMPLES = 5


def target_surfaces(row: dict) -> list[str]:
    out: list[str] = []
    diff = row.get("diff") or {}
    for side in ("claim", "evidence"):
        block = diff.get(side)
        if isinstance(block, dict):
            out += [str(block[k]) for k in ("span_before", "span_after") if block.get(k)]
    out += [str(row[k]) for k in ("claim_span", "evidence_span") if row.get(k)]
    seen: list[str] = []
    for s in out:
        s = s.replace("«", "").replace("»", "").strip()
        if s and s not in seen:
            seen.append(s)
    return seen


def m1_canonical(surface: str) -> str | None:
    m = M1_DOSE_RE_SPEC.search(surface)
    if not m:
        return None
    try:
        return canonicalize_dose_span(m.group(1), m.group(2))
    except Exception:  # noqa: BLE001
        return None


def classify(surface: str) -> tuple[str, dict]:
    m1 = m1_canonical(surface)
    lib = parse_surface(surface)
    info = {"surface": surface, "m1": m1, "lib": None if lib.quantity is None else f"{lib.quantity:~P}",
            "lib_reason": lib.reason, "micro_alias": lib.micro_alias}
    if m1 is None:
        return "m1_fail", info
    if lib.quantity is None:
        return "lib_fail", info
    try:
        m1_q = UREG(m1)
    except Exception as exc:  # noqa: BLE001
        info["m1_pint_error"] = str(exc)
        return "m1_fail", info
    return ("same" if same_quantity(m1_q, lib.quantity) else "differs"), info


def packs() -> dict[str, list[dict]]:
    t7 = load_rows(T7)
    t17 = load_rows(T17)
    main = load_rows(MAIN)
    return {
        "us_up_x1000": [r for r in t7 if r.get("magnitude") == "x1000"],
        "us_down_unit": [r for r in t17 if r.get("condition") == "E1-unit-down"],
        "ns_x10_claim": [r for r in main if r.get("condition") == "E1-claim" and r.get("magnitude") == "x10"],
        "ns_x10_evid": [r for r in main if r.get("condition") == "E1-evid" and r.get("magnitude") == "x10"],
        "ns_div10_claim": [r for r in t17 if r.get("condition") == "E1-down10" and "__claim__" in r["instance_id"]],
        "ns_div10_evid": [r for r in t17 if r.get("condition") == "E1-down10" and "__evid__" in r["instance_id"]],
    }


def main() -> None:
    old = json.loads(OLD_CACHE.read_text()) if OLD_CACHE.is_file() else {}
    report: dict = {"packs": {}}
    new_gate: dict[str, bool] = {}
    old_bases: set[str] = set()
    new_bases: set[str] = set()
    for name, rows in packs().items():
        counts = {"same": 0, "differs": 0, "lib_fail": 0, "m1_fail": 0}
        examples: dict[str, list] = {k: [] for k in counts}
        micro = 0
        inst_pass = 0
        for row in rows:
            ok = True
            spans = target_surfaces(row)
            for s in spans:
                cat, info = classify(s)
                counts[cat] += 1
                micro += int(info["micro_alias"])
                if cat != "same":
                    ok = False
                    if len(examples[cat]) < N_EXAMPLES:
                        examples[cat].append({"instance_id": row["instance_id"], **info})
            ok = ok and bool(spans)
            new_gate[row["instance_id"]] = ok
            inst_pass += int(ok)
            if ok:
                new_bases.add(row["base_id"])
            if old.get(row["instance_id"], False):
                old_bases.add(row["base_id"])
        report["packs"][name] = {
            "instances": len(rows),
            "inst_gate_pass_new": inst_pass,
            "inst_gate_pass_old": sum(bool(old.get(r["instance_id"])) for r in rows),
            "spans": sum(counts.values()),
            **counts,
            "spans_using_micro_alias": micro,
            "examples": {k: v for k, v in examples.items() if k != "same"},
            "instances_dropped": sorted(
                r["instance_id"] for r in rows if old.get(r["instance_id"]) and not new_gate[r["instance_id"]]
            ),
        }
    report["bases_old"] = len(old_bases)
    report["bases_new"] = len(new_bases)
    report["bases_dropped"] = sorted(old_bases - new_bases)
    report["bases_added"] = sorted(new_bases - old_bases)
    OUT_JSON.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    (ROOT / "results/cache/m1_strong_gate_indep.json").write_text(json.dumps(new_gate, indent=1) + "\n")

    lines = [
        "# M1-strong gate: M1 (spec) vs independent M1-lib (quantulum3 + pint)",
        "",
        "Script: `scripts/m1_gate_independent.py`; parser: `src/m1_lib_indep.py` (no repo imports).",
        "",
        "| Pack | instances | gate pass old → new | spans | same | differs | M1-lib fails | M1 fails |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, p in report["packs"].items():
        lines.append(
            f"| {name} | {p['instances']} | {p['inst_gate_pass_old']} → {p['inst_gate_pass_new']} | {p['spans']} | "
            f"{p['same']} | {p['differs']} | {p['lib_fail']} | {p['m1_fail']} |"
        )
    lines += ["", f"Bases in cohort: {report['bases_old']} → {report['bases_new']}; dropped: "
              f"{', '.join(report['bases_dropped']) or 'none'}", ""]
    for name, p in report["packs"].items():
        for cat, exs in p["examples"].items():
            if exs:
                lines.append(f"- **{name} / {cat}**: " + "; ".join(
                    f"`{e['surface']}` (M1 {e['m1']}, lib {e['lib'] or e['lib_reason']})" for e in exs))
    OUT_MD.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
