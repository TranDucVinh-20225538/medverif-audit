#!/usr/bin/env python3
"""Render annotation/iaa_v1/GUIDELINES_{en,vi}.md to PDF (markdown -> HTML -> LibreOffice).

Needs the `markdown` package and `soffice` (LibreOffice) on PATH. pandoc is not required.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

D = Path(__file__).resolve().parents[1] / "annotation" / "iaa_v1"
CSS = """body{font-family:'DejaVu Sans','Noto Sans',Arial,sans-serif;font-size:10.5pt;line-height:1.35}
h1{font-size:17pt}h2{font-size:14pt;margin-top:16pt}h3{font-size:12pt}
table{border-collapse:collapse;margin:6pt 0}td,th{border:1px solid #888;padding:3pt 5pt;vertical-align:top}
th{background:#ddebf7}code{font-family:'DejaVu Sans Mono',monospace;font-size:9.5pt}"""


def main():
    names = sys.argv[1:] or ["GUIDELINES_en", "GUIDELINES_vi"]
    with tempfile.TemporaryDirectory() as td:
        for n in names:
            html = markdown.markdown((D / (n + ".md")).read_text(encoding="utf-8"), extensions=["tables"])
            lang = "vi" if n.endswith("_vi") else "en"
            hp = Path(td) / (n + ".html")
            hp.write_text('<!DOCTYPE html><html lang="%s"><head><meta charset="utf-8"><style>%s</style></head><body>%s</body></html>'
                          % (lang, CSS, html), encoding="utf-8")
            subprocess.run(["soffice", "--headless", "--convert-to", "pdf:writer_web_pdf_Export", "--outdir", str(D), str(hp)],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("wrote", D / (n + ".pdf"))


if __name__ == "__main__":
    main()
