# Expanded DOSE spot-check failure types (dose2 PI notes)

- Labeled rows: **54** (34 Y / 20 N → **63.0%** Y; gate **85%**).

## Tag counts (N rows; multi-tag allowed)

- **missing_drug_or_generic_subject**: 9
- **c0_context_stripped**: 3
- **non_dose_volume**: 3
- **other**: 3
- **thousands_separator_bug**: 2
- **weak_e1_contrast**: 2
- **threshold_context**: 1

## Examples

### c0_context_stripped
- **D0020**: C0: thiếu tên thuốc (edoxaban) và bỏ bối cảnh NVAF
- **D0167**: C0: bỏ bối cảnh viêm phổi cộng đồng không nặng
- **D0195**: C0: bỏ bối cảnh INH, câu thành khuyến cáo chung

### missing_drug_or_generic_subject
- **D0020**: C0: thiếu tên thuốc (edoxaban) và bỏ bối cảnh NVAF
- **D0079**: C0: thiếu tên thuốc (methylene blue), khoảng 1 to 2 mg/kg bị rút còn 2
- **D0092**: C0: thiếu tên thuốc (baricitinib)
- **D0155**: C0: thiếu tên thuốc (albiglutide)
- **D0204**: C0: "The specific drug" gượng, evidence không có tên thuốc

### non_dose_volume
- **D0027**: LOẠI: 60 mL là thể tích khối máu tụ, không phải liều
- **D0122**: LOẠI: 1500 mL là lượng máu mất, không phải liều
- **D0367**: LOẠI: 2 mL là sức chứa bao khớp, không phải liều; C0 còn bỏ "1 to"

### other
- **D0259**: E1: 5 mg chỉ là liều dùng trong nghiên cứu dược động học, đổi liều không làm claim về thể tích phân bố sai rõ ràng
- **D0308**: E1: 10 mg vẫn có thể hiệu quả (evidence nhắc viên 10 mg), không mâu thuẫn rõ
- **D0345**: E1: câu sau sửa thành "60 mg rồi tăng lên 60 mg/d", tự mâu thuẫn trong câu

### thousands_separator_bug
- **D0043**: E1: 1,200 thành "1,2000", sai định dạng số
- **D0140**: E1: 1,500 thành "1,1000", sai số và sai định dạng

### threshold_context
- **D0212**: C0+E1: "The study" không rõ; sửa ngưỡng "above 100 mg" thành 200 mg chưa chắc mâu thuẫn

### weak_e1_contrast
- **D0212**: C0+E1: "The study" không rõ; sửa ngưỡng "above 100 mg" thành 200 mg chưa chắc mâu thuẫn
- **D0342**: E1: 1200 mg once daily vẫn khớp tổng liều 600 mg x2, mâu thuẫn không rõ

