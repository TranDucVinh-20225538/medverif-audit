# IAA v1 annotation kit (second annotator / clinician)

Built by `scripts/build_iaa_v1.py` (seed 20261001; deterministic). This kit supersedes the earlier v0 pilot (`qc/iaa_sample.csv`, `scripts/build_iaa_sample.py`, `scripts/iaa_kappa.py`), which used 120 items, only Q1/Q2, and a key kept outside git.

**Send to the annotator ONLY:** `annotation_sheet.xlsx` (or `.csv`), `GUIDELINES_vi.(md|pdf)`, `GUIDELINES_en.(md|pdf)`.
**Never send:** `private_key.jsonl` (author labels + instance ids), `sample_manifest.json`, `selftest_simulated_report.md`, or repo access.

| stratum | n | author accepted / rejected (Q1) | source of author label |
|---|---|---|---|
| conversion | 25 | 25 / 0 (Q2: 22 Natural, 3 Equivalent-unnatural) | qc/nat3_labels.csv `natural` |
| polarity_flip | 25 | 13 / 12 | qc/flip_PI_ok_labels.csv |
| rephrase | 20 | 12 / 8 | qc/inv_manual_review.csv (POLARITY/template) |
| freq_route | 20 | 10 / 10 (5+5 frequency, 5+5 route) | qc/inv_claim_PI_ok_labels.csv |
| unit_edit | 20 | 20 / 0 (15 claim-side, 5 evidence-side; x1000) | qc/t7_PI_ok_labels.csv (no rejected items exist) |
| value_edit | 20 | 11 / 9 (10 x2, 10 x10) | qc/dose3_labels.csv `E1x2_ok`/`E1x10_ok` |
| base_claim | 20 | 10 / 10 | qc/dose3_labels.csv `C0_ok` |

Scoring, after the sheet is returned:

```bash
python scripts/iaa_v1_kappa.py --sheet annotation/iaa_v1/filled/<name>.xlsx \
  --out-md notes/iaa_v1_report.md --out-json notes/iaa_v1_report.json
# optionally add --sheet2 <second annotator> for annotator-vs-annotator (incl. weighted kappa on Q3)
```

Rebuild the guideline PDFs with `python scripts/iaa_v1_guidelines_pdf.py` (requires markdown and LibreOffice).
