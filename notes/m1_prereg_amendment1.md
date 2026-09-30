# M1-strong pre-registration amendment 1

**Frozen after:** pre-registration commit `d3833a3` (`notes/m1_preregistration.md` — do not edit).

## (a) Gate change

**Amended gate (effective for all M1-strong runs after this file):** an instance enters the causal cohort only if **each edited target dose span** (from diff `span_before` / `span_after`, or `claim_span` / `evidence_span`) **parses under both** the in-repo M1 regex canonicalizer **and** M1-lib (quantulum3 + pint), and the **parsed quantity matches that target span** (same numeric value and unit family after alias normalization — not merely “some quantity parsed” elsewhere in the passage).

**Why:** Full-passage quantulum3 parsing on long claim/evidence text was too slow for batch runs on `instances_main.jsonl`; evaluating **only edited spans** preserves the pre-registered intent (M1 ∩ M1-lib on perturbation doses) with tractable runtime.

## (b) Status when amended

No **non-NA** M1-strong causal table had been accepted at amendment time. The first `m1_strong_run.py` execution reported **intersection = 0** on all packs because **quantulum3/pint were missing** in the default `python3` on the login node (M1-lib could not parse); subsequent partial installs used the **`vllm`** conda env.

## (c) Environment and code pointer

| Item | Value |
|------|--------|
| Python env | **`vllm`** (`/data2/cmdir/home/toandq/.conda/envs/vllm`) |
| quantulum3 | **0.10.0** |
| pint | **0.26.1** |
| Gate implementation | `src/m1_lib.py` (`target_span_gate`), `scripts/m1_strong_run.py` |
| Script commit | Recorded in git log immediately following **this** amendment commit (see `notes/batch_oct_status.md`) |

Primary criterion text remains verbatim in `notes/m1_preregistration.md`.
