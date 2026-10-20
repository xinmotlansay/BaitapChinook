# TECHSPEC — Hệ gợi ý Album & Track cho Customer (Chinook)

| | |
|---|---|
| Phiên bản | 2.0 |
| Ngày | 2026-10-20 |
| Loại dự án | Bài tập môn Học máy |
| Ngôn ngữ / UI | Python 3.11+ (đang chạy 3.12), PySide6 + Qt Designer (`.ui`), giao diện tiếng Việt |
| Thư viện | pandas, numpy, scikit-learn, lightgbm, matplotlib, PySide6, scipy (đi kèm scikit-learn) |
| Dữ liệu | `databases/Chinook_Sqlite.sqlite` (chỉ đọc) |

---

## 1. Mục tiêu & phạm vi

**Mục tiêu:** Với mỗi customer, gợi ý Top-K **album** họ có khả năng mua tiếp. Với mỗi album được gợi ý, hiển thị các **track chưa mua**, xếp theo mức phù hợp do mô hình track dự đoán, kèm lý do gợi ý.

**Gồm:**
- Huấn luyện offline: làm sạch → chia train/test 80/20 theo thời gian → chọn tham số trên validation → huấn luyện → đánh giá → đóng gói model.
- Ứng dụng desktop một màn hình: gợi ý cho khách đã có và khách mới, chỉ nạp model đã đóng gói để suy luận.

**Không gồm:** API/server, deep learning, cập nhật dữ liệu thời gian thực, đóng gói `.exe`, danh sách track gợi ý độc lập (track chỉ xuất hiện trong album đã chọn), huấn luyện lại từ giao diện.

**Kỳ vọng:** dữ liệu nhỏ và thưa (§2) nên mục tiêu là *quy trình ML đúng, so sánh công bằng với baseline, kết luận trung thực*, không phải độ chính xác cao.

---

## 2. Phân tích dữ liệu (đã đo trên file thật)

| Hạng mục | Giá trị |
|---|---|
| Customer / Track / Album / Artist / Genre | 59 / 3.503 / 347 / 275 / 25 |
| Dòng hóa đơn (`InvoiceLine`) | 2.240, `Quantity` luôn = 1, không trùng (customer, track) |
| Mỗi customer | 18–27 album (trung bình 22), 6–7 invoice |
| Thời gian | 2009-01-01 → 2013-12-22 |
| Độ thưa | 1.728/1.984 track chỉ 1 người mua; tối đa 2 người/track |
| Null | `Composer` 978 (28%); `Genre`, `Album` không null |
| Giá | 0,99 (95%) hoặc 1,99 (video/TV) |

**Kết luận thiết kế**
1. Ma trận customer×track thưa ~1%, gần như không chồng lấn → collaborative filtering thuần vô dụng → dùng **content-based + hybrid**.
2. Chỉ có tín hiệu implicit nhị phân (đã mua = 1), không có rating.
3. Track-level gần như không dự đoán được (Recall@10 khoảng 1–2%) → **đơn vị gợi ý chính là Album**, track được xếp hạng trong album đã chọn.
4. Chỉ 59 customer → dùng mô hình nhẹ, tránh overfit, báo cáo khoảng tin cậy.

Làm sạch trên dữ liệu này không loại dòng nào; báo cáo làm sạch ghi nhận điều đó.

---

## 3. Yêu cầu

### 3.1 Chức năng

| ID | Yêu cầu |
|---|---|
| FR-01 | Đọc SQLite qua DAO; báo lỗi rõ nếu file sai hoặc thiếu bảng |
| FR-02 | Làm sạch dữ liệu (§4) và ghi báo cáo làm sạch (số dòng trước/sau, số dòng bị loại) |
| FR-03 | Tạo bảng tương tác customer–album và customer–track có thời gian mua |
| FR-04 | Chia train/test 80/20 theo thời gian từng customer, kiểm tra không rò rỉ bằng `assert` |
| FR-05 | Huấn luyện M1–M5 (album) và T1–T2 (track); chọn tham số trên validation |
| FR-06 | Đánh giá trên test: Recall@K, Precision@K, NDCG@K, MAP@K, HitRate@K, Coverage, Diversity, CI 95% |
| FR-07 | Gợi ý Top-K album cho khách đã có (loại album đã mua), kèm lý do và track chưa mua xếp theo điểm |
| FR-08 | Gợi ý cho khách mới theo độ phổ biến của quốc gia và/hoặc một hoặc nhiều thể loại |
| FR-09 | Chọn mô hình album từ giao diện hoặc dòng lệnh; mặc định M5 |
| FR-10 | Đóng gói model (thống kê, LambdaRank album, LambdaRank track, bảng album) vào một file `.zip`; nạp lại để gợi ý mà không train lại |
| FR-11 | Xem lịch sử mua đầy đủ của khách đã có trong popup |

### 3.2 Phi chức năng

| ID | Yêu cầu |
|---|---|
| NFR-01 | Tái lập: seed cố định (42), cấu hình trong `config.py` |
| NFR-02 | **Không rò rỉ dữ liệu:** mọi thống kê (popularity, hồ sơ, feature, TF-IDF theo nhãn) chỉ tính từ train; nhãn test không dùng để chọn tham số |
| NFR-03 | Huấn luyện toàn bộ dưới 1 phút trên máy phát triển; gợi ý một khách dưới 1 giây |
| NFR-04 | UI không treo khi nạp model và gợi ý |
| NFR-05 | Code ML không phụ thuộc Qt (chạy được bằng `python -m ml.train`) |
| NFR-06 | Chỉ nạp file model do chính dự án tạo ra (pickle có thể chạy code tùy ý) |

---

## 4. Làm sạch & chuẩn bị dữ liệu

| Bước | Việc làm |
|---|---|
| 1 | Join `InvoiceLine → Invoice → Customer`, `Track → Album → Artist`, `Track → Genre` |
| 2 | Loại: dòng trùng `InvoiceLineId`, track không có trong catalog, `Quantity ≤ 0`, giá ≤ 0, ngày sai định dạng; ghi số dòng bị loại |
| 3 | Chuẩn hóa `InvoiceDate` sang `datetime`; strip tên artist và composer |
| 4 | `Composer` rỗng → `"Unknown"` và cờ `ComposerMissing` |
| 5 | Gộp thành tương tác customer–album: `NTracksBought`, `NTracksAlbum`, `Coverage`, `FirstPurchase`, `LastPurchase` |
| 6 | Gộp thành tương tác customer–track (kèm album của track) |
| 7 | Tạo bảng album (`NTracks`, `TotalMs`, `MeanPrice`, `ComposerMissingShare`, thể loại) |

Kết quả: báo cáo làm sạch (bảng `report`) được ghi vào log khi huấn luyện.

---

## 5. Bài toán, chia dữ liệu, feature

### 5.1 Bài toán
Top-K recommendation với implicit feedback (đã mua = 1). Ứng viên là album (hoặc track) customer chưa mua trong **train**. Nhãn `y(u,a)=1` nếu u mua a trong giai đoạn đánh giá.

### 5.2 Chia theo thời gian, từng customer
1. Sắp album của customer theo `FirstPurchase`.
2. 80% album đầu → **train**; 20% còn lại → **test** (trung bình 4,4 album test/customer, tổng 260 dòng test).
3. Từ train, 80% đầu → **sub_a**, 20% cuối → **sub_b**; từ sub, 80% đầu → **sub**, 20% cuối → **validation**. Tách theo thời gian, không trộn ngẫu nhiên.
4. Track đi theo album: track của một album thuộc đúng cửa sổ của album đó. Nhờ vậy không có track test nào nằm trong lịch sử train.

### 5.3 Quy trình huấn luyện LambdaRank (album và track dùng chung)
- **Tuning:** huấn luyện trên cửa sổ (sub_a → nhãn sub_b), đánh giá trên cửa sổ (sub → nhãn validation). Lưới 4 cấu hình (`num_leaves` ∈ {7, 15}, `n_estimators` ∈ {100, 300}), chọn theo NDCG@10 trên validation.
- **Huấn luyện cuối:** dùng cả hai cửa sổ với tham số đã chọn.
- **Mẫu:** nhãn dương là item của giai đoạn sau; mẫu âm lấy ngẫu nhiên 30 item/dương từ phần chưa mua (seed cố định).

### 5.4 Feature

**Album (`FEATURE_COLUMNS`, 12 cột):** `genre_cos`, `artist_genre_cos`, `tfidf_cos` (cosine với hồ sơ customer); `pop_global`, `pop_country`; `artist_bought`, `artist_recency`; `n_tracks`, `log_total_ms`, `mean_price`, `composer_missing`; `cust_n_albums`.

**Track (`TRACK_FEATURE_COLUMNS`, 11 cột):** `t_genre_cos`, `t_composer_cos` (cosine với hồ sơ customer); `t_artist_bought`, `t_album_bought` (số track đã mua cùng nghệ sĩ, cùng album); `t_album_content_cos`, `t_album_pop` (từ album chứa track); `t_track_pop`; `t_unit_price`, `t_log_ms`, `t_composer_missing`; `t_cust_n_tracks`.

Hồ sơ customer chỉ được tính từ cửa sổ lịch sử tương ứng. Không dùng `Invoice.Total`, `InvoiceId`, hay bất kỳ thống kê nào của giai đoạn nhãn.

---

## 6. Mô hình

### 6.1 Album

| # | Mô hình | Cách tính điểm |
|---|---|---|
| M1 | Popularity | Số customer trong train đã mua album |
| M2 | Genre-profile | Cosine giữa thể loại album và hồ sơ thể loại customer |
| M3 | Artist+Genre profile | Cosine giữa vector (nghệ sĩ + thể loại) và hồ sơ customer. **Baseline mạnh nhất** |
| M4 | Content TF-IDF | Cosine TF-IDF (nghệ sĩ, nhạc sĩ, thể loại) với hồ sơ customer |
| M5 | **Hybrid LightGBM (LambdaRank)** | Chấm điểm 12 feature (gồm điểm M2–M4). **Mô hình mặc định** |

### 6.2 Track

| # | Mô hình | Cách tính điểm |
|---|---|---|
| T1 | Track popularity | Số customer trong train đã mua track |
| T2 | **Track LightGBM (LambdaRank)** | Chấm điểm 11 feature track (§5.4). Dùng trong giao diện để xếp track của album |

Khi chọn album M1–M4 trong giao diện, track vẫn dùng T2. Khách mới không có hồ sơ nên track được xếp theo `track_pop` (T1).

---

## 7. Đánh giá

### 7.1 Cách đo
- Trên test (59 customer, 260 album test). Ứng viên là album/track chưa có trong train.
- Chính: NDCG@10, Recall@10. Phụ: Precision, MAP, HitRate ở K ∈ {5, 10, 20}; Coverage@K; Diversity@K (1 − cosine thể loại trung bình trong danh sách).
- CI 95% bằng bootstrap theo customer (1.000 lần). So sánh cặp với M3 theo từng customer.

### 7.2 Kết quả album (K = 10)

| Mô hình | Recall@10 | NDCG@10 | HitRate@10 | NDCG@10 CI 95% |
|---|---|---|---|---|
| M1 Popularity | 0,047 | 0,031 | 0,169 | [0,013; 0,050] |
| M2 Genre-profile | 0,000 | 0,000 | 0,000 | [0,000; 0,000] |
| M3 Artist+Genre | 0,074 | 0,052 | 0,153 | [0,020; 0,087] |
| M4 Content TF-IDF | 0,073 | 0,051 | 0,203 | [0,022; 0,088] |
| **M5 Hybrid LightGBM** | **0,100** | **0,085** | **0,322** | [0,045; 0,129] |

So sánh cặp với M3 (NDCG@10): M5 chênh lệch trung bình +0,033, CI 95% [−0,013; 0,080], thắng 14 / thua 7 customer. **CI chứa 0, nên chưa thể kết luận M5 vượt M3 có ý nghĩa thống kê.**

Ổn định theo seed (M5, 5 seed): NDCG@10 từ 0,082 đến 0,109, trung bình khoảng 0,091.

Tuning album chọn `num_leaves = 15, n_estimators = 100` (NDCG@10 validation 0,106).

M2 bằng 0 ở K = 5 và 10 vì nhiều album cùng thể loại Rock nên điểm bằng nhau, thứ tự do id quyết định.

### 7.3 Kết quả track (K = 10)

| Mô hình | Recall@10 | NDCG@10 | HitRate@10 |
|---|---|---|---|
| T1 Track popularity | 0,000 | 0,000 | 0,000 |
| **T2 Track LightGBM** | **0,016** | **0,015** | **0,102** |

Track gần như không dự đoán được, đúng với nhận định ở §2. Tuning track chọn `num_leaves = 7, n_estimators = 100`. Mô hình track chỉ huấn luyện với một seed (42).

### 7.4 Tiêu chí đạt
Đặc tả ban đầu yêu cầu M4 hoặc M5 vượt M1 và M3 về NDCG@10. **M5 đạt trên ước lượng điểm** (0,085 so với 0,031 và 0,052), nhưng khoảng tin cậy của chênh lệch với M3 chứa 0. Kết quả được ghi nhận như vậy.

### 7.5 Phân tích lỗi
Dự kiến thực hiện: theo thể loại, theo số giao dịch của customer, theo quốc gia. Chưa thực hiện trong phiên bản này.

---

## 8. Cấu trúc dự án

```
BaitapChinook/
├─ databases/
│  └─ Chinook_Sqlite.sqlite
├─ connectors/
│  └─ connector.py          # kết nối SQLite dùng chung (ensureConnection / close)
├─ models/                  # lớp dữ liệu thuần (dataclass) + model đã đóng gói
│  ├─ customer.py           # Customer
│  ├─ album.py              # Album, Track
│  ├─ recommendation.py     # Recommendation (album, điểm, lý do, [(Track, điểm)])
│  └─ recommender.zip       # tạo bởi ml.train
├─ dal/                     # truy cập dữ liệu, nơi duy nhất viết SQL
│  ├─ CustomerDAO.py        # danh sách khách, quốc gia, lịch sử mua
│  └─ AlbumDAO.py           # catalog, dòng mua, track theo album, album/track đã mua
├─ ml/                      # học máy, không phụ thuộc Qt
│  ├─ data_prep.py          # làm sạch, tương tác, chia cửa sổ, kiểm tra rò rỉ
│  ├─ features.py           # ProfileState, FEATURE_COLUMNS, TRACK_FEATURE_COLUMNS
│  ├─ recommenders.py       # M1–M5, T1–T2, huấn luyện LambdaRank
│  ├─ evaluate.py           # metric, bootstrap CI, so sánh cặp
│  ├─ train.py              # HUẤN LUYỆN
│  ├─ predict.py            # SUY LUẬN (Predictor), dòng lệnh
│  └─ package.py            # save_package / load_package
├─ ui/
│  ├─ RecommendMainWindow.ui     # thiết kế (Qt Designer)
│  ├─ RecommendMainWindow.py     # sinh bằng pyside6-uic, không sửa tay
│  ├─ RecommendMainWindowEx.py   # logic sự kiện, kế thừa Ui_MainWindow
│  ├─ HistoryDialog.py           # popup lịch sử mua
│  ├─ widgets.py                 # CheckComboBox (ô xổ xuống chọn nhiều)
│  └─ utils.py                   # showDataIntoTableWidget, drawGenreChart, relativeBars
├─ test/
│  └─ run_app.py            # mở ứng dụng (xem §8.2)
├─ artifacts/               # metrics.csv, track_metrics.csv, paired_vs_m3.csv, m5_seeds.csv, tuning
├─ config.py                # đường dẫn, seed, tỉ lệ chia, số mẫu âm, lưới K
├─ main.py                  # chạy ứng dụng
└─ requirements.txt
```

### 8.1 Quy tắc lập trình

**A. Học máy**
1. Khám phá dữ liệu trước khi huấn luyện: đếm dòng, giá trị thiếu, kiểu dữ liệu (ghi vào báo cáo làm sạch).
2. Feature khai báo tường minh (`FEATURE_COLUMNS`, `TRACK_FEATURE_COLUMNS`). Cột văn bản được mã hóa (TF-IDF, one-hot, đếm) trước khi đưa vào mô hình số.
3. Chia train/test trước khi fit; seed cố định.
4. Chỉ đánh giá trên test. Validation chỉ dùng để chọn tham số, và nhãn validation không được dùng để huấn luyện cửa sổ đang đánh giá.
5. Báo cáo chỉ số kèm CI, không chỉ in danh sách gợi ý.
6. Model lưu kèm tên feature. Khi suy luận, kiểm tra tên và thứ tự feature khớp với code; sai thì báo lỗi rõ.
7. Huấn luyện (`ml/train.py`) và suy luận (`ml/predict.py`) tách riêng. Suy luận chỉ nạp model đã đóng gói.
8. Đường dẫn tính bằng `Path(__file__)` trong `config.py`.
9. Model đóng gói dạng `.zip` chứa `meta.json` (đọc được) và `model.pkl` (pickle). Chỉ nạp file do dự án tạo ra (NFR-06).
10. Dùng `logging`, không dùng `print`, cho tiến trình huấn luyện và kết quả.
11. Chuỗi giao diện và thông báo hoàn toàn tiếng Việt; tên biến, hàm, class tiếng Anh; comment tiếng Việt có dấu.

**B. Giao diện**
1. Tách thiết kế và logic: `.ui` (Qt Designer) → `.py` (sinh bằng `pyside6-uic`, không sửa tay) → `*Ex.py` (logic).
2. Thứ tự khởi tạo: `__init__` → `setupUi()` → `setupTables()` → `setupSignalAndSlot()` → `setupChart()` → `loadModel()` → `loadFilters()` → `showWindow()`.
3. Lỗi hiển thị bằng `QMessageBox` (critical cho lỗi hệ thống/model, warning cho nhập sai). Mọi handler bọc `try/except`.
4. Kiểm tra đầu vào trước khi xử lý (chưa chọn khách, chưa chọn quốc gia hoặc thể loại cho khách mới).
5. Logic dữ liệu nằm ở DAO và `ml/`, UI chỉ gọi và hiển thị.
6. Bảng dùng chung `showDataIntoTableWidget(table, df)`.
7. SQL luôn dùng placeholder `?`.
8. Biểu đồ nhúng bằng `FigureCanvasQTAgg`; mỗi lần vẽ: `clear()` → vẽ → `tight_layout()` → `draw()`.
9. Mức phù hợp hiển thị theo `relativeBars`: tương đối trong danh sách (100% cao nhất, 0% thấp nhất). Không hiển thị điểm thô vì thang điểm của mô hình không cố định.

**C. Kiểm tra**
1. Thư mục `test/` chỉ chứa file khởi chạy giao diện, không có unit test.
2. Chống rò rỉ được kiểm tra bằng `assert` trong `ml/data_prep.py` (không album test nào nằm trong train của cùng customer; mọi customer test có lịch sử train).

---

## 8.2 Thư mục `test/`

`test/run_app.py` mở ứng dụng để xem giao diện và thử gợi ý, không cần chuẩn bị thêm. File có đoạn thêm thư mục gốc vào `sys.path`, nên chạy từ đâu cũng được.

Trước khi nộp, kiểm tra trong môi trường ảo mới: chỉ cài `requirements.txt`, chạy `python -m ml.train` để tạo model, rồi mở `test/run_app.py`; giao diện phải hiện và gợi ý được cho khách đã có và khách mới.

---

## 9. Giao diện

Một màn hình `RecommendMainWindow`, gồm:

| Khu vực | Nội dung |
|---|---|
| Tab **Khách hàng đã có** | Ô chọn khách (có ô tìm kiếm theo tên hoặc mã), ô chọn mô hình album (M1–M5, mặc định M5) |
| Tab **Khách hàng mới** | Ô chọn quốc gia (có thể để trống), ô xổ xuống `CheckComboBox` chọn nhiều thể loại, nút "Chọn tất cả" và "Xóa hết" |
| Ô **Số album (K)** và nút **Gợi ý** | Dùng chung cho cả hai tab |
| Bảng **Top-K album** | #, album, nghệ sĩ, thể loại, mức phù hợp (thanh chấm + %), lý do (nhiều dòng, gạch đầu dòng) |
| Bảng **Track của album đã chọn** | Track, thể loại, nhạc sĩ, thời lượng, giá, mức phù hợp. Chỉ track chưa mua, xếp theo điểm T2 |
| Nút **Xem lịch sử mua (N dòng)** | Mở popup `HistoryDialog` chứa toàn bộ lịch sử. Với khách mới, nút bị vô hiệu hóa |
| Biểu đồ **Thể loại đã mua** | Số lượt mua theo thể loại (khách đã có); trống với khách mới |
| Thanh trạng thái | Ghi chú về mức phù hợp và số album đã gợi ý |

**Luồng gợi ý**
- *Khách đã có:* loại album đã mua (lấy toàn bộ từ DB) → chấm điểm bằng mô hình đã chọn → lý do từ feature → track chưa mua xếp bằng T2.
- *Khách mới:* chỉ dùng độ phổ biến. Album được giữ nếu thuộc ít nhất một thể loại đã chọn; theo quốc gia nếu có.

---

## 10. Kế hoạch & sản phẩm bàn giao

| Giai đoạn | Nội dung | Trạng thái |
|---|---|---|
| 1 | `ml/data_prep.py`: làm sạch, tương tác, chia và kiểm tra rò rỉ | Xong |
| 2 | `ml/evaluate.py`, baseline M1–M3 | Xong |
| 3 | Feature, M4, M5, tuning, `ml/train.py`, `ml/predict.py`, đóng gói | Xong |
| 4 | Mô hình track T1–T2 | Xong |
| 5 | Giao diện một màn hình, hai tab khách, popup lịch sử, biểu đồ | Xong |
| 6 | Cập nhật tài liệu (README, TECHSPEC), báo cáo ngắn | README và TECHSPEC đã cập nhật; báo cáo ngắn chưa làm |

**Bàn giao:** mã nguồn, `databases/Chinook_Sqlite.sqlite`, `models/recommender.zip`, `requirements.txt`, file `.ui` và `.py` sinh ra, các CSV trong `artifacts/`, `README.md`, tài liệu này.

---

## 11. Rủi ro

| Rủi ro | Giảm thiểu |
|---|---|
| Dữ liệu nhỏ → kết quả dao động | CI bootstrap, nhiều seed, so sánh cặp |
| M5 không vượt M3 có ý nghĩa thống kê | Ghi nhận đúng khoảng tin cậy; không tuyên bố vượt trội |
| Track gần như không dự đoán được | Báo cáo rõ Recall thấp; track chỉ xếp trong album đã chọn |
| Rò rỉ dữ liệu | Thống kê chỉ trên cửa sổ tương ứng; track đi theo album; `assert` trong `data_prep.py` |
| Overfit khi tune | Validation tách riêng, lưới nhỏ |
| Pickle có thể chạy code tùy ý | Chỉ nạp file do dự án tạo ra (NFR-06) |
| Model cũ không khớp code | Kiểm tra tên feature khi nạp; báo lỗi và hướng dẫn chạy lại `ml.train` |
| Dữ liệu mới không tự vào model | Phải đưa dữ liệu vào DB và huấn luyện lại |

---

## 12. Các quyết định đã chốt

- Đơn vị gợi ý chính: **album**. Track được xếp hạng trong album đã chọn, không gợi ý độc lập.
- Chia 80/20 theo thời gian từng customer; track đi theo album.
- Mô hình: classical ML và LambdaRank (LightGBM), không deep learning.
- Huấn luyện offline bằng `python -m ml.train`. Ứng dụng chỉ suy luận từ `models/recommender.zip`.
- Đóng gói bằng zip chứa pickle, đặt trong `models/` để UI và dòng lệnh dùng chung.
- UI: Qt Designer + PySide6, tiếng Việt, một màn hình với hai tab khách, cấu trúc `ui / dal / models / ml / test`, mỗi màn hình có `.ui`, `.py` sinh tự động và `*Ex.py`.
- Không đóng gói `.exe`.
- Mức phù hợp hiển thị tương đối trong danh sách, không hiển thị điểm thô.
