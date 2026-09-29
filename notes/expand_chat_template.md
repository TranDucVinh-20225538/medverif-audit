# Expansion Stage-1 OpenRouter templates

Generator: `qwen/qwen-2.5-72b-instruct` tokenizer `Qwen/Qwen2.5-72B-Instruct`

Validator: `microsoft/phi-4` tokenizer `microsoft/phi-4` rev `2db69c1c3e91a05d2c64a3185acfbaf36f744e25`

```
<|im_start|>system
You write one patient-facing sentence that restates a medical fact from the evidence. The sentence must be fully supported by the evidence. Do not add facts, numbers, or advice. Copy the target span exactly, character for character. Return one sentence only, with no preamble.<|im_end|>
<|im_start|>user
Evidence:
If a bleeding ulcer develops in a patient taking NSAIDs, the NSAIDs should be discontinued. If NSAIDs must be given, a cyclooxygenase 2 (COX-2) selective inhibitor (coxib) plus a PPI should be used. PPI co-therapy alone or a coxib alone is associated with an annual rebleeding rate of ~10% in patients with a recent bleeding ulcer, whereas the combination of a coxib and PPI provides a further significant decrease in recurrent ulcer bleeding.

Target sentence:
If NSAIDs must be given, a cyclooxygenase 2 (COX-2) selective inhibitor (coxib) plus a PPI should be used.

Target span to copy exactly:
should be used

Patient-facing sentence:<|im_end|>
<|im_start|>assistant

```
