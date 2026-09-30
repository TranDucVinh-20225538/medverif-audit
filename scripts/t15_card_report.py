#!/usr/bin/env python3
"""T15 QVC card: main DOSE cohort (C0-conditional), base vs ft MiniCheck-RoBERTa scores."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from analyze import N_BOOT, SEED, _c0_pass_bases, _groups, _parsed, bootstrap_rate, read_jsonl  # noqa: E402
from non_dose_targets import invalidate_non_dose_row  # noqa: E402
from review_filters import analysis_keep_row, effective_unit_natural_y  # noqa: E402
from t14_t3_filter_report import inv_span_before  # noqa: E402
from text_utils import rule_natural_unit_conversion_label  # noqa: E402

RAW = ROOT / "results/raw/t15"
MAIN = ROOT / "data/v3/instances_main.jsonl"
T7 = ROOT / "data/t7/instances_e1_unit.jsonl"
T17 = ROOT / "data/v3/t17_downdose.jsonl"
OUT = ROOT / "notes/t15_report.md"
OUT_JSON = ROOT / "notes/t15_card.json"


def load_main_dose_instances() -> list[dict]:
    out = []
    for r in read_jsonl(MAIN):
        r = dict(r)
        invalidate_non_dose_row(r)
        if not r.get("valid", True):
            continue
        if r.get("type") != "DOSE" or r.get("subset") != "main":
            continue
        if not analysis_keep_row(r):
            continue
        out.append(r)
    return out


def read_scores(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for row in read_jsonl(path):
        iid = row.get("instance_id")
        if not iid:
            continue
        v = row.get("verdict")
        if v in ("PASS", "FAIL", "PARSE_FAIL"):
            out[str(iid)] = v
        elif row.get("score") is not None:
            out[str(iid)] = "PASS" if float(row["score"]) >= 0.5 else "FAIL"
    return out


def join_rows(instances: list[dict], scores: dict[str, str]) -> list[dict]:
    joined = []
    for inst in instances:
        v = scores.get(inst["instance_id"])
        if not v:
            continue
        row = dict(inst)
        row["verdict"] = v
        joined.append(row)
    return joined


def _natural_inv(r: dict) -> bool:
    if r.get("condition") != "INV-claim" or r.get("magnitude") != "unit_conversion":
        return False
    orig = inv_span_before(r)
    return effective_unit_natural_y(r["base_id"], bool(rule_natural_unit_conversion_label(orig)))


def _fail_groups(block: list[dict], pred) -> list[tuple[int, int]]:
    by: dict[str, list[dict]] = defaultdict(list)
    for r in block:
        if not _parsed(r) or not pred(r):
            continue
        by[r["base_id"]].append(r)
    groups: list[tuple[int, int]] = []
    for g in by.values():
        groups.append((sum(1 for x in g if x["verdict"] == "FAIL"), len(g)))
    return groups


def _pass_groups(block: list[dict], pred) -> list[tuple[int, int]]:
    by: dict[str, list[dict]] = defaultdict(list)
    for r in block:
        if not _parsed(r) or not pred(r):
            continue
        by[r["base_id"]].append(r)
    groups: list[tuple[int, int]] = []
    for g in by.values():
        groups.append((sum(1 for x in g if x["verdict"] == "PASS"), len(g)))
    return groups


def metrics_block(block: list[dict], cond: set[str]) -> dict:
    c0 = _c0_pass_bases(block)
    qi_all = bootstrap_rate(
        _pass_groups(block, lambda r: r["base_id"] in c0 and r.get("condition") == "INV-claim")
    )
    qi_nat = bootstrap_rate(
        _pass_groups(
            block,
            lambda r: r["base_id"] in c0 and _natural_inv(r),
        )
    )
    ns = bootstrap_rate(
        _fail_groups(block, lambda r: r["base_id"] in c0 and r.get("condition") == "E1-evid")
    )
    us_claim_up = bootstrap_rate(
        _fail_groups(
            block,
            lambda r: r["base_id"] in c0
            and r.get("condition") == "E1-unit-claim"
            and r.get("magnitude") == "x1000",
        )
    )
    us_evid_up = bootstrap_rate(
        _fail_groups(
            block,
            lambda r: r["base_id"] in c0
            and r.get("condition") == "E1-unit-evid"
            and r.get("magnitude") == "x1000",
        )
    )
    us_claim_down = bootstrap_rate(
        _fail_groups(
            block,
            lambda r: r["base_id"] in c0 and r.get("condition") == "E1-down10" and "__claim__" in r.get("instance_id", ""),
        )
    )
    us_evid_down = bootstrap_rate(
        _fail_groups(
            block,
            lambda r: r["base_id"] in c0 and r.get("condition") == "E1-down10" and "__evid__" in r.get("instance_id", ""),
        )
    )
    c0_stat = bootstrap_rate(_pass_groups(block, lambda r: r.get("condition") == "C0"))
    return {
        "n_c0_bases_scored": len({r["base_id"] for r in block if r.get("condition") == "C0"}),
        "n_c0_pass_bases": len(c0),
        "c0_pass_rate": c0_stat,
        "qi_all": qi_all,
        "qi_nat": qi_nat,
        "ns": ns,
        "us_claim_up": us_claim_up,
        "us_evid_up": us_evid_up,
        "us_claim_down": us_claim_down,
        "us_evid_down": us_evid_down,
    }


def join_extra(instances: list[dict], scores: dict[str, str], path: Path) -> list[dict]:
    if not path.is_file():
        return []
    extra = []
    main_bases = {r["base_id"] for r in instances}
    for r in read_jsonl(path):
        if not r.get("valid", True) or not analysis_keep_row(r):
            continue
        if r["base_id"] not in main_bases:
            continue
        v = scores.get(r["instance_id"])
        if not v:
            continue
        row = dict(r)
        row["verdict"] = v
        extra.append(row)
    return extra


def fmt_stat(st: dict) -> str:
    if st.get("rate") is None:
        return f"NA (n={st.get('den', 0)})"
    lo, hi = st.get("lo"), st.get("hi")
    ci = f" [{100*lo:.1f}%, {100*hi:.1f}%]" if lo is not None and hi is not None else ""
    return f"{100*st['rate']:.1f}%{ci} (n={st['den']}, q={st['n_bases']})"


def aggrefact_section() -> list[str]:
    test = ROOT / "data/t8/aggrefact/test.jsonl"
    if not test.is_file():
        return ["- **AggreFact:** missing test split"]
    labels: dict[str, int] = {}
    by_ds: dict[str, list[str]] = defaultdict(list)
    n_test = 0
    for row in read_jsonl(test):
        n_test += 1
        iid = row.get("contamination_identifier") or row.get("instance_id")
        labels[str(iid)] = int(row["label"])
        by_ds[row.get("dataset", "?")].append(str(iid))

    def read_raw(tag: str) -> dict[str, dict]:
        out: dict[str, dict] = {}
        path = RAW / f"{tag}_aggrefact_test.jsonl"
        for row in read_jsonl(path):
            out[row["instance_id"]] = row
        return out

    base = read_raw("base")
    ft = read_raw("ft")
    lines = [
        "## AggreFact test (paired base vs ft)",
        "",
        f"- Test split rows in file: **{n_test}** · scored paired: **{len(set(labels) & set(base) & set(ft))}**",
        "",
    ]

    def bal_acc(scores: dict[str, dict], ids: list[str]) -> tuple[float, int]:
        if not ids:
            return float("nan"), 0
        ok = sum(1 for iid in ids if (1 if scores[iid]["verdict"] == "PASS" else 0) == labels[iid])
        return ok / len(ids), len(ids)

    common = sorted(set(labels) & set(base) & set(ft))
    for tag, scores in (("base", base), ("ft", ft)):
        acc, n = bal_acc(scores, common)
        lines.append(f"- **{tag}** overall balanced acc={acc:.4f} (n={n} paired)")
        for ds, ids in sorted(by_ds.items()):
            sub = [i for i in ids if i in common]
            a, nn = bal_acc(scores, sub)
            if nn:
                lines.append(f"  - {ds}: {a:.4f} (n={nn})")
    return lines


def main() -> None:
    main_inst = load_main_dose_instances()
    legs = {}
    for leg in ("base", "ft"):
        scores = read_scores(RAW / f"{leg}_main_dose.jsonl")
        block = join_rows(main_inst, scores)
        # Unit US rows live on T7/T17; merge when leg has those scores in t15 raw.
        for extra_name, extra_path in (("t7", T7), ("t17", T17)):
            score_path = RAW / f"{leg}_{extra_name}.jsonl"
            if not score_path.is_file():
                continue
            block.extend(join_extra(main_inst, read_scores(score_path), extra_path))
        legs[leg] = metrics_block(block, set())

    lines = [
        "# T15 evaluation — QVC card (base vs fine-tuned MiniCheck-RoBERTa)",
        "",
        "Main **DOSE** cohort (`instances_main.jsonl`): non-dose bases excluded, `analysis_keep_row`, "
        f"bootstrap **{N_BOOT}** × `base_id`, seed **{SEED}**. "
        "Metrics **| C0 PASS** except C0 row. Same definitions as `scripts/compute_paper_numbers.py`.",
        "",
        "| Leg | C0 bases scored | C0 PASS bases | QI all | QI nat | NS (E1-evid FAIL) | "
        "US claim↑ | US evid↑ | US claim↓ | US evid↓ |",
        "| --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for leg in ("base", "ft"):
        m = legs[leg]
        lines.append(
            f"| {leg} | {m['n_c0_bases_scored']} | {m['n_c0_pass_bases']} | "
            f"{fmt_stat(m['qi_all'])} | {fmt_stat(m['qi_nat'])} | {fmt_stat(m['ns'])} | "
            f"{fmt_stat(m['us_claim_up'])} | {fmt_stat(m['us_evid_up'])} | "
            f"{fmt_stat(m['us_claim_down'])} | {fmt_stat(m['us_evid_down'])} |"
        )
    lines.extend(["", *aggrefact_section(), ""])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    OUT_JSON.write_text(json.dumps({"main_dose": legs, "bootstrap_n": N_BOOT, "seed": SEED}, indent=2) + "\n")
    print(json.dumps({"report": str(OUT), "c0_bases_base": legs["base"]["n_c0_bases_scored"]}, indent=2))


if __name__ == "__main__":
    main()
