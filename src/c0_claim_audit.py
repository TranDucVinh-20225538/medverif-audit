"""C0 claim checks: drug naming and target-sentence qualifier preservation."""

from __future__ import annotations

import re

C0_NO_DRUG_IN_EVIDENCE_OK = frozenset(
    {"D0002", "D0077", "D0081", "D0333", "D0351", "D0372"}
)

GENERIC_SUBJECT_RE = re.compile(
    r"^(It|They|This|That|The medication|The drug|The medicine)\b"
    r"|\b(the medication|the drug|this drug|this medication)\b",
    re.I,
)

DRUG_TOKEN_RE = re.compile(
    r"\b([a-z]{3,}(?:olol|pril|sartan|statin|cillin|mycin|cycline|prazole|dipine|"
    r"oxetine|parin|gliptin|formin|vir|mab|nib|tinib|zole|zolid|pam|pine|done|zine|"
    r"lam|navir|buvir|tegravir|afenib|ciclib|grastim|poetin|ximab|zumab|gnrh|afil|"
    r"gliflozin|semide|gliptin|lukast|setron|dronate|platin|taxel|ubicin|parin|"
    r"prednisone|prednisolone|succimer|amiloride|lurasidone|linezolid|ivermectin|"
    r"diethylcarbamazine|pramipexole|albendazole|telithromycin|haloperidol|naloxone|"
    r"amitriptyline|prasugrel|dexmedetomidine|voclosporin|sertraline|fulvestrant|"
    r"dabigatran|budesonide|pyrimethamine|leuprolide|cefazolin|sorafenib))\b",
    re.I,
)

ROUTE_POP_RE = re.compile(
    r"\b(subcutaneous(?:ly)?|intravenous(?:ly)?|intramuscular(?:ly)?|orally|oral(?:ly)?|"
    r"topical(?:ly)?|inhaled|intrathecal(?:ly)?|"
    r"pediatric|adult|children|neonat(?:e|al|es)|pregnant|elderly|"
    r"together with|in combination with)\b",
    re.I,
)

GENERIC_DRUG_WORDS = frozenset(
    {
        "medication",
        "medications",
        "drug",
        "drugs",
        "medicine",
        "medicines",
        "therapy",
        "agent",
        "agents",
        "vaccine",
        "vaccines",
    }
)


def _book_drug_hint(book: str | None) -> str | None:
    book = (book or "").strip()
    if not book or book in {"InternalMed_Harrison", "Pharmacology_Katzung"}:
        return None
    head = book.split("--")[0].strip()
    tok = head.split()[0]
    if len(tok) >= 4 and tok[0].isupper():
        return tok.lower()
    return None


def specific_drug_tokens(text: str) -> set[str]:
    names: set[str] = set()
    for match in DRUG_TOKEN_RE.finditer(text or ""):
        names.add(match.group(1).lower())
    return {n for n in names if n not in GENERIC_DRUG_WORDS}


def evidence_names_drug(base: dict) -> set[str]:
    ev = base.get("evidence") or ""
    tgt = base.get("target_sentence") or ""
    names = specific_drug_tokens(f"{ev} {tgt}")
    hint = _book_drug_hint(base.get("book"))
    if hint:
        names.add(hint)
    return names


def claim_names_drug(claim: str) -> set[str]:
    return specific_drug_tokens(claim or "")


def c0_missing_drug(base: dict) -> bool:
    if base.get("type") != "DOSE":
        return False
    if base.get("id") in C0_NO_DRUG_IN_EVIDENCE_OK:
        return False
    ev_drugs = evidence_names_drug(base)
    if not ev_drugs:
        return False
    claim = base.get("claim") or ""
    if ev_drugs & claim_names_drug(claim):
        return False
    if GENERIC_SUBJECT_RE.search(claim):
        return True
    if re.match(r"^(It|They)\b", claim.strip()):
        return True
    return "medication" in claim.lower() or "medicine" in claim.lower()


def c0_dropped_qualifier(base: dict) -> bool:
    tgt = base.get("target_sentence") or ""
    claim = base.get("claim") or ""
    tgt_q = {m.group(0).lower() for m in ROUTE_POP_RE.finditer(tgt)}
    cl_q = {m.group(0).lower() for m in ROUTE_POP_RE.finditer(claim)}
    return bool(tgt_q - cl_q)


def c0_regen_reasons(base: dict) -> list[str]:
    reasons: list[str] = []
    if c0_missing_drug(base):
        reasons.append("c0_missing_drug")
    if c0_dropped_qualifier(base):
        reasons.append("c0_dropped_qualifier")
    return reasons


def needs_c0_regen(base: dict) -> bool:
    return bool(c0_regen_reasons(base))
