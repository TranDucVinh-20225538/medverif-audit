# T8b dropped (2026-09-29)

PI review of `qc/t8_mismatch_check.csv`: **10/40** rows marked genuine (`PI_ok=Y`); **30/40** false alarms.

False positives are dominated by **RAGTruth** structured fields: opening hours, star ratings, and timestamp substrings (`09`, `00`, `4.0` vs `4`) mistaken for quantity-format mismatches.

Genuine rows are **trivial formatting** only (e.g. `9 km` vs `9km`, `130 lbs` vs `130 pounds`, star rating `4` vs `4.0`).

**Decision:** Do **not** run T8b build/score jobs; do **not** report automated mismatch counts (e.g. ~1058) as benchmark evidence. See `REPORT.md` Threats.

Jobs disabled: `jobs/run_t8b_aggrefact.sh`, `jobs/run_t8b_aggrefact_node30.sh`.
