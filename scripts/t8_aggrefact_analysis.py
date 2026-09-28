#!/usr/bin/env python3
"""T8: LLM-AggreFact quantity blind-spot stats (medical DOSE_RE + general quantities)."""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from general_quantity import (  # noqa: E402
    claim_has_any_number,
    claim_has_number_unit,
    format_quantity_mismatch,
)
from text_utils import DOSE_RE, parse_decimal  # noqa: E402

CACHE = ROOT / "data/t8/aggrefact"
OUT_JSON = ROOT / "notes/t8_aggrefact_unit_audit.json"
OUT_MD = ROOT / "notes/t8_aggrefact_unit_audit.md"

_MED_HINT = re.compile(
    r"\b(dose|mg|mcg|patient|drug|medication|prescri|intravenous|oral|tablet|insulin)\b",
    re.I,
)


def dose_tokens(text: str) -> list[tuple[str, str, str]]:
    return [(m.group(1), m.group(2), m.group(0).strip()) for m in DOSE_RE.finditer(text or "")]


def has_numeric_dose(text: str) -> bool:
    return bool(dose_tokens(text))


def dose_unit_mismatch(claim: str, doc: str) -> bool:
    ct = dose_tokens(claim)
    dt = dose_tokens(doc)
    if not ct or not dt:
        return False
    for na, ua, _ in ct:
        for nb, ub, _ in dt:
            if na != nb:
                try:
                    if parse_decimal(na) != parse_decimal(nb):
                        continue
                except ValueError:
                    continue
            if ua != ub:
                return True
    return False


def load_split(split: str = "dev") -> list[dict]:
    local = CACHE / f"{split}.jsonl"
    if not local.is_file():
        raise SystemExit(f"missing {local} — run scripts/t8_download_aggrefact.py")
    return [json.loads(line) for line in local.open() if line.strip()]


def audit_rows(rows: list[dict]) -> dict:
    return {
        "n": len(rows),
        "claim_with_any_number": sum(1 for r in rows if claim_has_any_number(r.get("claim", ""))),
        "claim_with_number_unit": sum(1 for r in rows if claim_has_number_unit(r.get("claim", ""))),
        "claim_doc_format_mismatch": sum(
            1 for r in rows if format_quantity_mismatch(r.get("claim", ""), r.get("doc", ""))
        ),
        "claim_with_numeric_dose": sum(1 for r in rows if has_numeric_dose(r.get("claim", ""))),
        "doc_with_numeric_dose": sum(1 for r in rows if has_numeric_dose(r.get("doc", ""))),
        "same_number_diff_dose_unit_pairs": sum(
            1 for r in rows if dose_unit_mismatch(r.get("claim", ""), r.get("doc", ""))
        ),
        "non_med_claim_with_dose": sum(
            1
            for r in rows
            if has_numeric_dose(r.get("claim", ""))
            and not _MED_HINT.search(r.get("claim", "") or "")
        ),
    }


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--splits", default="dev,test")
    args = p.parse_args()
    splits = [s.strip() for s in args.splits.split(",") if s.strip()]

    all_rows: list[dict] = []
    for sp in splits:
        all_rows.extend(load_split(sp))

    by_subset: dict[str, list[dict]] = defaultdict(list)
    for row in all_rows:
        by_subset[row.get("dataset") or "unknown"].append(row)

    summary = {
        "splits": splits,
        "n_total": len(all_rows),
        "by_subdataset": {name: audit_rows(subset) for name, subset in sorted(by_subset.items())},
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(summary, indent=2) + "\n")

    hdr = (
        "| sub-dataset | n | any # | #+unit | format mismatch | med dose claim | med # diff unit | non-med dose |"
    )
    sep = "|---|---:|---:|---:|---:|---:|---:|---:|"
    lines = [
        f"# T8 LLM-AggreFact quantity audit ({','.join(splits)})",
        "",
        f"Total rows: **{len(all_rows)}**",
        "",
        hdr,
        sep,
    ]
    for name, cell in summary["by_subdataset"].items():
        lines.append(
            f"| {name} | {cell['n']} | {cell['claim_with_any_number']} | "
            f"{cell['claim_with_number_unit']} | {cell['claim_doc_format_mismatch']} | "
            f"{cell['claim_with_numeric_dose']} | {cell['same_number_diff_dose_unit_pairs']} | "
            f"{cell['non_med_claim_with_dose']} |"
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
