import json, sys
a, b = (json.load(open(p)) for p in sys.argv[1:3])
k = lambda r: (r["table"], r["checker"], r["metric"])
A = {k(r): r for r in a}; B = {k(r): r for r in b}
for key in sorted(set(A) | set(B)):
    ra, rb = A.get(key), B.get(key)
    if ra is None: print("ADDED  ", " / ".join(key), "=", rb["value"], f"[{rb['env']}, {rb['status']}]"); continue
    if rb is None: print("REMOVED", " / ".join(key), "=", ra["value"]); continue
    ch = [f"{f}: {ra[f]} -> {rb[f]}" for f in ("value", "n") if ra[f] != rb[f]]
    if ch: print("VALUE  ", " / ".join(key), "|", "; ".join(ch))
from collections import Counter
for name, rows in (("before", a), ("after", b)):
    print(name, dict(Counter(r["status"] for r in rows)), dict(Counter(r["env"] for r in rows)))
