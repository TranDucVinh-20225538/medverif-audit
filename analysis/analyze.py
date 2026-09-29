"""Stage 4 tables and figures.

Rates are counts. PARSE_FAIL is never treated as FAIL. Conditional rates use only
bases whose C0 verdict is PASS. Bootstrap is 1000 resamples of base_id, seed 42,
percentile interval [2.5, 97.5]. MOCK runs refuse to write under results/.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path

VERIFIERS = (
    "v1_medscore",
    "v2a_minicheck",
    "v2b_bespoke",
    "v3_alignscore",
    "v4_ragas_nli",
)
TYPES = ("DOSE", "POLARITY")
CONDITIONS = ("C0", "E1-evid", "E1-claim", "E2", "INV-claim")
LABELS = ("PASS", "FAIL", "PARSE_FAIL")
N_BOOT = 1000
SEED = 42
LENGTH_BINS = ((0, 200), (200, 400), (400, 800), (800, 1600), (1600, None))
POSITION_BINS = ((0, 50), (50, 150), (150, 400), (400, 1000), (1000, None))


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def count_span(text: str, span: str) -> int:
    if not text or not span:
        return 0
    n = 0
    start = 0
    while True:
        found = text.find(span, start)
        if found < 0:
            return n
        n += 1
        start = found + len(span)
    return n


def original_evidence_span(inst: dict) -> str:
    diff = inst.get("diff") or {}
    evidence = diff.get("evidence")
    if isinstance(evidence, dict) and evidence.get("span_before"):
        return str(evidence["span_before"])
    return str(inst.get("evidence_span") or "")


def span_position(inst: dict) -> int:
    evidence = str(inst.get("evidence") or "")
    span = str(inst.get("evidence_span") or "")
    if not span:
        return -1
    return evidence.find(span)


def annotate(inst: dict) -> dict:
    span = original_evidence_span(inst)
    before = str(inst.get("evidence_c0") or inst.get("evidence") or "")
    after = str(inst.get("evidence") or "")
    n_before = count_span(before, span)
    n_after = count_span(after, span)
    row = dict(inst)
    row["original_span"] = span
    row["n_before"] = n_before
    row["n_after"] = n_after
    row["multi"] = n_before > 1
    row["evidence_len"] = len(after)
    row["span_position"] = span_position(inst)
    return row


def load_joined(instances_path: Path, verdicts_dir: Path) -> list[dict]:
    return load_joined_from_records(read_jsonl(instances_path), verdicts_dir)


def load_joined_from_records(instance_rows: list[dict], verdicts_dir: Path) -> list[dict]:
    from verifier_score_paths import read_verifier_scores

    instances = {
        row["instance_id"]: annotate(row)
        for row in instance_rows
        if row.get("valid", True)
    }
    joined = []
    for verifier in VERIFIERS:
        verdicts = read_verifier_scores(verdicts_dir, verifier, enforce=True)
        if not verdicts:
            continue
        for verdict in verdicts:
            inst = instances.get(verdict["instance_id"])
            if inst is None:
                continue
            row = dict(inst)
            row["verifier"] = verifier
            row["verdict"] = verdict["verdict"]
            row["score"] = verdict.get("score")
            joined.append(row)
    return joined


def _percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return float("nan")
    if len(sorted_values) == 1:
        return sorted_values[0]
    k = (len(sorted_values) - 1) * p
    lo = int(k)
    hi = min(lo + 1, len(sorted_values) - 1)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (k - lo)


def bootstrap_rate(groups: list[tuple[int, int]], seed: int = SEED) -> dict:
    """groups are (n_pass, n_parsed) per base. Empty denominator -> NA."""
    usable = [(n, d) for n, d in groups if d > 0]
    num = sum(n for n, _ in usable)
    den = sum(d for _, d in usable)
    if den == 0:
        return {"rate": None, "lo": None, "hi": None, "num": 0, "den": 0, "n_bases": 0}
    point = num / den
    if len(usable) < 2:
        return {"rate": point, "lo": None, "hi": None, "num": num, "den": den, "n_bases": len(usable)}
    rng = random.Random(seed)
    stats = []
    m = len(usable)
    for _ in range(N_BOOT):
        n_sum = d_sum = 0
        for _j in range(m):
            n, d = usable[rng.randrange(m)]
            n_sum += n
            d_sum += d
        if d_sum:
            stats.append(n_sum / d_sum)
    stats.sort()
    return {
        "rate": point,
        "lo": _percentile(stats, 0.025),
        "hi": _percentile(stats, 0.975),
        "num": num,
        "den": den,
        "n_bases": m,
    }


def bootstrap_gap(pairs: list[tuple[int, int, int, int]], seed: int = SEED) -> dict:
    """Each item is (inv_pass, inv_den, e1_pass, e1_den) for one base."""
    def _one(sample: list[tuple[int, int, int, int]]) -> tuple[float | None, int, int, int, int]:
        inv_n = inv_d = e1_n = e1_d = 0
        for a, b, c, d in sample:
            inv_n += a
            inv_d += b
            e1_n += c
            e1_d += d
        if inv_d == 0 or e1_d == 0:
            return None, inv_n, inv_d, e1_n, e1_d
        return (inv_n / inv_d) - (e1_n / e1_d), inv_n, inv_d, e1_n, e1_d

    point, inv_n, inv_d, e1_n, e1_d = _one(pairs)
    if point is None or len(pairs) < 2:
        return {"rate": point, "lo": None, "hi": None, "num": None, "den": None, "n_bases": len(pairs)}
    rng = random.Random(seed)
    stats = []
    m = len(pairs)
    for _ in range(N_BOOT):
        sample = [pairs[rng.randrange(m)] for _ in range(m)]
        gap, _, _, _, _ = _one(sample)
        if gap is not None:
            stats.append(gap)
    stats.sort()
    return {
        "rate": point,
        "lo": _percentile(stats, 0.025) if stats else None,
        "hi": _percentile(stats, 0.975) if stats else None,
        "num": None,
        "den": None,
        "n_bases": m,
        "inv_num": inv_n,
        "inv_den": inv_d,
        "e1_num": e1_n,
        "e1_den": e1_d,
    }


def _parsed(row: dict) -> bool:
    return row["verdict"] in ("PASS", "FAIL")


def _groups(rows: list[dict], keep) -> list[tuple[int, int]]:
    by: dict[str, list[int]] = {}
    for row in rows:
        if not keep(row) or not _parsed(row):
            continue
        num, den = by.setdefault(row["base_id"], [0, 0])
        den += 1
        if row["verdict"] == "PASS":
            num += 1
        by[row["base_id"]] = [num, den]
    return [(n, d) for n, d in by.values()]


def _c0_pass_bases(rows: list[dict]) -> set[str]:
    return {row["base_id"] for row in rows if row["condition"] == "C0" and row["verdict"] == "PASS"}


def _fmt(stat: dict) -> str:
    if stat["rate"] is None:
        return "NA"
    if stat["lo"] is None:
        return f"{stat['rate']:.4f}"
    return f"{stat['rate']:.4f} [{stat['lo']:.4f}, {stat['hi']:.4f}]"


def _fmt_point(stat: dict) -> str:
    if stat["den"] == 0 or stat["rate"] is None:
        return "NA"
    return f"{stat['rate']:.4f} ({stat['num']}/{stat['den']})"


def bin_label(lo: int, hi: int | None) -> str:
    if hi is None:
        return f"[{lo}, inf)"
    return f"[{lo}, {hi})"


def which_bin(value: int, bins: tuple[tuple[int, int | None], ...]) -> str | None:
    if value < 0:
        return None
    for lo, hi in bins:
        if value >= lo and (hi is None or value < hi):
            return bin_label(lo, hi)
    return None


def cohen_kappa(left: list[str], right: list[str]) -> float | None:
    if not left:
        return None
    index = {label: i for i, label in enumerate(LABELS)}
    k = len(LABELS)
    mat = [[0] * k for _ in range(k)]
    for a, b in zip(left, right):
        mat[index[a]][index[b]] += 1
    n = len(left)
    po = sum(mat[i][i] for i in range(k)) / n
    row_sum = [sum(mat[i]) for i in range(k)]
    col_sum = [sum(mat[i][j] for i in range(k)) for j in range(k)]
    pe = sum(row_sum[i] * col_sum[i] for i in range(k)) / (n * n)
    if pe == 1:
        return 1.0
    return (po - pe) / (1 - pe)


def auroc(scores_pos: list[float], scores_neg: list[float]) -> float | None:
    if not scores_pos or not scores_neg:
        return None
    wins = ties = 0.0
    for pos in scores_pos:
        for neg in scores_neg:
            if pos > neg:
                wins += 1
            elif pos == neg:
                ties += 1
    return (wins + 0.5 * ties) / (len(scores_pos) * len(scores_neg))


def subset(rows: list[dict], verifier: str, fact_type: str) -> list[dict]:
    return [row for row in rows if row["verifier"] == verifier and row["type"] == fact_type]


def rate_table(rows: list[dict]) -> list[dict]:
    out = []
    for verifier in VERIFIERS:
        for fact_type in TYPES:
            block = subset(rows, verifier, fact_type)
            if not block:
                continue
            n = len(block)
            n_pf = sum(row["verdict"] == "PARSE_FAIL" for row in block)
            c0 = _groups(block, lambda row: row["condition"] == "C0")
            cond_bases = _c0_pass_bases(block)
            inv = _groups(block, lambda row: row["base_id"] in cond_bases and row["condition"] == "INV-claim")
            e1e = _groups(block, lambda row: row["base_id"] in cond_bases and row["condition"] == "E1-evid")
            e1c = _groups(block, lambda row: row["base_id"] in cond_bases and row["condition"] == "E1-claim")
            out.append({
                "verifier": verifier,
                "type": fact_type,
                "n": n,
                "parse_fail": {"rate": (n_pf / n) if n else None, "lo": None, "hi": None, "num": n_pf, "den": n},
                "c0_pass": bootstrap_rate(c0),
                "inv_pass": bootstrap_rate(inv),
                "e1_evid_false_pass": bootstrap_rate(e1e),
                "e1_claim_false_pass": bootstrap_rate(e1c),
                "gap_evid": _gap(block, cond_bases, "E1-evid"),
                "gap_claim": _gap(block, cond_bases, "E1-claim"),
                "x2_evid": bootstrap_rate(_groups(block, lambda row: row["base_id"] in cond_bases and row["condition"] == "E1-evid" and row["magnitude"] == "x2")),
                "x10_evid": bootstrap_rate(_groups(block, lambda row: row["base_id"] in cond_bases and row["condition"] == "E1-evid" and row["magnitude"] == "x10")),
                "x2_claim": bootstrap_rate(_groups(block, lambda row: row["base_id"] in cond_bases and row["condition"] == "E1-claim" and row["magnitude"] == "x2")),
                "x10_claim": bootstrap_rate(_groups(block, lambda row: row["base_id"] in cond_bases and row["condition"] == "E1-claim" and row["magnitude"] == "x10")),
            })
    return out


def _gap(block: list[dict], cond_bases: set[str], e1_condition: str) -> dict:
    by: dict[str, list[int]] = {}
    for row in block:
        if row["base_id"] not in cond_bases or not _parsed(row):
            continue
        rec = by.setdefault(row["base_id"], [0, 0, 0, 0])
        if row["condition"] == "INV-claim":
            rec[1] += 1
            if row["verdict"] == "PASS":
                rec[0] += 1
        elif row["condition"] == e1_condition:
            rec[3] += 1
            if row["verdict"] == "PASS":
                rec[2] += 1
    pairs = [tuple(rec) for rec in by.values()]
    return bootstrap_gap(pairs)


def false_pass_split(rows: list[dict]) -> list[dict]:
    out = []
    for verifier in VERIFIERS:
        for fact_type in TYPES:
            block = subset(rows, verifier, fact_type)
            cond_bases = _c0_pass_bases(block)
            multi_bases = {row["base_id"] for row in block if row["multi"]}
            for condition in ("E1-evid", "E1-claim"):
                def _keep(which: str, condition: str = condition):
                    def inner(row: dict) -> bool:
                        if row["base_id"] not in cond_bases or row["condition"] != condition:
                            return False
                        if which == "all":
                            return True
                        if which == "without_multi":
                            return row["base_id"] not in multi_bases
                        return row["base_id"] in multi_bases
                    return inner

                out.append({
                    "verifier": verifier,
                    "type": fact_type,
                    "condition": condition,
                    "all": bootstrap_rate(_groups(block, _keep("all"))),
                    "without_multi": bootstrap_rate(_groups(block, _keep("without_multi"))),
                    "multi_only": bootstrap_rate(_groups(block, _keep("multi_only"))),
                    "n_multi_bases": len(multi_bases),
                })
    return out


def stratified(rows: list[dict], key: str, bins: tuple[tuple[int, int | None], ...] | None, missing_label: str | None) -> list[dict]:
    out = []
    for verifier in VERIFIERS:
        for fact_type in TYPES:
            block = subset(rows, verifier, fact_type)
            cond_bases = _c0_pass_bases(block)
            labels: list[str] = []
            if bins is not None:
                labels.extend(bin_label(lo, hi) for lo, hi in bins)
            if missing_label:
                labels.append(missing_label)
            for condition in ("E1-evid", "E1-claim"):
                for label in labels:
                    def _keep(row: dict, condition: str = condition, label: str = label) -> bool:
                        if row["base_id"] not in cond_bases or row["condition"] != condition:
                            return False
                        if key == "evidence_len":
                            return which_bin(row["evidence_len"], LENGTH_BINS) == label
                        if row["span_position"] < 0:
                            return label == missing_label
                        return which_bin(row["span_position"], POSITION_BINS) == label

                    stat = bootstrap_rate(_groups(block, _keep))
                    out.append({
                        "verifier": verifier,
                        "type": fact_type,
                        "condition": condition,
                        "bin": label,
                        "stat": stat,
                    })
    return out


def pass_rate_by_condition(rows: list[dict]) -> list[dict]:
    cells = []
    for verifier in VERIFIERS:
        for condition in CONDITIONS:
            for fact_type in TYPES:
                block = [
                    row for row in rows
                    if row["verifier"] == verifier and row["condition"] == condition and row["type"] == fact_type and _parsed(row)
                ]
                n_pass = sum(row["verdict"] == "PASS" for row in block)
                den = len(block)
                cells.append({
                    "verifier": verifier,
                    "condition": condition,
                    "type": fact_type,
                    "pass_rate": (n_pass / den) if den else None,
                    "num": n_pass,
                    "den": den,
                })
    return cells


def sensitivity_invariance(rows: list[dict]) -> list[dict]:
    points = []
    for verifier in VERIFIERS:
        for fact_type in TYPES:
            block = subset(rows, verifier, fact_type)
            cond = _c0_pass_bases(block)
            inv = bootstrap_rate(_groups(block, lambda row: row["base_id"] in cond and row["condition"] == "INV-claim"))
            e1 = _groups(block, lambda row: row["base_id"] in cond and row["condition"] == "E1-evid")
            # sensitivity = FAIL / parsed = 1 - false-PASS on the same parsed items
            fail_groups = []
            by: dict[str, list[int]] = {}
            for row in block:
                if row["base_id"] not in cond or row["condition"] != "E1-evid" or not _parsed(row):
                    continue
                num, den = by.setdefault(row["base_id"], [0, 0])
                den += 1
                if row["verdict"] == "FAIL":
                    num += 1
                by[row["base_id"]] = [num, den]
            fail_groups = [(n, d) for n, d in by.values()]
            sens = bootstrap_rate(fail_groups)
            points.append({
                "verifier": verifier,
                "type": fact_type,
                "invariance": inv["rate"],
                "sensitivity_e1_evid": sens["rate"],
                "false_pass_e1_evid": bootstrap_rate(e1)["rate"],
            })
    return points


def dose_curve(rows: list[dict]) -> list[dict]:
    points = []
    for verifier in VERIFIERS:
        block = [row for row in rows if row["verifier"] == verifier and row["type"] == "DOSE"]
        cond = _c0_pass_bases(block)
        for condition in ("E1-evid", "E1-claim"):
            for mag in ("x2", "x10"):
                groups = []
                by: dict[str, list[int]] = {}
                for row in block:
                    if row["base_id"] not in cond or row["condition"] != condition or row["magnitude"] != mag or not _parsed(row):
                        continue
                    num, den = by.setdefault(row["base_id"], [0, 0])
                    den += 1
                    if row["verdict"] == "FAIL":
                        num += 1
                    by[row["base_id"]] = [num, den]
                groups = [(n, d) for n, d in by.values()]
                stat = bootstrap_rate(groups)
                fp = bootstrap_rate(_groups(block, lambda row, condition=condition, mag=mag: row["base_id"] in cond and row["condition"] == condition and row["magnitude"] == mag))
                points.append({
                    "verifier": verifier,
                    "condition": condition,
                    "magnitude": mag,
                    "sensitivity": stat["rate"],
                    "false_pass": fp["rate"],
                    "false_pass_num": fp["num"],
                    "false_pass_den": fp["den"],
                    "sensitivity_num": stat["num"],
                    "sensitivity_den": stat["den"],
                })
    return points


def kappa_matrix(rows: list[dict]) -> list[dict]:
    by_id: dict[tuple[str, str], str] = {}
    for row in rows:
        by_id[(row["verifier"], row["instance_id"])] = row["verdict"]
    ids = sorted({row["instance_id"] for row in rows})
    cells = []
    for left in VERIFIERS:
        for right in VERIFIERS:
            ys_l = []
            ys_r = []
            for instance_id in ids:
                a = by_id.get((left, instance_id))
                b = by_id.get((right, instance_id))
                if a is None or b is None:
                    continue
                ys_l.append(a)
                ys_r.append(b)
            cells.append({
                "left": left,
                "right": right,
                "kappa": cohen_kappa(ys_l, ys_r),
                "n": len(ys_l),
            })
    return cells


def auroc_table(rows: list[dict]) -> list[dict]:
    out = []
    for verifier in VERIFIERS:
        for fact_type in TYPES:
            block = subset(rows, verifier, fact_type)
            cond = _c0_pass_bases(block)
            pos = []
            neg = []
            for row in block:
                if row["base_id"] not in cond or not _parsed(row) or not isinstance(row.get("score"), (int, float)):
                    continue
                if row["condition"] == "C0":
                    pos.append(float(row["score"]))
                elif row["condition"] in ("E1-evid", "E1-claim"):
                    neg.append(float(row["score"]))
            out.append({
                "verifier": verifier,
                "type": fact_type,
                "auroc_c0_vs_e1": auroc(pos, neg),
                "n_pos": len(pos),
                "n_neg": len(neg),
            })
    return out


def flagged_instances(instances_path: Path) -> list[dict]:
    rows = []
    for inst in (annotate(row) for row in read_jsonl(instances_path)):
        if not inst["multi"]:
            continue
        rows.append({
            "instance_id": inst["instance_id"],
            "base_id": inst["base_id"],
            "type": inst["type"],
            "condition": inst["condition"],
            "magnitude": inst["magnitude"],
            "n_before": inst["n_before"],
            "n_after": inst["n_after"],
            "evidence_len": inst["evidence_len"],
            "span_position": inst["span_position"],
        })
    return rows


def _md_stat(stat: dict) -> str:
    return _fmt(stat)


def slice_table(rows: list[dict]) -> list[dict]:
    out = []
    verifiers = sorted({row["verifier"] for row in rows})
    slices = (
        ("all_valid", None),
        ("ocr_noise=false", lambda row: not row.get("ocr_noise")),
        ("ocr_noise=true", lambda row: bool(row.get("ocr_noise"))),
        ("c0_drift=false", lambda row: not row.get("c0_drift")),
        ("c0_drift=true", lambda row: bool(row.get("c0_drift"))),
        ("domain=treatment", lambda row: row.get("domain_kind") == "treatment"),
    )
    for verifier in verifiers:
        for fact_type in TYPES:
            for name, pred in slices:
                if name == "domain=treatment" and fact_type != "POLARITY":
                    continue
                for condition in ("C0", "E1-evid", "E1-claim", "INV-claim"):
                    stat = _cond_pass(
                        rows, verifier, fact_type,
                        lambda row, condition=condition, pred=pred: (
                            row["condition"] == condition and (pred is None or pred(row))
                        ),
                    )
                    if stat["den"] == 0:
                        continue
                    out.append({
                        "verifier": verifier,
                        "type": fact_type,
                        "slice": name,
                        "condition": condition,
                        "stat": stat,
                    })
    return out


def _cond_pass(rows: list[dict], verifier: str, fact_type: str, keep) -> dict:
    block = subset(rows, verifier, fact_type)
    cond = _c0_pass_bases(block)
    return bootstrap_rate(_groups(block, lambda row: row["base_id"] in cond and keep(row)))


def subgroup_tables(rows: list[dict]) -> dict:
    out = {"flip_mechanism": [], "dose_kind": [], "inv_type": []}
    verifiers = sorted({row["verifier"] for row in rows})
    mechanisms = ("not_insert", "not_remove", "lexical")
    kinds = ("prescriptive", "descriptive", "measurement", "unclear")
    for verifier in verifiers:
        for mechanism in mechanisms:
            for condition, magnitude in (("C0", "none"), ("E1-evid", "flip"), ("E1-claim", "flip"), ("E2", "flip"), ("INV-claim", "paraphrase")):
                stat = _cond_pass(
                    rows, verifier, "POLARITY",
                    lambda row, condition=condition, magnitude=magnitude, mechanism=mechanism: (
                        row["condition"] == condition and row["magnitude"] == magnitude and row.get("flip_mechanism") == mechanism
                    ),
                )
                if stat["den"] == 0:
                    continue
                out["flip_mechanism"].append({
                    "verifier": verifier, "value": mechanism, "condition": condition, "magnitude": magnitude, "stat": stat,
                })
        for kind in kinds:
            for condition, magnitude in (("C0", "none"), ("E1-evid", "x2"), ("E1-evid", "x10"), ("E1-claim", "x2"), ("E1-claim", "x10"), ("INV-claim", "unit_conversion"), ("INV-claim", "paraphrase")):
                stat = _cond_pass(
                    rows, verifier, "DOSE",
                    lambda row, condition=condition, magnitude=magnitude, kind=kind: (
                        row["condition"] == condition and row["magnitude"] == magnitude and row.get("dose_kind") == kind
                    ),
                )
                if stat["den"] == 0:
                    continue
                out["dose_kind"].append({
                    "verifier": verifier, "value": kind, "condition": condition, "magnitude": magnitude, "stat": stat,
                })
        for fact_type in TYPES:
            for inv_type in ("unit_conversion", "paraphrase", "rephrase"):
                stat = _cond_pass(
                    rows, verifier, fact_type,
                    lambda row, inv_type=inv_type: row["condition"] == "INV-claim" and row["magnitude"] == inv_type,
                )
                if stat["den"] == 0:
                    continue
                out["inv_type"].append({
                    "verifier": verifier, "type": fact_type, "value": inv_type, "stat": stat,
                })
    out["slices"] = slice_table(rows)
    return out


def write_checklist(path: Path, stamp: str | None, main: list[dict], splits: list[dict], by_len: list[dict], by_pos: list[dict], flagged: list[dict], groups: dict | None = None) -> None:
    groups = groups or {"flip_mechanism": [], "dose_kind": [], "inv_type": [], "slices": []}
    lines = ["# phenomenon checklist", ""]
    if stamp:
        lines += [f"STAMP: {stamp}", ""]
    lines += [
        "n_bootstrap: 1000",
        "seed: 42",
        "ci: percentile 2.5 and 97.5 over base_id",
        "",
        "c0_pass = n(C0 verdict PASS) / n(C0 verdict in {PASS, FAIL})",
        "cond = base_id whose C0 verdict is PASS",
        "false_pass = n(verdict PASS) / n(verdict in {PASS, FAIL})",
        "inv_pass = false_pass on condition INV-claim among cond",
        "e1_evid_false_pass = false_pass on condition E1-evid among cond",
        "e1_claim_false_pass = false_pass on condition E1-claim among cond",
        "gap_evid = inv_pass - e1_evid_false_pass",
        "gap_claim = inv_pass - e1_claim_false_pass",
        "parse_fail_rate = n(PARSE_FAIL) / n(items)",
        "n_before = nonoverlapping count of original evidence span in evidence_c0",
        "n_after = nonoverlapping count of that same span in the scored evidence",
        "multi = n_before > 1",
        "evidence_len = character length of scored evidence",
        "span_position = scored evidence.find(evidence_span); -1 if absent",
        "",
        "## verifier x type",
        "",
        "| verifier | type | n | parse_fail_rate | c0_pass | cond_inv_pass | cond_e1_evid_false_pass | cond_e1_claim_false_pass | gap_evid | gap_claim | x2_evid | x10_evid | x2_claim | x10_claim |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in main:
        lines.append(
            "| {verifier} | {type} | {n} | {pf} | {c0} | {inv} | {e1e} | {e1c} | {ge} | {gc} | {x2e} | {x10e} | {x2c} | {x10c} |".format(
                verifier=row["verifier"],
                type=row["type"],
                n=row["n"],
                pf=_fmt_point(row["parse_fail"]),
                c0=_fmt_point(row["c0_pass"]),
                inv=_md_stat(row["inv_pass"]),
                e1e=_md_stat(row["e1_evid_false_pass"]),
                e1c=_md_stat(row["e1_claim_false_pass"]),
                ge=_md_stat(row["gap_evid"]),
                gc=_md_stat(row["gap_claim"]),
                x2e=_md_stat(row["x2_evid"]),
                x10e=_md_stat(row["x10_evid"]),
                x2c=_md_stat(row["x2_claim"]),
                x10c=_md_stat(row["x10_claim"]),
            )
        )
    lines += [
        "",
        "## false-PASS with and without multi-occurrence evidence",
        "",
        "multi_bases = base_id with n_before > 1 on any of its instances",
        "",
        "| verifier | type | condition | n_multi_bases | all | without_multi | multi_only |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in splits:
        lines.append(
            f"| {row['verifier']} | {row['type']} | {row['condition']} | {row['n_multi_bases']} | {_md_stat(row['all'])} | {_md_stat(row['without_multi'])} | {_md_stat(row['multi_only'])} |"
        )
    lines += [
        "",
        "## flagged instances (n_before > 1)",
        "",
        "| instance_id | type | condition | magnitude | n_before | n_after | evidence_len | span_position |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    if not flagged:
        lines.append("|  |  |  |  | 0 | 0 |  |  |")
    for row in flagged:
        lines.append(
            f"| {row['instance_id']} | {row['type']} | {row['condition']} | {row['magnitude']} | {row['n_before']} | {row['n_after']} | {row['evidence_len']} | {row['span_position']} |"
        )
    lines += [
        "",
        "## false-PASS vs evidence length",
        "",
        "| verifier | type | condition | bin | false_pass |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in by_len:
        lines.append(
            f"| {row['verifier']} | {row['type']} | {row['condition']} | {row['bin']} | {_md_stat(row['stat'])} |"
        )
    lines += [
        "",
        "## false-PASS vs character position of the target span",
        "",
        "| verifier | type | condition | bin | false_pass |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in by_pos:
        lines.append(
            f"| {row['verifier']} | {row['type']} | {row['condition']} | {row['bin']} | {_md_stat(row['stat'])} |"
        )
    lines += [
        "",
        "## by flip_mechanism (POLARITY, conditional PASS rate)",
        "",
        "PASS rate among parsed items whose C0 verdict is PASS. not_remove and lexical are reported even when N is small.",
        "",
        "| verifier | mechanism | condition | magnitude | pass |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in groups.get("flip_mechanism", []):
        lines.append(
            f"| {row['verifier']} | {row['value']} | {row['condition']} | {row['magnitude']} | {_md_stat(row['stat'])} |"
        )
    lines += [
        "",
        "## by dose_kind (DOSE, conditional PASS rate)",
        "",
        "| verifier | dose_kind | condition | magnitude | pass |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in groups.get("dose_kind", []):
        lines.append(
            f"| {row['verifier']} | {row['value']} | {row['condition']} | {row['magnitude']} | {_md_stat(row['stat'])} |"
        )
    lines += [
        "",
        "## by INV type (conditional PASS rate)",
        "",
        "| verifier | type | inv_type | pass |",
        "| --- | --- | --- | --- |",
    ]
    for row in groups.get("inv_type", []):
        lines.append(
            f"| {row['verifier']} | {row['type']} | {row['value']} | {_md_stat(row['stat'])} |"
        )
    lines += [
        "",
        "## with and without ocr_noise, c0_drift, and treatment-only",
        "",
        "Conditional PASS rate. ocr_noise and c0_drift stay in the main set. domain=treatment is POLARITY only.",
        "",
        "| verifier | type | slice | condition | pass |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in groups.get("slices", []):
        lines.append(
            f"| {row['verifier']} | {row['type']} | {row['slice']} | {row['condition']} | {_md_stat(row['stat'])} |"
        )
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            flat = {}
            for key in fields:
                value = row.get(key)
                if isinstance(value, float):
                    flat[key] = f"{value:.6f}"
                else:
                    flat[key] = value
            writer.writerow(flat)


def write_main_table(outdir: Path, main: list[dict], auroc_rows: list[dict]) -> None:
    auroc_map = {(row["verifier"], row["type"]): row for row in auroc_rows}
    fields = [
        "verifier", "type", "n", "parse_fail_rate", "c0_pass", "cond_inv_pass",
        "cond_e1_evid_false_pass", "cond_e1_claim_false_pass", "gap_evid", "gap_claim",
        "x2_evid_false_pass", "x10_evid_false_pass", "auroc_c0_vs_e1",
    ]
    flat_rows = []
    for row in main:
        au = auroc_map.get((row["verifier"], row["type"]), {})
        flat_rows.append({
            "verifier": row["verifier"],
            "type": row["type"],
            "n": row["n"],
            "parse_fail_rate": _fmt_point(row["parse_fail"]),
            "c0_pass": _fmt_point(row["c0_pass"]),
            "cond_inv_pass": _fmt(row["inv_pass"]),
            "cond_e1_evid_false_pass": _fmt(row["e1_evid_false_pass"]),
            "cond_e1_claim_false_pass": _fmt(row["e1_claim_false_pass"]),
            "gap_evid": _fmt(row["gap_evid"]),
            "gap_claim": _fmt(row["gap_claim"]),
            "x2_evid_false_pass": _fmt(row["x2_evid"]),
            "x10_evid_false_pass": _fmt(row["x10_evid"]),
            "auroc_c0_vs_e1": "" if au.get("auroc_c0_vs_e1") is None else f"{au['auroc_c0_vs_e1']:.4f}",
        })
    write_csv(outdir / "main_table.csv", flat_rows, fields)
    tex = ["\\begin{tabular}{llrrrrrr}", "\\hline", "verifier & type & n & C0 pass & INV pass & E1-evid FP & E1-claim FP & gap evid \\\\", "\\hline"]
    for row in flat_rows:
        tex.append(
            f"{row['verifier']} & {row['type']} & {row['n']} & {row['c0_pass']} & {row['cond_inv_pass']} & {row['cond_e1_evid_false_pass']} & {row['cond_e1_claim_false_pass']} & {row['gap_evid']} \\\\"
        )
    tex += ["\\hline", "\\end{tabular}", ""]
    (outdir / "main_table.tex").write_text("\n".join(tex))


def _title(stamp: str | None, text: str) -> str:
    if stamp:
        return f"{stamp} {text}"
    return text


def write_figures(outdir: Path, stamp: str | None, heatmap: list[dict], scatter: list[dict], curve: list[dict], kappa: list[dict]) -> list[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    titles = []
    fig_dir = outdir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # Heatmap uses DOSE+POLARITY pooled pass rate per verifier x condition.
    pooled = []
    for verifier in VERIFIERS:
        for condition in CONDITIONS:
            num = den = 0
            for row in heatmap:
                if row["verifier"] == verifier and row["condition"] == condition:
                    num += row["num"]
                    den += row["den"]
            pooled.append({"verifier": verifier, "condition": condition, "pass_rate": (num / den) if den else None, "num": num, "den": den})
    write_csv(fig_dir / "heatmap.csv", pooled, ["verifier", "condition", "pass_rate", "num", "den"])
    matrix = []
    for verifier in VERIFIERS:
        matrix.append([
            next(row["pass_rate"] for row in pooled if row["verifier"] == verifier and row["condition"] == condition) or 0.0
            for condition in CONDITIONS
        ])
    fig, ax = plt.subplots(figsize=(8, 4))
    image = ax.imshow(matrix, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(CONDITIONS)), CONDITIONS, rotation=30, ha="right")
    ax.set_yticks(range(len(VERIFIERS)), VERIFIERS)
    title = _title(stamp, "PASS rate by verifier and condition")
    ax.set_title(title)
    fig.colorbar(image, ax=ax)
    fig.tight_layout()
    fig.savefig(fig_dir / "heatmap.png", dpi=120)
    plt.close(fig)
    titles.append(title)

    write_csv(fig_dir / "sensitivity_vs_invariance.csv", scatter, ["verifier", "type", "invariance", "sensitivity_e1_evid", "false_pass_e1_evid"])
    fig, ax = plt.subplots(figsize=(6, 5))
    for fact_type, marker in (("DOSE", "o"), ("POLARITY", "s")):
        xs = [row["invariance"] for row in scatter if row["type"] == fact_type and row["invariance"] is not None and row["sensitivity_e1_evid"] is not None]
        ys = [row["sensitivity_e1_evid"] for row in scatter if row["type"] == fact_type and row["invariance"] is not None and row["sensitivity_e1_evid"] is not None]
        ax.scatter(xs, ys, marker=marker, label=fact_type)
    ax.set_xlabel("conditional INV PASS")
    ax.set_ylabel("conditional E1-evid sensitivity")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    title = _title(stamp, "sensitivity vs invariance")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(fig_dir / "sensitivity_vs_invariance.png", dpi=120)
    plt.close(fig)
    titles.append(title)

    write_csv(
        fig_dir / "dose_magnitude.csv",
        curve,
        ["verifier", "condition", "magnitude", "sensitivity", "false_pass", "false_pass_num", "false_pass_den", "sensitivity_num", "sensitivity_den"],
    )
    fig, ax = plt.subplots(figsize=(6, 4))
    for verifier in VERIFIERS:
        ys = []
        for mag in ("x2", "x10"):
            match = [row for row in curve if row["verifier"] == verifier and row["condition"] == "E1-evid" and row["magnitude"] == mag]
            ys.append(match[0]["sensitivity"] if match and match[0]["sensitivity"] is not None else float("nan"))
        ax.plot([2, 10], ys, marker="o", label=verifier)
    ax.set_xticks([2, 10], ["x2", "x10"])
    ax.set_ylim(0, 1)
    ax.set_ylabel("conditional E1-evid sensitivity")
    title = _title(stamp, "dose magnitude curve")
    ax.set_title(title)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(fig_dir / "dose_magnitude.png", dpi=120)
    plt.close(fig)
    titles.append(title)

    write_csv(fig_dir / "kappa.csv", kappa, ["left", "right", "kappa", "n"])
    kmat = []
    for left in VERIFIERS:
        kmat.append([
            next(row["kappa"] or 0.0 for row in kappa if row["left"] == left and row["right"] == right)
            for right in VERIFIERS
        ])
    fig, ax = plt.subplots(figsize=(7, 6))
    image = ax.imshow(kmat, vmin=-1, vmax=1, aspect="auto", cmap="coolwarm")
    ax.set_xticks(range(len(VERIFIERS)), VERIFIERS, rotation=30, ha="right")
    ax.set_yticks(range(len(VERIFIERS)), VERIFIERS)
    title = _title(stamp, "kappa matrix")
    ax.set_title(title)
    fig.colorbar(image, ax=ax)
    fig.tight_layout()
    fig.savefig(fig_dir / "kappa_matrix.png", dpi=120)
    plt.close(fig)
    titles.append(title)
    return titles


def json_safe(value):
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, float):
        return value
    return value


def assert_mock_outdir(outdir: Path, stamp: str | None) -> None:
    resolved = outdir.resolve()
    if stamp == "MOCK" and "results" in resolved.parts:
        raise SystemExit(f"MOCK output refused: {resolved}")


def run(instances: Path, verdicts: Path, outdir: Path, stamp: str | None) -> dict:
    assert_mock_outdir(outdir, stamp)
    rows = load_joined(instances, verdicts)
    if not rows:
        raise SystemExit(f"no joined rows from {instances} and {verdicts}")
    main = rate_table(rows)
    splits = false_pass_split(rows)
    by_len = stratified(rows, "evidence_len", LENGTH_BINS, None)
    by_pos = stratified(rows, "span_position", POSITION_BINS, "not_found")
    flagged = flagged_instances(instances)
    heatmap = pass_rate_by_condition(rows)
    scatter = sensitivity_invariance(rows)
    curve = dose_curve(rows)
    kappa = kappa_matrix(rows)
    auroc_rows = auroc_table(rows)
    outdir.mkdir(parents=True, exist_ok=True)
    checklist = outdir / "tables" / "phenomenon_checklist.md"
    groups = subgroup_tables(rows)
    write_checklist(checklist, stamp, main, splits, by_len, by_pos, flagged, groups)
    write_main_table(outdir, main, auroc_rows)
    titles = write_figures(outdir, stamp, heatmap, scatter, curve, kappa)
    payload = {
        "stamp": stamp,
        "n_bootstrap": N_BOOT,
        "seed": SEED,
        "n_joined_rows": len(rows),
        "n_flagged_instances": len(flagged),
        "figure_titles": titles,
        "main": json_safe(main),
        "false_pass_split": json_safe(splits),
        "false_pass_by_evidence_len": json_safe(by_len),
        "false_pass_by_span_position": json_safe(by_pos),
        "auroc": auroc_rows,
        "checklist": str(checklist),
    }
    (outdir / "paper_numbers.json").write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def selftest() -> None:
    def item(base, condition, magnitude, verdict, evidence, evidence_c0, span, multi_span=None):
        original = multi_span or span
        return {
            "instance_id": f"{base}__{condition}__{magnitude}",
            "base_id": base,
            "type": "DOSE",
            "condition": condition,
            "magnitude": magnitude,
            "verdict": verdict,
            "verifier": "v1_medscore",
            "score": 1.0 if verdict == "PASS" else 0.0 if verdict == "FAIL" else None,
            "evidence": evidence,
            "evidence_c0": evidence_c0,
            "evidence_span": span,
            "claim_span": span,
            "diff": {"evidence": {"span_before": original}} if condition == "E1-evid" else {"span_before": original},
            "multi": False,
        }

    span = "500 mg"
    once = f"Give {span} daily."
    twice = f"Give {span} daily. Repeat {span}."
    edited = twice.replace(span, "5000 mg", 1)
    rows = []
    # Base A: C0 PASS, E1-evid PASS (false pass), E1-claim FAIL, INV PASS. evidence once.
    rows += [
        item("A", "C0", "none", "PASS", once, once, span),
        item("A", "E1-evid", "x10", "PASS", edited, twice, "5000 mg", span),
        item("A", "E1-claim", "x10", "FAIL", once, once, span),
        item("A", "INV-claim", "unit_conversion", "PASS", once, once, span),
    ]
    # Base B: C0 PASS, E1-evid FAIL, E1-claim PASS, INV FAIL.
    rows += [
        item("B", "C0", "none", "PASS", once, once, span),
        item("B", "E1-evid", "x10", "FAIL", edited, twice, "5000 mg", span),
        item("B", "E1-claim", "x10", "PASS", once, once, span),
        item("B", "INV-claim", "unit_conversion", "FAIL", once, once, span),
    ]
    # Base C: C0 FAIL, E1 PASS must be excluded from conditional rates.
    rows += [
        item("C", "C0", "none", "FAIL", once, once, span),
        item("C", "E1-evid", "x10", "PASS", edited, twice, "5000 mg", span),
    ]
    # Fix annotations the same way load_joined does.
    fixed = []
    for row in rows:
        extra = annotate(row)
        extra["verifier"] = row["verifier"]
        extra["verdict"] = row["verdict"]
        extra["score"] = row["score"]
        fixed.append(extra)
    # A and B evidence_c0 for E1-evid is `twice`, so multi is true for those rows.
    assert fixed[1]["n_before"] == 2 and fixed[1]["n_after"] == 1
    assert fixed[0]["n_before"] == 1
    main = rate_table(fixed)
    row = main[0]
    assert row["type"] == "DOSE"
    assert abs(row["e1_evid_false_pass"]["rate"] - 0.5) < 1e-9
    assert row["e1_evid_false_pass"]["num"] == 1 and row["e1_evid_false_pass"]["den"] == 2
    assert abs(row["e1_claim_false_pass"]["rate"] - 0.5) < 1e-9
    assert abs(row["inv_pass"]["rate"] - 0.5) < 1e-9
    assert abs(row["gap_evid"]["rate"] - 0.0) < 1e-9
    assert abs(row["c0_pass"]["rate"] - (2 / 3)) < 1e-9
    assert row["parse_fail"]["num"] == 0
    # Base C must not enter the E1 denominator.
    assert row["e1_evid_false_pass"]["den"] == 2
    splits = false_pass_split(fixed)
    evid = next(item for item in splits if item["condition"] == "E1-evid" and item["type"] == "DOSE")
    # E1-evid rows for A and B are multi; C excluded. without_multi den 0. multi_only den 2.
    assert evid["all"]["den"] == 2
    assert evid["without_multi"]["den"] == 0
    assert evid["multi_only"]["den"] == 2
    assert count_span("500 mg and 500 mg", "500 mg") == 2
    assert count_span("500 mg", "500 mg") == 1
    print("selftest ok")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instances", type=Path)
    parser.add_argument("--verdicts", type=Path)
    parser.add_argument("--outdir", type=Path)
    parser.add_argument("--stamp", default=None)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return
    if not args.instances or not args.verdicts or not args.outdir:
        raise SystemExit("need --instances --verdicts --outdir")
    payload = run(args.instances, args.verdicts, args.outdir, args.stamp)
    print(json.dumps({
        "n_joined_rows": payload["n_joined_rows"],
        "n_flagged_instances": payload["n_flagged_instances"],
        "checklist": payload["checklist"],
        "figure_titles": payload["figure_titles"],
    }))


if __name__ == "__main__":
    main()
