#!/usr/bin/env python3
"""Write notes/t14_pi_fix_report.md from pipeline artifacts."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notes/t14_pi_fix_report.md"


def main() -> None:
    nd = json.loads((ROOT / "notes/non_dose_pack_apply.json").read_text())
    manifest = json.loads((ROOT / "data/t14/manifest_t14.json").read_text())
    pending = json.loads((ROOT / "notes/t14_score_pending_manifest.json").read_text())
    inst = ROOT / "data/t14/instances_t14.jsonl"
    d066 = d063 = None
    for line in inst.open():
        row = json.loads(line)
        if row.get("base_id") == "D0066" and row.get("magnitude") == "unit_spell":
            d066 = row.get("claim")
        if row.get("base_id") == "D0063" and row.get("magnitude") == "unit_spell":
            d063 = row.get("claim")

    lines = [
        "# T14 PI fix report",
        "",
        "## Non-dose exclusion (D0077, D0164)",
        "",
        "| pack | valid removed | path |",
        "|---|---:|---|",
    ]
    for p in nd.get("packs", []):
        if p.get("missing"):
            lines.append(f"| {p.get('pack')} | — (missing) | `{p.get('path')}` |")
        else:
            lines.append(
                f"| {p.get('pack')} | **{p.get('removed_valid', 0)}** | `{p.get('path')}` |"
            )
    lines.extend(
        [
            "",
            f"T13: {nd.get('t13_note', '')}",
            "",
            "### Cohort (T13-derived)",
            f"- Before: **{nd.get('cohort_before', {}).get('main_dose_bases', '?')}** main DOSE bases",
            f"- After: **{nd.get('cohort_after', {}).get('main_dose_bases', '?')}** main DOSE bases",
            "",
            "### Headline deltas > 1 percentage point",
        ]
    )
    flags = nd.get("headline_flags_delta_gt_1pt") or []
    if not flags:
        lines.append("- None (all verifiers QI / US / T13 pair(1) moved ≤ 0.01).")
    else:
        lines.append("| model | metric | before | after | Δ |")
        lines.append("|---|---|---:|---:|---:|")
        for f in flags:
            lines.append(
                f"| {f.get('display')} | {f.get('metric')} | {f.get('before'):.3f} | "
                f"{f.get('after'):.3f} | {f.get('delta'):+.3f} |"
            )

    lines.extend(
        [
            "",
            "## T14 pack after regen",
            "",
            f"- Instances (valid): **{manifest.get('n_instances')}** "
            f"({manifest.get('by_magnitude')})",
            f"- symbol_micro: **{manifest.get('by_magnitude', {}).get('symbol_micro', 0)}**",
            f"- Appendix µ↔μ: **{manifest.get('appendix_symbol_micro_unicode_n', 0)}** (not scored)",
            f"- PI excluded: **{pending.get('pi_excluded', {}).get('excluded_pi_n', 0)}** rows",
            f"- Pending score: **{pending.get('pending')}**",
            "",
            "## D0066 / D0063 unit_spell claims (regenerated)",
            "",
            f"- **D0066:** {d066}",
            f"- **D0063:** {d063}",
            "",
        ]
    )
    OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
