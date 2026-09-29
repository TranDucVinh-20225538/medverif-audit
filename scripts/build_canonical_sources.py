#!/usr/bin/env python3
"""Regenerate release/canonical_sources.tsv for paper metric score paths."""

from __future__ import annotations

import json

from canonical_scores import CANONICAL_TSV, write_canonical_tsv


def main() -> None:
    path = write_canonical_tsv()
    n = sum(1 for line in path.open() if line.strip()) - 1
    print(json.dumps({"canonical_tsv": str(path), "rows": n}))


if __name__ == "__main__":
    main()
