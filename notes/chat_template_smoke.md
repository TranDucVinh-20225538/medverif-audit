# Exact chat-template strings

Generator: `Qwen/Qwen2.5-32B-Instruct` revision `5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd`

Call: `tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)` with a system message and a user message. Temperature 0, seed 42, max_tokens 256. Thinking mode is not a parameter of this checkpoint.

```
<|im_start|>system
You write one patient-facing sentence that restates a medical fact from the evidence. The sentence must be fully supported by the evidence. Do not add facts, numbers, or advice. Copy the target span exactly, character for character. Return one sentence only, with no preamble.<|im_end|>
<|im_start|>user
Evidence:
Fasting glucose ≥126 mg/dL (in which fasting is defined as no food intake for 8 hours), 3. Two-hour oral glucose tolerance test of 75 g, with serum glucose ≥200 mg/dL, or 4. Hemoglobin A1c ≥6.5%.

Target sentence:
Two-hour oral glucose tolerance test of 75 g, with serum glucose ≥200 mg/dL, or 4.

Target span to copy exactly:
75 g

Patient-facing sentence:<|im_end|>
<|im_start|>assistant

```

Validator and INV checker: `microsoft/phi-4` revision `2db69c1c3e91a05d2c64a3185acfbaf36f744e25`

Same call shape. Temperature 0, seed 42, max_tokens 16. Thinking mode is not a parameter of this checkpoint.

```
<|im_start|>system<|im_sep|>You check whether the evidence fully supports the claim. Reply with one word: YES or NO. YES only if every factual part of the claim, including numbers, units, and recommendation direction, is stated by the evidence. If the claim adds, changes, or contradicts any fact, reply NO.<|im_end|><|im_start|>user<|im_sep|>Evidence:
Fasting glucose ≥126 mg/dL (in which fasting is defined as no food intake for 8 hours), 3. Two-hour oral glucose tolerance test of 75 g, with serum glucose ≥200 mg/dL, or 4. Hemoglobin A1c ≥6.5%.

Claim:
A two-hour oral glucose tolerance test involves drinking a solution containing exactly 75 g of glucose.<|im_end|><|im_start|>assistant<|im_sep|>
```
