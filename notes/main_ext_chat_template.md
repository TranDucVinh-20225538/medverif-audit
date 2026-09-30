# Expansion Stage-1 OpenRouter templates

Generator: `qwen/qwen-2.5-72b-instruct` tokenizer `Qwen/Qwen2.5-72B-Instruct`

Validator: `microsoft/phi-4` tokenizer `microsoft/phi-4` rev `2db69c1c3e91a05d2c64a3185acfbaf36f744e25`

```
<|im_start|>system
You write one patient-facing sentence that restates a medical fact from the evidence. The sentence must be fully supported by the evidence. Do not add facts, numbers, or advice. Copy the target span exactly, character for character. Return one sentence only, with no preamble.<|im_end|>
<|im_start|>user
Evidence:
The drug is given at a dose of 2.5 mg once daily for prevention of venous thromboembolism. For initial treatment of established venous thromboembolism, fondaparinux is given at a dose of 7.5 mg once daily. The dose can be reduced to 5 mg once daily for those weighing <50 kg and increased to 10 mg for those >100 kg.

Target sentence:
For initial treatment of established venous thromboembolism, fondaparinux is given at a dose of 7.5 mg once daily.

Target span to copy exactly:
7.5 mg

Patient-facing sentence:<|im_end|>
<|im_start|>assistant

```
