# Node30 CPU verifier scores (`env=node30`)

Copied from `origin/node30-results` at commit `c48093bdc73a6b11161a26a2b11124a0e2ba5612`.

These files mirror `results/raw/**` layout from the Node30 scoring environment.
They are **not** merged into `results/raw/` on master (HPC/OpenRouter scores stay authoritative there).

Rebuilt into `release/audit_snapshot.zip` under the `results/raw_node30/` prefix.

## POL flip-ok pending (42 rows, commit `c48093b`)

There are **no** separate `pol*.jsonl` score files on `node30-results`. POL pending
instances (`data/v3/instances_pol_flip_pending_node30.jsonl`, see
`notes/pol_flip_pending_node30_manifest.json`) were **appended into the root encoders**:

- `v2a_minicheck.jsonl`, `v3_alignscore.jsonl`
- `t6_*.jsonl` at repo root (MiniCheck / AlignScore / SummaC / HHEM / Granite / Bespoke)

Paper metrics for pack `pol` use those node30 root files via `release/canonical_sources.tsv`.
