# Hệ gợi ý Album & Track cho Customer (Chinook)

Bài tập môn Học máy: gợi ý Top-K **album** (kèm **track đại diện**) cho từng customer dựa trên lịch sử mua trong database Chinook. Dự án có đủ quy trình làm sạch dữ liệu, chia train/test 80/20, huấn luyện và so sánh mô hình, đánh giá, và giao diện desktop bằng Qt.

> Trạng thái: đang phát triển. Tài liệu thiết kế chi tiết nằm trong [`TECHSPEC.md`](TECHSPEC.md).

## Tính năng

- Đọc và làm sạch dữ liệu từ file SQLite, có báo cáo làm sạch
- Chia train/test 80/20 theo thời gian của từng customer (không rò rỉ dữ liệu)
- 5 mô hình: Popularity, Genre-profile, Artist+Genre profile, Content-based, Hybrid LightGBM Ranker
- Đánh giá bằng Recall@K, Precision@K, NDCG@K, MAP@K, HitRate@K, Coverage, Diversity, kèm khoảng tin cậy 95%
- Giao diện Qt (tiếng Việt) với 4 màn hình: Dữ liệu, Huấn luyện, Đánh giá, Gợi ý
- Gợi ý cho customer mới (cold-start) theo quốc gia hoặc genre

## Về dữ liệu

Chinook là dữ liệu cửa hàng nhạc nhỏ và thưa:

| | |
|---|---|
| Customer / Album / Track | 59 / 347 / 3.503 |
| Lượt mua | 2.240 (mỗi dòng `Quantity = 1`) |
| Mỗi customer | khoảng 38 track, 22 album |
| Track chỉ có 1 người mua | 1.728 / 1.984 |

Vì rất ít customer mua trùng track, collaborative filtering gần như không dùng được. Dự án vì thế gợi ý **album** bằng content-based và hybrid (genre, artist, composer, popularity). Kết quả được kỳ vọng ở mức khiêm tốn; điều quan trọng là so sánh công bằng với baseline và kết luận trung thực.

## Cài đặt

Yêu cầu: Python 3.11+.

```bash
git clone <repo-url>
cd chinook-recsys
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Đặt file database vào `databases/Chinook_Sqlite.sqlite`.

Thư viện chính: pandas, numpy, scikit-learn, lightgbm, matplotlib, PySide6.

## Cách chạy

**Giao diện:**

```bash
python main.py
```

Thứ tự dùng: màn hình *Dữ liệu* (chọn file, làm sạch) → *Huấn luyện* (chọn mô hình, Train) → *Đánh giá* (xem bảng/biểu đồ so sánh) → *Gợi ý* (chọn customer, xem Top-K album và track).

Luôn chạy từ thư mục gốc dự án. Để thử riêng một màn hình: `python -m test.test_recommend_window` (tương tự cho các màn khác).

**Kiểm thử tự động:**

```bash
python -m pytest test/test_split_metrics.py
```

Kết quả (model, `metrics.csv`, biểu đồ) lưu trong `artifacts/`.

## Cấu trúc thư mục

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

- `ui/`: mỗi màn hình gồm `.ui` (Qt Designer), `.py` (sinh bằng `pyside6-uic`) và `*Ex.py` (logic sự kiện).
- `dal/`: nơi duy nhất viết SQL. `models/`: lớp dữ liệu thuần. `ml/`: làm sạch, chia dữ liệu, mô hình, đánh giá.
- `test/`: file mở riêng từng cửa sổ để thử tay, và `test_split_metrics.py` kiểm tra tự động.

## Phương pháp tóm tắt

- **Bài toán:** Top-K recommendation với implicit feedback (đã mua = 1); ứng viên là album customer chưa mua.
- **Chia dữ liệu:** với mỗi customer, 80% album mua trước → train, 20% album mua sau → test; validation cắt từ train để chọn tham số.
- **Chống rò rỉ:** popularity, profile và feature chỉ tính từ tập train.
- **Đánh giá:** NDCG@10 và Recall@10 là chính; bootstrap theo customer để có khoảng tin cậy; so sánh với baseline Artist+Genre.

## Chỉnh sửa giao diện

Mở file `.ui` trong `ui/` bằng Qt Designer (`pyside6-designer`), sửa rồi lưu, sau đó sinh lại file `.py`:

```bash
pyside6-uic ui/RecommendMainWindow.ui -o ui/RecommendMainWindow.py
```

Không sửa tay file `.py` sinh tự động; logic viết trong `*Ex.py`.

## Hạn chế

- Chỉ 59 customer nên kết quả dao động mạnh; luôn xem kèm khoảng tin cậy.
- Chinook là dữ liệu tổng hợp, ít cấu trúc sở thích thật như dữ liệu nghe nhạc thực tế.
- Không có rating hay lượt nghe, chỉ có lịch sử mua.

## Giấy phép & dữ liệu

Database Chinook là dữ liệu mẫu mã nguồn mở, dùng cho mục đích học tập. Kiểm tra giấy phép của bản bạn tải trước khi phân phối lại.
