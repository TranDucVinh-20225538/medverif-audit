"""Append the Stage 1–2 report section from JSON files already on disk."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path("/data2/hpcshared/medverif-audit")
REPORT = ROOT / "REPORT.md"
START = "<!-- stage12-final -->"
END = "<!-- /stage12-final -->"


def load(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def render() -> str:
    extract = load(ROOT / "data" / "extract_stats.json")
    llm = load(ROOT / "data" / "llm_stats.json")
    smoke = load(ROOT / "data" / "smoke_llm_stats.json")
    lines = [
        "## Stage 1–2 — base pairs and counterfactuals",
        "",
        "Numbers below are copied from `data/extract_stats.json`, `data/llm_stats.json`, and `data/smoke_llm_stats.json`.",
        "",
        f"- Chunks read: {extract.get('chunks')}. Sentences: {extract.get('sentences')}.",
        f"- Pool after rules: DOSE {extract.get('pool_DOSE')}, POLARITY {extract.get('pool_POLARITY')}.",
        f"- Sent to the generator: {extract.get('selected')} candidates "
        f"(cap {extract.get('attempt_per_type')} per type).",
        f"- Smoke bases kept: {smoke.get('bases_kept')} "
        f"(attempted {smoke.get('candidates_attempted')}).",
        f"- Full bases kept: {llm.get('bases_kept')} by type `{json.dumps(llm.get('bases_kept_by_type'))}`.",
        f"- Instances: {llm.get('instances')}.",
        f"- Claim generator: {llm.get('generator_model')} `{llm.get('generator_revision')}`.",
        f"- Support and INV checker: {llm.get('validator_model')} `{llm.get('validator_revision')}`.",
        f"- Drops: `{json.dumps(llm.get('drops'), sort_keys=True)}`.",
        "",
        "QC sample: `qc/qc_samples.md`. QC counts: `qc/qc_stats.md`.",
        "Stage 3 was not started.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blocker", default="")
    args = parser.parse_args()
    text = REPORT.read_text() if REPORT.exists() else ""
    if args.blocker:
        banner = f"BLOCKER: {args.blocker}\n\n"
        if not text.startswith("BLOCKER:"):
            REPORT.write_text(banner + text)
        print(banner.strip())
        return
    block = f"{START}\n{render()}{END}\n"
    if START in text and END in text:
        pre, rest = text.split(START, 1)
        _, post = rest.split(END, 1)
        text = pre + block + post.lstrip("\n")
    else:
        text = text.rstrip() + "\n\n" + block
    REPORT.write_text(text)
    print("updated REPORT.md")


if __name__ == "__main__":
    main()
