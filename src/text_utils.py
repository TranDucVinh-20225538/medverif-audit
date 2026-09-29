"""Rule helpers for dose/polarity extraction and span edits."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Iterable, List, Optional, Sequence, Tuple

# Case-sensitive units. A capital "G" in "1 G proteins" is not grams.
_UNIT = (
    r"(?:mg/kg/min|mg/kg/day|mg/kg/h|mcg/kg/min|mcg/kg/day|mg/kg|"
    r"mcg|µg|μg|mg|mL|ml|g|units|micrograms|milligrams|grams)"
)
DOSE_RE = re.compile(
    rf"(?<![\w./])(\d+(?:\.\d+)?)\s*({_UNIT})(?![\w/])"
)
RANGE_RE = re.compile(
    rf"(?<![\w./])\d+(?:\.\d+)?\s*[-–—]\s*\d+(?:\.\d+)?\s*{_UNIT}(?![\w/])"
)
DOSE_CONTEXT_RE = re.compile(
    r"\b(?:dose|doses|dosing|dosage|administer|administered|administration|"
    r"oral|orally|intravenous|intravenously|intramuscular|subcutaneous|"
    r"tablet|tablets|capsule|capsules|injection|infusion|daily|twice|"
    r"adults?|children|pediatric|recommended|patients?)\b",
    re.I,
)
# Longest cues first. "should not" alone is intentionally absent.
POLARITY_CUES: Tuple[str, ...] = (
    "should not be administered",
    "should not be given",
    "should not be used",
    "are not recommended",
    "is not recommended",
    "are not indicated",
    "is not indicated",
    "are contraindicated",
    "is contraindicated",
    "contraindicated in",
    "are indicated for",
    "is indicated for",
    "are recommended for",
    "is recommended for",
    "should be administered",
    "should be given",
    "should be used",
)
POLARITY_RE = re.compile(
    "|".join(re.escape(c) for c in POLARITY_CUES),
    re.I,
)
DRUG_RE = re.compile(
    r"\b(?:drug|drugs|medication|medications|medicine|medicines|"
    r"antibiotic|antibiotics|vaccine|vaccines|insulin|"
    r"antagonist|antagonists|agonist|agonists|inhibitor|inhibitors|"
    r"blocker|blockers|diuretic|diuretics|agent|agents|"
    r"\w{4,}(?:olol|pril|sartan|statin|cillin|mycin|cycline|prazole|"
    r"dipine|oxetine|parin|gliptin|formin))\b",
    re.I,
)
CALC_RE = re.compile(r"\d+(?:\.\d+)?\s*[×x]\s*\d")

# Mass-unit conversions. Rate/weight suffixes after the mass unit are kept.
_MASS_FACTOR = {
    "mg": ("g", Decimal("0.001")),
    "g": ("mg", Decimal("1000")),
    "mcg": ("mg", Decimal("0.001")),
    "µg": ("mg", Decimal("0.001")),
    "μg": ("mg", Decimal("0.001")),
    "micrograms": ("mg", Decimal("0.001")),
    "milligrams": ("g", Decimal("0.001")),
    "grams": ("mg", Decimal("1000")),
    "ml": ("L", Decimal("0.001")),
    "mL": ("L", Decimal("0.001")),
}

FLIP = {
    "should not be administered": "should be administered",
    "should not be given": "should be given",
    "should not be used": "should be used",
    "should be administered": "should not be administered",
    "should be given": "should not be given",
    "should be used": "should not be used",
    "are not recommended": "are recommended",
    "is not recommended": "is recommended",
    "are recommended for": "are not recommended for",
    "is recommended for": "is not recommended for",
    "are not indicated": "are indicated",
    "is not indicated": "is indicated",
    "are indicated for": "are contraindicated for",
    "is indicated for": "is contraindicated for",
    "are contraindicated": "are indicated",
    "is contraindicated": "is indicated",
    "contraindicated in": "indicated in",
}

# Syntax-preserving meaning-preserving swaps. The second LLM still has to agree.
# Decision G: equivalence rephrase INV (not flip).
POLARITY_REPHRASE_INV = {
    "should not be used": "is contraindicated",
    "is contraindicated": "should not be used",
}

# Equivalence rephrases for INV-claim (subset also used by inv_cue where applicable).
# Excluded: contraindicated ↔ not recommended / not indicated (clinically distinct).
INV_POLARITY = {
    "should not be administered": "must not be administered",
    "should not be given": "must not be given",
    "should not be used": "must not be used",
    "should be administered": "ought to be administered",
    "should be given": "ought to be given",
    "should be used": "ought to be used",
    "are recommended for": "are indicated for",
    "is recommended for": "is indicated for",
    "are indicated for": "are recommended for",
    "is indicated for": "is recommended for",
}

_ABBREV = (
    ("e.g.", "e<dot>g<dot>"),
    ("i.e.", "i<dot>e<dot>"),
    ("vs.", "vs<dot>"),
    ("Fig.", "Fig<dot>"),
    ("fig.", "fig<dot>"),
    ("Dr.", "Dr<dot>"),
    ("Mr.", "Mr<dot>"),
    ("Mrs.", "Mrs<dot>"),
    ("No.", "No<dot>"),
    ("approx.", "approx<dot>"),
)


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_sentences(text: str) -> List[str]:
    text = normalize_ws(text)
    if not text:
        return []
    for src, dst in _ABBREV:
        text = text.replace(src, dst)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    out = []
    for part in parts:
        for src, dst in _ABBREV:
            part = part.replace(dst, src)
        part = part.strip()
        if part:
            out.append(part)
    return out


def word_count(text: str) -> int:
    return len(text.split())


def looks_like_table(text: str) -> bool:
    upper = text.upper()
    return (
        "TABLE" in upper
        or "FIGURE" in upper
        or "FIG." in upper
        or "HTTP" in upper
        or "CHAPTER" in upper
    )


def dose_matches(text: str) -> List[re.Match]:
    return list(DOSE_RE.finditer(text))


def is_range_sentence(text: str) -> bool:
    return RANGE_RE.search(text) is not None


def convertible_unit(unit: str) -> Optional[Tuple[str, Decimal, str]]:
    """Return (new_mass_unit, factor, suffix) or None.

    suffix is whatever follows the mass unit, such as '/kg/min'.
    """
    for mass, (new_mass, factor) in sorted(_MASS_FACTOR.items(), key=lambda kv: -len(kv[0])):
        if unit == mass or unit.startswith(mass + "/"):
            suffix = unit[len(mass):]
            return new_mass, factor, suffix
    return None


def format_decimal(value: Decimal) -> str:
    quantized = value.normalize()
    text = format(quantized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in {"", "-0"}:
        text = "0"
    return text


def parse_decimal(text: str) -> Decimal:
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"not a decimal: {text}") from exc


def scale_dose_span(span: str, factor: Decimal) -> str:
    match = DOSE_RE.fullmatch(span.strip())
    if match is None:
        # fullmatch can fail if the span has no extra chars but group spacing differs
        match = DOSE_RE.search(span)
        if match is None or match.group(0) != span.strip():
            raise ValueError(f"span is not a single dose: {span!r}")
    number = parse_decimal(match.group(1))
    unit = match.group(2)
    new_number = number * factor
    # Rebuild with a single space, preserving the original unit string.
    return f"{format_decimal(new_number)} {unit}"


def expand_dose_numeric_bounds(text: str, start: int, end: int) -> Tuple[int, int]:
    """Expand [start, end) to the full dose token (number + unit) in text."""
    match = None
    for m in DOSE_RE.finditer(text):
        if m.start() <= start < m.end() or m.start() < end <= m.end() or (start <= m.start() and m.end() <= end):
            match = m
            break
    if match is None:
        return start, end
    return match.start(), match.end()


def scale_dose_in_context(text: str, start: int, end: int, factor: Decimal) -> Tuple[str, str]:
    s, e = expand_dose_numeric_bounds(text, start, end)
    old_span = text[s:e]
    new_span = scale_dose_span(old_span, factor)
    return replace_span(text, s, e, new_span), new_span


def normalize_micro_sign(text: str) -> str:
    return (text or "").replace("\u03bc", "\u00b5")


def _dose_span_parts(span: str) -> Tuple[str, str]:
    match = DOSE_RE.fullmatch(span.strip())
    if match is None:
        match = DOSE_RE.search(span)
        if match is None or match.group(0) != span.strip():
            raise ValueError(f"span is not a single dose: {span!r}")
    return match.group(1), match.group(2)


def unit_swap_numeral_fixed(span: str, direction: str) -> Optional[Tuple[str, str]]:
    """Replace mass/volume unit by one SI step; keep numeral. direction: up|down."""
    try:
        number, unit = _dose_span_parts(span)
    except ValueError:
        return None
    up_map = {
        "mcg": ("mg", "mcg→mg"),
        "µg": ("mg", "µg→mg"),
        "μg": ("mg", "μg→mg"),
        "micrograms": ("milligrams", "micrograms→milligrams"),
        "mg": ("g", "mg→g"),
        "milligrams": ("grams", "milligrams→grams"),
        "g": ("kg", "g→kg"),
        "grams": ("kilograms", "grams→kilograms"),
        "ml": ("L", "ml→L"),
        "mL": ("L", "mL→L"),
    }
    down_map = {
        "kg": ("g", "kg→g"),
        "kilograms": ("grams", "kilograms→grams"),
        "g": ("mg", "g→mg"),
        "grams": ("milligrams", "grams→milligrams"),
        "mg": ("mcg", "mg→mcg"),
        "milligrams": ("micrograms", "milligrams→micrograms"),
        "mcg": ("µg", "mcg→µg"),
        "L": ("mL", "L→mL"),
        "l": ("ml", "l→ml"),
    }
    mapping = up_map if direction == "up" else down_map
    if unit not in mapping:
        return None
    new_unit, pair = mapping[unit]
    return f"{number} {new_unit}", pair


def e1_unit_only_swap(span: str) -> Optional[Tuple[str, str]]:
    """×1000 unit error with numeral fixed (T7 E1-unit default direction)."""
    try:
        _, unit = _dose_span_parts(span)
    except ValueError:
        return None
    up = unit_swap_numeral_fixed(span, "up")
    down = unit_swap_numeral_fixed(span, "down")
    prefer_up = unit in {"mcg", "µg", "μg", "micrograms", "mg", "milligrams", "ml", "mL"}
    if prefer_up and up:
        return up
    if down:
        return down
    return up


# Common pairs only. The converted number must fall in [0.1, 1000].
_NATURAL_PAIRS = (
    ("mg/kg", "mcg/kg", Decimal("1000")),
    ("mcg/kg", "mg/kg", Decimal("0.001")),
    ("µg/kg", "mg/kg", Decimal("0.001")),
    ("μg/kg", "mg/kg", Decimal("0.001")),
    ("mg", "g", Decimal("0.001")),
    ("g", "mg", Decimal("1000")),
    ("mg", "mcg", Decimal("1000")),
    ("mcg", "mg", Decimal("0.001")),
    ("µg", "mg", Decimal("0.001")),
    ("μg", "mg", Decimal("0.001")),
    ("mL", "L", Decimal("0.001")),
    ("ml", "L", Decimal("0.001")),
    ("L", "mL", Decimal("1000")),
)


def rule_natural_unit_conversion_label(span: str) -> bool:
    """True if span has a rule-approved natural mass/volume conversion."""
    return natural_unit_conversion(span) is not None


def natural_unit_conversion(span: str) -> Optional[str]:
    """Return a common-unit rewrite with value in [0.1, 1000], or None."""
    match = DOSE_RE.search(span)
    if match is None or match.group(0) != span.strip():
        return None
    number = parse_decimal(match.group(1))
    unit = match.group(2)
    for src, dst, factor in _NATURAL_PAIRS:
        if unit != src:
            continue
        value = number * factor
        if Decimal("0.1") <= value <= Decimal("1000"):
            return f"{format_decimal(value)} {dst}"
    return None


def convert_dose_span(span: str) -> str:
    converted = natural_unit_conversion(span)
    if converted is None:
        raise ValueError(f"no natural unit conversion for {span!r}")
    return converted


def unit_inv_conversion(span: str) -> Optional[Tuple[str, str]]:
    converted = natural_unit_conversion(span)
    if converted is None:
        return None
    return converted, "natural"


def polarity_matches(text: str) -> List[re.Match]:
    return list(POLARITY_RE.finditer(text))


def cue_key(text: str) -> str:
    return text.lower()


# Lexical swaps do not insert the word "not".
LEXICAL_FLIP = {
    "should be used": "should be avoided",
    "should be avoided": "should be used",
    "is recommended for": "is contraindicated for",
    "are recommended for": "are contraindicated for",
    "is indicated for": "is contraindicated for",
    "are indicated for": "are contraindicated for",
    "is contraindicated": "is indicated",
    "are contraindicated": "are indicated",
    "contraindicated in": "indicated in",
    "is effective": "is ineffective",
    "are effective": "are ineffective",
    "is safe": "is unsafe",
    "are safe": "are unsafe",
}


def flip_mechanism(cue: str) -> str:
    key = cue_key(cue)
    if key in LEXICAL_FLIP:
        return "lexical"
    flipped = FLIP.get(key, "")
    if " not " in f" {key} " and " not " not in f" {flipped} ":
        return "not_remove"
    return "not_insert"


def flip_cue(cue: str) -> str:
    key = cue_key(cue)
    mechanism = flip_mechanism(cue)
    if mechanism == "lexical":
        return LEXICAL_FLIP[key]
    if key not in FLIP:
        raise ValueError(f"no flip for {cue!r}")
    return FLIP[key]


def inv_cue(cue: str) -> str:
    key = cue_key(cue)
    if key not in INV_POLARITY:
        raise ValueError(f"no invariance rephrase for {cue!r}")
    return INV_POLARITY[key]


def rephrase_polarity_mapping(cue: str) -> tuple[str, str, str]:
    """Return (cue_key, rewritten_cue, table) where table is G_pair or INV_POLARITY."""
    key = cue_key(cue)
    if key in POLARITY_REPHRASE_INV:
        return key, POLARITY_REPHRASE_INV[key], "POLARITY_REPHRASE_INV"
    if key not in INV_POLARITY:
        raise ValueError(f"no rephrase INV for {cue!r}")
    return key, INV_POLARITY[key], "INV_POLARITY"


def rephrase_polarity_cue(cue: str) -> str:
    """Template equivalence rephrase (QC v3 G): explicit pairs first, then INV_POLARITY."""
    return rephrase_polarity_mapping(cue)[1]


def replace_span(text: str, start: int, end: int, new: str) -> str:
    if text[start:end] == "":
        raise ValueError("empty span")
    return text[:start] + new + text[end:]


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            ins = cur[j - 1] + 1
            delete = prev[j] + 1
            sub = prev[j - 1] + (ca != cb)
            cur.append(min(ins, delete, sub))
        prev = cur
    return prev[-1]


def outside_identical(original: str, edited: str, start: int, end: int, new_span: str) -> bool:
    return edited == original[:start] + new_span + original[end:]


def highlight(text: str, start: int, end: int) -> str:
    return text[:start] + "«" + text[start:end] + "»" + text[end:]


def first_word(text: str) -> str:
    match = re.match(r"\s*([A-Za-z]+)", text or "")
    return match.group(1).lower() if match else ""


def join_window(sentences: Sequence[str], index: int) -> Tuple[str, int, int]:
    """Target sentence plus up to one sentence on each side.

    Returns evidence, start of the target sentence, end of the target sentence.
    """
    left = sentences[index - 1] if index > 0 else ""
    mid = sentences[index]
    right = sentences[index + 1] if index + 1 < len(sentences) else ""
    pieces: List[str] = []
    if left:
        pieces.append(left)
    start = len(" ".join(pieces))
    if pieces:
        start += 1
    pieces.append(mid)
    end = start + len(mid)
    if right:
        pieces.append(right)
    return " ".join(pieces), start, end
