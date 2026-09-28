"""QC v3 samples and stats. Counts come from data/v3 files."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from write_qc import stats_md

ROOT = Path("/data2/hpcshared/medverif-audit")
V3 = ROOT / "data" / "v3"
QC = ROOT / "qc"


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def block(row: dict) -> str:
    return "\n".join([
        f"### {row['instance_id']}",
        "",
        f"- type: {row['type']}",
        f"- subset: {row.get('subset')}",
        f"- condition: {row['condition']} / {row['magnitude']}",
        f"- expected: {row['expected_verdict']}",
        f"- valid: {row.get('valid')}",
        f"- flip_mechanism: {row.get('flip_mechanism')}",
        f"- dose_kind: {row.get('dose_kind')}",
        f"- domain_kind: {row.get('domain_kind')}",
        f"- c0_drift: {row.get('c0_drift')}",
        f"- ocr_noise: {row.get('ocr_noise')}",
        f"- claim span: {row.get('claim_span')}",
        "",
        "Claim:",
        "",
        row["claim"],
        "",
        "Evidence:",
        "",
        (row.get("evidence") or "")[:500],
        "",
    ])


def main() -> None:
    summary = json.loads((V3 / "apply_stats.json").read_text())
    rows = read_jsonl(V3 / "instances_main.jsonl")
    extract = json.loads((ROOT / "data" / "extract_stats.json").read_text())
    llm = json.loads((ROOT / "data" / "llm_stats.json").read_text())
    lines = [
        stats_md(extract, llm).rstrip(),
        "",
        "## Label-validity fix (v3)",
        "",
        "Analysis set is `valid=true` in `data/v3/instances_main.jsonl`.",
        "Invalid rows are kept in `data/v3/instances_audit.jsonl`.",
        "v2 INV-paraphrase instances are `valid=false` (`inv_paraphrase_v2`).",
        "",
        f"- valid main bases: {summary['valid_main_bases']}",
        f"- valid main by type: `{json.dumps(summary['valid_main_by_type'])}`",
        f"- valid threshold bases: {summary['valid_threshold_bases']}",
        f"- paraphrase bases asked: {summary['paraphrase_bases_asked']}",
        f"- paraphrase bases passed: {summary['paraphrase_bases_passed']}",
        f"- paraphrase pass rate: {summary['paraphrase_pass_rate']}",
        f"- bases with no valid INV-paraphrase: {len(summary['paraphrase_missing'])}",
        f"- flip_ungrammatical bases: {summary['flip_ungrammatical_bases']}",
        f"- dose_kind main: `{json.dumps(summary['dose_kind_main'])}`",
        f"- flip_mechanism main: `{json.dumps(summary['flip_mechanism_main'])}`",
        f"- domain_kind main: `{json.dumps(summary['domain_kind_main'])}`",
        f"- c0_drift main bases: {summary['c0_drift_main']}",
        f"- ocr_noise main bases: {summary['ocr_noise_main']}",
        f"- valid main instances: {summary['instances_main_valid']}",
        f"- valid threshold instances: {summary['instances_threshold_valid']}",
        "",
        "### Main-set N by type × flip_mechanism × dose_kind",
        "",
    ]
    for key, count in summary["valid_main_cross"].items():
        lines.append(f"- {key}: {count}")
    if summary["paraphrase_missing"]:
        lines += ["", "### Bases with no valid INV-paraphrase", ""]
        lines.extend(f"- {base_id}" for base_id in summary["paraphrase_missing"])
    (QC / "qc_stats.md").write_text("\n".join(lines) + "\n")

    picked = []
    seen = set()

    def take(pool, n):
        got = 0
        for row in pool:
            if len(picked) >= 12 or got >= n:
                return
            if row["instance_id"] in seen:
                continue
            picked.append(row)
            seen.add(row["instance_id"])
            got += 1

    take([row for row in rows if row["magnitude"] == "paraphrase"], 6)
    lexical = [row for row in rows if row.get("flip_mechanism") == "lexical"]
    take([row for row in lexical if row["condition"] == "E1-evid"], 2)
    take([row for row in lexical if row["condition"] == "E2"], 1)
    take([row for row in rows if row.get("flip_mechanism") == "not_remove" and row["condition"] == "E1-evid"], 3)
    text = [
        "# QC samples v3",
        "",
        "Twelve items: 6 new INV-paraphrase, 3 lexical flips (E1-evid and E2), 3 E1-evid not_remove.",
        "",
    ]
    for row in picked:
        text.append(block(row))
    (QC / "qc_samples_v3.md").write_text("\n".join(text))
    print(json.dumps({"samples": len(picked), "pass_rate": summary["paraphrase_pass_rate"]}))


if __name__ == "__main__":
    main()
