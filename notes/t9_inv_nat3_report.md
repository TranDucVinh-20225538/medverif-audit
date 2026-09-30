# T9 NeMo — INV-claim unit subset (nat3 labels)

Subset: main+expand **INV-claim** `unit_conversion`. **nat3 Y** = `effective_unit_natural_y` from `qc/nat3_labels.csv`. Block if AlignScore rail score < 0.5. Rates reported as **k/n**.

- INV-unit rows: **62** (nat3 Y: **22**, N: **40**)

## AlignScore-base rail

| slice | n scored | blocked k/n | 95% CI |
| --- | ---: | --- | --- |
| all INV-unit | 21 | **16/21** (0.762) | [0.571, 0.952] |
| nat3 Y (natural) | 20 | **15/20** (0.750) | [0.550, 0.900] |
| nat3 N (unnatural) | 1 | **1/1** (1.000) | [1.000, 1.000] |

## AlignScore-large rail

| slice | n scored | blocked k/n | 95% CI |
| --- | ---: | --- | --- |
| all INV-unit | 21 | **17/21** (0.810) | [0.619, 0.952] |
| nat3 Y (natural) | 20 | **16/20** (0.800) | [0.600, 0.950] |
| nat3 N (unnatural) | 1 | **1/1** (1.000) | [1.000, 1.000] |

