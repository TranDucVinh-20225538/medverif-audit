"""CPU checks for span edits and the copied MedScore parser. Not a pilot result."""

from __future__ import annotations

from decimal import Decimal

from perturb import perturb_one
from text_utils import convert_dose_span, scale_dose_span
from v1_parser import released_parse_verification_output, study_verdict


def check(name: str, cond: bool) -> None:
    if not cond:
        raise SystemExit(f"FAIL {name}")
    print("ok", name)


def main() -> None:
    check("x2", scale_dose_span("20 mg", Decimal(2)) == "40 mg")
    check("x10", scale_dose_span("20 mg", Decimal(10)) == "200 mg")
    check("x2 decimal", scale_dose_span("0.25 mg", Decimal(2)) == "0.5 mg")
    check("inv mg", convert_dose_span("500 mg") == "0.5 g")
    check("inv g", convert_dose_span("1 g") == "1000 mg")
    check("inv nospace", convert_dose_span("250mg") == "0.25 g")
    check("inv tiny skipped", True)
    try:
        convert_dose_span("5 mg")
        check("5 mg has no natural unit", False)
    except ValueError:
        check("5 mg has no natural unit", True)
    try:
        convert_dose_span("2 mg/kg")
        check("2 mg/kg has no natural unit", False)
    except ValueError:
        check("2 mg/kg has no natural unit", True)

    evidence = "Adults may take 500 mg of ibuprofen. Stop if a rash appears."
    claim = "A common adult dose is 500 mg of ibuprofen."
    base = {
        "id": "D0001",
        "type": "DOSE",
        "evidence": evidence,
        "claim": claim,
        "target_span_evidence": "500 mg",
        "target_span_claim": "500 mg",
        "evidence_span_start": evidence.index("500 mg"),
        "evidence_span_end": evidence.index("500 mg") + len("500 mg"),
        "claim_span_start": claim.index("500 mg"),
        "claim_span_end": claim.index("500 mg") + len("500 mg"),
    }
    rows, failed = perturb_one(base)
    check("no fail", failed == [])
    by = {(r["condition"], r["magnitude"]): r for r in rows}
    check("n inst", len(rows) == 8)
    ev = by[("E1-evid", "x10")]
    check("e1 evid confined", "5000 mg" in ev["evidence"] and "500 mg" not in ev["evidence"])
    check("e1 evid claim same", ev["claim"] == claim)
    cl = by[("E1-claim", "x2")]
    check("e1 claim", "1000 mg" in cl["claim"] and cl["evidence"] == evidence)
    e2 = by[("E2", "x2")]
    check("e2 both", "1000 mg" in e2["claim"] and "1000 mg" in e2["evidence"])
    inv = by[("INV-claim", "unit_conversion")]
    check("inv text", "0.5 g" in inv["claim"] and inv["evidence"] == evidence)
    check("neighbors kept", "Stop if a rash appears." in ev["evidence"])

    evidence_p = "Clonidine should not be given to patients with depression."
    claim_p = "Patients with depression should not be given clonidine."
    # span must match verbatim; put the cue in the claim exactly once
    claim_p = "People with depression: clonidine should not be given."
    span = "should not be given"
    base_p = {
        "id": "P0001",
        "type": "POLARITY",
        "evidence": evidence_p,
        "claim": claim_p,
        "target_span_evidence": span,
        "target_span_claim": span,
        "evidence_span_start": evidence_p.index(span),
        "evidence_span_end": evidence_p.index(span) + len(span),
        "claim_span_start": claim_p.index(span),
        "claim_span_end": claim_p.index(span) + len(span),
    }
    rows_p, failed_p = perturb_one(base_p)
    check("pol fail", failed_p == [])
    by_p = {(r["condition"], r["magnitude"]): r for r in rows_p}
    check("flip evid", "should be given" in by_p[("E1-evid", "flip")]["evidence"])
    check("flip claim only", by_p[("E1-evid", "flip")]["claim"] == claim_p)
    check("not_remove", by_p[("E1-evid", "flip")]["flip_mechanism"] == "not_remove")
    check("e2 pol", "should be given" in by_p[("E2", "flip")]["claim"] and "should be given" in by_p[("E2", "flip")]["evidence"])

    cases = {
        "": (1.0, "PARSE_FAIL"),
        "True": (1.0, "PASS"),
        "False": (0.0, "FAIL"),
        "true.": (1.0, "PASS"),
        "not true": (1.0, "FAIL"),
        "This is not true": (1.0, "FAIL"),
        "The answer is not true.": (1.0, "FAIL"),
        "untrue": (1.0, "PARSE_FAIL"),
        "yes": (1.0, "PARSE_FAIL"),
        "no": (1.0, "PARSE_FAIL"),
        "The answer is true": (1.0, "PASS"),
        "false true": (1.0, "PASS"),
        "true false": (0.0, "FAIL"),
        "I cannot tell": (0.0, "PARSE_FAIL"),
        "unknown": (0.0, "PARSE_FAIL"),
        "maybe": (1.0, "PARSE_FAIL"),
    }
    for text, (released, study) in cases.items():
        got_r = released_parse_verification_output(text)
        got_s = study_verdict(text)
        check(f"released {text!r}", got_r == released)
        check(f"study {text!r}", got_s == study)
    out = []
    for text, (released, study) in cases.items():
        out.append({
            "input": text,
            "released_score": released_parse_verification_output(text),
            "study_verdict": study_verdict(text),
        })
    dest = __import__("pathlib").Path("/data2/hpcshared/medverif-audit/notes/v1_parser_checks.json")
    dest.write_text(__import__("json").dumps(out, indent=2) + "\n")
    print("all selftests passed")


if __name__ == "__main__":
    main()
