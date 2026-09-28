# T9 setup — NeMo Guardrails 0.24.1 + AlignScore rail

Verified on **bright92** (`conda` env `vllm`): `nemoguardrails==0.24.1`.

Package root (example):  
`/data2/cmdir/home/toandq/.conda/envs/vllm/lib/python3.12/site-packages/nemoguardrails/`

## Pin

```bash
pip install 'nemoguardrails==0.24.1'
python3 -c "import nemoguardrails; print(nemoguardrails.__version__)"
```

## AlignScore server (official helper in package)

Default CLI loads **`base`** checkpoint only, port **5000**:

```94:111:/data2/cmdir/home/toandq/.conda/envs/vllm/lib/python3.12/site-packages/nemoguardrails/library/factchecking/align_score/server.py
@cli_app.command()
def start(
    port: int = typer.Option(default=5000, help="The port that the server should listen on. "),
    models: List[str] = typer.Option(
        default=["base"],
        help="The list of models to be loaded on startup",
    ),
    initialize_only: bool = typer.Option(default=False, help="Whether to run only the initialization for the models."),
):
    # Preload the models
    for model in models:
        typer.echo(f"Pre-loading model {model}.")
        get_model(model)
```

Checkpoint path on disk (`ALIGN_SCORE_PATH` required):

```49:55:/data2/cmdir/home/toandq/.conda/envs/vllm/lib/python3.12/site-packages/nemoguardrails/library/factchecking/align_score/server.py
    return AlignScore(
        model="roberta-base",
        batch_size=32,
        device=device,
        ckpt_path=os.path.join(models_path, f"AlignScore-{model}.ckpt"),
        evaluation_mode="nli_sp",
    )
```

Dockerfile in the same directory downloads **`AlignScore-base.ckpt`** from HuggingFace `yzha/AlignScore` (official integration default).

HTTP route for base model:

```79:82:/data2/cmdir/home/toandq/.conda/envs/vllm/lib/python3.12/site-packages/nemoguardrails/library/factchecking/align_score/server.py
@app.post("/alignscore_base")
def alignscore_base(request: AlignScoreRequest):
    model = get_model("base")
    return get_alignscore(model, request.evidence, request.claim)
```

## Rail action → API → decision

`alignscore_check_facts` reads config, calls AlignScore HTTP, then applies shared outcome helper:

```42:72:/data2/cmdir/home/toandq/.conda/envs/vllm/lib/python3.12/site-packages/nemoguardrails/library/factchecking/align_score/actions.py
    fact_checking_config = llm_task_manager.config.rails.config.fact_checking
    fallback_to_self_check = fact_checking_config.fallback_to_self_check

    alignscore_api_url = fact_checking_config.parameters.get("endpoint")
    ...
    alignscore = await alignscore_request(
        alignscore_api_url,
        evidence,
        response,
        http_client=http_client,
    )
    if alignscore is None:
        log.warning("AlignScore endpoint not set up properly. Falling back to the ask_llm approach for fact-checking.")
        if fallback_to_self_check:
            return await self_check_facts(...)
        else:
            return _fact_check_outcome(1.0)
    else:
        return _fact_check_outcome(alignscore)
```

Empty evidence short-circuits to score **1.0** (allow) in the HTTP client action:

```33:34:/data2/cmdir/home/toandq/.conda/envs/vllm/lib/python3.12/site-packages/nemoguardrails/library/factchecking/align_score/request.py
    if not evidence:
        return 1.0
```

Note: `alignscore_request`’s **Python default** URL is `http://localhost:5000/alignscore_large`; production configs should set `parameters.endpoint` explicitly (this repo uses **`/alignscore_base`** to match the default server model).

## Threshold (block if accuracy < 0.5)

```31:37:/data2/cmdir/home/toandq/.conda/envs/vllm/lib/python3.12/site-packages/nemoguardrails/library/self_check/facts/actions.py
FACT_CHECK_THRESHOLD = 0.5


def _fact_check_outcome(accuracy: float) -> RailOutcome:
    if accuracy < FACT_CHECK_THRESHOLD:
        return RailOutcome.block(metadata={"accuracy": accuracy})
    return RailOutcome.allow(metadata={"accuracy": accuracy})
```

## Fallback default

```30:33:/data2/cmdir/home/toandq/.conda/envs/vllm/lib/python3.12/site-packages/nemoguardrails/library/factchecking/rail_config.py
    fallback_to_self_check: bool = Field(
        default=False,
        description="Whether to fall back to self-check if another method fail.",
    )
```

With **`fallback_to_self_check: false`** (default) and a failed AlignScore HTTP call, the rail **allows** the answer (`_fact_check_outcome(1.0)`).

## Medical RAG mapping (this study)

| Guardrails field | T9 instance field |
|------------------|-------------------|
| `relevant_chunks` | `[evidence]` (single passage) |
| `bot_message` | eco answer or verifier `claim` |

Minimal config: `config/t9/config.yml` (`endpoint: http://127.0.0.1:5000/alignscore_base`, `fallback_to_self_check: false`).

## Input sets (a–d)

Built by `scripts/t9_build_input_sets.py` → `data/t9/instances_*.jsonl` + `data/t9/manifest.json`:

| Set | Cohort |
|-----|--------|
| **a** | T4 eco `exact_verbatim`, human `PI_ok=Y`, main |
| **b** | T4 eco `exact_surface_variant` + `frequency_rephrased` (PI_ok=Y) + **INV-unit natural** (main+expand) |
| **c** | DOSE main `E1-claim` **x2** |
| **d** | T7 `instances_e1_unit.jsonl` (E1-unit) |

## node30 runner (do not run on HPC login)

```bash
# on node30 after git pull
bash jobs/run_t9_node30.sh
```

Logs: `jobs/logs/t9_node30_*.log`  
Scores: `results/raw/t9/alignscore_rail.jsonl`  
Report: `scripts/t9_report.py` → `notes/t9_report.json`, appends T9 section to `notes/t9_t10_report.md`.
