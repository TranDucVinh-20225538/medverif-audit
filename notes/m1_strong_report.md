# M1-strong (steps 1–2)

Pre-registration: `notes/m1_preregistration.md` · Amendment: `notes/m1_prereg_amendment1.md`
M1-lib backend: **quantulum3+pint** · Gate bases: **104**

## Criterion (verbatim)

> Numeral binding is supported for a checker if US_up_after >= NS_x10 - 5 points AND US_down_after >= NS_div10 - 5 points, or the 95% cluster-bootstrap CIs overlap. US_after above NS is expected and not counted against. Evaluated on spans parsed by BOTH M1 and M1-lib.

## Coverage by pack (edited target spans; before US/NS metrics)

| Pack | instances | inst gate pass | target spans | M1 only | M1-lib only | both |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| us_up_x1000 | 214 | 170 | 430 | 0 | 34 | 376 |
| us_down_unit | 150 | 150 | 300 | 0 | 0 | 300 |
| ns_x10_claim | 106 | 100 | 212 | 0 | 0 | 200 |
| ns_x10_evid | 106 | 100 | 212 | 0 | 0 | 200 |
| ns_div10_claim | 98 | 93 | 196 | 0 | 0 | 186 |
| ns_div10_evid | 98 | 93 | 196 | 0 | 0 | 186 |

Cohort intersection: **104** bases with ≥1 gated instance across causal packs.

| Checker | NS_x10 evid (gate) | US_up before (all ×1000) | US_up after (gate) | NS_div10 evid | US_down | binding? |
| --- | --- | --- | --- | --- | --- | --- |
| V2a | 83.3% [76.0,90.6] (80/96) | 67.3% [60.7,74.0] (132/196) | 75.3% [69.3,80.7] (125/166) | 88.9% [82.2,94.4] (80/90) | NA | True |
| V3 | 89.4% [83.0,95.7] (84/94) | 80.2% [73.4,86.5] (154/192) | 87.8% [82.3,92.7] (144/164) | 96.6% [92.0,100.0] (85/88) | NA | True |
| MiniCheck-RoBERTa | NA | NA | NA | NA | NA | pending |
| AlignScore-base | NA | NA | NA | NA | NA | pending |
| MiniCheck-DeBERTa | NA | NA | NA | NA | NA | pending |
| Bespoke | NA | NA | NA | NA | NA | pending |
| V1-Mistral24B | 93.0% [88.0,98.0] (93/100) | NA | NA | 97.8% [94.6,100.0] (91/93) | NA | pending |
| V4-Llama70B | 90.0% [84.0,96.0] (90/100) | 91.1% [87.1,95.1] (185/203) | 92.3% [88.2,95.9] (156/169) | 92.3% [85.7,96.7] (84/91) | NA | True |
