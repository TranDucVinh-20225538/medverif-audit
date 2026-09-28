#!/usr/bin/env python3
"""HTTP AlignScore server compatible with NeMo Guardrails fact-checking endpoints.

Same routes and env vars as
``nemoguardrails.library.factchecking.align_score.server`` (NVIDIA docs).
Uses the repo AlignScore install (``alignscore.alignscore.AlignScore``).
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List

import typer
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, ".cache", "src", "AlignScore", "src")
if SRC not in os.sys.path:
    os.sys.path.insert(0, SRC)

from alignscore.alignscore import AlignScore  # noqa: E402

models_path = os.environ.get("ALIGN_SCORE_PATH")
if models_path is None:
    raise ValueError(
        "Set ALIGN_SCORE_PATH to the folder containing AlignScore-base.ckpt and "
        "AlignScore-large.ckpt (see NeMo Guardrails AlignScore deployment guide)."
    )

app = FastAPI()
device = os.environ.get("ALIGN_SCORE_DEVICE", "cpu")

ROBERTA = {"base": "roberta-base", "large": "roberta-large"}


@lru_cache
def get_model(model: str):
    key = model.lower()
    if key not in ROBERTA:
        raise ValueError(f"unknown model {model!r}; use base or large")
    return AlignScore(
        model=ROBERTA[key],
        batch_size=32,
        device=device,
        ckpt_path=os.path.join(models_path, f"AlignScore-{key}.ckpt"),
        evaluation_mode="nli_sp",
        verbose=False,
    )


class AlignScoreRequest(BaseModel):
    evidence: str
    claim: str


@app.get("/")
def hello_world():
    return (
        "AlignScore HTTP server (NeMo Guardrails-compatible). "
        "POST /alignscore_base or /alignscore_large with JSON {evidence, claim}."
    )


def get_alignscore(model, evidence: str, claim: str) -> dict:
    score = model.score(contexts=[evidence], claims=[claim])[0]
    return {"alignscore": float(score)}


@app.post("/alignscore_base")
def alignscore_base(request: AlignScoreRequest):
    return get_alignscore(get_model("base"), request.evidence, request.claim)


@app.post("/alignscore_large")
def alignscore_large(request: AlignScoreRequest):
    return get_alignscore(get_model("large"), request.evidence, request.claim)


cli_app = typer.Typer()


@cli_app.command()
def start(
    port: int = typer.Option(default=5000, help="Listen port."),
    models: List[str] = typer.Option(default=["base"], help="Models to preload."),
    initialize_only: bool = typer.Option(default=False, help="Preload only, then exit."),
):
    for model in models:
        typer.echo(f"Pre-loading model {model}.")
        get_model(model)
    if initialize_only:
        print("Initialization successful.")
    else:
        uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 2 and sys.argv[1] == "start":
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("cmd", choices=["start"])
        parser.add_argument("--port", type=int, default=5000)
        parser.add_argument("--models", action="append", default=["base"])
        parser.add_argument("--initialize-only", action="store_true")
        args = parser.parse_args()
        for model in args.models:
            print(f"Pre-loading model {model}.")
            get_model(model)
        if args.initialize_only:
            print("Initialization successful.")
        else:
            uvicorn.run(app, host="0.0.0.0", port=args.port)
    else:
        cli_app()
