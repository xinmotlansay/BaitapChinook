from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "databases" / "Chinook_Sqlite.sqlite"
ARTIFACTS_DIR = ROOT / "artifacts"
MODELS_DIR = ROOT / "models"
MODEL_PATH = MODELS_DIR / "recommender.zip"
METRICS_PATH = ARTIFACTS_DIR / "metrics.csv"

SEED = 42
TRAIN_RATIO = 0.8          # 80% album đầu của mỗi customer -> train
VALID_RATIO = 0.2          # 20% cuối của phần train -> validation (chọn tham số)
K_VALUES = (5, 10, 20)
BOOTSTRAP_N = 1000
NEG_RATIO = 30             # số mẫu âm cho mỗi mẫu dương khi huấn luyện LambdaRank
LGB_SEEDS = (42, 43, 44, 45, 46)
