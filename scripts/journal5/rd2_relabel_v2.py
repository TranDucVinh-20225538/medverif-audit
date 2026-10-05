#!/usr/bin/env python3
"""(RD2 amendment 1, A1/A2) v2 automatic labels: extended BSA-superscript surface pre-pass + the FROZEN classifier.

Why: openFDA flattens m<sup>2</sup> to "m 2".  The pre-registered repair (rd2_questions.repair_m2) only rewrites
"<lower-case unit>/m 2" with a word boundary before the unit, so "100mg/m 2", "International Units/m 2",
"1.2 grams per m 2", "400 mg per m 2" stay flattened in the label text and find_spans reads them as plain mg / units
(BSA basis lost).  Answers that state the same dose with a readable "/m2" are then auto-classified as per_m2 unit
errors (false positives); answers in "per m 2" / "sq m" style lose their basis the same way.

v2 = surface pre-pass (below) applied identically to the answer, the label target sentence, the excerpt and the
primary-target string, then scripts/journal2/rd_extract.classify UNCHANGED on top.  The pre-pass rewrites an
m-token to "m2" ONLY when it follows a dose unit + "/" or the word "per"; lengths ("2 m"), drug names / codes
containing "m2" and all other text are untouched.

A2 (no-dose recovery) is applied ONLY to answers the frozen classifier calls no_dose, so it cannot change any
other label: "N million units" -> "<N*10^6> units" and "N, unit: <u>" -> "N <u>" (dose units outside the frozen
vocabulary -- fl oz, PE, microdrops, AUC, %, tablets -- stay no_dose and are reported as missed-but-unparseable).

Outputs (results/journal5/rd2/amend1/): labels_v2.jsonl (one row per answer, both label sets), relabel_diff.md,
relabel_manifest.json, nodose_rescan.jsonl, nodose_rescan.md
Usage:  python scripts/journal5/rd2_relabel_v2.py
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rd2_common import QUESTIONS, RD2, RD2_DIR, read_jsonl, sha256_file, write_jsonl  # noqa: E402
from rd_extract import ERRORS, classify  # noqa: E402  (frozen, unchanged)

OUT = RD2_DIR / "amend1"
CLASSES = ("correct", "unit_error", "basis_error", "value_error", "match_other_context", "time_ambiguous",
           "unverifiable", "no_dose")
UNIT_TYPE = ("unit_error", "basis_error")

_DOSE_UNIT = (r"(?:international\s+units|micrograms?|milligrams?|grams?|units?|mcg|µg|μg|ug|mg|gm|g|IU|U|mEq|meq|mmol|"
              r"mL|ml|ng)")
_M2_TOKEN = r"m\s*(?:2|²|\^\s*2)(?!\d|[.,]\d)"
_SQ = r"(?:sq\.?\s*m(?:eters?|etres?)?|square\s+m(?:eters?|etres?))\b"
# (1) "<dose unit> / m 2" (any case, digits may touch the unit: "100mg/m 2")
_RE_UNIT_SLASH = re.compile(rf"(?i)(?<![A-Za-z])({_DOSE_UNIT})\s*/\s*{_M2_TOKEN}")
# (2) "per m 2" / "per m^2" / "per m²"
_RE_PER = re.compile(rf"(?i)\bper\s+{_M2_TOKEN}")
# (3) "<dose unit>/sq m", "per sq m", "per square meters"
_RE_UNIT_SLASH_SQ = re.compile(rf"(?i)(?<![A-Za-z])({_DOSE_UNIT})\s*/\s*{_SQ}")
_RE_PER_SQ = re.compile(rf"(?i)\bper\s+{_SQ}")
# (4) markdown emphasis closing right after the dose unit: "**400 mg** per m 2"
_RE_EMPH = re.compile(rf"(?i)(?<![A-Za-z])({_DOSE_UNIT})[*_]{{1,2}}(?=\s*(?:/|per\s)\s*(?:{_M2_TOKEN}|{_SQ}))")


def patch_m2(text: str) -> str:
    """Extended BSA surface pre-pass (A1)."""
    if not text:
        return text
    t = _RE_EMPH.sub(lambda m: m.group(1), text)
    t = _RE_UNIT_SLASH.sub(lambda m: m.group(1) + "/m2", t)
    t = _RE_UNIT_SLASH_SQ.sub(lambda m: m.group(1) + "/m2", t)
    t = _RE_PER.sub("per m2", t)
    t = _RE_PER_SQ.sub("per m2", t)
    return t


_RE_MILLION = re.compile(r"(?i)(?<![\w.,/])(\d+(?:\.\d+)?)\s*(?:-|to)?\s*(\d+(?:\.\d+)?)?\s+million\s+(units?|IU)\b")
_RE_UNIT_COLON = re.compile(r"(?i)(?<![\w.,/])(\d+(?:\.\d+)?)\s*,\s*units?\s*:\s*(mg|mcg|g|mL|units?)\b")


def _mil(x: str) -> str:
    v = (Decimal(x) * Decimal(1000000)).normalize()
    return format(v, "f")


def recover_nodose(text: str) -> str:
    """A2 recovery pass (only for frozen no_dose answers)."""
    t = _RE_MILLION.sub(lambda m: (_mil(m.group(1)) + (" to " + _mil(m.group(2)) if m.group(2) else "") + " " + m.group(3)), text)
    t = _RE_UNIT_COLON.sub(lambda m: m.group(1) + " " + m.group(2), t)
    return t


def classify_v2(answer: str, target: str, excerpt: str, primary: str = None, frozen_class: str = None) -> dict:
    a = patch_m2(answer)
    if frozen_class == "no_dose":
        a = recover_nodose(a)
    return classify(a, patch_m2(target), patch_m2(excerpt), patch_m2(primary) if primary else primary)


def reason(o: dict, n: dict, row: dict, q: dict) -> str:
    pt = [f for f in ("answer", "target_sentence", "excerpt") if patch_m2(row[f] if f != "target_sentence" else q["target_sentence"]) !=
          (row[f] if f != "target_sentence" else q["target_sentence"])]
    if o["auto_class"] == "no_dose":
        return "A2 no-dose recovery: " + (n.get("primary") or "")
    where = "+".join({"answer": "answer", "target_sentence": "label target", "excerpt": "label excerpt"}[f] for f in pt) or "?"
    return "m2 pre-pass on %s: answer %r vs label %r" % (where, n.get("primary"), n.get("matched") or "")


def build():
    qs = {q["qid"]: q for q in read_jsonl(QUESTIONS)}
    rows = read_jsonl(RD2 / "extract_rows.jsonl")
    out, changed = [], []
    for r in rows:
        q = qs[r["qid"]]
        o = classify(r["answer"], q["target_sentence"], q["excerpt"], q.get("primary_target"))
        assert o["auto_class"] == r["auto_class"], r["instance_id"]  # frozen labels reproduce exactly
        n = classify_v2(r["answer"], q["target_sentence"], q["excerpt"], q.get("primary_target"), o["auto_class"])
        rec = {"instance_id": r["instance_id"], "qid": r["qid"], "drug": r["drug"], "generator": r["generator"],
               "condition": r["condition"], "class_v1": o["auto_class"], "subtype_v1": o.get("subtype", ""),
               "class_v2": n["auto_class"], "subtype_v2": n.get("subtype", ""), "primary_v1": o.get("primary", ""),
               "primary_v2": n.get("primary", ""), "matched_v2": n.get("matched", ""),
               "answer_patched": patch_m2(r["answer"]) != r["answer"],
               "label_patched": patch_m2(q["target_sentence"]) != q["target_sentence"] or patch_m2(q["excerpt"]) != q["excerpt"]}
        if (o["auto_class"], o.get("subtype")) != (n["auto_class"], n.get("subtype")):
            rec["reason"] = reason(o, n, r, q)
            changed.append(rec)
        out.append(rec)
    return out, changed


def nodose_rescan(rows: list) -> list:
    """A2: every frozen no_dose answer -> refusal / non-answer / dose present (parseable under v2 or not)."""
    ans = {r["instance_id"]: r for r in read_jsonl(RD2 / "extract_rows.jsonl")}
    refusal = re.compile(r"(?i)\b(can'?t provide|cannot provide|unable to (?:verify|provide)|not able to (?:provide|verify)|"
                         r"not aware|don'?t have|do not have|need to know)\b")
    not_in_label = re.compile(r"(?i)(does not (?:specify|contain|provide)|not explicitly stated|not part of)")
    dose_any = re.compile(r"(?i)(?<![\w.])\d+(?:\.\d+)?\s*(?:-|to)?\s*(?:\d+(?:\.\d+)?)?\s*"
                          r"(?:fluid\s+ounces|fl\.?\s*oz|PE\b|microdrops|tablets?|%|million\s+units|anti-Xa|,\s*unit:)"
                          r"|\bAUC\s*\d|\bdose is \d+(?:\.\d+)?\.")
    res = []
    for r in rows:
        if r["class_v1"] != "no_dose":
            continue
        a = ans[r["instance_id"]]["answer"]
        if r["class_v2"] != "no_dose":
            kind = "dose_parseable_v2"
        elif dose_any.search(a):
            kind = "dose_unparseable"
        elif refusal.search(a):
            kind = "refusal"
        elif not_in_label.search(a):
            kind = "states_no_dose_in_label"
        else:
            kind = "other_no_dose"
        res.append({"instance_id": r["instance_id"], "generator": r["generator"], "condition": r["condition"],
                    "rescan": kind, "class_v2": r["class_v2"], "subtype_v2": r["subtype_v2"], "primary_v2": r["primary_v2"],
                    "dose_text": (dose_any.search(a).group(0) if dose_any.search(a) else "")})
    return res


def table(rows: list, key: str) -> list:
    c = Counter((r[key], r["condition"]) for r in rows)
    lines = ["| class | closed | grounded | total |", "|---|---|---|---|"]
    for k in CLASSES:
        lines.append("| %s | %d | %d | %d |" % (k, c[(k, "closed")], c[(k, "grounded")], c[(k, "closed")] + c[(k, "grounded")]))
    lines.append("| **total** | %d | %d | %d |" % (sum(v for (k, d), v in c.items() if d == "closed"),
                                                   sum(v for (k, d), v in c.items() if d == "grounded"), len(rows)))
    return lines


def totals(rows: list, key: str) -> dict:
    c = Counter(r[key] for r in rows)
    return {"unit_error": c["unit_error"], "basis_error": c["basis_error"], "unit_type": c["unit_error"] + c["basis_error"],
            "value_error": c["value_error"], "correct": c["correct"],
            "others": sum(v for k, v in c.items() if k not in ("unit_error", "basis_error", "value_error", "correct")),
            "by_class": dict(sorted(c.items()))}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows, changed = build()
    write_jsonl(OUT / "labels_v2.jsonl", rows)
    nd = nodose_rescan(rows)
    write_jsonl(OUT / "nodose_rescan.jsonl", nd)
    t1, t2 = totals(rows, "class_v1"), totals(rows, "class_v2")
    trans = Counter("%s -> %s" % (r["class_v1"], r["class_v2"]) for r in changed if r["class_v1"] != r["class_v2"])
    sub_only = sum(1 for r in changed if r["class_v1"] == r["class_v2"])
    fp_unit = [r for r in changed if r["class_v1"] in UNIT_TYPE and r["class_v2"] not in UNIT_TYPE]
    man = {"script": "scripts/journal5/rd2_relabel_v2.py", "classifier": "scripts/journal2/rd_extract.classify (frozen, unchanged)",
           "answers": len(rows), "changed_items": len(changed), "class_changed": sum(trans.values()), "subtype_only_changed": sub_only,
           "transitions": dict(trans.most_common()), "unit_type_v1_to_non_unit_type_v2": len(fp_unit),
           "unit_type_removed_by_subtype_v1": dict(Counter(r["subtype_v1"] for r in fp_unit)),
           "unit_type_removed_grounded": sum(r["condition"] == "grounded" for r in fp_unit),
           "totals_v1": t1, "totals_v2": t2,
           "nodose": {"n": len(nd), **dict(Counter(r["rescan"] for r in nd)),
                      "by_generator": dict(Counter(r["generator"] for r in nd)),
                      "by_condition": dict(Counter(r["condition"] for r in nd)),
                      "parseable_v2_classes": dict(Counter(r["class_v2"] for r in nd if r["rescan"] == "dose_parseable_v2"))},
           "inputs_sha256": {"questions": sha256_file(QUESTIONS), "extract_rows": sha256_file(RD2 / "extract_rows.jsonl")}}
    (OUT / "relabel_manifest.json").write_text(json.dumps(man, indent=1) + "\n")
    md = ["# RD2 amendment 1 — v2 automatic labels (relabel diff)", "",
          "Generated by `scripts/journal5/rd2_relabel_v2.py`: extended BSA-superscript surface pre-pass on answer + label text, "
          "then the frozen `rd_extract.classify` unchanged. A2 no-dose recovery applies only to frozen no_dose answers.", "",
          "## Before (pre-registered extractor, v1)", ""] + table(rows, "class_v1") + ["", "## After (v2)", ""] + table(rows, "class_v2")
    md += ["", "## New totals (every class; each column sums to %d)" % len(rows), "",
           "| class | v1 (pre-registered) | v2 | change |", "|---|---|---|---|"]
    for k in CLASSES:
        a, b = t1["by_class"].get(k, 0), t2["by_class"].get(k, 0)
        md.append("| %s | %d | %d | %+d |" % (k, a, b, b - a))
    s1, s2 = sum(t1["by_class"].values()), sum(t2["by_class"].values())
    assert s1 == s2 == len(rows) and set(t1["by_class"]) | set(t2["by_class"]) <= set(CLASSES)
    md += ["| **total** | %d | %d | %+d |" % (s1, s2, s2 - s1), "",
           "Unit-type (unit + basis): v1 %d, v2 %d." % (t1["unit_type"], t2["unit_type"])]
    md += ["", "Changed items: %d (class changed %d, subtype only %d). Unit/basis (v1) -> not unit/basis (v2): %d (%s; grounded %d)."
           % (len(changed), sum(trans.values()), sub_only, len(fp_unit), ", ".join("%s %d" % kv for kv in
              sorted(man["unit_type_removed_by_subtype_v1"].items())), man["unit_type_removed_grounded"]), "",
           "Transitions: " + "; ".join("%s: %d" % kv for kv in trans.most_common()), "",
           "## Changed items", "", "| instance_id | v1 class (subtype) | v2 class (subtype) | reason |", "|---|---|---|---|"]
    for r in sorted(changed, key=lambda r: r["instance_id"]):
        md.append("| %s | %s (%s) | %s (%s) | %s |" % (r["instance_id"], r["class_v1"], r["subtype_v1"], r["class_v2"], r["subtype_v2"],
                                                     r["reason"].replace("|", "/")))
    (OUT / "relabel_diff.md").write_text("\n".join(md) + "\n")
    ndm = ["# RD2 amendment 1 — A2 no-dose rescan", "", "Generated by `scripts/journal5/rd2_relabel_v2.py` (rule-based; categories in "
           "precedence order: parseable under v2 > dose present but unit outside the frozen vocabulary > refusal > states the label "
           "has no dose > other).", "", "| category | n |", "|---|---|"]
    for k, v in Counter(r["rescan"] for r in nd).most_common():
        ndm.append("| %s | %d |" % (k, v))
    ndm += ["| **total** | %d |" % len(nd), "", "By generator: " + ", ".join("%s %d" % kv for kv in sorted(man["nodose"]["by_generator"].items())),
            "By condition: " + ", ".join("%s %d" % kv for kv in sorted(man["nodose"]["by_condition"].items())), "",
            "| instance_id | category | v2 class (subtype) | dose text |", "|---|---|---|---|"]
    for r in nd:
        ndm.append("| %s | %s | %s (%s) | %s |" % (r["instance_id"], r["rescan"], r["class_v2"], r["subtype_v2"],
                                                  (r["primary_v2"] or r["dose_text"]).replace("|", "/")))
    (OUT / "nodose_rescan.md").write_text("\n".join(ndm) + "\n")
    print(json.dumps({k: man[k] for k in ("answers", "changed_items", "class_changed", "subtype_only_changed", "transitions",
                                          "unit_type_v1_to_non_unit_type_v2", "unit_type_removed_by_subtype_v1",
                                          "unit_type_removed_grounded", "nodose")}, indent=1))
    print("v1", {k: t1[k] for k in ("unit_error", "basis_error", "value_error", "correct", "others")})
    print("v2", {k: t2[k] for k in ("unit_error", "basis_error", "value_error", "correct", "others")})


if __name__ == "__main__":
    main()
