import logging
import sys

from PySide6.QtWidgets import QApplication, QMainWindow

from ui.RecommendMainWindowEx import RecommendMainWindowEx

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    app = QApplication(sys.argv)
    window = QMainWindow()
    ui = RecommendMainWindowEx()
    ui.setupUi(window)
    ui.showWindow()
    sys.exit(app.exec())
