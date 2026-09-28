# V4 OpenRouter smoke — Llama 3.3 70B (DeepInfra)

Pre-probe sanity check (2026-09-28): **20/20 parsed** (`parse_rate=1.0`).

Model: `meta-llama/llama-3.3-70b-instruct`  
Provider: **DeepInfra** (pinned)  
Prompt: same RAGAS-NLI `nli_prompt` + `parse_verdict`; chat template via `Llama3InstructTokenizer` (no HF gate).

## Raw examples (3)

### D0123__E1-evid__x10 — FAIL

```json
{
    "statements": [
        {
            "statement": "A study used 100 mg of micronized progesterone intravaginally daily.",
            "reason": "The context mentions that Cetingoz and coworkers (2011) gave 1000 mg of micronized progesterone intravaginally daily, not 100 mg.",
            "verdict": 0
        }
    ]
}
```

### D0020__E2__x2 — PASS

```json
{
    "statements": [
        {
            "statement": "Men who took famciclovir (500 mg every 12 hours) daily for 18 weeks did not experience changes in sperm shape or movement.",
            "reason": "The context explicitly states that men receiving daily famciclovir (500 mg every 12 hours) for 18 weeks had no changes in sperm morphology or motility, which directly corresponds to the statement about sperm shape or movement.",
            "verdict": 1
        }
    ]
}
```

### D0004__E2__x2 — PASS

```json
{
    "statements": [
        {
            "statement": "It is important to note that peripheral neuropathies can be seen in doses of 400 mg per day or higher, as well as interaction with other medications.",
            "reason": "The statement is directly mentioned in the context.",
            "verdict": 1
        }
    ]
}
```

Full run: `nohup jobs/run_v4_openrouter_full.sh` after Qwen3 probe completes (expected: no `/no_think` gate pass).
