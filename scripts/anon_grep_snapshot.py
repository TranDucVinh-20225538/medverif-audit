#!/usr/bin/env python3
"""Anonymity grep over an unzipped snapshot tree. Usage: anon_grep.py <dir> [--examples N]"""
import re, sys, collections, os
root = sys.argv[1]
NEX = int(sys.argv[sys.argv.index("--examples") + 1]) if "--examples" in sys.argv else 2
VN = "ăâđêôơưĂÂĐÊÔƠƯạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼẾỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỴỶỸ"
PATS = {
    # substring (as requested) and word-boundary variants for the short names
    "toan(substr)": r"toan", "toan(word)": r"\btoan\b|toandq",
    "vinh(substr)": r"vinh", "tran(word)": r"\btran\b|tranduc", "tran(substr)": r"tran",
    "dao(word)": r"\bdao\b", "dao(substr)": r"dao", "quang": r"quang", "cubo": r"cubo",
    "hpcshared": r"hpcshared", "bright92": r"bright92", "cm.cluster": r"cm\.cluster",
    "node30": r"node30", "node3x-host": r"\bnode\d{2,3}\b(?!_)",
    "@gmail": r"@gmail", "email": r"[\w.+-]+@[\w-]+\.[\w.]+", "@(any)": r"@",
    "/home/": r"/home/", "/root/": r"/root/", "/Users/": r"/users/", "tmlr": r"tmlr",
    "thầy": r"thầy|thay\b", "vn_diacritic": f"[{VN}]",
}
CRE = {k: re.compile(v, re.I) for k, v in PATS.items()}
hits = collections.defaultdict(lambda: collections.Counter()); ex = collections.defaultdict(list)
for dp, _, fs in os.walk(root):
    for f in fs:
        p = os.path.join(dp, f); rel = os.path.relpath(p, root)
        for k, c in CRE.items():
            if c.search(rel): hits[k]["<FILENAME>" + rel] += 1
        try:
            data = open(p, "rb").read()
        except Exception:
            continue
        if b"\x00" in data[:4096]:
            continue  # binary
        t = data.decode("utf-8", "replace")
        if rel.endswith((".json", ".jsonl")):  # also see \\uXXXX-escaped text
            t = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), t)
        for k, c in CRE.items():
            n = 0
            for m in c.finditer(t):
                n += 1
                if len(ex[(k, rel)]) < NEX:
                    s = t[max(0, m.start() - 40): m.end() + 40].replace("\n", " ")
                    ex[(k, rel)].append(s)
            if n: hits[k][rel] += n
for k in PATS:
    h = hits.get(k, {})
    print(f"== {k}: {sum(h.values())} hits in {len(h)} files")
    for rel, n in sorted(h.items(), key=lambda x: -x[1])[:15]:
        print(f"   {n:6d}  {rel}  e.g. {ex.get((k, rel), [''])[:1]}")
