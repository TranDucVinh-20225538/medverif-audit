# T20 appendix — openFDA label vs textbook dose surfaces

Descriptive check only (not a headline prevalence claim). M1 canonical matching + PI review of unit-surface differences.

## Cohort

- Drugs in list: **194**
- Cached FDA labels: **115**
- **Unique** M1-matched dose pairs (deduped by drug + sentences + spans): **55** (pre-fix matcher counted **363** duplicate cross-product rows)
- Unique pairs with differing unit surface: **11**

## PI review (`qc/t20_diff_unit_labels.csv`)

- Review rows in file: **33** (matcher emitted duplicates before dedupe fix)
- **Unique** surface-difference pairs reviewed: **11**
- PI **same quantity + same context (Y)**: **3 / 11**
- Of those Y, **true scale conversion** (mg↔g, µg↔mg style): **1** (valacyclovir 2 g↔2 grams and dexamethasone 1 mg↔1.0 mg are spelling/formatting; cosyntropin 250 µg↔0.25 mg is scale conversion)

## Surface-difference categories (unique diff pairs, rule-based)

- **scale_conversion**: 3
- **spelling**: 5
- **symbol**: 2
- **formatting**: 1

## BM25 retrieval simulation

Prior aggregate **9.4%** query hit rate was on undeduplicated matcher output and is **withdrawn**. No recomputed rate on PI-confirmed pairs (n=3 contexts).
- Raw query count (drug×base dose claims): **288** (diagnostic only)

Details: `notes/t20_match_retrieval.json` · Review export: `qc/t20_diff_unit_review.csv`
