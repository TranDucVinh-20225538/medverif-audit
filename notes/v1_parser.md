# V1 parser: released behavior and study label

Source copied into `src/v1_parser.py` from `Verifier.parse_verification_output` in
Heyuan9/MedScore commit `207c2b723f02339091ecc29628bf745d184952f6`.
The function was not edited. Checks below were produced by `src/selftest_rules.py`
and written to `notes/v1_parser_checks.json`.

The released parser always returns `0.0` or `1.0`. It has no unparseable state.

When the lowercased completion contains the substring `true` or `false`:

- only `true` → `1.0`
- only `false` → `0.0`
- both → `1.0` if the last `true` is after the last `false`, else `0.0`

Substring, not whole word. `untrue` contains `true` and not `false`, so the released score is `1.0`.
`not true` also scores `1.0`, because the negation-keyword fallback does not run once `true` is present.

When neither substring is present, the completion is split into tokens after punctuation is removed.
The score is `1.0` if none of the tokens `not`, `cannot`, `unknown`, `information` appear, and `0.0` otherwise.
`all([])` is true in Python, so an empty completion scores `1.0`.
`yes`, `no`, and `maybe` also score `1.0`.
`I cannot tell` and `unknown` score `0.0`.

Study label (`study_verdict`), applied **post-hoc** via `src/reparse_v1_study.py` on `raw_output` in
`results/raw/`. Scoring stores `released_parser_score` and a released-map `verdict` only.

- `\bnot\s+true\b` anywhere → FAIL (disagrees with released `1.0` on phrases like `This is not true`)
- else whole word `true` and no whole word `false` → PASS
- whole word `false` and no whole word `true` → FAIL
- both whole words → PASS if the last `true` is after the last `false`, else FAIL
- neither whole word → PARSE_FAIL

PARSE_FAIL is not mapped to FAIL. Report `disagree_rate` between released-map and study labels.
Smoke strings: `tests/v1_study_smoke.jsonl`. `untrue`, empty text, `yes`, `no`, and `maybe` are
PARSE_FAIL under the study label even though the released score is `1.0`.

gpt-4o was not used. This note does not come from a verifier run.
