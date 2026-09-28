# Verifier prompt wording: evidence scope

Exact strings used in this repo for the **provided-evidence MedScore** path and **RAGAS-NLI** faithfulness judge.

## MedScore “provided evidence” (V1 / V1b / V1c)

Source: `src/verifiers/v1_medscore.py` — docstring states *“Wrap MedScore's provided-evidence verifier. Prompt and parser are not edited.”*  
Upstream reference: `medscore/verifier.py` `ProvidedEvidenceVerifier.format_input`, commit `207c2b7`.

**Full user message template** (evidence inserted as `{evidence}`, claim as `{claim}`):

```
Answer the question based on the given context.

{evidence}

Input: {claim} True or False?
Output:
```

**Does it say to rely ONLY on the evidence?**  
No explicit “only use the context / do not use outside knowledge” clause. The instruction is **“Answer the question based on the given context.”** The claim is framed as a True/False question with the evidence block labeled implicitly as “context” (not “evidence” in the template text). V1b/V1c reuse the same `format_input` via `v1.format_input`.

Chat template: Mistral-style `[INST] … [/INST]` around the user string (`v1_medscore.render`).

## RAGAS-NLI (V4 / V5 / V6 slugs)

Source: `src/verifiers/ragas_nli_prompt.py` — frozen from `vibrantlabsai/ragas` commit `298b682` (`_faithfulness.py` / `pydantic_prompt.py`).

**Instruction string (`INSTRUCTION`):**

```
Your task is to judge the faithfulness of a series of statements based on a given context. For each statement you must return verdict as 1 if the statement can be directly inferred based on the context or 0 if the statement can not be directly inferred based on the context.
```

**Layout:** JSON Schema for `NLIStatementOutput`, two fixed examples, then:

```
Now perform the same with the following input
input: {"context": "<evidence>", "statements": ["<claim>"]}
Output:
```

**Evidence scope:** Verdict is **1** iff the statement **“can be directly inferred based on the context”** — i.e. context-bound entailment, not world-knowledge plausibility alone. There is no separate “ignore your prior knowledge” sentence; scope is defined by **direct inference from the supplied context string** (mapped from instance `evidence`).

## Mapping in scoring

| Field in instances | MedScore template | RAGAS-NLI |
|---|---|---|
| `evidence` | “given context” block | `context` in JSON input |
| `claim` | True/False `Input` | single `statements[]` entry |
