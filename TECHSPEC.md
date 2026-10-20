# TECHSPEC — Hệ gợi ý Album & Track cho Customer (Chinook)

| | |
|---|---|
| Phiên bản | 1.3 |
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
| FR-10 | Lưu mô hình đã train (`.joblib`) cùng tên feature/thứ tự cột; nạp lại để gợi ý mà không train lại; xuất kết quả đánh giá (CSV) |

### 3.2 Phi chức năng

| ID | Yêu cầu |
|---|---|
| NFR-01 | Tái lập: seed cố định (42), cấu hình trong `config.py` |
| NFR-02 | **Không rò rỉ dữ liệu:** mọi thống kê (popularity, profile, feature) chỉ tính từ train |
| NFR-03 | Train toàn bộ < 2 phút; gợi ý 1 customer < 1 giây |
| NFR-04 | UI không treo khi train (dùng `QThread`) |
| NFR-05 | Code ML không phụ thuộc Qt (có thể chạy bằng dòng lệnh `python -m ml.train`) |

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
│  ├─ train.py              # HUẤN LUYỆN: làm sạch → chia → fit → đánh giá → lưu model
│  ├─ predict.py            # SUY LUẬN: nạp model đã lưu và gợi ý (không train lại)
│  └─ evaluate.py           # metric, bootstrap, so sánh model
├─ ui/                      # mỗi màn hình có 3 file
│  ├─ DataMainWindow.ui / .py / DataMainWindowEx.py
│  ├─ TrainMainWindow.ui / .py / TrainMainWindowEx.py
│  ├─ EvaluateMainWindow.ui / .py / EvaluateMainWindowEx.py
│  ├─ RecommendMainWindow.ui / .py / RecommendMainWindowEx.py
│  └─ utils.py              # hàm dùng chung: showDataIntoTableWidget, vẽ biểu đồ
├─ test/                    # mở file nào là xem được giao diện và chạy được mô hình
│  ├─ test_app.py           # mở toàn bộ ứng dụng (4 màn hình)
│  ├─ test_data_window.py   # mở màn Dữ liệu
│  ├─ test_train_window.py  # mở màn Huấn luyện
│  ├─ test_evaluate_window.py # mở màn Đánh giá
│  └─ test_recommend_window.py # mở màn Gợi ý
├─ images/                  # icon
├─ artifacts/               # recommender.joblib, metrics.csv, biểu đồ
├─ config.py                # seed, tỉ lệ chia, đường dẫn (Path(__file__).parent)
├─ main.py                  # chạy app (mở RecommendMainWindow)
└─ requirements.txt
```

**Vai trò**

| Thư mục | Nội dung |
|---|---|
| `ui/` | `.ui` thiết kế bằng Qt Designer; `.py` sinh tự động bằng `pyside6-uic`; `*Ex.py` chứa logic gắn sự kiện, kế thừa lớp sinh tự động |
| `dal/` | Chỉ nơi này viết SQL; luôn dùng truy vấn tham số hóa (`?`) |
| `models/` | Lớp dữ liệu thuần (dataclass) |
| `ml/` | Làm sạch, chia dữ liệu, feature, mô hình, đánh giá; `train.py` và `predict.py` tách riêng; trả về pandas/dataclass cho UI |
| `test/` | Các file khởi chạy: mở lên là thấy giao diện và chạy được mô hình (không phải unit test) |

Giao diện thống nhất của mô hình: `fit(train)`, `recommend(customer_id, k, exclude)`.

---

## 8.1 Quy tắc lập trình bắt buộc

### A. Quy tắc làm mô hình máy học

1. **Khám phá dữ liệu trước khi train:** in `head()`, `info()`, `describe()`, đếm giá trị thiếu và kiểu dữ liệu (ghi vào báo cáo làm sạch).
2. **Định nghĩa feature tường minh ở một chỗ** (`FEATURE_COLUMNS` trong `ml/features.py`). Không đưa cột văn bản thô (tên album, composer thô) vào mô hình số; phải mã hóa (TF-IDF, one-hot, đếm) trước.
3. **Chia train/test trước khi fit**, seed cố định (`SEED = 42` trong `config.py`) để kết quả tái lập.
4. **Chỉ đánh giá trên tập test** (validation chỉ để chọn tham số). Không bao giờ báo cáo chỉ số tính trên train.
5. **Báo cáo chỉ số, không chỉ in danh sách gợi ý:** Recall@K, NDCG@K... kèm CI. Với mô hình LightGBM, kèm feature importance; với mô hình profile, kèm điểm thành phần để giải thích.
6. **Lưu model kèm tên feature và thứ tự cột.** Khi dự đoán, kiểm tra thứ tự cột khớp lúc train; sai thì báo lỗi rõ.
7. **Tách training và inference thành hai file:** `ml/train.py` và `ml/predict.py`. Inference chỉ nạp `artifacts/recommender.joblib`, không phụ thuộc việc train lại.
8. **Đường dẫn dùng `Path(__file__).parent`** (gom trong `config.py`), không dùng đường dẫn tương đối theo thư mục chạy.
9. **Đuôi file model là `.joblib`** (không đặt `.zip`/`.pkl` gây hiểu nhầm). Chỉ nạp file do chính dự án tạo ra, vì pickle/joblib có thể chạy code tùy ý.
10. **Dùng `logging`** (không dùng `print`) cho tiến trình train, số dòng bị loại khi làm sạch, kết quả đánh giá; UI hiển thị log qua signal.
11. **Ngôn ngữ nhất quán:** chuỗi giao diện và thông báo hoàn toàn tiếng Việt; tên biến/hàm/class tiếng Anh; comment tiếng Việt có dấu.

### B. Quy tắc giao diện

1. **Tách thiết kế và logic:** `XxxMainWindow.ui` (Qt Designer) → `XxxMainWindow.py` (sinh tự động bằng `pyside6-uic`, **không sửa tay**) → `XxxMainWindowEx.py` (kế thừa `Ui_MainWindow`, chứa mọi xử lý sự kiện).
2. **Khởi tạo đúng thứ tự:** `__init__` → `setupUi(MainWindow)` → `setupSignalAndSlot()` → `showWindow()`. Mọi `connect(...)` gom trong `setupSignalAndSlot()`.
3. **Bắt lỗi và báo bằng hộp thoại:** hàm xử lý sự kiện bọc `try/except`, dùng `QMessageBox.critical` (lỗi hệ thống/DB/train) hoặc `warning` (nhập sai). Tiêu đề ngắn, tiếng Việt: "Lỗi dữ liệu", "Thông báo", "Lỗi biểu đồ".
4. **Kiểm tra đầu vào trước khi xử lý:** chưa chọn customer, chưa làm sạch, chưa train, K không hợp lệ... thì cảnh báo và dừng, không chạy với dữ liệu rỗng.
5. **Logic dữ liệu nằm ở DAO/`ml/`, không nằm trong UI.** UI chỉ gọi hàm rồi hiển thị. DAO dùng `@staticmethod` và trả về `DataFrame`.
6. **Một hàm hiển thị bảng dùng chung:** `showDataIntoTableWidget(table, df)` trong `ui/utils.py`, mọi màn hình dùng lại, không viết lặp.
7. **Kết nối gói trong `ensureConnection()`** (ở `connectors/connector.py`): kiểm tra còn dùng được trước mỗi truy vấn, mở lại nếu cần; mỗi DAO không tự mở kết nối riêng rải rác, và luôn đóng bằng `with`/`finally`.
8. **Biểu đồ nhúng Qt bằng `FigureCanvasQTAgg` + `NavigationToolbar2QT`.** Mỗi lần vẽ lại: `figure.clear()` → vẽ → `tight_layout()` → `canvas.draw()`.
9. **SQL luôn dùng placeholder** (`?` với SQLite) và truyền tham số qua `execute(sql, params)`; không nối chuỗi/f-string vào câu SQL.
10. **Tác vụ nặng (train, đánh giá) chạy trong `QThread`/worker**, khóa nút khi đang chạy, mở lại khi xong hoặc lỗi.

### C. Quy tắc kiểm tra

1. Thư mục `test/` chỉ chứa các file **khởi chạy giao diện** (xem §8.2), không viết unit test riêng.
2. Việc chống rò rỉ dữ liệu và kiểm tra chia train/test được **kiểm tra ngay trong code** (`assert` và log trong `ml/data_prep.py`: không album test nào nằm trong train, mỗi customer có đủ train và test), và kết quả hiện ở màn Dữ liệu.

---

## 8.2 Yêu cầu: thư mục `test/` mở lên là xem được giao diện và chạy được mô hình

`test/` là nơi giảng viên mở file bất kỳ (bằng IDE rồi bấm Run, hoặc `python test/test_xxx.py` từ thư mục nào cũng được) để **thấy ngay giao diện và chạy mô hình**, không cần chuẩn bị gì thêm. Không có test thủ công hay unit test riêng.

| File | Mở lên là |
|---|---|
| `test_app.py` | Toàn bộ ứng dụng: điều hướng giữa 4 màn hình, chạy được cả quy trình làm sạch → train → đánh giá → gợi ý |
| `test_data_window.py` | Màn Dữ liệu: đã nạp database, bấm "Làm sạch" là có báo cáo |
| `test_train_window.py` | Màn Huấn luyện: bấm Train là chạy mô hình, có thanh tiến độ và log |
| `test_evaluate_window.py` | Màn Đánh giá: bảng và biểu đồ so sánh mô hình, bấm "Đánh giá" để chạy lại |
| `test_recommend_window.py` | Màn Gợi ý: chọn customer, bấm Gợi ý là có Top-K album và track |

**Quy tắc đảm bảo**

1. **Tự định vị thư mục gốc:** đầu mỗi file có đoạn `Path(__file__)` thêm gốc dự án vào `sys.path`, nên chạy từ đâu cũng import được `ui`, `dal`, `ml`, `models`, `connectors`:

```python
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, ROOT.as_posix())

from PySide6.QtWidgets import QApplication, QMainWindow
from ui.RecommendMainWindowEx import RecommendMainWindowEx

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QMainWindow()
    ui = RecommendMainWindowEx()
    ui.setupUi(window)
    ui.showWindow()
    sys.exit(app.exec())
```

2. **Đi kèm sẵn dữ liệu và model:** `databases/Chinook_Sqlite.sqlite`, `artifacts/recommender.joblib`, `artifacts/metrics.csv` nằm trong bài nộp để màn Đánh giá và Gợi ý có dữ liệu ngay khi mở. Nếu thiếu model, chương trình tự huấn luyện nhanh (dưới 1 phút) và ghi log.
3. **Chạy được mô hình ngay trong giao diện:** màn nào cũng có nút hành động rõ ràng (Làm sạch, Train, Đánh giá, Gợi ý); giá trị mặc định đã điền sẵn (customer đầu tiên, K=10, mô hình tốt nhất), bấm nút là chạy, không cần nhập tham số.
4. **Thiếu điều kiện tiên quyết thì tự xử lý hoặc hướng dẫn:** ví dụ chưa làm sạch thì tự làm sạch, hoặc hiện `QMessageBox` tiếng Việt chỉ rõ bước cần làm; không để văng traceback.
5. **Chỉ phụ thuộc thư viện trong `requirements.txt`**; thiếu thư viện thì in đúng lệnh `pip install -r requirements.txt`.
6. **Checklist trước khi nộp:** trong môi trường ảo mới, chỉ cài `requirements.txt`, rồi từ một thư mục khác mở lần lượt cả 5 file trong `test/`; cả 5 phải hiện giao diện và bấm nút chạy được mô hình, không lỗi import hay lỗi đường dẫn.

---

## 9. Giao diện Qt (Qt Designer + PySide6, tiếng Việt)

4 màn hình (mỗi màn hình là một `QMainWindow`, `RecommendMainWindow` mở đầu tiên, các màn khác mở từ menu/nút điều hướng):

| Màn hình | Chức năng |
|---|---|
| **1. Dữ liệu** (`DataMainWindow`) | Nút chọn file SQLite; nút "Làm sạch"; bảng báo cáo làm sạch; thống kê (số customer/album/track, phân bố genre); xem bảng chia train/test theo từng customer |
| **2. Huấn luyện** (`TrainMainWindow`) | Chọn mô hình (M1–M5) và tham số chính, tỉ lệ chia (mặc định 80/20); nút Train; thanh tiến độ và log (chạy `QThread`); nút lưu/nạp model |
| **3. Đánh giá** (`EvaluateMainWindow`) | Bảng metric của các mô hình đã train (kèm CI); biểu đồ cột so sánh; chọn K; nút xuất CSV |
| **4. Gợi ý** (`RecommendMainWindow`) | Chọn customer (có ô tìm kiếm) hoặc "Customer mới" (chọn quốc gia/genre); chọn mô hình và K; bảng Top-K album (artist, genre, điểm, lý do); chọn album → danh sách track đại diện; bên cạnh là lịch sử mua và biểu đồ genre của customer |

Biểu đồ, thông báo lỗi, kiểm tra đầu vào và khóa nút tuân theo §8.1-B. Ví dụ: chưa làm sạch thì chưa train được; chưa train thì chưa đánh giá/gợi ý được.

---

## 10. Kế hoạch & sản phẩm bàn giao

| Giai đoạn | Nội dung | Kết quả |
|---|---|---|
| 1 | `ml/data_prep.py`: làm sạch, interactions, chia 80/20 + kiểm tra rò rỉ bằng `assert` | Dữ liệu sạch, báo cáo làm sạch |
| 2 | `ml/evaluate.py` + baseline M1–M3 | Bảng baseline có CI |
| 3 | `ml/features.py` + M4, M5, `ml/train.py`/`ml/predict.py`, tuning | Mô hình chính, phân tích lỗi |
| 4 | Thiết kế 4 file `.ui` + `*Ex.py` nối chức năng | App chạy đủ 4 màn hình |
| 5 | Rà soát theo §8.1, chạy checklist §8.2, viết báo cáo ngắn (kết quả, hạn chế) | Mã nguồn + báo cáo |

**Bàn giao:** mã nguồn, `databases/Chinook_Sqlite.sqlite`, `artifacts/recommender.joblib`, `requirements.txt`, file `.ui` (và `.py` sinh ra), `metrics.csv` và biểu đồ, hướng dẫn chạy ngắn.

---

## 11. Rủi ro

| Rủi ro | Giảm thiểu |
|---|---|
| Dữ liệu nhỏ → kết quả dao động | CI bootstrap, nhiều seed, so sánh paired |
| Mô hình không thắng M3 | Chấp nhận và phân tích; ghi vào báo cáo |
| Rò rỉ dữ liệu | Thống kê chỉ trên train; có `assert` kiểm tra ngay trong `data_prep.py` |
| Overfit khi tune | Validation tách riêng, ít tham số |
| Chinook là dữ liệu tổng hợp | Nêu rõ trong phần hạn chế của báo cáo |

---

## 12. Các quyết định đã chốt

- Đơn vị gợi ý: Album (track chỉ là phụ kèm theo).
- Chia 80/20 theo thời gian từng customer.
- Mô hình: classical ML + hybrid, không deep learning.
- UI: Qt Designer + PySide6, tiếng Việt, cấu trúc `ui / dal / models / ml / test`, mỗi màn hình 3 file (`.ui`, `.py`, `*Ex.py`).
- Không đóng gói .exe; không gợi ý track độc lập.
- Tuân theo bộ quy tắc ở §8.1 (ML, giao diện, kiểm thử).
- Thư mục `test/` chỉ chứa file khởi chạy: mở ra là xem được giao diện và chạy được mô hình (§8.2); bài nộp kèm sẵn database và model đã train.
