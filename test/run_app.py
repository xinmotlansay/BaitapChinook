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
