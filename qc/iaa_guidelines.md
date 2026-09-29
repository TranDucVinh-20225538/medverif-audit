# IAA guidelines

Reviewers mark PASS or FAIL in `reviewer_a` / `reviewer_b` for whether the claim is supported by the evidence.

The review CSV contains only `blind_id`, claim, and evidence — no condition, stratum, or expected labels.

Adjudication metadata lives locally in `qc/iaa_key_DO_NOT_SHARE.csv` (do not share with reviewers).

Design strata (n=120): {"conversion_naturalness": 30, "polarity_flips": 30, "rephrases": 20, "frequency_route": 25, "dose_value": 15}
