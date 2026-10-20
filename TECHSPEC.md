# TECHSPEC — Chinook Recommender (Album & Track cho Customer)

| | |
|---|---|
| Phiên bản | 0.1 (draft để duyệt) |
| Ngày | 2026-10-20 |
| Loại dự án | Demo / portfolio |
| Stack | Python 3.11+, SQLite, pandas, scikit-learn, LightGBM, PySide6 + Qt Designer (`.ui`) |
| Nguồn dữ liệu | `Chinook_Sqlite.sqlite` (chỉ đọc) |

---

## 1. Mục tiêu & phạm vi

**Mục tiêu:** Với mỗi customer, gợi ý Top-K **album** (chính) mà họ nhiều khả năng sẽ mua tiếp, kèm danh sách **track** đại diện (phụ) và lý do gợi ý.

**Trong phạm vi**
- Pipeline dữ liệu từ SQLite → bảng tương tác, feature.
- Huấn luyện & so sánh nhiều mô hình (baseline → hybrid).
- Đánh giá offline với chia thời gian 80/20.
- Ứng dụng desktop Qt: xem customer, xem gợi ý, giải thích, so sánh model, chạy train/evaluate.

**Ngoài phạm vi (v1):** serving online/API, A/B test, deep learning, cập nhật dữ liệu thời gian thực.

**Quan điểm trung thực về kỳ vọng:** dữ liệu rất nhỏ và thưa (xem §2). Mục tiêu của dự án là *chứng minh quy trình ML đúng và mô hình tốt hơn baseline có ý nghĩa*, không phải đạt độ chính xác tuyệt đối cao.

---

## 2. Phân tích dữ liệu (đã đo)

| Hạng mục | Giá trị |
|---|---|
| Customer / Track / Album / Artist / Genre | 59 / 3.503 / 347 / 275 (204 có album) / 25 |
| Tương tác (`InvoiceLine`) | 2.240; `Quantity` luôn = 1; không trùng cặp (customer, track) |
| Track/customer | 36–38 (TB 38); Album/customer: 18–27 (TB 22) |
| Invoice/customer | 6–7; khoảng thời gian 2009-01-01 → 2013-12-22 (~83 invoice/năm) |
| Track được mua | 1.984/3.503 (57%); **1.728 track chỉ 1 người mua**, tối đa 2 người/track |
| Album được mua | 304/347 (88%) |
| Tracks/album | 1–57 (TB 10) |
| Genre | Rock 1.297, Latin 579, Metal 374, Alt&Punk 332... |
| Null | `Composer` 978 (28%); `Genre` 0 |
| Giá | 0,99 (95%) hoặc 1,99 (video/TV) |

**Kết luận thiết kế**
1. Ma trận customer×track thưa ~1% và gần như không chồng lấn → **collaborative filtering thuần không dùng được**; cần content-based/hybrid.
2. Tín hiệu là **implicit, nhị phân** (đã mua = 1); không có rating.
3. **Track-level** gần như không thể dự đoán (Recall@10 ≈ 1%) → chọn **Album làm đơn vị gợi ý chính**.
4. Với 59 customer, mô hình lớn sẽ overfit → chọn mô hình nhẹ, ít tham số, đánh giá lặp nhiều seed.

### Baseline thăm dò (Recall@10, album, tham chiếu để đặt mục tiêu)

| Cách chia | Popularity | Genre | Artist+Genre |
|---|---|---|---|
| Theo thời gian | 5,3% | 4,2% | 7,7% |
| Ngẫu nhiên | 7,1% | 5,2% | 19,6% |

(Chia ngẫu nhiên cao hơn vì rò rỉ: các album cùng artist rải đều qua các invoice.)

---

## 3. Yêu cầu

### 3.1 Chức năng (FR)

| ID | Yêu cầu | Ưu tiên |
|---|---|---|
| FR-01 | Nạp dữ liệu từ file SQLite, kiểm tra schema, chỉ đọc | Must |
| FR-02 | Tạo bảng tương tác customer–album và customer–track kèm timestamp | Must |
| FR-03 | Chia train/validation/test theo thời gian trong từng customer (80/20) | Must |
| FR-04 | Huấn luyện các mô hình: Popularity, Genre/Artist-profile, Content-based, Hybrid LightGBM Ranker | Must |
| FR-05 | Đánh giá bằng Recall@K, Precision@K, NDCG@K, MAP@K, HitRate@K, Coverage, Diversity | Must |
| FR-06 | Gợi ý Top-K album cho 1 customer, loại các album đã mua | Must |
| FR-07 | Với mỗi album gợi ý, hiển thị track đại diện (top track theo độ phổ biến/khớp profile) | Must |
| FR-08 | Giải thích lý do gợi ý (genre/artist khớp, độ phổ biến, điểm thành phần) | Should |
| FR-09 | Xử lý cold-start (customer chưa có giao dịch): popularity theo quốc gia + genre chọn tay | Should |
| FR-10 | Lưu/nạp model và báo cáo đánh giá (`artifacts/`) | Must |
| FR-11 | UI Qt: chọn customer, xem lịch sử mua, xem gợi ý, so sánh model, chạy train/evaluate | Must |
| FR-12 | Gợi ý track độc lập (content-based) ở chế độ thử nghiệm | Could |

### 3.2 Phi chức năng (NFR)

| ID | Yêu cầu |
|---|---|
| NFR-01 | Tái lập được: seed cố định, cấu hình trong `config.yaml`, version thư viện trong `requirements.txt` |
| NFR-02 | Không rò rỉ dữ liệu: mọi thống kê (popularity, profile, target encoding) chỉ tính trên tập train |
| NFR-03 | Train toàn bộ pipeline < 2 phút trên laptop thường; suy luận 1 customer < 200 ms |
| NFR-04 | UI không treo khi train (chạy `QThread`/worker) |
| NFR-05 | Tách lớp: `ml/` không import Qt; UI chỉ gọi service |
| NFR-06 | Test tự động cho split, metric và không-rò-rỉ |

---

## 4. Định nghĩa bài toán ML

- **Loại:** Top-K recommendation với implicit feedback.
- **Đơn vị gợi ý:** Album. Ứng viên = mọi album mà customer chưa mua trong tập train.
- **Nhãn:** `y(u, a) = 1` nếu u mua ít nhất một track của a trong giai đoạn test.
- **Tín hiệu mạnh hơn (tùy chọn):** số track của album u đã mua / tổng track album (độ phủ), dùng làm trọng số khi dựng profile.

### Chia dữ liệu (80/20 theo thời gian, từng customer)

1. Với mỗi customer, sắp xếp invoice theo `InvoiceDate`.
2. Lấy các album theo thứ tự lần đầu xuất hiện; **80% đầu → train, 20% cuối → test**. (Trung bình ~4 album test/customer.)
3. Validation: cắt 20% cuối của *phần train* để chọn siêu tham số; sau đó huấn luyện lại trên toàn bộ train.
4. Album đã nằm trong train bị loại khỏi ứng viên khi đánh giá.
5. Bắt buộc báo cáo kèm **khoảng tin cậy** (bootstrap theo customer) vì chỉ có 59 customer.

> Lưu ý: "80% huấn luyện / 20% test" là tỉ lệ dữ liệu. Phần lớn công sức ML nằm ở feature engineering, tuning, so sánh model và phân tích lỗi.

---

## 5. Feature

**Item (album):** artist, genre chủ đạo + phân bố genre (vector), số track, tổng thời lượng, tỉ lệ media type, giá TB, tỉ lệ Composer null, độ phổ biến (số customer mua trong train), số artist-album liên quan.

**User (từ train):** phân bố genre/artist/media type đã mua (chuẩn hóa), quốc gia, số album đã mua, độ đa dạng genre, thời điểm giao dịch gần nhất.

**User×Item (cặp):**
- cosine(user-genre, album-genre), cosine TF-IDF (artist, composer, genre)
- số album/track cùng artist user đã mua; cùng genre
- popularity trong cùng quốc gia
- recency-weighted affinity (giao dịch gần được trọng số cao hơn)
- khoảng cách thời gian (nếu dùng chuỗi)

**Tránh:** dùng `Invoice.Total`, `InvoiceId` hoặc bất kỳ thứ gì tính từ giai đoạn test.

---

## 6. Mô hình

| # | Mô hình | Vai trò | Ghi chú |
|---|---|---|---|
| M0 | Random | Sàn tham chiếu | |
| M1 | Popularity (global / theo quốc gia) | Baseline | Cũng dùng cho cold-start |
| M2 | Genre-profile | Baseline content | |
| M3 | Artist+Genre profile | Baseline mạnh | Tham chiếu thực tế |
| M4 | Content-based (TF-IDF/embedding + cosine) | Mô hình chính 1 | Có thể thêm trọng số recency |
| M5 | Item-item kNN theo nội dung | So sánh | Không dùng đồng-mua do quá thưa |
| M6 | **Hybrid LightGBM Ranker (LambdaRank)** | Mô hình chính 2 | Feature §5, negative sampling 1:20–1:50 |
| M7 | (Could) LightFM với item features | So sánh | Chỉ để kiểm chứng không thắng M6 |

**Huấn luyện M6:** positives = cặp (u, album) trong train-target (dựng bằng cách lùi một bước thời gian: dùng 60% đầu làm lịch sử, 20% tiếp theo làm nhãn để học ranker), negatives lấy mẫu từ album chưa mua. Tune bằng validation, Optuna ≤ 50 trial, `early_stopping`.

**Gợi ý track:** trong mỗi album gợi ý, xếp track theo `0.6*popularity_trong_album + 0.4*độ_khớp_genre/composer` (rule-based v1).

**Cold-start:** customer không có lịch sử → popularity theo quốc gia, có thể lọc theo genre do người dùng chọn.

---

## 7. Đánh giá

- **Metric chính:** NDCG@10, Recall@10. **Phụ:** Precision@K, MAP@10, HitRate@K, K ∈ {5, 10, 20}.
- **Beyond-accuracy:** Catalog Coverage@10, Intra-list Diversity (khác genre/artist), Novelty (−log popularity).
- **Thống kê:** lặp 5 seed (cho phần ngẫu nhiên trong negative sampling/tuning), bootstrap 1.000 lần theo customer để có CI 95%; kiểm định paired với M3.
- **Tiêu chí chấp nhận:** M6 hoặc M4 cao hơn M3 (Artist+Genre) và M1 về NDCG@10, CI không chứa 0 ở chênh lệch trung bình; nếu không đạt, báo cáo trung thực kèm phân tích lỗi (đây vẫn là kết quả hợp lệ với dữ liệu này).
- **Phân tích lỗi:** theo genre, theo customer nhiều/ít giao dịch, theo quốc gia.

---

## 8. Kiến trúc & cấu trúc thư mục

```
chinook-recsys/
├─ config.yaml
├─ requirements.txt
├─ data/                  # đặt Chinook_Sqlite.sqlite (không commit)
├─ artifacts/             # model, metrics.json, plots
├─ src/
│  ├─ data/      loader.py  interactions.py  split.py
│  ├─ features/  item_features.py  user_features.py  pair_features.py
│  ├─ models/    base.py  popularity.py  profile.py  content.py  ranker.py
│  ├─ evaluation/ metrics.py  evaluator.py  bootstrap.py
│  ├─ services/  recommender_service.py  train_service.py   # lớp duy nhất UI gọi
│  └─ ui/
│     ├─ designer/  main_window.ui  customer_panel.ui  compare_panel.ui
│     ├─ main_window.py  workers.py  widgets/
│     └─ app.py
├─ notebooks/             # EDA
├─ tests/                 # split, metrics, leakage, service
└─ TECHSPEC.md
```

**Luồng:** `SQLite → loader → interactions → split → features → models → evaluator → artifacts`; UI → `services` → `models`/`artifacts`.

Giao diện model thống nhất: `fit(train_df)`, `score(user_id, candidate_ids) -> ndarray`, `recommend(user_id, k, exclude)`.

---

## 9. Giao diện Qt (Qt Designer + PySide6)

Thiết kế `.ui` bằng Qt Designer, nạp bằng `QUiLoader` hoặc biên dịch `pyside6-uic`. Logic trong `main_window.py`.

| Tab | Nội dung |
|---|---|
| **Gợi ý** | Chọn customer (combobox + tìm kiếm), chọn model, K. Bảng Top-K album (artist, genre, điểm, lý do); chọn album → danh sách track đại diện. Bên trái: lịch sử mua (biểu đồ genre). |
| **So sánh model** | Bảng metric các model, biểu đồ cột có CI, so sánh Top-K của 2 model cho cùng customer |
| **Huấn luyện & đánh giá** | Chọn model/tham số, nút Train/Evaluate, thanh tiến độ, log (chạy trong worker thread), xuất báo cáo |
| **Dữ liệu** | Thống kê dataset, phân bố mua, kiểm tra split (hiển thị train/test của từng customer) |

Biểu đồ dùng `pyqtgraph` hoặc `matplotlib` backend Qt. Hỗ trợ light/dark theo palette hệ thống.

---

## 10. Kế hoạch triển khai

| Giai đoạn | Nội dung | Kết quả |
|---|---|---|
| P0 | Khung dự án, loader, EDA, config | Dataset sạch, notebook EDA |
| P1 | Interaction, split 80/20 theo thời gian, metric + test | Evaluator đã test |
| P2 | Baseline M0–M3 | Bảng baseline có CI |
| P3 | Feature + M4, M5 | Content-based chạy được |
| P4 | M6 Ranker + tuning + phân tích lỗi | Mô hình chính, báo cáo |
| P5 | Service layer + UI Qt (Designer) | App chạy được end-to-end |
| P6 | Đóng gói, README, ảnh chụp/GIF demo | Sẵn sàng portfolio |

---

## 11. Rủi ro

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| Dữ liệu quá nhỏ, kết quả dao động mạnh | Cao | CI bootstrap, nhiều seed, so sánh paired, báo cáo trung thực |
| Mô hình không thắng baseline Artist+Genre | Trung bình | Chấp nhận như kết luận; tập trung phân tích lỗi và giải thích |
| Rò rỉ dữ liệu qua popularity/profile | Cao | Test tự động NFR-06, tính thống kê chỉ trên train |
| Overfit khi tune | Trung bình | Validation tách riêng, tune ít tham số |
| Dữ liệu Chinook là tổng hợp, ít cấu trúc thật | Trung bình | Ghi rõ giới hạn trong README |

---

## 12. Câu hỏi còn mở (chốt ở lượt sau)

1. Có thêm chế độ gợi ý track độc lập (FR-12) trong v1 không?
2. Ngôn ngữ giao diện: Việt, Anh hay song ngữ?
3. Cần đóng gói thành file thực thi (PyInstaller) cho portfolio không?
