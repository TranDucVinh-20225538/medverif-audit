# Hướng dẫn gán nhãn: IAA v1, "Same Dose, Different Verdict"

**Phiên bản:** iaa_v1 (tháng 10/2026) | **Số mục:** 150 | **Thời gian ước tính:** khoảng 2–3 giờ (khoảng 1 phút/mục; có thể nghỉ giữa chừng và làm thành nhiều buổi)

## 1. Mục đích

Chúng tôi đang đánh giá các **mô hình kiểm chứng (fact-checker) cho văn bản y khoa**. Các mô hình này đọc một đoạn *bằng chứng* (evidence, trích từ sách giáo khoa hoặc bài báo y khoa) và quyết định xem một *mệnh đề* (claim) có được bằng chứng đó ủng hộ hay không. Để kiểm tra chúng, chúng tôi tạo ra những chỉnh sửa nhỏ, có kiểm soát trên các mệnh đề về liều thuốc, khuyến cáo điều trị, v.v. Có loại chỉnh sửa phải **giữ nguyên** ý nghĩa (mô hình nên giữ nguyên kết luận). Có loại phải **làm sai** ý nghĩa (mô hình nên đổi kết luận).

Mọi chỉnh sửa đều được tạo tự động, sau đó được một tác giả kiểm tra. Chúng tôi cần **ý kiến độc lập của một chuyên gia lâm sàng** để đo mức độ tin cậy của việc kiểm tra đó (độ đồng thuận giữa người gán nhãn, hệ số Cohen's kappa). Với các lỗi liều, chúng tôi cũng mong nhận được đánh giá lâm sàng của thầy/cô về **mức độ nguy hại** nếu liều sai được dùng thật.

Thầy/cô **không** cần đánh giá các mô hình và không cần biết kết quả của chúng. Không có câu hỏi đánh đố. Nếu phân vân, xin chọn *Unsure* và ghi chú thêm.

## 2. Tài liệu nhận được

- `annotation_sheet.xlsx`: tệp chính (trang *Annotation*; các cột trả lời có danh sách chọn sẵn). `annotation_sheet.csv` có nội dung tương tự, dùng khi không có Excel.
- Tài liệu này (`GUIDELINES_vi.md` / `.pdf`), cùng bản tiếng Anh (`GUIDELINES_en.md` / `.pdf`).

Mỗi dòng gồm các cột sau:

| cột | ý nghĩa |
|---|---|
| `item_id` | mã mục ẩn danh (ví dụ `IAA1-3f9a0c`). Xin đừng sửa. |
| `condition` | loại chỉnh sửa (xem §3) |
| `intended_change` | chỉnh sửa này **lẽ ra** phải làm gì |
| `evidence` | đoạn bằng chứng (với mục *Unit error* sửa trong bằng chứng, đây là bằng chứng **đã bị sửa**) |
| `original_evidence` | **chỉ** có nội dung khi chính bằng chứng bị sửa |
| `what_changed` | phần khác biệt được tính tự động (`[cũ] -> [mới]`), chỉ để giúp nhìn nhanh chỗ sửa |
| `original_claim` | mệnh đề trước khi sửa |
| `edited_claim` | mệnh đề sau khi sửa (với mục *Base claim* thì không có chỉnh sửa) |
| **Q1, Q2, Q3, comment** | câu trả lời của thầy/cô |

Các mục được xếp ngẫu nhiên, các loại chỉnh sửa được trộn lẫn. Cùng một câu gốc có thể xuất hiện ở nhiều mục; xin đánh giá **từng dòng độc lập**.

## 3. Các câu hỏi

### Q1 (mọi dòng): *Mệnh đề sau chỉnh sửa có phải là một ví dụ hợp lệ của loại chỉnh sửa dự định không?*  Yes / No / Unsure

Đọc cột `intended_change`, rồi so sánh văn bản gốc với văn bản đã sửa (và đối chiếu bằng chứng khi cần). Chọn **Yes** nếu chỉnh sửa làm đúng và gọn gàng điều nó phải làm. Chọn **No** nếu không, ví dụ: nghĩa bị thay đổi trong khi lẽ ra phải giữ nguyên; "lỗi" tạo ra thực ra không sai; hoặc câu trở nên sai ngữ pháp hay kỳ quặc về mặt lâm sàng đến mức không còn kiểm tra đúng điều cần kiểm tra. Chọn **Unsure** nếu không quyết định được; xin ghi thêm nhận xét.

### Q2 (chỉ các dòng *Unit conversion*): *Có tương đương về mặt lâm sàng và tự nhiên không?*

- **Natural**: cùng một lượng thuốc, và được viết theo cách mà bác sĩ hoặc tờ hướng dẫn sử dụng thuốc có thể viết (ví dụ `0.5 g → 500 mg`).
- **Equivalent-unnatural**: về số học là cùng lượng, nhưng không ai viết như vậy (ví dụ `75 g → 75000 mg` glucose, `1 mg/kg → 1000 mcg/kg`).
- **Not equivalent**: quy đổi sai, hoặc lượng thuốc đã thay đổi.

### Q3 (chỉ các dòng *Unit error* và *Dose value error*): *Nếu liều sai này thực sự được dùng cho bệnh nhân, mức độ nguy hại sẽ thế nào?*

Giả sử liều **đã bị sửa** (liều sai) được dùng thật cho một bệnh nhân điển hình, trong bối cảnh mà mệnh đề mô tả, thay cho liều đúng. Xin đánh giá hậu quả **có khả năng xảy ra nhất**, không phải trường hợp xấu nhất có thể tưởng tượng. Thang đo dựa theo chỉ số sai sót dùng thuốc NCC MERP:

| Giá trị Q3 | ý nghĩa | tương ứng NCC MERP (gần đúng) |
|---|---|---|
| **None** | không gây hại (liều vẫn trong khoảng an toàn hoặc thường dùng, hoặc không có ý nghĩa lâm sàng) | C |
| **Minor** | có thể gây hại nhẹ, tạm thời, hoặc cần theo dõi thêm để xác nhận không có hại | D |
| **Moderate** | gây hại tạm thời, cần điều trị hoặc can thiệp, hoặc phải nhập viện hay kéo dài thời gian nằm viện | E–F |
| **Severe** | gây hại vĩnh viễn, đe dọa tính mạng (cần can thiệp để duy trì sự sống), hoặc tử vong | G–I |
| **Unsure** | không thể đánh giá (ví dụ không rõ thuốc hoặc bối cảnh) | – |

Q3 độc lập với Q1: xin vẫn đánh giá mức độ nguy hại kể cả khi Q1 = No (ví dụ, liều ×2 vẫn nằm trong khoảng của bằng chứng có thể là *No* ở Q1 và *None* ở Q3).

### comment (không bắt buộc)

Ghi bất cứ điều gì hữu ích, ví dụ lý do chọn *No* hoặc *Unsure*, cách viết tốt hơn, hay "bằng chứng bị cắt cụt". Có thể viết bằng tiếng Việt hoặc tiếng Anh.

## 4. Định nghĩa và ví dụ cho từng loại

Các ví dụ dưới đây **chỉ mang tính minh họa** (không phải các mục trong bảng).

### 4.1 Unit conversion: quy đổi đơn vị (giữ nguyên nghĩa)
Liều được viết lại bằng đơn vị khác và phải là **cùng một lượng**.
- `amoxicillin 0.5 g ba lần mỗi ngày` → `500 mg ba lần mỗi ngày`: Q1 **Yes**, Q2 **Natural**.
- `75 g glucose` → `75000 mg glucose`: Q1 **Yes** (cùng lượng), Q2 **Equivalent-unnatural**.
- `0.1 mg` → `10 mcg`: Q1 **No** (lượng đã thay đổi), Q2 **Not equivalent**.

### 4.2 Polarity flip: đảo nghĩa
Mệnh đề sau khi sửa phải nói điều **ngược lại** (khuyến cáo hoặc sự kiện), sao cho bằng chứng giờ đây mâu thuẫn với nó.
- `X được khuyến cáo (recommended) cho VVC` → `X chống chỉ định (contraindicated) cho VVC`: **Yes**.
- `nên tránh dùng khi mang thai` → `không cần tránh dùng khi mang thai`: **Yes**, nếu thực sự mang nghĩa ngược lại.
- `relatively contraindicated ở bệnh nhân động kinh` → `relatively indicated`: thường là **No**, vì "relatively indicated" không phải cách nói ngược tự nhiên và rõ ràng.
- Nếu chỉ phủ định một chi tiết phụ còn khuyến cáo chính không đổi: **No**.

### 4.3 Rephrase: diễn đạt lại (giữ nguyên nghĩa)
Thay đổi cách diễn đạt (ví dụ `should be given` → `ought to be given`); nghĩa lâm sàng phải **giữ nguyên**, kể cả mức độ khuyến cáo (must / should / may) và phạm vi áp dụng.
- `should be administered` → `ought to be administered`: **Yes**.
- `is recommended` → `is indicated`: **Yes** nếu mức độ khuyến cáo tương đương trong ngữ cảnh, **No** nếu làm thay đổi mức độ khuyến cáo.
- `may be used` → `must be used`: **No** (mức độ khuyến cáo đã thay đổi).

### 4.4 Frequency/route rewording: viết lại tần suất hoặc đường dùng (giữ nguyên nghĩa)
Tần suất hoặc đường dùng được viết theo cách khác; nghĩa phải **giữ nguyên** trong bối cảnh lâm sàng.
- `twice daily` → `every 12 hours`: **Yes** trong đa số trường hợp.
- `intravenously` → `IV`: **Yes**.
- `ba lần mỗi ngày trong bữa ăn` → `mỗi 8 giờ`: **No** (mất liên hệ với bữa ăn).
- `orally or intravenously` → `PO or IV`: **Yes**. Nếu chỉ một phần bị đổi khiến câu trở nên mơ hồ: **No**.

### 4.5 Unit error: lỗi đơn vị (làm sai nghĩa; giữ số, đổi đơn vị)
Con số giữ nguyên nhưng đơn vị bị đổi (ví dụ mg ↔ g, μg ↔ mg), khiến liều sai lệch rất lớn (×1000). Chỉnh sửa có thể nằm ở **mệnh đề** hoặc ở **bằng chứng** (khi đó cột `original_evidence` hiển thị bằng chứng gốc).
- `90 mg` → `90 g`: Q1 **Yes**; Q3 tùy thuốc (thường là **Severe**).
- Sửa trong bằng chứng: `200 mg` → `200 g`, mệnh đề giữ nguyên: Q1 **Yes** nếu mệnh đề và bằng chứng giờ đây mâu thuẫn rõ ràng.
- Q1 **No** nếu con số bị đổi đơn vị không phải là liều của thuốc, hoặc mâu thuẫn không thực sự tồn tại.

### 4.6 Dose value error: lỗi giá trị liều (làm sai nghĩa; nhân con số)
Con số liều được nhân **2** hoặc **10** (ví dụ `500 mg` → `1000 mg` hoặc `5000 mg`). Q1 hỏi: mệnh đề sau khi sửa có **sai rõ ràng so với bằng chứng** không?
- Bằng chứng: "liều khởi đầu 100 μg"; mệnh đề sửa thành "200 μg": **Yes**.
- Bằng chứng: "liều từ 50 đến 200 μg"; mệnh đề sửa thành "200 μg": **No** (vẫn nằm trong khoảng, nên chưa chắc sai).
- Bằng chứng: "≥200 mg có hiệu quả"; mệnh đề sửa thành "≥400 mg có hiệu quả": **No** (ngưỡng cao hơn không mâu thuẫn).
- Q3: đánh giá mức nguy hại của liều đã nhân (×2 thường là *None* hoặc *Minor*; ×10 thường là *Moderate* hoặc *Severe*, tùy khoảng điều trị của thuốc).

### 4.7 Base claim: mệnh đề gốc (không chỉnh sửa)
Ở đây thầy/cô đánh giá chính **mệnh đề gốc** (cột `edited_claim` ghi "no edit"). Q1 = **Yes** nếu mệnh đề (a) **trung thành** với bằng chứng (được ủng hộ đầy đủ, không thêm thông tin) **và** (b) **tự đủ nghĩa, đủ cụ thể**: người chỉ đọc mệnh đề vẫn biết đó là thuốc hoặc can thiệp nào, cho đối tượng hay bối cảnh nào, với liều nào. Q1 = **No** nếu mệnh đề không được ủng hộ, bị bóp méo, hoặc thiếu cụ thể (ví dụ "Thuốc được tiêm 50 μg nhiều lần mỗi ngày" mà không nêu tên thuốc, hoặc liều chỉ là chi tiết phụ trong câu).

## 5. Lưu ý thực hành

- Đánh giá từng dòng độc lập, và không tra cứu nguồn gốc của câu.
- Các đoạn bằng chứng được sao chép từ sách hoặc bài báo, có thể bị cắt cụt hoặc lẫn ký tự lỗi do trích từ PDF (ví dụ "follow-ing"). Hãy bỏ qua những lỗi này, trừ khi chúng làm thay đổi nghĩa.
- Cột `what_changed` được tính tự động và có thể kèm dấu câu thừa. Xin luôn đọc toàn bộ câu.
- Giữ nguyên `N/A` ở những ô Q2/Q3 đã điền sẵn. Xin trả lời Q1 cho mọi dòng.
- Nhớ lưu thường xuyên. Khi xong, xin gửi lại tệp `.xlsx` (hoặc `.csv`), không đổi tên cột và không đổi thứ tự dòng.

Xin chân thành cảm ơn thầy/cô! Câu trả lời chỉ được dùng ở dạng tổng hợp (thống kê độ đồng thuận), và thầy/cô sẽ được ghi nhận trong bài báo theo hình thức thầy/cô mong muốn.
