# Prompt × model 2×2 (crossed assignment)

| cell | model | prompt | E1-unit-evid PASS | E2-x2 PASS |
|---|---|---|---:|---:|
| pxm_gpt4o_ragas | openai/gpt-4o | RAGAS-NLI | 0.150 (16/107) | 0.974 (114/117) |
| pxm_sonnet_medscore | anthropic/claude-sonnet-4.6 | MedScore-provided | 0.710 (76/107) | 0.974 (114/117) |

Expected: **E1-unit-evid** → low PASS (FAIL); **E2-x2** → high PASS.

