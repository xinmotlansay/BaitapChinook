# Hệ gợi ý Album & Track cho Customer (Chinook)

Bài tập môn Học máy: gợi ý Top-K **album** (kèm **track đại diện**) cho từng customer dựa trên lịch sử mua trong database Chinook. Dự án có đủ quy trình làm sạch dữ liệu, chia train/test 80/20, huấn luyện và so sánh mô hình, đánh giá, và giao diện desktop bằng Qt.

> Trạng thái: đang phát triển. Tài liệu thiết kế chi tiết nằm trong [`TECHSPEC.md`](TECHSPEC.md).

## Tính năng

- Đọc và làm sạch dữ liệu từ file SQLite, có báo cáo làm sạch
- Chia train/test 80/20 theo thời gian của từng customer (không rò rỉ dữ liệu)
- 5 mô hình: Popularity, Genre-profile, Artist+Genre profile, Content-based, Hybrid LightGBM Ranker
- Đánh giá bằng Recall@K, Precision@K, NDCG@K, MAP@K, HitRate@K, Coverage, Diversity, kèm khoảng tin cậy 95%
- Giao diện Qt (tiếng Việt) với 4 tab: Dữ liệu, Huấn luyện, Đánh giá, Gợi ý
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

Đặt file database vào `data/Chinook_Sqlite.sqlite`.

Thư viện chính: pandas, numpy, scikit-learn, lightgbm, matplotlib, PySide6.

## Cách chạy

**Giao diện:**

```bash
python main.py
```

Thứ tự dùng: tab *Dữ liệu* (chọn file, làm sạch) → *Huấn luyện* (chọn mô hình, Train) → *Đánh giá* (xem bảng/biểu đồ so sánh) → *Gợi ý* (chọn customer, xem Top-K album và track).

**Dòng lệnh (không cần giao diện):**

```bash
python train.py            # làm sạch → chia 80/20 → train → đánh giá
python -m pytest tests/    # kiểm thử chia dữ liệu và metric
```

Kết quả (model, `metrics.csv`, biểu đồ) lưu trong `artifacts/`.

## Cấu trúc thư mục

```
chinook-recsys/
├─ data/                 # Chinook_Sqlite.sqlite
├─ ml/
│  ├─ data_prep.py       # đọc, làm sạch, tạo interactions, chia train/test
│  ├─ features.py        # feature album / customer / cặp
│  ├─ models.py          # 5 mô hình, chung fit() / recommend()
│  └─ evaluate.py        # metric, bootstrap, so sánh
├─ ui/
│  ├─ main_window.ui     # thiết kế bằng Qt Designer
│  └─ main_window.py     # logic giao diện
├─ artifacts/            # kết quả sinh ra
├─ tests/
├─ config.py             # seed, tỉ lệ chia, tham số
├─ train.py
├─ main.py
└─ requirements.txt
```

## Phương pháp tóm tắt

- **Bài toán:** Top-K recommendation với implicit feedback (đã mua = 1); ứng viên là album customer chưa mua.
- **Chia dữ liệu:** với mỗi customer, 80% album mua trước → train, 20% album mua sau → test; validation cắt từ train để chọn tham số.
- **Chống rò rỉ:** popularity, profile và feature chỉ tính từ tập train.
- **Đánh giá:** NDCG@10 và Recall@10 là chính; bootstrap theo customer để có khoảng tin cậy; so sánh với baseline Artist+Genre.

## Chỉnh sửa giao diện

Mở `ui/main_window.ui` bằng Qt Designer (`pyside6-designer`), sửa rồi lưu. App nạp trực tiếp file `.ui` nên không cần biên dịch lại.

## Hạn chế

- Chỉ 59 customer nên kết quả dao động mạnh; luôn xem kèm khoảng tin cậy.
- Chinook là dữ liệu tổng hợp, ít cấu trúc sở thích thật như dữ liệu nghe nhạc thực tế.
- Không có rating hay lượt nghe, chỉ có lịch sử mua.

## Giấy phép & dữ liệu

Database Chinook là dữ liệu mẫu mã nguồn mở, dùng cho mục đích học tập. Kiểm tra giấy phép của bản bạn tải trước khi phân phối lại.
