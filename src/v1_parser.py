"""MedScore released parser, copied verbatim, plus the study label.

The released function is the body of Verifier.parse_verification_output from
Heyuan9/MedScore commit 207c2b723f02339091ecc29628bf745d184952f6.
Do not edit it. The study label is applied by the wrapper only.
"""

from __future__ import annotations

import re
import string


def released_parse_verification_output(completion_message: str) -> float:
    generated_answer = completion_message.strip().lower()
    is_supported = 0.0

    if "true" in generated_answer or "false" in generated_answer:
        if "true" in generated_answer and "false" not in generated_answer:
            is_supported = 1.0
        elif "false" in generated_answer and "true" not in generated_answer:
            is_supported = 0.0
        else:
            try:
                # If 'true' appears after 'false', it's likely the final answer.
                is_supported = float(generated_answer.rindex("true") > generated_answer.rindex("false"))
            except ValueError:
                is_supported = 0.0  # One of the words wasn't found
    else:
        generated_answer_tokens = generated_answer.translate(str.maketrans("", "", string.punctuation)).split()
        is_supported = float(all(
            [keyword not in generated_answer_tokens for keyword in ["not", "cannot", "unknown", "information"]]))
    return is_supported


def study_verdict(completion_message: str) -> str:
    """PASS/FAIL only when a whole word true/false is present. Otherwise PARSE_FAIL.

    This does not replace the released score. Both are stored.
    Whole-word 'true' with no whole-word 'false' is PASS, including 'not true',
    because the released parser also treats that as supported. Absence of either
    word is PARSE_FAIL, which the released parser never emits.
    """
    text = completion_message.strip().lower()
    true_at = [m.start() for m in re.finditer(r"\btrue\b", text)]
    false_at = [m.start() for m in re.finditer(r"\bfalse\b", text)]
    if not true_at and not false_at:
        return "PARSE_FAIL"
    if true_at and not false_at:
        return "PASS"
    if false_at and not true_at:
        return "FAIL"
    return "PASS" if true_at[-1] > false_at[-1] else "FAIL"
