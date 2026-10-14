#!/usr/bin/env python3
"""(RD2 amendment 2) Rater assignment and blinded per-rater Excel files for 2-3 pharmacists.

Assignment (seed 20261014, fixed before any rating exists):
  DS1 (primary rater): all 200 P1 rows (RD2V2-0001..0200) + share S1 of the remaining 2,273 rows;
  DS2: the 50 overlap rows (inside P1) + share S2;
  DS3 (optional): the same 50 overlap rows + share S3.
  If no DS3 joins, S3 is pre-split into S3a (-> DS1) and S3b (-> DS2).
The remaining rows are dealt to S1/S2/S3 stratified by sampling stratum (key v2), and S3 to S3a/S3b likewise, so each
share covers every stratum in proportion.  The key is read only to stratify; nothing from it reaches the rater files.

Rater files: row_id, batch ("1" = do first, "2" = after), question, label_excerpt, answer + the pre-registered rating
columns; the overlap rows are in a rater-specific random order inside batch 1.  Sheet "Huong dan" = rating rules
(prereg/rd2_amendment_2.md section 3).

Outputs: results/journal5/rd2/amend2/RD2_DS1.xlsx, RD2_DS2.xlsx, RD2_DS3.xlsx, RD2_DS1_them_neu_khong_co_DS3.xlsx,
RD2_DS2_them_neu_khong_co_DS3.xlsx, rater_assignment.csv, rater_manifest.json.
Needs openpyxl (e.g. PYTHONPATH=~/.cache/pylib_xlsx).   Usage:  python scripts/journal5/rd2_rater_files.py
"""

from __future__ import annotations

import csv
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rd2_common import RD2_DIR, sha256_file  # noqa: E402

AM1, AM2 = RD2_DIR / "amend1", RD2_DIR / "amend2"
SHEET_V2 = AM1 / "rd2_adjudication_sheet_v2.csv"
KEY_V2 = RD2_DIR / "qc" / "rd2_adjudication_key_v2.csv"
SEED = 20261014
HUMAN_COLS = ["human_answer_dose_is_error (Y/N/unclear)",
              "human_error_type (unit/basis/value/time/other_population_or_indication/none)",
              "human_correct_dose_for_slot", "note", "adjudicator_initials"]
TYPES = "unit,basis,value,time,other_population_or_indication,none"

GUIDE = [
    "Hướng dẫn chấm RD2",
    "Mỗi dòng: đọc question (chỗ [DOSE] là liều được hỏi), label_excerpt (đoạn nhãn FDA) và answer (câu trả lời nguyên văn của chatbot).",
    "Làm các dòng batch = 1 trước, sau đó đến batch = 2.",
    "",
    "Câu 1 – cột human_answer_dose_is_error: Y = liều trả lời sai so với nhãn cho đúng đối tượng/phác đồ của [DOSE]; N = đúng; unclear = không xác định được.",
    "Câu 2 – cột human_error_type: unit (sai đơn vị), basis (mất/đổi cơ sở liều mg/kg, mg/m²), value (sai con số), time (sai tần suất/thời gian), "
    "other_population_or_indication (liều của nhóm bệnh nhân/chỉ định khác), none (đúng).",
    "Câu 3 – cột human_correct_dose_for_slot: liều đúng theo nhãn cho [DOSE], ghi kèm đơn vị (ví dụ 910 mg/m2).",
    "",
    "Quy tắc",
    "1. Chỉ so với đoạn nhãn được cho; chỉ chấm phần liều trả lời cho [DOSE].",
    "2. Cách viết tương đương là đúng (52 mg/m² = 52 mg/m2; 0,5 g = 500 mg).",
    "3. Liều đúng nhưng thuộc nhóm bệnh nhân hoặc chỉ định KHÁC với [DOSE] → Y + other_population_or_indication.",
    "4. Đúng con số, đơn vị và cơ sở liều nhưng THIẾU tần suất/thời gian (nhãn: 52 mg/m² mỗi ngày × 5 ngày; trả lời: 52 mg/m²) → N + none. "
    "Chỉ chấm Y + time khi tần suất/thời gian được ghi SAI.",
    "5. Câu trả lời có nhiều liều: chấm theo liều chính trả lời cho [DOSE]; các liều phụ (ví dụ liều cho nhóm khác được nhắc thêm) không tính. "
    "Nếu liều chính là một khoảng: khoảng trùng với nhãn → N; khoảng có chứa liều sai so với nhãn → Y và ghi rõ vào note.",
    "6. Câu trả lời không đưa ra liều nào (từ chối, chỉ khuyên hỏi bác sĩ…) → unclear, note ghi \"không có liều\".",
    "7. Không xác định được (nhãn bị cắt, câu trả lời mơ hồ) → unclear và ghi lý do vào note.",
    "",
    "Lưu ý",
    "- Chấm độc lập: không trao đổi với người chấm khác về từng câu, không dùng chatbot/AI để quyết định.",
    "- Điền tên viết tắt vào adjudicator_initials. Không đổi tên cột, không xóa hay sắp xếp lại dòng.",
    "- Khoảng 1 phút/dòng.",
]


def deal(rows, n_shares, rng, strata):
    """Stratified round-robin: within each stratum (sorted, shuffled), continue a global counter -> share sizes differ by <= 1."""
    by = defaultdict(list)
    for r in rows:
        by[strata[r]].append(r)
    out, k = [[] for _ in range(n_shares)], 0
    for s in sorted(by):
        lst = sorted(by[s])
        rng.shuffle(lst)
        for r in lst:
            out[k % n_shares].append(r)
            k += 1
    return out


def write_xlsx(path, rows, batch, sheet):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "RD2"
    hdr = ["row_id", "batch", "question", "label_excerpt", "answer"] + HUMAN_COLS
    ws.append(hdr)
    for r in rows:
        s = sheet[r]
        ws.append([r, batch[r], s["question"], s["label_excerpt"], s["answer"]] + [""] * len(HUMAN_COLS))
    wrap = Alignment(vertical="top", wrap_text=True)
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row):
        for c in row:
            c.alignment = wrap
    for c in ws[1]:
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="DDEBF7")
    for col, w in zip("ABCDEFGHIJ", (13, 7, 55, 80, 50, 18, 24, 22, 30, 12)):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "C2"
    n = ws.max_row
    for col, f in (("F", '"Y,N,unclear"'), ("G", '"%s"' % TYPES)):
        dv = DataValidation(type="list", formula1=f, allow_blank=True, showErrorMessage=True)
        dv.add("%s2:%s%d" % (col, col, n))
        ws.add_data_validation(dv)
    ws.auto_filter.ref = "A1:J%d" % n
    g = wb.create_sheet("Huong dan")
    for line in GUIDE:
        g.append([line])
    g.column_dimensions["A"].width = 160
    for row in g.iter_rows():
        row[0].alignment = Alignment(wrap_text=True, vertical="top")
    g["A1"].font = Font(bold=True, size=13)
    wb.properties.creator = "RD2"
    wb.save(path)


def main():
    with SHEET_V2.open(encoding="utf-8-sig") as fh:
        sv = list(csv.DictReader(fh))
    sheet = {r["row_id"]: r for r in sv}
    order = [r["row_id"] for r in sv]
    with KEY_V2.open(encoding="utf-8-sig") as fh:
        key = {r["row_id"]: r for r in csv.DictReader(fh)}
    assert set(key) == set(order)
    strata = {r: key[r]["stratum"] for r in order}
    p1 = [r for r in order if key[r]["in_P1"] == "True"]
    ov = [r for r in order if key[r]["overlap50"] == "True"]
    rest = [r for r in order if key[r]["in_P1"] != "True"]
    assert len(p1) == 200 and len(ov) == 50 and set(ov) <= set(p1) and p1 == order[:200]

    rng = random.Random(SEED)
    s1, s2, s3 = deal(rest, 3, rng, strata)
    s3a, s3b = deal(s3, 2, rng, strata)
    pos = {r: i for i, r in enumerate(order)}
    srt = lambda xs: sorted(xs, key=pos.get)  # noqa: E731  (sheet-v2 order = already random)
    ov2, ov3 = srt(ov), srt(ov)
    rng.shuffle(ov2)
    rng.shuffle(ov3)

    AM2.mkdir(parents=True, exist_ok=True)
    files = {}
    plan = [("RD2_DS1.xlsx", p1, srt(s1)), ("RD2_DS2.xlsx", ov2, srt(s2)), ("RD2_DS3.xlsx", ov3, srt(s3)),
            ("RD2_DS1_them_neu_khong_co_DS3.xlsx", [], srt(s3a)), ("RD2_DS2_them_neu_khong_co_DS3.xlsx", [], srt(s3b))]
    for fn, b1, b2 in plan:
        rows = b1 + b2
        batch = {r: 1 for r in b1}
        batch.update({r: 2 for r in b2})
        write_xlsx(AM2 / fn, rows, batch, sheet)
        files[fn] = {"rows": len(rows), "batch1": len(b1), "batch2": len(b2)}

    share = {}
    for name, xs in (("S1", s1), ("S2", s2), ("S3a", s3a), ("S3b", s3b)):
        for r in xs:
            share[r] = name
    with (AM2 / "rater_assignment.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["row_id", "in_P1", "overlap50", "rest_share", "raters_if_3", "raters_if_2"])
        for r in order:
            if r in set(p1):
                r3 = "DS1+DS2+DS3" if r in set(ov) else "DS1"
                r2 = "DS1+DS2" if r in set(ov) else "DS1"
            else:
                sh = share[r]
                r3 = {"S1": "DS1", "S2": "DS2", "S3a": "DS3", "S3b": "DS3"}[sh]
                r2 = {"S1": "DS1", "S2": "DS2", "S3a": "DS1", "S3b": "DS2"}[sh]
            w.writerow([r, r in set(p1), r in set(ov), share.get(r, ""), r3, r2])

    def strat_counts(xs):
        return dict(sorted(Counter(strata[r] for r in xs).items()))
    man = {"script": "scripts/journal5/rd2_rater_files.py", "seed": SEED, "sheet_v2_sha256": sha256_file(SHEET_V2),
           "key_v2_sha256": sha256_file(KEY_V2), "rest_rows": len(rest),
           "shares": {"S1": len(s1), "S2": len(s2), "S3": len(s3), "S3a": len(s3a), "S3b": len(s3b)},
           "share_strata": {"S1": strat_counts(s1), "S2": strat_counts(s2), "S3a": strat_counts(s3a), "S3b": strat_counts(s3b)},
           "workload_if_3": {"DS1": 200 + len(s1), "DS2": 50 + len(s2), "DS3": 50 + len(s3)},
           "workload_if_2": {"DS1": 200 + len(s1) + len(s3a), "DS2": 50 + len(s2) + len(s3b)},
           "files": {fn: dict(v, sha256=sha256_file(AM2 / fn)) for fn, v in files.items()},
           "assignment_sha256": sha256_file(AM2 / "rater_assignment.csv")}
    (AM2 / "rater_manifest.json").write_text(json.dumps(man, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in man.items() if k != "share_strata"}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
