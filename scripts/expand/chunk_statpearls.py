#!/usr/bin/env python3
"""Chunk StatPearls NXML into MedRAG-style jsonl (per MedRAG src/data/statpearls.py)."""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path


def ends_with_ending_punctuation(s: str) -> bool:
    return any(s.endswith(c) for c in (".", "?", "!"))


def concat(title: str, content: str) -> str:
    t = title.strip()
    c = content.strip()
    if ends_with_ending_punctuation(t):
        return t + " " + c
    return t + ". " + c


def extract_text(element: ET.Element) -> str:
    text = (element.text or "").strip()
    for child in element:
        text += (" " if text else "") + extract_text(child)
        if child.tail and child.tail.strip():
            text += (" " if text else "") + child.tail.strip()
    return text.strip()


def is_subtitle(element: ET.Element) -> bool:
    if element.tag != "p":
        return False
    kids = list(element)
    if len(kids) != 1 or kids[0].tag != "bold":
        return False
    if kids[0].tail and kids[0].tail.strip():
        return False
    return True


def extract_file(fpath: Path) -> list[dict]:
    fname = fpath.name.replace(".nxml", "")
    tree = ET.parse(fpath)
    root = tree.getroot()
    title_el = root.find(".//title")
    title = title_el.text if title_el is not None else fname
    sections = root.findall(".//sec")
    saved: list[dict] = []
    j = 0
    for sec in sections:
        sec_title_el = sec.find("./title")
        sec_title = sec_title_el.text.strip() if sec_title_el is not None and sec_title_el.text else ""
        sub_title = ""
        prefix = " -- ".join([title, sec_title])
        last_text = None
        last_json: dict | None = None
        last_node = None
        for ch in sec:
            if is_subtitle(ch):
                last_text = None
                last_json = None
                sub_title = extract_text(ch)
                prefix = " -- ".join(prefix.split(" -- ")[:2] + [sub_title])
            elif ch.tag == "p":
                curr_text = extract_text(ch)
                if last_text is not None and len(curr_text) < 200 and len(last_text + curr_text) < 1000:
                    merged = " ".join([last_json["content"], curr_text])
                    last_json = {
                        "id": last_json["id"],
                        "title": last_json["title"],
                        "content": merged,
                    }
                    saved[-1] = last_json
                    last_text = merged
                else:
                    last_text = curr_text
                    last_json = {
                        "id": f"{fname}_{j}",
                        "title": prefix,
                        "content": curr_text,
                    }
                    saved.append(last_json)
                    j += 1
            elif ch.tag == "list":
                list_text = [extract_text(c) for c in ch]
                joined = " ".join(list_text)
                if last_text is not None and len(joined + last_text) < 1000:
                    merged = " ".join([last_json["content"]] + list_text)
                    last_json = {
                        "id": last_json["id"],
                        "title": last_json["title"],
                        "content": merged,
                    }
                    saved[-1] = last_json
                    last_text = merged
                elif len(joined) < 1000:
                    last_text = joined
                    last_json = {"id": f"{fname}_{j}", "title": prefix, "content": last_text}
                    saved.append(last_json)
                    j += 1
                else:
                    last_text = None
                    last_json = None
                    for c in list_text:
                        saved.append(
                            {"id": f"{fname}_{j}", "title": prefix, "content": c}
                        )
                        j += 1
            if last_node is not None and is_subtitle(last_node):
                sub_title = ""
                prefix = " -- ".join([title, sec_title])
            last_node = ch
    return saved


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nxml-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    n_files = 0
    n_rows = 0
    for fpath in sorted(args.nxml_dir.glob("*.nxml")):
        rows = extract_file(fpath)
        if not rows:
            continue
        out = args.out_dir / f"{fpath.stem}.jsonl"
        with out.open("w") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        n_files += 1
        n_rows += len(rows)
    print(json.dumps({"chunk_files": n_files, "chunk_rows": n_rows, "out_dir": str(args.out_dir)}))


if __name__ == "__main__":
    main()
