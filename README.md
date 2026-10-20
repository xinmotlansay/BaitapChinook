# Hệ gợi ý Album & Track cho Customer (Chinook)

Bài tập môn Học máy: gợi ý Top-K **album** cho từng customer dựa trên lịch sử mua trong database Chinook, kèm **track** được dự đoán trong từng album. Mô hình được huấn luyện offline; ứng dụng desktop (PySide6) chỉ nạp model đã đóng gói để gợi ý.

Chi tiết thiết kế, mô hình và đánh giá nằm trong [`TECHSPEC.md`](TECHSPEC.md).

## Tính năng

- Gợi ý Top-K album cho **khách hàng đã có**, chọn mô hình album (M1–M5)
- Gợi ý cho **khách hàng mới** theo quốc gia và nhiều thể loại (theo độ phổ biến)
- Với mỗi album: lý do gợi ý và **danh sách track chưa mua, xếp theo mức phù hợp** (mô hình T2)
- Lịch sử mua trong popup, biểu đồ số lượt mua theo thể loại

## Về dữ liệu

Chinook là dữ liệu cửa hàng nhạc nhỏ và thưa:

| | |
|---|---|
| Customer / Album / Track | 59 / 347 / 3.503 |
| Lượt mua (dòng hóa đơn) | 2.240 (mỗi dòng `Quantity = 1`) |
| Mỗi customer | khoảng 38 track, 22 album |
| Track chỉ có 1 người mua | 1.728 / 1.984 |

Vì rất ít customer mua trùng track, collaborative filtering gần như không dùng được. Dự án vì thế dùng content-based và hybrid (thể loại, nghệ sĩ, nhạc sĩ, độ phổ biến). Kết quả được kỳ vọng ở mức khiêm tốn; điều quan trọng là so sánh công bằng với baseline và kết luận trung thực.

## Cài đặt

Yêu cầu: Python 3.11+ (dự án đang chạy trên 3.12).

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Đặt file database vào `databases/Chinook_Sqlite.sqlite`.

Thư viện chính: pandas, numpy, scikit-learn, lightgbm, matplotlib, PySide6.

## Cách chạy

**1. Huấn luyện (chạy một lần, hoặc khi đổi dữ liệu / code feature):**

```bash
python -m ml.train
```

Lệnh này làm sạch dữ liệu, chia train/test, chọn tham số trên validation, huấn luyện và đánh giá, rồi ghi:

- `models/recommender.zip`: model đã đóng gói (dùng cho UI và dòng lệnh)
- `artifacts/`: `metrics.csv`, `track_metrics.csv`, `paired_vs_m3.csv`, `m5_seeds.csv`, `m5_tuning.csv`, `track_tuning.csv`

Thời gian chạy khoảng 15–45 giây.

**2. Giao diện:**

```bash
python main.py
```

Nếu chưa có `models/recommender.zip`, ứng dụng tự huấn luyện lần đầu (khoảng 10–45 giây).

Cách dùng:
- Tab **Khách hàng đã có**: chọn khách, chọn mô hình album, chọn K, bấm **Gợi ý**.
- Tab **Khách hàng mới**: chọn quốc gia (không bắt buộc) và đánh dấu một hoặc nhiều thể loại trong ô xổ xuống, rồi bấm **Gợi ý**.
- Bấm một dòng trong bảng album để xem các track chưa mua của album đó.
- Bấm **Xem lịch sử mua** để mở lịch sử đầy đủ trong popup.

**3. Dòng lệnh:**

```bash
python -m ml.predict --customer 5 --k 10
python -m ml.predict --customer 5 --k 10 --model M3
```

**4. Chạy thử giao diện từ IDE:** mở `test/run_app.py` rồi bấm Run, hoặc chạy `python test/run_app.py` từ thư mục bất kỳ.

## Cấu trúc thư mục

```
BaitapChinook/
├─ databases/
│  └─ Chinook_Sqlite.sqlite      # dữ liệu gốc (chỉ đọc)
├─ connectors/
│  └─ connector.py               # kết nối SQLite dùng chung
├─ models/                       # lớp dữ liệu thuần, không có hành vi
│  ├─ customer.py
│  ├─ album.py                   # Album, Track
│  ├─ recommendation.py          # Recommendation (album, điểm, lý do, track kèm điểm)
│  └─ recommender.zip            # model đã đóng gói (tạo bởi ml.train)
├─ dal/                          # truy cập dữ liệu, chỉ nơi này viết SQL
│  ├─ CustomerDAO.py
│  └─ AlbumDAO.py
├─ ml/                           # học máy, không phụ thuộc Qt
│  ├─ data_prep.py               # làm sạch, tương tác customer-album và customer-track, chia cửa sổ
│  ├─ features.py                # ProfileState: thống kê và feature (album và track)
│  ├─ recommenders.py            # M1–M5, T1–T2, hàm huấn luyện LambdaRank
│  ├─ evaluate.py                # metric, bootstrap CI, so sánh cặp
│  ├─ train.py                   # HUẤN LUYỆN
│  ├─ predict.py                 # SUY LUẬN: nạp model, gợi ý (không train lại)
│  └─ package.py                 # đóng gói / nạp model (zip + pickle)
├─ ui/
│  ├─ RecommendMainWindow.ui     # thiết kế giao diện (Qt Designer)
│  ├─ RecommendMainWindow.py     # sinh tự động bằng pyside6-uic, không sửa tay
│  ├─ RecommendMainWindowEx.py   # logic sự kiện
│  ├─ HistoryDialog.py           # popup lịch sử mua
│  ├─ widgets.py                 # CheckComboBox: ô xổ xuống chọn nhiều
│  └─ utils.py                   # bảng dùng chung, biểu đồ, thanh mức phù hợp
├─ test/
│  └─ run_app.py                 # mở ứng dụng
├─ artifacts/                    # kết quả huấn luyện (CSV)
├─ config.py                     # đường dẫn, seed, tỉ lệ chia, số mẫu âm
├─ main.py                       # chạy ứng dụng
├─ requirements.txt
├─ README.md
└─ TECHSPEC.md
```

## Lưu ý về model

- File `models/recommender.zip` chứa pickle. **Chỉ nạp file do chính dự án tạo ra**, vì pickle có thể chạy code tùy ý khi nạp.
- Model được tạo khi huấn luyện. Nếu bạn đổi code feature hoặc thêm dữ liệu vào database, cần chạy lại `python -m ml.train`.
- Điểm gợi ý dựa trên lịch sử train (80% album đầu của mỗi customer). Lịch sử mua trong database vẫn được dùng để loại album/track đã mua và để hiển thị.

## Giới hạn

- Chỉ 59 customer nên kết quả dao động mạnh; luôn xem kèm khoảng tin cậy.
- Track gần như không dự đoán được (Recall@10 khoảng 1,6%).
- Chinook là dữ liệu mẫu, ít cấu trúc sở thích thật như dữ liệu nghe nhạc thực tế.
- Không có rating hay lượt nghe, chỉ có lịch sử mua.

## Giấy phép & dữ liệu

Database Chinook là dữ liệu mẫu mã nguồn mở, dùng cho mục đích học tập. Kiểm tra giấy phép của bản bạn tải trước khi phân phối lại.
