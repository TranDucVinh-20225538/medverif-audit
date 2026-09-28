# LLM-AggreFact local cache (not in git)

Large HF exports live under `data/t8/aggrefact/{dev,test}.jsonl` (~90 MB each). They are **gitignored**; clone fresh with:

```bash
# Accept dataset terms on Hugging Face, then:
export HF_TOKEN=...   # or huggingface-cli login
cd /path/to/medverif-audit
python3 scripts/t8_download_aggrefact.py
```

Audit / T8b sampling read these paths via `scripts/t8_aggrefact_analysis.load_split()`.
