#!/usr/bin/env python3
"""QC pack for POL template rephrase INV + merge inv_manual_review.csv."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from inv_manual_review_csv import build_manual_review_rows, write_manual_review_csv  # noqa: E402
from qc_v3 import sentence_rule_failure  # noqa: E402
from text_utils import rephrase_polarity_mapping  # noqa: E402

MAIN = ROOT / "data" / "v3" / "instances_main.jsonl"
AUDIT = ROOT / "data" / "v3" / "instances_audit.jsonl"
G_INV = ROOT / "data" / "v3" / "instances_g_inv_paraphrase.jsonl"
OUT_MD = ROOT / "qc" / "qc_pol_rephrase.md"
OUT_CSV = ROOT / "qc" / "inv_manual_review.csv"
C0_MAIN = ROOT / "data" / "v3" / "instances_cpu_main.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def pol_c0_by_base() -> dict[str, dict]:
    """All POL C0 rows (audit has invalid-domain C0 not present in main)."""
    out: dict[str, dict] = {}
    for path in (AUDIT, MAIN):
        for r in read_jsonl(path):
            if r.get("type") == "POLARITY" and r.get("condition") == "C0":
                out.setdefault(r["base_id"], r)
    return out


def mapping_for_rephrase_row(row: dict, c0_by_base: dict[str, dict]) -> tuple[str, str, str]:
    """Cue → rephrase from C0 polarity span (INV claim stores rephrased span in claim_span)."""
    c0 = c0_by_base.get(row["base_id"])
    cue = (c0.get("claim_span") if c0 else "") or ""
    if not cue:
        raise ValueError(f"no C0 cue for {row['base_id']}")
    return rephrase_polarity_mapping(cue)


def template_mapping_counts(rows: list[dict], c0_by_base: dict[str, dict]) -> Counter:
    counts: Counter = Counter()
    for row in rows:
        if row.get("type") != "POLARITY" or row.get("magnitude") != "rephrase":
            continue
        try:
            cue, rep, table = mapping_for_rephrase_row(row, c0_by_base)
            counts[(table, cue, rep)] += 1
        except ValueError as exc:
            counts[("UNMAPPED", str(exc), "")] += 1
    return counts


def merge_manual_review_csv(template_accepted: list[dict]) -> None:
    c0 = {
        r["base_id"]: r["claim"]
        for r in read_jsonl(C0_MAIN)
        if r.get("condition") == "C0"
    }
    accepted: list[dict] = []
    for row in read_jsonl(G_INV):
        if not row.get("valid"):
            continue
        bid = row["base_id"]
        accepted.append(
            {
                "base_id": bid,
                "type": row["type"],
                "mechanism": "llm",
                "mapping": "",
                "original": c0.get(bid, row.get("claim_c0") or ""),
                "rewrite": row["claim"],
            }
        )
    for row in template_accepted:
        accepted.append(
            {
                "base_id": row["base_id"],
                "type": "POLARITY",
                "mechanism": "template",
                "mapping": row.get("mapping") or "",
                "original": row["original"],
                "rewrite": row["rewrite"],
            }
        )
    write_manual_review_csv(OUT_CSV, accepted)


def main() -> None:
    audit_rep = [
        r
        for r in read_jsonl(AUDIT)
        if r.get("type") == "POLARITY"
        and r.get("magnitude") == "rephrase"
        and r.get("condition") == "INV-claim"
    ]
    valid = [r for r in audit_rep if r.get("valid")]
    invalid = [r for r in audit_rep if not r.get("valid")]
    c0_by_base = pol_c0_by_base()
    c0_claim = {bid: r["claim"] for bid, r in c0_by_base.items()}
    counts = template_mapping_counts(audit_rep, c0_by_base)
    lines = [
        "# POLARITY template rephrase INV (QC review)",
        "",
        f"Generated from `{MAIN.relative_to(ROOT)}` / `{AUDIT.relative_to(ROOT)}`.",
        "",
        "## Why not 78?",
        "",
        "- **78** POLARITY bases each get a `rephrase` row from `perturb_one` (equivalent "
        "template only: should↔ought, recommended for↔indicated for, G pairs).",
        "- Rows with no kept mapping → `pol_rephrase_nonequivalent`.",
        "- Valid rows also pass the same main gate as POL **C0** after QC **I** "
        "(`domain_kind==treatment`, main subset).",
        "",
        f"- Valid rephrase INV for scoring/analysis: **{len(valid)}**",
        f"- Invalid (audit only): **{len(invalid)}**",
        "",
        "## Template mappings (cue → rephrase) with counts",
        "",
        "Counts are over all generated rephrase rows (valid + invalid).",
        "",
        "| Table | Cue | Rephrase | n |",
        "| --- | --- | --- | --- |",
    ]
    for (table, cue, rep), n in sorted(counts.items(), key=lambda x: (-x[1], x[0][1])):
        lines.append(f"| `{table}` | `{cue}` | `{rep}` | {n} |")

    lines += [
        "",
        "## Valid rows for PI review",
        "",
        "| base_id | mapping | sentence_rule | original | rephrased |",
        "| --- | --- | --- | --- | --- |",
    ]
    template_accepted: list[dict] = []
    for row in sorted(valid, key=lambda r: r["base_id"]):
        cue, rep, table = mapping_for_rephrase_row(row, c0_by_base)
        mapping = f"{cue} → {rep} ({table})"
        sent = sentence_rule_failure(row.get("claim") or "") or "ok"
        orig = c0_claim.get(row["base_id"], row.get("claim_c0") or "")
        lines.append(
            f"| **{row['base_id']}** | {mapping} | {sent} | {orig} | {row['claim']} |"
        )
        template_accepted.append(
            {
                "base_id": row["base_id"],
                "original": orig,
                "rewrite": row["claim"],
                "mapping": f"{cue} → {rep}",
            }
        )

    if invalid:
        lines += ["", "## Invalid rephrase rows (audit)", ""]
        by_reason = Counter(r.get("invalid_reason") or "?" for r in invalid)
        for reason, n in sorted(by_reason.items(), key=lambda x: -x[1]):
            lines.append(f"- `{reason}`: {n}")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    merge_manual_review_csv(template_accepted)
    print(
        json.dumps(
            {
                "md": str(OUT_MD),
                "valid_rephrase": len(valid),
                "invalid_rephrase": len(invalid),
                "manual_review_csv": str(OUT_CSV),
                "template_rows_in_csv": len(template_accepted),
                "mapping_kinds": len(counts),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
