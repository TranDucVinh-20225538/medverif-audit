"""Render QC markdown from pipeline files. Does not invent counts."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

CONDITIONS = ["C0", "E1-evid", "E1-claim", "E2", "INV-claim"]


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def pick(instances: list[dict], seed: int = 42) -> tuple[list[dict], list[str]]:
    rng = random.Random(seed)
    cells = defaultdict(list)
    for row in instances:
        cells[(row["type"], row["condition"])].append(row)
    picked = []
    notes = []
    for kind in ("DOSE", "POLARITY"):
        for cond in CONDITIONS:
            pool = list(cells.get((kind, cond), []))
            rng.shuffle(pool)
            chosen = []
            if kind == "DOSE" and cond in {"E1-evid", "E1-claim", "E2"}:
                by_mag = defaultdict(list)
                for row in pool:
                    by_mag[row["magnitude"]].append(row)
                for mag in ("x2", "x10"):
                    if by_mag[mag]:
                        chosen.append(by_mag[mag][0])
                if len(chosen) < 2:
                    for row in pool:
                        if row not in chosen:
                            chosen.append(row)
                        if len(chosen) == 2:
                            break
            else:
                chosen = pool[:2]
            if len(chosen) < 2:
                notes.append(f"{kind} {cond}: {len(chosen)} available, wanted 2")
            picked.extend(chosen[:2])
    return picked, notes


def _pieces(diff: dict) -> list[str]:
    lines = []
    if "highlight_before" in diff:
        lines.append(f"claim span: {diff.get('highlight_before')}")
        lines.append(f"edit distance: {diff.get('edit_distance')}")
        return lines
    evid = diff.get("evidence")
    claim = diff.get("claim")
    if isinstance(evid, dict):
        lines.append(f"evidence before: {evid.get('highlight_before')}")
        lines.append(f"evidence after: {evid.get('highlight_after')}")
        lines.append(f"evidence edit distance: {evid.get('edit_distance')}")
        lines.append(f"evidence confined to span: {evid.get('confined_to_span')}")
    elif diff.get("evidence_unchanged"):
        lines.append("evidence unchanged")
    if isinstance(claim, dict):
        lines.append(f"claim before: {claim.get('highlight_before')}")
        lines.append(f"claim after: {claim.get('highlight_after')}")
        lines.append(f"claim edit distance: {claim.get('edit_distance')}")
        lines.append(f"claim confined to span: {claim.get('confined_to_span')}")
    elif diff.get("claim_unchanged"):
        lines.append("claim unchanged")
    return lines


def side_by_side(row: dict) -> str:
    highlighted = "\n".join(_pieces(row["diff"]))
    lines = [
        f"### {row['instance_id']}",
        "",
        f"- type: `{row['type']}`",
        f"- condition: `{row['condition']}`",
        f"- magnitude: `{row['magnitude']}`",
        f"- expected faithfulness verdict: `{row['expected_verdict']}`",
        f"- base_id: `{row['base_id']}`",
        "",
        "Highlighted diff (`« »` marks the span)",
        "",
        "```",
        highlighted,
        "```",
        "",
        "Evidence before",
        "",
        "```",
        row["evidence_c0"],
        "```",
        "",
        "Evidence after",
        "",
        "```",
        row["evidence"],
        "```",
        "",
        "Claim before",
        "",
        "```",
        row["claim_c0"],
        "```",
        "",
        "Claim after",
        "",
        "```",
        row["claim"],
        "```",
        "",
    ]
    return "\n".join(lines)


def stats_md(extract: dict, llm: dict) -> str:
    lines = [
        "# QC stats",
        "",
        "Counts below are copied from `data/extract_stats.json` and `data/llm_stats.json`.",
        "",
        "## Extraction (Textbooks only)",
        "",
        f"- chunks: {extract.get('chunks')}",
        f"- sentences: {extract.get('sentences')}",
        f"- pool DOSE: {extract.get('pool_DOSE')}",
        f"- pool POLARITY: {extract.get('pool_POLARITY')}",
        f"- selected for generation: {extract.get('selected')}",
        f"- attempt cap per type: {extract.get('attempt_per_type')}",
        f"- per-book cap: {extract.get('per_book')}",
        f"- per-passage cap: {extract.get('per_passage')}",
        f"- seed: {extract.get('seed')}",
        "",
        "### Extract drops",
        "",
    ]
    for key, value in sorted((extract.get("extract_drops") or {}).items()):
        lines.append(f"- {key}: {value}")
    lines += ["", "### Selection drops", ""]
    for key, value in sorted((extract.get("selection") or {}).items()):
        lines.append(f"- {key}: {value}")
    lines += [
        "",
        "## Generation and validation",
        "",
        f"- claim generator: {llm.get('generator_model')} @ `{llm.get('generator_revision')}`",
        f"- support validator and INV checker: {llm.get('validator_model')} @ `{llm.get('validator_revision')}`",
        f"- candidates attempted: {llm.get('candidates_attempted')}",
        f"- attempted by type: `{json.dumps(llm.get('attempted_by_type'))}`",
        f"- passed span rule: {llm.get('rule_passed')}",
        f"- validator YES: {llm.get('validator_yes')}",
        f"- bases kept after INV check: {llm.get('bases_kept')}",
        f"- bases kept by type: `{json.dumps(llm.get('bases_kept_by_type'))}`",
        f"- instances: {llm.get('instances')}",
        "",
        "### LLM and perturb drops",
        "",
    ]
    for key, value in sorted((llm.get("drops") or {}).items()):
        lines.append(f"- {key}: {value}")
    lines += ["", "### Instances by type, condition, magnitude", ""]
    for key, value in sorted((llm.get("instances_by_type_condition_magnitude") or {}).items()):
        lines.append(f"- {key}: {value}")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extract-stats", type=Path, required=True)
    parser.add_argument("--llm-stats", type=Path, required=True)
    parser.add_argument("--instances", type=Path, required=True)
    parser.add_argument("--samples-out", type=Path, required=True)
    parser.add_argument("--stats-out", type=Path, required=True)
    args = parser.parse_args()
    extract = load_json(args.extract_stats)
    llm = load_json(args.llm_stats)
    instances = read_jsonl(args.instances)
    picked, notes = pick(instances)
    header = [
        "# QC samples",
        "",
        "Random sample, seed 42, up to 2 items for each of DOSE/POLARITY × "
        "C0, E1-evid, E1-claim, E2, INV-claim. "
        "DOSE edits prefer one `x2` and one `x10` when both exist. "
        "Changed spans are marked with « ». "
        f"Sampled {len(picked)} instances from {len(instances)}.",
        "",
    ]
    if notes:
        header.append("Short cells:")
        header.append("")
        header.extend(f"- {note}" for note in notes)
        header.append("")
    body = "\n".join(side_by_side(row) for row in picked)
    args.samples_out.parent.mkdir(parents=True, exist_ok=True)
    args.samples_out.write_text("\n".join(header) + body)
    args.stats_out.write_text(stats_md(extract, llm))
    print(json.dumps({"sampled": len(picked), "instances": len(instances), "notes": notes}))


if __name__ == "__main__":
    main()
