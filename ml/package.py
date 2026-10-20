"""Đóng gói model thành một file .zip (model.pkl bên trong), nạp lại bằng pickle.

Bên trong file zip:
    meta.json        tham số, tên feature, phiên bản đóng gói (đọc được bằng text)
    model.pkl        pickle của state, LambdaRank album, LambdaRank track và bảng album
    using_model.py   ví dụ cách dùng model: chạy từ thư mục gốc của dự án

File zip nằm trong thư mục models/ để UI và dòng lệnh dùng chung.

Chỉ nạp file do chính dự án tạo ra, vì pickle có thể chạy code tùy ý khi nạp.
"""
import json
import pickle
import zipfile

FORMAT_VERSION = 1

USING_MODEL_SRC = '''"""Cách dùng model đã đóng gói. Chạy từ thư mục gốc của dự án:

    python using_model.py 5 10
"""
import sys
from pathlib import Path

from ml.predict import Predictor

ZIP_PATH = Path("models") / "recommender.zip"

if __name__ == "__main__":
    customer_id = int(sys.argv[1])
    k = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    predictor = Predictor(ZIP_PATH)
    for rank, rec in enumerate(predictor.recommend(customer_id, k), start=1):
        print(f"{rank:2d}. {rec.title} - {rec.artist} ({rec.score:.3f})")
'''


def save_package(path, state, ranker, track_ranker, albums, meta):
    """Ghi state (thống kê của train), hai LambdaRank, bảng album và ví dụ sử dụng vào một file zip."""
    full_meta = {**meta, "format_version": FORMAT_VERSION}
    payload = pickle.dumps({
        "state": state,
        "ranker": ranker,
        "track_ranker": track_ranker,
        "albums": albums,
    })

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("meta.json", json.dumps(full_meta, ensure_ascii=False, indent=2))
        z.writestr("model.pkl", payload)
        z.writestr("using_model.py", USING_MODEL_SRC)
    return path


def load_package(path):
    """Nạp lại (state, ranker, track_ranker, albums, meta) từ file zip đã đóng gói."""
    with zipfile.ZipFile(path) as z:
        meta = json.loads(z.read("meta.json").decode("utf-8"))
        if meta.get("format_version") != FORMAT_VERSION:
            raise ValueError("Phiên bản đóng gói model không được hỗ trợ. Hãy chạy lại: python -m ml.train")
        bundle = pickle.loads(z.read("model.pkl"))

    return bundle["state"], bundle["ranker"], bundle["track_ranker"], bundle["albums"], meta
