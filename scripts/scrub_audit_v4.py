#!/usr/bin/env python3
"""Audit snapshot v4 scrubber: re-applies the v3 exclusions and adds anonymity scrubbing.

Input: an existing snapshot zip (--src-zip, e.g. a v3/v4 zip built on the HPC with the untracked inputs) or a repo
checkout (--src-repo, file selection = scripts/build_audit_zip_v3.collect()). Output: a new zip + manifest.

Extra scrubbing on top of build_audit_zip_v3.SCRUB:
  * personal names / account names (advisor, author, other HPC accounts), student id, GitHub username
  * hostnames: bright92(.cm.cluster), *.cm.cluster, node001/002/004 -> computeA/B/C,
    node30 -> gpunode (case-preserving, applied to text AND file paths so loaders stay consistent)
  * absolute paths: /data2/..., /root/medverif-audit, /home/<user>, /Users/<user>, Cursor attachment dirs
  * e-mail addresses outside public-dataset text
  * Vietnamese reviewer free text: CSV note/notes cells (qc/*.csv) and Vietnamese segments in notes/, scripts/,
    src/ etc. are replaced by a neutral English label that keeps machine-relevant tags (e.g. "duplicate of T24_003",
    "not a dose", "missing drug name"); the keyword literals in the scripts that parse those notes are translated
    with the same table so note-dependent outputs (t24b duplicate filter, dose2 failure tags) still reproduce.
    Label value LOẠI (= exclude) in qc/dose3_labels.csv and scripts/apply_dose3_main_audit.py -> EXCLUDE.
Public-dataset text (LLM-AggreFact, Wikipedia/T18, FDA labels, T15 training pairs) is left untouched.

Usage:
  scrub_audit_v4.py --src-zip release/audit_snapshot_v4.zip --out release/audit_snapshot_v4.zip [--head <sha>]
  scrub_audit_v4.py --src-repo . --out /tmp/audit_snapshot_v4.zip
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

VN_CHARS = ("ăâđêôơưĂÂĐÊÔƠƯạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ"
            "ẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼẾỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỴỶỸáàãéèíìóòõúùýÁÀÃÉÈÍÌÓÒÕÚÙÝ")
# characters that are (practically) only Vietnamese; â/ê/ô/á/é... also occur in French/Portuguese names
VN_STRICT = re.compile("[ăđơưĂĐƠƯạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ"
                       "ẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼẾỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỴỶỸ]")
VN_ANY = re.compile(f"[{VN_CHARS}]")
# unaccented Vietnamese function words (reviewer notes typed without diacritics)
VN_PLAIN = re.compile(r"\b(?:trong|khong|duoc|nhung|voi|thuoc|lieu|cung|nay|rat|chi|thi|cua|nhan|sach)\b", re.I)

# Vietnamese reviewer keywords -> English tags (applied to notes and to the keyword literals in parsing scripts)
KEYWORDS = [
    ("Dòng trùng", "duplicate row"),
    ("trùng", "duplicate of"),
    ("sai định dạng số", "number format error"),
    ("không phải liều", "not a dose"),
    ("loại:", "exclude:"),
    ("thiếu tên thuốc", "missing drug name"),
    ("ngưỡng", "threshold"),
    ("bỏ bối cảnh", "context dropped"),
    ("mâu thuẫn không rõ", "unclear contradiction"),
    ("chưa chắc mâu thuẫn", "uncertain contradiction"),
    ("không ai viết", "unnatural form"),
]
# English cue strings that note-parsing scripts key on (scripts/log_dose2_failure_types.py); kept verbatim in the label
CUES = [r"1,\d{4}", r"\bthe gel\b", r"\bthe specific drug\b", r"\bthe study\b", r"\babove\b", r"\bat doses\b",
        r"\bcontext\b", r"\bweak e1\b", r"\bhematoma\b", r"\bblood loss\b", r"\bthousands\b", r"\bthreshold\b"]
NOTE_COLS = {"note", "notes", "comment", "comments", "remark", "reason", "pi_note"}

TEXT_SUFFIX = {".jsonl", ".json", ".md", ".csv", ".tsv", ".txt", ".py", ".sh", ".sbatch", ".toml", ".yaml", ".yml",
               ".cfg", ".ini", ".co", ".tex", ".log", ""}
PUBLIC_TEXT = ("data/t8/aggrefact/", "data/t15/", "data/t20/labels/", "data/t18/", "results/raw/t15",
               "results/raw/t18/", "results/raw_node30/t15", "results/raw/t8", "data/v3/instances_aggrefact",
               "data/t8/instances_aggrefact")
VN_FREE_TEXT_SCOPE = ("notes/", "scripts/", "src/", "analysis/", "tests/", "configs/", "config/", "jobs/",
                      "README.md", "paper_numbers_final.md", "release/")

# ordered (regex, replacement); applied to every text file
RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"(?:\$HOME|/data2/cmdir/home/[A-Za-z0-9_.-]+)/\.cursor/projects/[^/\"'\s]+/attachments/?"), "<attachments>/"),
    (re.compile(r"data2-hpcshared-[A-Za-z0-9_-]+"), "<cursor-project>"),
    (re.compile(r"/data2/hpcshared/medverif-(?:audit|wt-[A-Za-z0-9_.-]+)"), "<repo>"),
    (re.compile(r"/data2/cmdir/home/[A-Za-z0-9_.-]+"), "$HOME"),
    (re.compile(r"/data2/hpcshared/[A-Za-z0-9_.-]+"), "<shared>/<dir>"),
    (re.compile(r"/data2/[A-Za-z0-9_./-]*"), "<shared>"),
    (re.compile(r"/root/medverif-audit"), "<repo>"),
    (re.compile(r"/root/(?=[A-Za-z.])"), "$HOME/"),
    (re.compile(r"(?<![\w.:/])/home/[A-Za-z0-9_.-]+"), "$HOME"),
    (re.compile(r"(?<![\w.:/])/Users/[A-Za-z0-9_.-]+"), "$HOME"),
    (re.compile(r"~/kkk/"), "~/<secrets-dir>/"),
    (re.compile(r"\b[A-Za-z0-9-]+\.cm\.cluster\b"), "<login-node>"),
    (re.compile(r"\bbright92\b", re.I), "<login-node>"),
    (re.compile(r"\bnode001\b"), "computeA"), (re.compile(r"\bnode002\b"), "computeB"),
    (re.compile(r"\bnode004\b"), "computeC"),
    (re.compile(r"\bnode0\d\d\b"), "computeX"),
    (re.compile(r"Đào Quang Toàn|Dao Quang Toan", re.I), "<advisor>"),
    (re.compile(r"\bthầy\s+(?:Toàn|Toan)\b", re.I), "the advisor"),
    (re.compile(r"\btoandq\b"), "<user>"),
    (re.compile(r"\banhnv\b"), "<user2>"),
    (re.compile(r"\b(?:Toàn|Toan)\b"), "<advisor>"),
    (re.compile(r"TranDucVinh-20225538|TranDucVinh|\b20225538\b"), "<author-id>"),
    (re.compile(r"Trần Đức Vinh|Tran Duc Vinh|Trần Vinh|Tran Vinh", re.I), "<author>"),
    (re.compile(r"\bVinh-?(?=/)"), "<author-dir>"),
    (re.compile(r"\bVinh\b"), "<author>"),
    (re.compile(r"\bthầy\b", re.I), "advisor"),
]
NODE30 = re.compile(r"node30", re.I)
EMAIL = re.compile(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
EMAIL_KEEP = re.compile(r"@users\.noreply\.github\.com$|@example\.(?:com|org)$")


VN_WORDS = re.compile(r"\b(?:là|và|không|của|cho|thì|bị|đã|trùng|dòng|câu|nhầm|sửa|thành)\b", re.I)


def is_vn(s: str) -> bool:
    return bool(VN_STRICT.search(s) or (VN_ANY.search(s) and VN_WORDS.search(s)))


def node30_sub(s: str) -> str:
    def rep(m: re.Match) -> str:
        t = m.group(0)
        return "GPUNODE" if t.isupper() else ("Gpunode" if t[0].isupper() else "gpunode")
    return NODE30.sub(rep, s)


def neutral_note(note: str) -> str:
    low = note.lower()
    tags = []
    for m in re.finditer(r"trùng\s+(T24_\d+|D\d{4})", note, re.I):
        tags.append(f"duplicate of {m.group(1)}")
    for vn, en in KEYWORDS:
        if vn.lower() in low and not (vn == "trùng" and tags) and en not in tags:
            tags.append(en)
    cues = []
    for c in CUES:
        for m in re.finditer(c, note, re.I):
            if m.group(0) not in cues:
                cues.append(m.group(0))
    return ("[reviewer note withheld" + (f"; tags: {'; '.join(tags)}" if tags else "")
            + (f"; cues: {'; '.join(cues)}" if cues else "") + "]")


def scrub_csv(text: str, counts: dict) -> str:
    bom = text.startswith("\ufeff")
    body = text[1:] if bom else text
    nl = "\r\n" if "\r\n" in body[:5000] else "\n"
    rows = list(csv.reader(io.StringIO(body, newline="")))
    if not rows:
        return text
    head = [h.strip().lower() for h in rows[0]]
    changed = False
    for r in rows[1:]:
        for i, v in enumerate(r):
            col = head[i] if i < len(head) else ""
            if v.strip() == "LOẠI":
                r[i] = "EXCLUDE"; changed = True; counts["label_LOAI"] += 1
            elif col in NOTE_COLS and (VN_ANY.search(v) or VN_PLAIN.search(v)):
                r[i] = neutral_note(v); changed = True; counts["vn_note_cells"] += 1
    if not changed:
        return text
    out = io.StringIO(newline="")
    w = csv.writer(out, lineterminator=nl)
    w.writerows(rows)
    return ("\ufeff" if bom else "") + out.getvalue()


def scrub_vn_free_text(text: str, path: str, counts: dict) -> str:
    if path.endswith(".py"):
        for vn, en in KEYWORDS:
            if vn in text:
                counts["code_keywords"] += text.count(vn)
                text = text.replace(vn, en)
        if '"LOẠI"' in text:
            text = text.replace('"LOẠI"', '"EXCLUDE"'); counts["label_LOAI"] += 1
        return text
    if path.endswith((".json", ".jsonl")):
        def walk(o):
            if isinstance(o, str):
                if is_vn(o):
                    counts["vn_json_strings"] += 1
                    return neutral_note(o)
                return o
            if isinstance(o, list):
                return [walk(x) for x in o]
            if isinstance(o, dict):
                return {k: walk(v) for k, v in o.items()}
            return o
        try:
            if path.endswith(".jsonl"):
                before = counts["vn_json_strings"]
                new = "".join(json.dumps(walk(json.loads(l)), ensure_ascii=False) + "\n" if l.strip() else l
                              for l in text.splitlines(keepends=True))
                return new if counts["vn_json_strings"] > before else text
            before = counts["vn_json_strings"]
            obj = walk(json.loads(text))
            return json.dumps(obj, ensure_ascii=False, indent=2) + "\n" if counts["vn_json_strings"] > before else text
        except json.JSONDecodeError:
            pass
    # markdown / other: replace each delimited segment that contains Vietnamese
    out = []
    for line in text.splitlines(keepends=True):
        if not VN_ANY.search(line):
            out.append(line); continue
        m = re.match(r"^(\s*(?:[-*]|\d+\.)?\s*(?:\*\*[^*]+\*\*:?\s*)?)(.*?)(\r?\n?)$", line)
        prefix, rest, eol = m.group(1), m.group(2), m.group(3)
        parts = re.split(r"(\|)", rest)
        parts = [neutral_note(p) if VN_ANY.search(p) else p for p in parts]
        counts["vn_text_lines"] += 1
        out.append(prefix + "".join(parts) + eol)
    return "".join(out)


def scrub_text(path: str, text: str, counts: dict) -> str:
    for rx, rep in RULES:
        text, n = rx.subn(rep, text)
        if n:
            counts[f"rule_{RULES.index((rx, rep)):02d}->{rep}"] += n
    if NODE30.search(text):
        counts["gpu_host_label"] += len(NODE30.findall(text))
        text = node30_sub(text)
    public = path.startswith(PUBLIC_TEXT)
    if not public:
        def em(m):
            if EMAIL_KEEP.search(m.group(0)) or path.startswith(("data/", "results/")):
                return m.group(0)
            counts["emails"] += 1
            return "<email>"
        text = EMAIL.sub(em, text)
    if path.startswith("qc/") and path.endswith(".csv"):
        text = scrub_csv(text, counts)
    elif path.startswith(VN_FREE_TEXT_SCOPE):
        text = scrub_vn_free_text(text, path, counts)
    return text


def iter_source(args) -> list[tuple[str, bytes]]:
    if "--src-zip" in args:
        z = zipfile.ZipFile(args[args.index("--src-zip") + 1])
        return [(n, z.read(n)) for n in z.namelist() if not n.endswith("/")
                and not re.match(r"(AUDIT_SNAPSHOT_V\d+_README\.md|release/audit_snapshot_v\d+_manifest\.json)$", n)]
    root = Path(args[args.index("--src-repo") + 1]).resolve()
    sys.path.insert(0, str(root / "scripts"))
    import build_audit_zip_v3 as v3  # noqa: E402
    v3.ROOT = root
    return [(p.relative_to(root).as_posix(), p.read_bytes()) for p in v3.collect()]


def main() -> None:
    args = sys.argv[1:]
    if "--out" not in args or not ({"--src-zip", "--src-repo"} & set(args)):
        sys.exit(__doc__)
    out_zip = Path(args[args.index("--out") + 1])
    head = args[args.index("--head") + 1] if "--head" in args else "unknown"
    here = Path(__file__).resolve().parent
    sys.path.insert(0, str(here))
    try:
        import build_audit_zip_v3 as v3
        excluded, secret_re = v3.excluded, v3.SECRET_RE
    except ImportError:
        excluded, secret_re = (lambda rel: False), re.compile(r"$^")
    from collections import Counter
    counts: Counter = Counter()
    files, hits, renamed = {}, [], 0
    for rel, raw in iter_source(args):
        if excluded(rel):
            counts["excluded_by_v3_policy"] += 1
            continue
        new_rel = node30_sub(rel)
        renamed += new_rel != rel
        data = raw
        if Path(rel).suffix.lower() in TEXT_SUFFIX:
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = None
            if text is not None:
                hits += [f"{rel}: {m.group(0)[:10]}…" for m in secret_re.finditer(text)]
                new = scrub_text(rel, text, counts)
                if new != text:
                    counts["files_changed"] += 1
                data = new.encode("utf-8")
        files[new_rel] = data
    if hits:
        sys.exit("SECRET SCAN FAILED:\n" + "\n".join(hits[:20]))
    tag = re.search(r"(v\d+)", out_zip.name).group(1) if re.search(r"v\d+", out_zip.name) else "v4"
    manifest = {"built_at": datetime.now(timezone.utc).isoformat(), "git_head": head, "scrubber": "scripts/scrub_audit_v4.py",
                "files_renamed_gpu_label": renamed, "counts": dict(counts),
                "files": {k: hashlib.sha256(v).hexdigest() for k, v in sorted(files.items())}}
    readme = (f"# Audit snapshot {tag} (anonymized)\n\nBuilt {manifest['built_at']} from commit `{head}` by "
              "`scripts/scrub_audit_v4.py` (v3 exclusions + anonymity scrub).\n\n"
              "Absolute paths -> `<repo>`, `<shared>`, `$HOME`; account / person names -> `<user>`, `<advisor>`, "
              "`<author>`; hostnames -> `<login-node>`, `computeA/B/C`; the GPU host label -> `gpunode` "
              "(also in file names, e.g. `results/raw_gpunode/`), consistently in code and data so loaders still work.\n"
              "Vietnamese reviewer notes in `qc/*.csv` are replaced by `[reviewer note withheld; tags: ...]`; labels "
              "(Y/N, categories) are unchanged except `LOẠI` -> `EXCLUDE` (same change in the parsing script).\n"
              "Public-dataset text (LLM-AggreFact, Wikipedia, FDA labels) is unmodified and may contain third-party "
              "names, e-mails and non-ASCII letters.\n").replace("LOẠI", "LOAI")
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_zip.with_suffix(".zip.tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for k in sorted(files):
            z.writestr(k, files[k])
        z.writestr(f"AUDIT_SNAPSHOT_{tag.upper()}_README.md", readme)
        z.writestr(f"release/audit_snapshot_{tag}_manifest.json", json.dumps(manifest, indent=1) + "\n")
    tmp.replace(out_zip)
    summary = {k: v for k, v in manifest.items() if k != "files"}
    summary.update(n_files=len(files), zip_bytes=out_zip.stat().st_size,
                   zip_sha256=hashlib.sha256(out_zip.read_bytes()).hexdigest())
    out_zip.with_name(f"audit_snapshot_{tag}_manifest.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps({k: summary[k] for k in ("n_files", "zip_bytes", "files_renamed_gpu_label")}), dict(counts))


if __name__ == "__main__":
    main()
