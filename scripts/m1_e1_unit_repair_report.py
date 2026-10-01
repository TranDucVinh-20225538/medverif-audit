#!/usr/bin/env python3
"""LLM-judge E1-unit-evid repair counts (T7 ×1000, T17 unit-down evid) before vs after M1."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "src"))

from analyze import _parsed, read_jsonl  # noqa: E402

OUT_MD = ROOT / "notes/m1_e1_unit_repair_report.md"
OUT_JSON = ROOT / "notes/m1_e1_unit_repair_report.json"

REPAIR_KW = re.compile(
    r"typo|error|mistake|likely\s*mg|wrong\s*unit|unit\s*error|incorrect\s*unit|"
    r"conversion|misread|mis-?label|mcg|microgram|milligram|gram",
    re.I,
)

LLM_VERIFIERS = (
    ("v1_medscore", "V1", ROOT / "results/raw/t7", ROOT / "results/raw_m1/t7"),
    ("v1b_medscore", "V1b", ROOT / "results/raw/t7", ROOT / "results/raw_m1/t7"),
    ("v1c_medscore", "V1c", ROOT / "results/raw/t7", ROOT / "results/raw_m1/t7"),
    ("v4_ragas_nli", "V4-Llama", ROOT / "results/raw/t7", ROOT / "results/raw_m1/t7"),
    ("v5_ragas_nli", "V5", ROOT / "results/raw/t7", ROOT / "results/raw_m1/t7"),
    ("v6_ragas_gpt4o_mini", "V6-gpt4o", ROOT / "results/raw/t7", ROOT / "results/raw_m1/t7"),
    ("v6_ragas_haiku45", "V6-haiku", ROOT / "results/raw/t7", ROOT / "results/raw_m1/t7"),
    ("v6_ragas_llama31_8b", "V6-llama8b", ROOT / "results/raw/t7", ROOT / "results/raw_m1/t7"),
    ("v6_ragas_mistral_small32", "V6-mistral", ROOT / "results/raw/t7", ROOT / "results/raw_m1/t7"),
)

AFTER_M1_T7 = ROOT / "results/raw_m1/t7"
AFTER_M1_T7_AMEND5 = ROOT / "results/raw_m1/t7_amend5"  # amendment 5: spec-M1 rescores of off-spec rows (last wins)

T17_LLMS = (
    ("v1_medscore", "V1", ROOT / "results/raw/t17", ROOT / "results/raw/lane_b/t17_downdose"),
    ("v4_ragas_nli", "V4-Llama", ROOT / "results/raw/t17", ROOT / "results/raw/lane_b/t17_downdose"),
    ("v6_ragas_llama31_8b", "V6-llama8b", ROOT / "results/raw/t17", ROOT / "results/raw/lane_b/t17_downdose"),
)


def score_file(raw_dir: Path, verifier: str) -> Path | None:
    if verifier == "v4_ragas_nli":
        for n in ("v4_ragas_nli.llama.jsonl", "v4_ragas_nli.jsonl"):
            p = raw_dir / n
            if p.is_file():
                return p
        return None
    p = raw_dir / f"{verifier}.jsonl"
    return p if p.is_file() else None


def load_scores(raw_dir: Path, verifier: str) -> dict[str, dict]:
    path = score_file(raw_dir, verifier)
    if not path:
        return {}
    return {json.loads(l)["instance_id"]: json.loads(l) for l in path.open() if l.strip()}


def explanation(row: dict) -> str:
    for k in ("raw_output", "explanation", "reasoning", "detail"):
        v = row.get(k)
        if v:
            return str(v)
    return ""


def analyze_cohort(
    *,
    label: str,
    inst_path: Path,
    filter_fn,
    llm_specs: tuple,
) -> dict:
    inst = {r["instance_id"]: r for r in read_jsonl(inst_path) if filter_fn(r)}
    rows_out = []
    for slug, disp, before_dir, after_dir in llm_specs:
        sb, sa = load_scores(before_dir, slug), load_scores(after_dir, slug)
        if after_dir == AFTER_M1_T7:
            sa.update(load_scores(AFTER_M1_T7_AMEND5, slug))
        if not sb and not sa:
            continue
        pass_before = pass_after = 0
        n = 0
        kw_hits = 0
        pass_expl: list[str] = []
        for iid in inst:
            rb, ra = sb.get(iid), sa.get(iid)
            if not rb or not ra or not _parsed(rb) or not _parsed(ra):
                continue
            n += 1
            if rb["verdict"] == "PASS":
                pass_before += 1
            if ra["verdict"] == "PASS":
                pass_after += 1
                expl = explanation(ra)
                if REPAIR_KW.search(expl):
                    kw_hits += 1
                if len(pass_expl) < 10:
                    pass_expl.append(f"`{iid}` [{disp} after M1 PASS]: {expl[:350].replace(chr(10), ' ')}")
        rows_out.append(
            {
                "verifier": slug,
                "label": disp,
                "n_paired": n,
                "pass_before": pass_before,
                "pass_after": pass_after,
                "pass_after_keyword_hits": kw_hits,
                "pass_after_keyword_rate": (kw_hits / pass_after) if pass_after else None,
                "verbatim_pass_after": pass_expl,
            }
        )
    return {"cohort": label, "n_instances": len(inst), "verifiers": rows_out}


def main() -> None:
    t7_inst = ROOT / "data/t7/instances_e1_unit.jsonl"
    t17_inst = ROOT / "data/v3/t17_downdose.jsonl"

    payload = {
        "t7_e1_unit_evid_x1000": analyze_cohort(
            label="T7 E1-unit-evid (×1000)",
            inst_path=t7_inst,
            filter_fn=lambda r: r.get("condition") == "E1-unit-evid" and r.get("magnitude") == "x1000",
            llm_specs=LLM_VERIFIERS,
        ),
        "t17_e1_unit_down_evid": analyze_cohort(
            label="T17 E1-unit-down evid (÷1000-style pack)",
            inst_path=t17_inst,
            filter_fn=lambda r: r.get("condition") == "E1-unit-down" and "__evid__" in r.get("instance_id", ""),
            llm_specs=T17_LLMS,
        ),
    }

    lines = [
        "# M1 repair — LLM judges on E1-unit evidence",
        "",
        "PASS **n/N** before vs after M1; keyword rate = share of **after-M1 PASS** explanations "
        "matching typo/error/likely-mg/unit/conversion (heuristic).",
        "",
    ]
    for block in payload.values():
        lines.extend([f"## {block['cohort']}", "", f"Instances: **{block['n_instances']}**", ""])
        lines.append("| Judge | PASS before | PASS after M1 | kw / after PASS |")
        lines.append("| --- | --- | --- | --- |")
        for v in block["verifiers"]:
            lines.append(
                f"| {v['label']} | {v['pass_before']}/{v['n_paired']} | {v['pass_after']}/{v['n_paired']} | "
                f"{v['pass_after_keyword_hits']}/{v['pass_after'] or 0} |"
            )
        lines.append("")
        for v in block["verifiers"]:
            if v["verbatim_pass_after"]:
                lines.append(f"### {v['label']} — sample after-M1 PASS explanations")
                for ex in v["verbatim_pass_after"][:10]:
                    lines.append(f"- {ex}")
                lines.append("")

    OUT_MD.write_text("\n".join(lines) + "\n")
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"wrote": str(OUT_MD)}, indent=2))


if __name__ == "__main__":
    main()
