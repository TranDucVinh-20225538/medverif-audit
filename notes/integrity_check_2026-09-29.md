# Data integrity check (2026-09-29)

Generated: 2026-09-29T17:20:28+07:00  
Resolution table updated: 2026-09-29T17:25+07:00

Scanned **277** `.jsonl` files under `data/` and `results/raw/`.

## Truncation root cause (`para_attempts.jsonl`)

- **Writer:** `src/apply_qc_v3_decisions.py` reset block (QC **G**); now **opt-in** via `MEDVERIF_QC_V3_RESET_PARA=1` + `src/safe_jsonl.py`.
- **~2026-09-28 23:58:31 +07:** `apply_qc_v3_decisions.py` on main `data/v3/` when live `para_attempts.jsonl` was already empty → empty `pre_qc` backup.
- **Guards:** `src/safe_jsonl.py`, `scripts/check_data_linecounts.py`, git `pre-commit` / `pre-push`, `notes/allow_data_shrink.json`.

## Per-file resolution (16 shrunk vs git `HEAD`)

All rows classified. Line counts re-checked on disk after restores.

| # | Path | HEAD | Now | Cause | Action |
|---|------|-----:|----:|-------|--------|
| 1 | `data/expand/bases_main.jsonl` | 557 | 138 | **Intended filter** — expand rebuild after PI (`scripts/expand/rebuild_after_pi.py`); HEAD was pre-rebuild WIP (`32d2352`). | **Kept** — canonical expand bases in rebuild notes (`notes/expand_rebuild_after_pi.json`, 351 bases audit-wide). |
| 2 | `data/expand/instances_cpu_early.jsonl` | 3487 | 623 | **Intended filter** — regenerated expand **scoring/pending slice** after QC v3 expand + dose spotcheck gate; not the full audit (see `data/expand/v3/instances_cpu_main.jsonl`, 2532 lines). | **Kept** — expand is non-headline; do not use HEAD superset for analysis. |
| 3 | `data/expand/instances_main.jsonl` | 3203 | 623 | **Intended filter** — same rebuild; 623 rows all `valid=true` (post-gate pending pack). HEAD mixed valid/invalid superset. | **Kept** — matches `data/expand/v3/instances_main.jsonl` (623). |
| 4 | `data/expand/instances_pending_node30.jsonl` | 3487 | 734 | **Intended filter** — node30 pending rebuilt from post-PI expand packs (`build_expand_scoring_packs.py`). | **Kept** — reconcile with `notes/expand_node30_manifest.json` when rescoring expand. |
| 5 | `data/expand/instances_pending_t6a.jsonl` | 1371 | 319 | **Intended filter** — T6-A pending slice regenerated on smaller valid expand cohort. | **Kept** — expand-only queue. |
| 6 | `data/expand/instances_score_pending.jsonl` | 2469 | 537 | **Intended filter** — HPC OpenRouter pending queue rebuilt after expand QC / PI dose gate. | **Kept** — expand-only queue. |
| 7 | `data/t14/instances_t14.jsonl` | 237 | 233 | **Intended filter** — T14 PI fix + non-dose exclusion: removed 4 repr rows for **D0077**, **D0164** (2 magnitudes each). | **Kept** — canonical **n=233** per `data/t14/manifest_t14.json`. |
| 8 | `data/t14/instances_t14_pending_openrouter.jsonl` | 237 | 233 | **Intended filter** — pending rebuilt from current T14 pack (233). | **Kept** — matches manifest. |
| 9 | `data/t3/instances_inv_families.jsonl` | 114 | 113 | **Intended filter** — dropped `D0164__INV-claim__inv_numerals__6_to_six` (non-dose target **D0164**, `af440ee`). | **Kept** — aligned with main non-dose policy. |
| 10 | `data/v3/instances_cpu_early.jsonl` | 1258 | 1249 | **Intended filter** — non-dose invalidation on main pack (`af440ee` / `apply_non_dose_packs.py`); −9 rows. | **Kept** — do not restore HEAD (would re-include excluded bases). |
| 11 | `data/v3/instances_inv_families.jsonl` | 114 | 113 | **Intended filter** — same **D0164** family row removed as t3. | **Kept** — aligned with non-dose policy. |
| 12 | `data/v3/instances_m1_pending_node30.jsonl` | 942 | 942 | **Accidental** — file was **0 bytes** (truncate / failed rewrite); scores/manifests expect 942. | **Restored from `HEAD`** (+ `.bak.*` via `safe_jsonl`) on 2026-09-29. |
| 13 | `data/v3/instances_score_pending_g_inv.jsonl` | 109 | 109 | **Accidental** — file was **0 bytes**. | **Restored from `HEAD`** on 2026-09-29. |
| 14 | `data/v3/instances_t14.jsonl` | 237 | 233 | **Intended filter** — mirror T14 pack (non-dose **D0077/D0164** repr rows out). | **Kept** — matches `manifest_t14.json`. |
| 15 | `data/v3/instances_t14_pending_node30.jsonl` | 237 | 233 | **Intended filter** — node30 T14 pending synced to 233-row pack. | **Kept** — matches manifest. |
| 16 | `data/v3/para_attempts.pre_qc_v3.jsonl` | 244 | 244 | **Accidental** — emptied by `apply_qc_v3_decisions.py` reset when source already empty (~23:58 28/9). | **Restored from git `dac0b08`** (244 lines); synced with `para_attempts.jsonl`. |

**Related (not in the 16):** `data/v3/para_attempts.jsonl` — same accidental truncate; **restored from `dac0b08`** (244 lines). **medverif-v3 paraphrase pipeline on HOLD** — do not consume into `instances_main*` (see decision **L**).

## Guards added

- `src/safe_jsonl.py` — backup + atomic replace; shrink guard on `data/**` and `results/raw/**`.
- `.git/hooks/pre-commit` and `pre-push` → `scripts/check_data_linecounts.py` (`scripts/install_git_hooks.sh`).
- Override list: `notes/allow_data_shrink.json`.
