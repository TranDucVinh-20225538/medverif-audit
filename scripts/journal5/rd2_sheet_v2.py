#!/usr/bin/env python3
"""(RD2 amendment 1, A3) Blinded adjudication sheet v2 with a priority subset P1.

Selection (a superset of the pre-registered rd2_adjudication_sheet.py rule and of its 1,845 rows):
  census (inclusion probability 1):
    - every answer that is NOT "correct" under the pre-registered labels (v1) OR under the v2 labels
      (incl. match_other_context, time_ambiguous, unverifiable and all 72 v1 no_dose answers),
    - every answer flagged by the frozen basis check (full variant),
  sample (inclusion probability 0.1):
    - answers "correct" under BOTH label sets and not basis-flagged: exactly the members of this set that the
      pre-registered control draw selected (random.Random(20261002).sample of k = round(0.10 * 4,270) = 427 out of the
      4,270 pre-registered "rest" rows, i.e. every rest row had inclusion probability 427/4,270 = 0.1).  The
      pre-registered draw is REPRODUCED here from extract_rows.jsonl + basis_check/per_item.jsonl and checked
      row-by-row against the committed blinded v1 sheet (question + answer text); the v1 key file is never read.

Strata (for weights): (v2 class x condition), with "correct" split into correct_sampled (pi = 0.1) and
correct_census (pi = 1: correct under v2 but not v1, or basis-flagged), plus the no_dose_v1 stratum (all 72 answers
that v1 calls no_dose, whatever their v2 class).  Weight = 1 / pi.

P1 (seed 20261005, drawn here before anything is sent): 120 v2 unit/basis errors (all grounded; closed allocated
proportionally to unit vs basis), 40 correct from the 10% sample (proportional to closed/grounded), 20 value errors
(proportional), 20 others (5 each from match_other_context / time_ambiguous / unverifiable / no_dose_v1).
Overlap set: 50 rows inside P1 for a second rater (30 unit/basis, 10 correct, 5 value, 5 other; seed 20261005).

Sheet order: P1 rows first (shuffled within P1), then the rest (shuffled).  Sheet columns: row_id, question,
label_excerpt, answer + the pre-registered rating columns.  No generator, condition, class, verdict, basis flag or
selection source.

Outputs: results/journal5/rd2/amend1/rd2_adjudication_sheet_v2.csv, sheet_strata.md, sheet_manifest.json;
results/journal5/rd2/qc/rd2_adjudication_key_v2.csv (protected; NOT committed until adjudication is complete).
Usage:  python scripts/journal5/rd2_sheet_v2.py
"""

from __future__ import annotations

import csv
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rd2_common import RD2, RD2_DIR, SEED, read_jsonl, sha256_file  # noqa: E402

AM = RD2_DIR / "amend1"
QC = RD2_DIR / "qc"
SHEET_V1 = QC / "rd2_adjudication_sheet.csv"
SHEET_V2 = AM / "rd2_adjudication_sheet_v2.csv"
KEY_V2 = QC / "rd2_adjudication_key_v2.csv"
P1_SEED = 20261005
A_CLASSES = ("unit_error", "basis_error", "value_error", "time_ambiguous", "unverifiable")  # pre-registered source A
HUMAN_COLS = ["human_answer_dose_is_error (Y/N/unclear)",
              "human_error_type (unit/basis/value/time/other_population_or_indication/none)",
              "human_correct_dose_for_slot", "note", "adjudicator_initials"]  # pre-registered rating columns
UNIT_TYPE = ("unit_error", "basis_error")
OTHER_GROUPS = ("match_other_context", "time_ambiguous", "unverifiable", "no_dose_v1")


def reproduce_v1(rows: dict, bc: dict):
    """Pre-registered selection (rd2_adjudication_sheet.py, seed 20261002) -> (order, sources, rest, k)."""
    dose = {i: r for i, r in rows.items() if r["auto_class"] != "no_dose"}
    src = {}
    for iid, r in dose.items():
        s = []
        if r["auto_class"] in A_CLASSES:
            s.append("A_auto")
        if bc.get(iid, {}).get("flag_full"):
            s.append("B_basis_flag")
        if s:
            src[iid] = s
    rest = sorted(i for i in dose if i not in src)
    rng = random.Random(SEED)
    k = min(len(rest), max(150, int(round(0.10 * len(rest)))))
    for iid in rng.sample(rest, k):
        src[iid] = ["C_control"]
    order = sorted(src)
    rng.shuffle(order)
    return order, src, rest, k


def check_against_v1_sheet(order: list, rows: dict) -> int:
    with SHEET_V1.open(encoding="utf-8-sig") as fh:
        sheet = list(csv.DictReader(fh))
    if len(sheet) != len(order):
        raise SystemExit("reproduced v1 selection has %d rows, committed sheet %d" % (len(order), len(sheet)))
    for i, (iid, s) in enumerate(zip(order, sheet)):
        r = rows[iid]
        if (s["check_id"], s["question"], s["answer"]) != ("RD2Q%04d" % i, r["question"], r["answer"]):
            raise SystemExit("reproduced v1 selection differs from the committed sheet at row %d" % i)
    return len(sheet)


def alloc(total: int, sizes: dict) -> dict:
    """Largest-remainder proportional allocation, capped at stratum size."""
    n = sum(sizes.values())
    raw = {k: total * v / n for k, v in sizes.items()} if n else {}
    out = {k: min(sizes[k], int(raw[k])) for k in sizes}
    for k in sorted(sizes, key=lambda k: -(raw[k] - int(raw[k]))):
        if sum(out.values()) >= total:
            break
        if out[k] < sizes[k]:
            out[k] += 1
    return out


def main() -> None:
    rows = {r["instance_id"]: r for r in read_jsonl(RD2 / "extract_rows.jsonl")}
    lab = {r["instance_id"]: r for r in read_jsonl(AM / "labels_v2.jsonl")}
    bc = {r["instance_id"]: r for r in read_jsonl(RD2_DIR / "basis_check" / "per_item.jsonl")}
    assert set(rows) == set(lab)
    order_v1, src_v1, rest_v1, k_v1 = reproduce_v1(rows, bc)
    n_v1 = check_against_v1_sheet(order_v1, rows)
    controls_v1 = {i for i, s in src_v1.items() if s == ["C_control"]}

    # ---- v2 selection
    info = {}
    for iid, l in lab.items():
        c1, c2, flag = l["class_v1"], l["class_v2"], bool(bc.get(iid, {}).get("flag_full"))
        both_correct = c1 == "correct" and c2 == "correct"
        if c1 == "no_dose":
            stratum, pi = "no_dose_v1", 1.0
        elif both_correct and not flag:
            stratum, pi = "correct_sampled|" + l["condition"], 0.1
        elif c2 == "correct":
            stratum, pi = "correct_census|" + l["condition"], 1.0
        else:
            stratum, pi = c2 + "|" + l["condition"], 1.0
        sel = pi == 1.0 or iid in controls_v1
        srcs = []
        if c1 != "correct":
            srcs.append("not_correct_v1")
        if c2 != "correct":
            srcs.append("not_correct_v2")
        if flag:
            srcs.append("basis_flag")
        if c1 == "no_dose":
            srcs.append("no_dose_v1")
        if pi < 1 and iid in controls_v1:
            srcs.append("sample10_prereg_draw")
        info[iid] = dict(stratum=stratum, pi=pi, selected=sel, sources="+".join(srcs), flag=flag, c1=c1, c2=c2,
                         cond=l["condition"], in_v1_sheet=iid in src_v1)
    sel = sorted(i for i, d in info.items() if d["selected"])
    assert set(src_v1) <= set(sel), "v2 sheet must contain every v1 sheet row"
    pop = Counter(d["stratum"] for d in info.values())
    smp = Counter(info[i]["stratum"] for i in sel)

    # ---- P1
    rng = random.Random(P1_SEED)

    def draw(pool, n):
        pool = sorted(pool)
        return rng.sample(pool, min(n, len(pool)))

    by = defaultdict(list)
    for i in sel:
        by[info[i]["stratum"]].append(i)
    p1, p1_group = [], {}
    ut_strata = {s: len(v) for s, v in by.items() if s.split("|")[0] in UNIT_TYPE}
    grounded_ut = [s for s in ut_strata if s.endswith("|grounded")]
    n_g = sum(ut_strata[s] for s in grounded_ut)
    a_ut = {s: ut_strata[s] for s in grounded_ut}
    a_ut.update(alloc(120 - n_g, {s: v for s, v in ut_strata.items() if s.endswith("|closed")}))
    corr = {s: len(v) for s, v in by.items() if s.startswith("correct_sampled|")}
    a_c = alloc(40, corr)
    val = {s: len(v) for s, v in by.items() if s.startswith("value_error|")}
    a_v = alloc(20, val)
    a_o = {}
    for g in OTHER_GROUPS:
        ss = {s: len(v) for s, v in by.items() if s.split("|")[0] == g}
        a_o.update(alloc(5, ss))
    allocation = {**a_ut, **a_c, **a_v, **a_o}
    group_of = {}
    for s in a_ut:
        group_of[s] = "unit_basis"
    for s in a_c:
        group_of[s] = "correct"
    for s in a_v:
        group_of[s] = "value"
    for s in a_o:
        group_of[s] = "other"
    for s, n in sorted(allocation.items()):
        for i in draw(by[s], n):
            p1.append(i)
            p1_group[i] = group_of[s]
    p1_set = set(p1)
    p1_n = Counter(info[i]["stratum"] for i in p1)
    # overlap set (second rater): 30 / 10 / 5 / 5 from the P1 groups
    overlap = set()
    for g, n in (("unit_basis", 30), ("correct", 10), ("value", 5), ("other", 5)):
        overlap |= set(draw([i for i in p1 if p1_group[i] == g], n))

    # ---- order + write
    p1_order = sorted(p1)
    rng.shuffle(p1_order)
    rest_order = sorted(i for i in sel if i not in p1_set)
    rng.shuffle(rest_order)
    order = p1_order + rest_order
    AM.mkdir(parents=True, exist_ok=True)
    with SHEET_V2.open("w", newline="", encoding="utf-8-sig") as fh, KEY_V2.open("w", newline="", encoding="utf-8-sig") as fk:
        w, wk = csv.writer(fh), csv.writer(fk)
        w.writerow(["row_id", "question", "label_excerpt", "answer"] + HUMAN_COLS)
        wk.writerow(["row_id", "instance_id", "sources", "class_v1", "subtype_v1", "class_v2", "subtype_v2", "basis_flag_full",
                     "basis_flag_strict", "generator", "answer_condition", "stratum", "pi", "weight", "N_stratum",
                     "n_stratum_sheet", "in_v1_sheet", "in_P1", "P1_group", "N_stratum_P1", "n_stratum_P1", "weight_P1",
                     "overlap50"])
        for n, iid in enumerate(order, 1):
            r, l, d = rows[iid], lab[iid], info[iid]
            rid = "RD2V2-%04d" % n
            w.writerow([rid, r["question"], r["excerpt"], r["answer"]] + [""] * len(HUMAN_COLS))
            inp1 = iid in p1_set
            st = d["stratum"]
            wk.writerow([rid, iid, d["sources"], l["class_v1"], l["subtype_v1"], l["class_v2"], l["subtype_v2"], d["flag"],
                         bool(bc.get(iid, {}).get("flag_strict")), l["generator"], l["condition"], st, d["pi"],
                         round(1 / d["pi"], 6), pop[st], smp[st], d["in_v1_sheet"], inp1, p1_group.get(iid, ""),
                         pop[st] if inp1 else "", p1_n[st] if inp1 else "",
                         round(pop[st] / p1_n[st], 6) if inp1 else "", iid in overlap])

    # ---- reconciliation with the v1 sheet
    v2_only = [i for i in sel if i not in src_v1]
    recon = Counter()
    for i in v2_only:
        d = info[i]
        if d["c1"] == "no_dose":
            recon["no_dose_v1 (excluded from the v1 sheet)"] += 1
        elif d["c1"] == "match_other_context":
            recon["match_other_context under v1, not drawn as v1 control"] += 1
        elif d["c1"] == "correct" and d["c2"] != "correct":
            recon["correct under v1, not correct under v2"] += 1
        else:
            recon["other: %s/%s" % (d["c1"], d["c2"])] += 1
    man = {"script": "scripts/journal5/rd2_sheet_v2.py", "seed_sample10": SEED, "seed_P1_overlap": P1_SEED,
           "v1_sheet_rows_reproduced": n_v1, "v1_rest": len(rest_v1), "v1_controls_k": k_v1,
           "sample10_pi": round(k_v1 / len(rest_v1), 6), "sheet_rows": len(order), "P1_rows": len(p1), "overlap_rows": len(overlap),
           "rows_added_vs_v1": len(v2_only), "rows_dropped_vs_v1": 0, "reconciliation": dict(recon),
           "population_by_stratum": dict(sorted(pop.items())), "sheet_by_stratum": dict(sorted(smp.items())),
           "P1_by_stratum": dict(sorted(p1_n.items())), "P1_by_group": dict(Counter(p1_group.values())),
           "P1_row_ids": "RD2V2-0001..RD2V2-%04d" % len(p1),
           "sha256": {"sheet_v2": sha256_file(SHEET_V2), "key_v2": sha256_file(KEY_V2), "sheet_v1": sha256_file(SHEET_V1),
                      "key_v1": sha256_file(QC / "rd2_adjudication_key.csv"), "labels_v2": sha256_file(AM / "labels_v2.jsonl")}}
    (AM / "sheet_manifest.json").write_text(json.dumps(man, indent=1) + "\n")

    md = ["# RD2 amendment 1 — adjudication sheet v2: strata and P1", "",
          "Generated by `scripts/journal5/rd2_sheet_v2.py`. Sheet: `results/journal5/rd2/amend1/rd2_adjudication_sheet_v2.csv` "
          "(%d rows; P1 = %s). Key v2 is in the protected qc/ location and is not committed until adjudication is complete." %
          (len(order), man["P1_row_ids"]), "",
          "Pre-registered v1 sheet: %d rows, reproduced exactly from the data (seed %d; rest %d, controls k = %d, inclusion "
          "probability %.3f). Every v1 row is in the v2 sheet; %d rows added, 0 dropped." %
          (n_v1, SEED, len(rest_v1), k_v1, k_v1 / len(rest_v1), len(v2_only)), "",
          "| rows added vs v1 sheet | n |", "|---|---|"] + ["| %s | %d |" % kv for kv in sorted(recon.items())] + [
          "| **total added** | %d |" % len(v2_only), "", "## Strata", "",
          "| stratum (v2 class / condition) | population N | in sheet n | sampling fraction | weight | P1 n | P1 weight (N / P1 n) |",
          "|---|---|---|---|---|---|---|"]
    for st in sorted(pop):
        pf = smp[st] / pop[st] if pop[st] else 0
        md.append("| %s | %d | %d | %.3f | %s | %d | %s |" % (st, pop[st], smp[st], pf, "10" if st.startswith("correct_sampled")
                                                            else "1", p1_n[st], ("%.3f" % (pop[st] / p1_n[st])) if p1_n[st] else "–"))
    md += ["| **total** | %d | %d | | | %d | |" % (sum(pop.values()), len(order), len(p1)), "",
           "Weight (full sheet) = 1 / sampling fraction: 10 for correct_sampled (realised fraction n/N differs slightly from the "
           "design probability 0.1 because the pre-registered draw was a simple random sample of the 4,270-row v1 rest), 1 elsewhere.", "",
           "## P1 allocation (seed %d)" % P1_SEED, "",
           "| group | target | drawn |", "|---|---|---|",
           "| unit/basis errors (v2; all grounded, closed proportional to unit vs basis) | 120 | %d |" % man["P1_by_group"].get("unit_basis", 0),
           "| automatically correct (from the 10%% sample, proportional to condition) | 40 | %d |" % man["P1_by_group"].get("correct", 0),
           "| value errors (proportional to condition) | 20 | %d |" % man["P1_by_group"].get("value", 0),
           "| other context / timing / unverifiable / no-dose (5 each) | 20 | %d |" % man["P1_by_group"].get("other", 0),
           "| **total** | 200 | %d |" % len(p1), "",
           "Strata not represented in P1 (handled in the full-sheet analysis only): " +
           (", ".join("%s (N = %d)" % (s, pop[s]) for s in sorted(pop) if not p1_n[s]) or "none") + ".", "",
           "Overlap set for a second rater: %d rows inside P1 (30 unit/basis, 10 correct, 5 value, 5 other)." % len(overlap), "",
           "## Lock", "", "- sha256(rd2_adjudication_sheet_v2.csv) = `%s`" % man["sha256"]["sheet_v2"],
           "- sha256(rd2_adjudication_key_v2.csv) = `%s`" % man["sha256"]["key_v2"],
           "- sha256(rd2_adjudication_key.csv, v1) = `%s`" % man["sha256"]["key_v1"]]
    (AM / "sheet_strata.md").write_text("\n".join(md) + "\n")
    print(json.dumps({k: v for k, v in man.items() if k not in ("population_by_stratum",)}, indent=1))


if __name__ == "__main__":
    main()
