"""Frozen RAGAS NLI prompt from vibrantlabsai/ragas commit 298b682.

The instruction, examples, and to_string layout are copied from
src/ragas/metrics/_faithfulness.py and src/ragas/prompt/pydantic_prompt.py.
The statement-decomposition prompt is not included.
"""

from __future__ import annotations

import json
from typing import List

from pydantic import BaseModel, Field

INSTRUCTION = (
    "Your task is to judge the faithfulness of a series of statements based on a given context. "
    "For each statement you must return verdict as 1 if the statement can be directly inferred "
    "based on the context or 0 if the statement can not be directly inferred based on the context."
)


class StatementFaithfulnessAnswer(BaseModel):
    statement: str = Field(..., description="the original statement, word-by-word")
    reason: str = Field(..., description="the reason of the verdict")
    verdict: int = Field(..., description="the verdict(0/1) of the faithfulness.")


class NLIStatementOutput(BaseModel):
    statements: List[StatementFaithfulnessAnswer]


class NLIStatementInput(BaseModel):
    context: str = Field(..., description="The context of the question")
    statements: List[str] = Field(..., description="The statements to judge")


EXAMPLES = [
    (
        NLIStatementInput(
            context=(
                "John is a student at XYZ University. He is pursuing a degree in Computer Science. "
                "He is enrolled in several courses this semester, including Data Structures, Algorithms, "
                "and Database Management. John is a diligent student and spends a significant amount of "
                "time studying and completing assignments. He often stays late in the library to work on "
                "his projects."
            ),
            statements=[
                "John is majoring in Biology.",
                "John is taking a course on Artificial Intelligence.",
                "John is a dedicated student.",
                "John has a part-time job.",
            ],
        ),
        NLIStatementOutput(
            statements=[
                StatementFaithfulnessAnswer(
                    statement="John is majoring in Biology.",
                    reason="John's major is explicitly mentioned as Computer Science. There is no information suggesting he is majoring in Biology.",
                    verdict=0,
                ),
                StatementFaithfulnessAnswer(
                    statement="John is taking a course on Artificial Intelligence.",
                    reason="The context mentions the courses John is currently enrolled in, and Artificial Intelligence is not mentioned. Therefore, it cannot be deduced that John is taking a course on AI.",
                    verdict=0,
                ),
                StatementFaithfulnessAnswer(
                    statement="John is a dedicated student.",
                    reason="The context states that he spends a significant amount of time studying and completing assignments. Additionally, it mentions that he often stays late in the library to work on his projects, which implies dedication.",
                    verdict=1,
                ),
                StatementFaithfulnessAnswer(
                    statement="John has a part-time job.",
                    reason="There is no information given in the context about John having a part-time job.",
                    verdict=0,
                ),
            ]
        ),
    ),
    (
        NLIStatementInput(
            context="Photosynthesis is a process used by plants, algae, and certain bacteria to convert light energy into chemical energy.",
            statements=["Albert Einstein was a genius."],
        ),
        NLIStatementOutput(
            statements=[
                StatementFaithfulnessAnswer(
                    statement="Albert Einstein was a genius.",
                    reason="The context and statement are unrelated",
                    verdict=0,
                )
            ]
        ),
    ),
]


def _examples_block() -> str:
    chunks = []
    for idx, (inp, out) in enumerate(EXAMPLES):
        chunks.append(
            f"Example {idx + 1}\n"
            + "Input: "
            + inp.model_dump_json(indent=4)
            + "\n"
            + "Output: "
            + out.model_dump_json(indent=4)
        )
    return "\n--------EXAMPLES-----------\n" + "\n\n".join(chunks)


def nli_prompt(context: str, statements: List[str]) -> str:
    """Same layout as PydanticPrompt.to_string at the pinned commit."""
    data = NLIStatementInput(context=context, statements=statements)
    signature = (
        "Please return the output in a JSON format that complies with the "
        "following schema as specified in JSON Schema:\n"
        f"{json.dumps(NLIStatementOutput.model_json_schema())}"
        "Do not use single quotes in your response but double quotes,"
        "properly escaped with a backslash."
    )
    return (
        f"{INSTRUCTION}\n"
        + signature
        + "\n"
        + _examples_block()
        + "\n-----------------------------\n"
        + "\nNow perform the same with the following input\n"
        + "input: "
        + data.model_dump_json(indent=4, exclude_none=True)
        + "\n"
        + "Output: "
    )
