"""QC v2 samples and stats after the label-validity fixes."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from write_qc import stats_md

ROOT = Path("/data2/hpcshared/medverif-audit")
V2 = ROOT / "data" / "v2"
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
        f"- flip_mechanism: {row.get('flip_mechanism')}",
        f"- dose_kind: {row.get('dose_kind')}",
        f"- threshold_quantifier: {row.get('threshold_quantifier')}",
        f"- claim span: {row.get('claim_span')}",
        "",
        "Claim:",
        "",
        row["claim"],
        "",
        "Evidence span in claim context is the claim above. Evidence:",
        "",
        row["evidence"][:500],
        "",
    ])


def main() -> None:
    stats = json.loads((V2 / "rebuild_stats.json").read_text())
    main_rows = read_jsonl(V2 / "instances_main.jsonl")
    thr = read_jsonl(V2 / "instances_threshold.jsonl")
    labels = read_jsonl(V2 / "paraphrase_labels.jsonl") if (V2 / "paraphrase_labels.jsonl").exists() else []
    yes = Counter()
    bases_yes = set()
    for row in labels:
        if row.get("label") == "YES":
            bases_yes.add(row["base_id"])
            yes[row.get("template")] += 1
    main_bases = {row["base_id"] for row in main_rows if row["condition"] == "C0"}
    no_para = sorted(base for base in main_bases if base not in bases_yes)
    ought = sum(1 for row in main_rows if row["type"] == "POLARITY" and row["magnitude"] == "paraphrase" and "ought to" in row["claim"].lower())
    pol_para = sum(1 for row in main_rows if row["type"] == "POLARITY" and row["magnitude"] == "paraphrase")
    extract = json.loads((ROOT / "data" / "extract_stats.json").read_text())
    llm = json.loads((ROOT / "data" / "llm_stats.json").read_text())
    lines = [
        stats_md(extract, llm).rstrip(),
        "",
        "## Label-validity fix (v2)",
        "",
        "Main set excludes threshold-governed DOSE bases and scope-marked POLARITY bases.",
        "Counts are copied from `data/v2/rebuild_stats.json` and the instance files.",
        "",
        f"- bases in (stage 1–2 kept): {stats['bases_in']}",
        f"- DOSE main: {stats['dose_main']}",
        f"- DOSE threshold (excluded from main, scored separately): {stats['dose_threshold']}",
        f"- POLARITY main: {stats['polarity_main']}",
        f"- POLARITY scope excluded: {stats['polarity_scope_excluded']}",
        f"- scope terms: `{json.dumps(stats['scope_terms'])}`",
        f"- flip_mechanism on main POLARITY C0: `{json.dumps(stats['flip_mechanism_main'])}`",
        f"- dose_kind on main DOSE: `{json.dumps(stats['dose_kind_main'])}`",
        f"- unit INV kept on main: {stats['unit_inv_main']}",
        f"- main DOSE bases with no natural unit INV: {stats['dose_main_without_unit_inv']}",
        f"- instances main: {stats['instances_main']}",
        f"- instances threshold: {stats['instances_threshold']}",
        f"- paraphrase YES bases (any candidate): {len(bases_yes)}",
        f"- main bases with no valid paraphrase INV: {len(no_para)}",
        f"- polarity paraphrase instances containing 'ought to': {ought} / {pol_para}",
        "",
        "### paraphrase YES by template",
        "",
    ]
    for key, count in sorted(yes.items()):
        lines.append(f"- {key}: {count}")
    if no_para:
        lines += ["", "### main bases with no valid INV paraphrase", ""]
        lines.extend(f"- {base}" for base in no_para)
    (QC / "qc_stats.md").write_text("\n".join(lines) + "\n")

    picked = []
    seen = set()

    def take(pool, n):
        got = 0
        for row in pool:
            if len(picked) >= 20 or got >= n:
                return
            if row["instance_id"] in seen:
                continue
            picked.append(row)
            seen.add(row["instance_id"])
            got += 1

    flips = [row for row in main_rows if row["condition"] == "E1-claim" and row["magnitude"] == "flip"]
    take([row for row in flips if row.get("flip_mechanism") == "not_remove"], 5)
    take([row for row in flips if row.get("flip_mechanism") == "lexical"], 6)
    take([row for row in main_rows if row["magnitude"] == "paraphrase"], 4)
    take([row for row in main_rows if row["magnitude"] == "unit_conversion"], 2)
    by_base = {}
    for row in thr:
        by_base.setdefault(row["base_id"], []).append(row)
    thr_bases = read_jsonl(V2 / "bases_threshold.jsonl")
    for base in thr_bases:
        if len(picked) >= 20:
            break
        if sum(1 for row in picked if row.get("subset") == "threshold") >= 3:
            break
        siblings = by_base.get(base["id"], [])
        e1 = next((row for row in siblings if row["condition"] == "E1-claim" and row["magnitude"] == "x10"), None)
        if e1 is None or e1["instance_id"] in seen:
            continue
        e1 = dict(e1)
        e1["threshold_quantifier"] = base.get("threshold_quantifier")
        picked.append(e1)
        seen.add(e1["instance_id"])
    take(flips, 20)
    text = ["# QC samples v2", "", "Twenty items focused on the new flips, the new INV, and three threshold exclusions.", ""]
    for row in picked[:20]:
        text.append(block(row))
    (QC / "qc_samples_v2.md").write_text("\n".join(text))
    print(json.dumps({"samples": min(20, len(picked)), "no_paraphrase": len(no_para), "stats": str(QC / "qc_stats.md")}))


if __name__ == "__main__":
    main()
