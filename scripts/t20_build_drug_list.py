#!/usr/bin/env python3
"""T20 step 1: distinct medication names paired with dose spans (main + main_ext)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from text_utils import DOSE_RE, DRUG_RE  # noqa: E402

OUT = ROOT / "data/t20/drug_list.jsonl"
LABEL_DIR = ROOT / "data/t20/labels"
MANIFEST = ROOT / "notes/t20_drug_list_manifest.json"
TARGET = 80

GENERIC_SUFFIX = re.compile(
    r"\b([a-z][a-z0-9-]*(?:"
    r"cillin|mycin|cycline|prazole|dipine|sartan|statin|formin|xacin|navir|"
    r"mab|pril|olol|zepam|zosin|platin|taxel|nib|vir|azole|idine|amine|"
    r"metronidazole|acetaminophen|valacyclovir|amoxicillin|ampicillin|"
    r"ceftriaxone|azithromycin|ciprofloxacin|clarithromycin|vancomycin|"
    r"prednisone|warfarin|insulin|aspirin|folate|folic|ribavirin|acyclovir|"
    r"omeprazole|lisinopril|metoprolol|hydrochlorothiazide|furosemide|"
    r"ibuprofen|morphine|fentanyl|midazolam|lorazepam|levothyroxine|"
    r"doxycycline|fluconazole|albuterol|salbutamol|colchicine|allopurinol|"
    r"methotrexate|tamoxifen|finasteride|gabapentin|pregabalin|sertraline|"
    r"fluoxetine|quetiapine|risperidone|carbamazepine|phenytoin|valproate|"
    r"levetiracetam|lamotrigine|duloxetine|bupropion|haloperidol|lithium"
    r"))\b",
    re.I,
)
COMMA_DOSE = re.compile(r"\b([A-Za-z][a-z0-9-]{3,})\s*,\s*(?:\d|\~|\~)", re.I)
WITH_DRUG = re.compile(r"\b(?:with|of|using|receive|given|take|taking)\s+([a-z][a-z0-9-]{4,})\b", re.I)
CAP_NOUN = re.compile(r"\b([A-Z][a-z]{4,})\s+(?:is|are|was|were)\b")

STOP = frozenset(
    {
        "daily",
        "oral",
        "given",
        "patient",
        "patients",
        "adult",
        "adults",
        "dose",
        "doses",
        "treatment",
        "therapy",
        "women",
        "men",
        "children",
        "infants",
        "recommended",
        "standard",
        "initial",
        "maintenance",
        "single",
        "total",
        "about",
        "approximately",
        "body",
        "stores",
        "severe",
        "mild",
        "moderate",
        "history",
        "alternative",
        "safely",
        "hours",
        "times",
        "weeks",
        "months",
        "years",
        "day",
        "days",
        "week",
        "hour",
        "intravenous",
        "intravenously",
        "orally",
        "mg",
        "gram",
        "grams",
        "elemental",
        "supplemental",
        "low",
        "high",
        "maximum",
        "minimum",
        "usual",
        "typical",
        "average",
        "normal",
        "healthy",
        "study",
        "large",
        "small",
        "first",
        "second",
        "third",
        "fourth",
        "doses",
        "dosing",
        "dosage",
        "receive",
        "receiving",
        "treated",
        "treat",
        "used",
        "use",
        "using",
        "administered",
        "administration",
        "prophylaxis",
        "prevention",
        "infection",
        "disease",
        "disorder",
        "syndrome",
        "deficiency",
        "chronic",
        "acute",
        "primary",
        "secondary",
        "other",
        "some",
        "many",
        "most",
        "each",
        "every",
        "once",
        "twice",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "ten",
    }
)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open() if line.strip()]


def openfda_generics() -> set[str]:
    names: set[str] = set()
    if not LABEL_DIR.is_dir():
        return names
    for path in LABEL_DIR.glob("*.json"):
        try:
            doc = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        openfda = doc.get("openfda") or {}
        for key in ("generic_name", "brand_name", "substance_name"):
            for raw in openfda.get(key) or []:
                for part in re.split(r"[,;/]", str(raw)):
                    token = part.strip().lower()
                    if len(token) >= 4:
                        names.add(token)
    return names


def candidates_from_claim(claim: str) -> list[str]:
    out: list[str] = []
    if not DOSE_RE.search(claim):
        return out
    for pat in (COMMA_DOSE, WITH_DRUG, GENERIC_SUFFIX):
        for m in pat.finditer(claim):
            out.append(m.group(1).lower())
    for m in DRUG_RE.finditer(claim):
        out.append(m.group(0).lower())
    for m in CAP_NOUN.finditer(claim):
        out.append(m.group(1).lower())
    for m in DOSE_RE.finditer(claim):
        before = claim[max(0, m.start() - 70) : m.start()]
        words = re.findall(r"\b([a-z]{5,})\b", before.lower())
        for w in reversed(words):
            if w not in STOP:
                out.append(w)
                break
    return out


def collect_bases() -> list[dict]:
    rows: list[dict] = []
    paths = [
        ROOT / "data/main_ext/bases_main_ext.jsonl",
        ROOT / "data/v3/instances_main.jsonl",
    ]
    seen: set[str] = set()
    for path in paths:
        if not path.is_file():
            continue
        for row in read_jsonl(path):
            if row.get("type") != "DOSE":
                continue
            bid = row.get("base_id") or row.get("id")
            if not bid or bid in seen:
                continue
            if path.name.startswith("instances") and not row.get("valid", True):
                continue
            seen.add(str(bid))
            rows.append(row)
    return rows


def main() -> None:
    fda = openfda_generics()
    by_drug: dict[str, dict] = {}
    for base in collect_bases():
        claim = base.get("claim_c0") or base.get("claim") or ""
        bid = base.get("base_id") or base.get("id")
        for drug in candidates_from_claim(claim):
            if drug in STOP or len(drug) < 4:
                continue
            rec = by_drug.setdefault(
                drug,
                {
                    "drug": drug,
                    "bases": set(),
                    "example_claim": claim[:240],
                    "from_openfda_vocab": drug in fda,
                },
            )
            rec["bases"].add(str(bid))
    drugs = sorted(
        by_drug.values(),
        key=lambda r: (-len(r["bases"]), -int(r["from_openfda_vocab"]), r["drug"]),
    )
    if len(drugs) < TARGET:
        print(
            json.dumps(
                {
                    "warn": f"only {len(drugs)} drugs (target {TARGET}); widen patterns or fetch more labels",
                }
            ),
            flush=True,
        )
    picked = drugs[: max(TARGET, len(drugs))]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as handle:
        for rec in picked:
            handle.write(
                json.dumps(
                    {
                        "drug": rec["drug"],
                        "n_bases": len(rec["bases"]),
                        "bases": sorted(rec["bases"])[:10],
                        "from_openfda_vocab": rec["from_openfda_vocab"],
                        "example_claim": rec["example_claim"],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    manifest = {
        "target": TARGET,
        "distinct_drugs_found": len(by_drug),
        "written": len(picked),
        "openfda_vocab_size": len(fda),
        "path": str(OUT.relative_to(ROOT)),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
