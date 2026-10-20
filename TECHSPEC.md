# TECHSPEC — Hệ gợi ý Album & Track cho Customer (Chinook)

| | |
|---|---|
| Phiên bản | 1.0 |
| Ngày | 2026-10-20 |
| Loại dự án | Bài tập môn Học máy |
| Ngôn ngữ / UI | Python 3.11+, PySide6 + Qt Designer (`.ui`), giao diện tiếng Việt |
| Thư viện | pandas, numpy, scikit-learn, lightgbm, matplotlib, PySide6 |
| Dữ liệu | `Chinook_Sqlite.sqlite` (chỉ đọc) |

---

## 1. Mục tiêu & phạm vi

**Mục tiêu:** Với mỗi customer, gợi ý Top-K **album** họ có khả năng mua tiếp; mỗi album kèm vài **track đại diện** và lý do gợi ý.

**Gồm:** làm sạch dữ liệu → chia train/test 80/20 → huấn luyện & so sánh mô hình → đánh giá → giao diện Qt để dùng thử.

**Không gồm:** API/server, deep learning, cập nhật dữ liệu thời gian thực, đóng gói file .exe, gợi ý track độc lập (track chỉ gợi ý kèm trong album).

**Kỳ vọng:** dữ liệu nhỏ và thưa (§2) nên mục tiêu là *quy trình ML đúng, so sánh công bằng với baseline, kết luận trung thực*, không phải độ chính xác cao.

---

## 2. Phân tích dữ liệu (đã đo trên file thật)

| Hạng mục | Giá trị |
|---|---|
| Customer / Track / Album / Artist / Genre | 59 / 3.503 / 347 / 275 / 25 |
| Tương tác (`InvoiceLine`) | 2.240, `Quantity` luôn = 1, không trùng (customer, track) |
| Mỗi customer | ~38 track, ~22 album, 6–7 invoice |
| Thời gian | 2009-01-01 → 2013-12-22 |
| Độ thưa | 1.728/1.984 track chỉ 1 người mua; tối đa 2 người/track |
| Null | `Composer` 978 (28%); `Genre`, `Album` không null |
| Giá | 0,99 (95%) hoặc 1,99 (video/TV) |

**Kết luận thiết kế**
1. Ma trận customer×track thưa ~1%, gần như không chồng lấn → collaborative filtering thuần vô dụng → dùng **content-based + hybrid**.
2. Chỉ có tín hiệu implicit nhị phân (đã mua = 1), không có rating.
3. Track-level gần như không dự đoán được (Recall@10 ≈ 1%) → **đơn vị gợi ý là Album**.
4. Chỉ 59 customer → dùng mô hình nhẹ, tránh overfit, báo cáo khoảng tin cậy.

Baseline thăm dò (Recall@10, album, chia theo thời gian): Popularity 5,3% · Genre 4,2% · Artist+Genre 7,7%.

---

## 3. Yêu cầu

### 3.1 Chức năng

| ID | Yêu cầu |
|---|---|
| FR-01 | Đọc SQLite, kiểm tra schema, báo lỗi rõ nếu file sai |
| FR-02 | Làm sạch dữ liệu (§4) và hiển thị báo cáo làm sạch |
| FR-03 | Tạo bảng tương tác customer–album có thời gian |
| FR-04 | Chia train/test 80/20 theo thời gian từng customer; xem được kết quả chia |
| FR-05 | Huấn luyện các mô hình M1–M5 (§6), chọn mô hình/tham số từ UI |
| FR-06 | Đánh giá trên tập test: Recall@K, Precision@K, NDCG@K, MAP@K, HitRate@K, Coverage, Diversity |
| FR-07 | Gợi ý Top-K album cho 1 customer (loại album đã mua), kèm track đại diện và lý do |
| FR-08 | Xử lý customer mới (cold-start): gợi ý theo popularity của quốc gia / genre chọn tay |
| FR-09 | So sánh nhiều mô hình trên cùng bảng/biểu đồ |
| FR-10 | Lưu/nạp mô hình đã train và xuất kết quả đánh giá (CSV) |

### 3.2 Phi chức năng

| ID | Yêu cầu |
|---|---|
| NFR-01 | Tái lập: seed cố định (42), cấu hình trong `config.py` |
| NFR-02 | **Không rò rỉ dữ liệu:** mọi thống kê (popularity, profile, feature) chỉ tính từ train |
| NFR-03 | Train toàn bộ < 2 phút; gợi ý 1 customer < 1 giây |
| NFR-04 | UI không treo khi train (dùng `QThread`) |
| NFR-05 | Code ML không phụ thuộc Qt (để test độc lập) |

---

## 4. Làm sạch & chuẩn bị dữ liệu

| Bước | Việc làm |
|---|---|
| 1 | Join `InvoiceLine → Invoice → Customer`, `Track → Album → Artist`, `Track → Genre/MediaType` |
| 2 | Kiểm tra: khóa ngoại mồ côi, trùng lặp, `Quantity ≤ 0`, giá ≤ 0, ngày sai định dạng; ghi log số dòng bị loại |
| 3 | Chuẩn hóa `InvoiceDate` sang `datetime`; chuẩn hóa chuỗi (strip, lower) cho tên artist/composer |
| 4 | `Composer` null → `"Unknown"` và thêm cờ `composer_missing`; tách nhiều composer bằng `,`/`/`/`;` |
| 5 | Gộp track thành tương tác customer–album: `n_tracks_bought`, `coverage = n_tracks_bought / n_tracks_album`, `first_purchase_date` |
| 6 | Tạo bảng item (album) và bảng user (customer) |
| 7 | Giữ lại mọi customer (đều có giao dịch); không loại album ít track |

Kết quả: `interactions.csv`, `albums.csv`, `customers.csv` và một báo cáo làm sạch (số dòng trước/sau, vấn đề phát hiện).

---

## 5. Bài toán, chia dữ liệu, feature

**Bài toán:** Top-K recommendation, implicit feedback. Ứng viên = album customer chưa mua trong train. Nhãn: `y(u,a)=1` nếu u mua album a ở giai đoạn test.

**Chia 80/20 theo thời gian, từng customer**
1. Sắp xếp album của customer theo `first_purchase_date`.
2. 80% album đầu → **train**; 20% album cuối → **test** (TB ~4 album/customer).
3. Từ train, 20% cuối → **validation** để chọn tham số; sau đó train lại trên toàn bộ train.
4. Báo cáo kèm khoảng tin cậy 95% bằng bootstrap theo customer (1.000 lần).

**Feature**
- *Album:* artist, phân bố genre (vector), số track, tổng thời lượng, tỉ lệ media type, giá TB, độ phổ biến (đếm trong train).
- *Customer:* phân bố genre/artist đã mua (chuẩn hóa), quốc gia, số album đã mua, độ đa dạng genre.
- *Cặp customer–album:* cosine(genre), cosine TF-IDF (artist+composer+genre), số album cùng artist đã mua, popularity theo quốc gia, affinity có trọng số thời gian gần.

Không dùng `Invoice.Total`, `InvoiceId` hay thống kê từ giai đoạn test.

---

## 6. Mô hình

| # | Mô hình | Ghi chú |
|---|---|---|
| M1 | Popularity (toàn cục / theo quốc gia) | Baseline, cũng dùng cho cold-start |
| M2 | Genre-profile | Baseline |
| M3 | Artist+Genre profile | Baseline mạnh nhất, mốc để so sánh |
| M4 | Content-based (TF-IDF + cosine với profile customer) | Mô hình chính 1 |
| M5 | **Hybrid LightGBM Ranker (LambdaRank)** | Mô hình chính 2; negative sampling 1:30; tune trên validation |

**Track đại diện:** trong mỗi album được gợi ý, xếp track theo độ phổ biến trong train và độ khớp genre/composer với profile customer.

**Giải thích:** hiển thị điểm thành phần (genre khớp, artist khớp, popularity) và câu mô tả, ví dụ "Bạn đã mua 5 album Rock, 2 album của AC/DC".

---

## 7. Đánh giá

- **Chính:** NDCG@10, Recall@10. **Phụ:** Precision@K, MAP@10, HitRate@K với K ∈ {5, 10, 20}.
- **Ngoài độ chính xác:** Catalog Coverage@10, Diversity (độ khác nhau genre/artist trong danh sách).
- **Thống kê:** lặp 5 seed cho mô hình có ngẫu nhiên, CI bootstrap, so sánh paired với M3.
- **Tiêu chí đạt:** M4 hoặc M5 vượt M1 và M3 về NDCG@10 trên test. Nếu không vượt, ghi nhận kết quả thật và phân tích nguyên nhân (cũng được chấp nhận).
- **Phân tích lỗi:** theo genre, theo số giao dịch của customer, theo quốc gia.

---

## 8. Cấu trúc dự án (đơn giản, theo kiểu `ui / dal / models / test`)

```
ChinookRecommender/
├─ databases/
│  └─ Chinook_Sqlite.sqlite
├─ connectors/
│  └─ connector.py          # mở/đóng kết nối SQLite (dùng with, luôn đóng)
├─ models/                  # lớp chỉ chứa dữ liệu, không có hành vi
│  ├─ customer.py           # Customer
│  ├─ album.py              # Album, Track
│  └─ recommendation.py     # Recommendation (album, điểm, lý do, track đại diện)
├─ dal/                     # truy cập dữ liệu
│  ├─ CustomerDAO.py        # lấy customer, tìm kiếm, lịch sử mua
│  └─ AlbumDAO.py           # lấy album/track, bảng dữ liệu để làm sạch
├─ ml/                      # phần học máy, không phụ thuộc Qt
│  ├─ data_prep.py          # làm sạch, tạo interactions, chia train/test 80/20
│  ├─ features.py           # feature album / customer / cặp
│  ├─ recommenders.py       # M1–M5, cùng fit() / recommend()
│  └─ evaluate.py           # metric, bootstrap, so sánh model
├─ ui/                      # mỗi màn hình có 3 file
│  ├─ DataMainWindow.ui / .py / DataMainWindowEx.py
│  ├─ TrainMainWindow.ui / .py / TrainMainWindowEx.py
│  ├─ EvaluateMainWindow.ui / .py / EvaluateMainWindowEx.py
│  └─ RecommendMainWindow.ui / .py / RecommendMainWindowEx.py
├─ test/                    # mở riêng từng cửa sổ để thử bằng tay
│  ├─ test_data_window.py
│  ├─ test_train_window.py
│  ├─ test_evaluate_window.py
│  ├─ test_recommend_window.py
│  └─ test_split_metrics.py # kiểm tra tự động chia dữ liệu và metric
├─ images/                  # icon
├─ artifacts/               # model đã train, metrics.csv, biểu đồ
├─ config.py                # seed, tỉ lệ chia, đường dẫn
├─ main.py                  # chạy app (mở RecommendMainWindow)
└─ requirements.txt
```

**Vai trò**

| Thư mục | Nội dung |
|---|---|
| `ui/` | `.ui` thiết kế bằng Qt Designer; `.py` sinh tự động bằng `pyside6-uic`; `*Ex.py` chứa logic gắn sự kiện, kế thừa lớp sinh tự động |
| `dal/` | Chỉ nơi này viết SQL; luôn dùng truy vấn tham số hóa (`?`) |
| `models/` | Lớp dữ liệu thuần (dataclass) |
| `ml/` | Làm sạch, chia dữ liệu, feature, mô hình, đánh giá; trả về pandas/dataclass cho UI |
| `test/` | Các file mở cửa sổ thử tay, thêm một file kiểm tra tự động cho chia dữ liệu và metric |

**Quy ước tránh lỗi thường gặp**
- Luôn chạy từ thư mục gốc (`python main.py`); import dùng đường dẫn tính từ gốc dự án.
- Kết nối SQLite mở bằng `with`/`try-finally` để không rò rỉ.
- Đường dẫn database lấy từ `config.py`, không hard-code trong từng file.
- Tên cột thống nhất theo schema Chinook (`CustomerId`, `AlbumId`, `TrackId`, `InvoiceDate`...).

Giao diện thống nhất của mô hình: `fit(train)`, `recommend(customer_id, k, exclude)`.

---

## 9. Giao diện Qt (Qt Designer + PySide6, tiếng Việt)

4 màn hình (mỗi màn hình là một `QMainWindow`, `RecommendMainWindow` mở đầu tiên, các màn khác mở từ menu/nút điều hướng):

| Màn hình | Chức năng |
|---|---|
| **1. Dữ liệu** (`DataMainWindow`) | Nút chọn file SQLite; nút "Làm sạch"; bảng báo cáo làm sạch; thống kê (số customer/album/track, phân bố genre); xem bảng chia train/test theo từng customer |
| **2. Huấn luyện** (`TrainMainWindow`) | Chọn mô hình (M1–M5) và tham số chính, tỉ lệ chia (mặc định 80/20); nút Train; thanh tiến độ và log (chạy `QThread`); nút lưu/nạp model |
| **3. Đánh giá** (`EvaluateMainWindow`) | Bảng metric của các mô hình đã train (kèm CI); biểu đồ cột so sánh; chọn K; nút xuất CSV |
| **4. Gợi ý** (`RecommendMainWindow`) | Chọn customer (có ô tìm kiếm) hoặc "Customer mới" (chọn quốc gia/genre); chọn mô hình và K; bảng Top-K album (artist, genre, điểm, lý do); chọn album → danh sách track đại diện; bên cạnh là lịch sử mua và biểu đồ genre của customer |

Biểu đồ dùng matplotlib nhúng Qt (`FigureCanvasQTAgg`). Thông báo lỗi bằng `QMessageBox`; các nút bị khóa khi chưa đủ điều kiện (ví dụ chưa làm sạch thì chưa train được).

---

## 10. Kế hoạch & sản phẩm bàn giao

| Giai đoạn | Nội dung | Kết quả |
|---|---|---|
| 1 | `ml/data_prep.py`: làm sạch, interactions, chia 80/20 + test | Dữ liệu sạch, báo cáo làm sạch |
| 2 | `ml/evaluate.py` + baseline M1–M3 | Bảng baseline có CI |
| 3 | `ml/features.py` + M4, M5, tuning | Mô hình chính, phân tích lỗi |
| 4 | Thiết kế 4 file `.ui` + `*Ex.py` nối chức năng | App chạy đủ 4 màn hình |
| 5 | Kiểm thử, viết báo cáo ngắn (kết quả, hạn chế) | Mã nguồn + báo cáo |

**Bàn giao:** mã nguồn, `requirements.txt`, file `.ui`, `metrics.csv` và biểu đồ, hướng dẫn chạy ngắn.

---

## 11. Rủi ro

| Rủi ro | Giảm thiểu |
|---|---|
| Dữ liệu nhỏ → kết quả dao động | CI bootstrap, nhiều seed, so sánh paired |
| Mô hình không thắng M3 | Chấp nhận và phân tích; ghi vào báo cáo |
| Rò rỉ dữ liệu | Thống kê chỉ trên train; có test tự động |
| Overfit khi tune | Validation tách riêng, ít tham số |
| Chinook là dữ liệu tổng hợp | Nêu rõ trong phần hạn chế của báo cáo |

---

## 12. Các quyết định đã chốt

- Đơn vị gợi ý: Album (track chỉ là phụ kèm theo).
- Chia 80/20 theo thời gian từng customer.
- Mô hình: classical ML + hybrid, không deep learning.
- UI: Qt Designer + PySide6, tiếng Việt, cấu trúc `ui / dal / models / ml / test`, mỗi màn hình 3 file (`.ui`, `.py`, `*Ex.py`).
- Không đóng gói .exe; không gợi ý track độc lập.
