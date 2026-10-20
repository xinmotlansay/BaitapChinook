import logging

import pandas as pd
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHeaderView,
    QMessageBox,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

from config import MODEL_PATH
from connectors.connector import Connector
from dal.CustomerDAO import CustomerDAO
from ml.predict import Predictor
from ui.HistoryDialog import HistoryDialog
from ui.RecommendMainWindow import Ui_MainWindow
from ui.utils import drawGenreChart, relativeBars, showDataIntoTableWidget

logger = logging.getLogger(__name__)

RECOMMEND_COLUMNS = ["#", "Album", "Nghệ sĩ", "Thể loại", "Mức phù hợp", "Lý do"]
TRACK_COLUMNS = ["Track", "Thể loại", "Nhạc sĩ", "Thời lượng (phút)", "Giá (USD)", "Mức phù hợp"]
SCALE_NOTE = "Mức phù hợp là tương đối trong danh sách: 100% là cao nhất, 0% là thấp nhất."
HISTORY_COLUMNS = ["Ngày mua", "Track", "Album", "Nghệ sĩ", "Thể loại"]


class RecommendMainWindowEx(Ui_MainWindow):

    def __init__(self):
        super().__init__()
        self.window = None
        self.predictor = None
        self.recommendations = []
        self.allCustomers = []
        self.context = ""
        self.historyRows = pd.DataFrame(columns=HISTORY_COLUMNS)
        self.historyWho = ""
        self.figure = None
        self.canvas = None

    def setupUi(self, MainWindow):
        super().setupUi(MainWindow)
        self.window = MainWindow
        self.setupTables()
        self.setupSignalAndSlot()
        self.setupChart()
        self.verticalLayoutResults.setStretch(1, 1)
        self.verticalLayoutResults.setStretch(2, 3)
        self.horizontalLayoutBottom.setStretch(0, 2)
        self.horizontalLayoutBottom.setStretch(1, 3)
        self.verticalLayoutRight.setStretch(1, 1)
        self.verticalLayoutRight.setStretch(3, 3)
        self.loadModel()
        self.loadFilters()

    def setupTables(self):
        for table in (self.tableRecommend, self.tableTracks):
            table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

    def setupSignalAndSlot(self):
        self.btnRecommend.clicked.connect(self.onRecommend)
        self.btnHistory.clicked.connect(self.openHistoryDialog)
        self.btnSelectAllGenres.clicked.connect(lambda: self.cbGenres.setAllChecked(True))
        self.btnClearGenres.clicked.connect(lambda: self.cbGenres.setAllChecked(False))
        self.txtSearch.textChanged.connect(self.onSearchChanged)
        self.tableRecommend.itemSelectionChanged.connect(self.onRecommendationSelected)
        self.lblTracksTitle.setText("Track dự đoán của album đã chọn (chưa mua, xếp theo điểm)")

    def setupChart(self):
        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvasQTAgg(self.figure)
        toolbar = NavigationToolbar2QT(self.canvas, self.window)
        layout = self.chartHost.layout()
        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)
        drawGenreChart(self.canvas, pd.Series(dtype=int))

    def loadModel(self):
        try:
            if not MODEL_PATH.exists():
                self.lblStatus.setText("Chưa có model, đang huấn luyện lần đầu (khoảng 10 giây)...")
                QApplication.processEvents()
                from ml.train import run
                run()
            self.predictor = Predictor()
        except Exception as error:
            logger.exception("Không nạp được model")
            QMessageBox.critical(self.window, "Lỗi model", f"Không nạp được model: {error}")

    def loadFilters(self):
        if self.predictor is None:
            return

        self.allCustomers = [
            (f"{r.CustomerId} - {r.Name} ({r.Country})", int(r.CustomerId))
            for r in CustomerDAO.getAll().itertuples(index=False)
        ]
        self.fillCustomers(self.allCustomers)

        self.cbCountry.addItem("")
        for country in CustomerDAO.getCountries()["Country"]:
            self.cbCountry.addItem(country)

        self.fillGenres(self.predictor.state.genre_names)

        for key, name in self.predictor.model_names().items():
            self.cbModel.addItem(name, key)
        default_index = self.cbModel.findData(self.predictor.default_model)
        self.cbModel.setCurrentIndex(max(default_index, 0))

        self.lblStatus.setText("Sẵn sàng.")

    def fillGenres(self, genres):
        for genre in genres:
            self.cbGenres.addCheckItem(genre)

    def selectedGenres(self):
        return self.cbGenres.checkedItems()

    def fillCustomers(self, items):
        self.cbCustomer.clear()
        for text, customer_id in items:
            self.cbCustomer.addItem(text, customer_id)

    def showWindow(self):
        QApplication.instance().aboutToQuit.connect(Connector.close)
        self.window.show()

    def onSearchChanged(self, text):
        keyword = text.strip().lower()
        matched = [item for item in self.allCustomers if keyword in item[0].lower()]
        self.fillCustomers(matched)

    def onRecommend(self):
        try:
            if self.predictor is None:
                QMessageBox.warning(self.window, "Thông báo", "Model chưa sẵn sàng.")
                return

            k = self.spinK.value()
            if self.tabCustomer.currentWidget() is self.tabNew:
                country = self.cbCountry.currentText() or None
                genres = self.selectedGenres()
                if country is None and not genres:
                    QMessageBox.warning(self.window, "Thông báo", "Hãy chọn quốc gia hoặc ít nhất một thể loại.")
                    return
                recs = self.predictor.cold_start(k, country, genres)
                history = None
                who = f"khách mới ({country or 'mọi quốc gia'}, {', '.join(genres) or 'mọi thể loại'})"
                model_name = "độ phổ biến"
            else:
                customer_id = self.cbCustomer.currentData()
                if customer_id is None:
                    QMessageBox.warning(self.window, "Thông báo", "Hãy chọn khách hàng.")
                    return
                model_key = self.cbModel.currentData()
                recs = self.predictor.recommend(customer_id, k, model_key)
                history = CustomerDAO.getPurchaseHistory(customer_id)
                who = self.cbCustomer.currentText()
                model_name = self.predictor.model_names()[model_key]

            self.recommendations = recs
            self.context = f"Gợi ý cho {who} · mô hình: {model_name}"
            self.showRecommendations(recs)
            self.showHistory(history)
            self.lblStatus.setText(f"{SCALE_NOTE}  Đã gợi ý {len(recs)} album.")
        except Exception as error:
            logger.exception("Gợi ý thất bại")
            QMessageBox.critical(self.window, "Lỗi hệ thống", f"Không thể gợi ý: {error}")

    def showRecommendations(self, recs):
        self.lblRecommendTitle.setText(f"Top-{len(recs)} album · {self.context}" if recs else "Top-K album gợi ý")
        bars = relativeBars([r.score for r in recs])
        rows = [
            {
                "#": i,
                "Album": r.title,
                "Nghệ sĩ": r.artist,
                "Thể loại": r.genres,
                "Mức phù hợp": bar,
                "Lý do": "\n".join(f"• {reason}" for reason in r.reasons),
            }
            for i, (r, bar) in enumerate(zip(recs, bars), start=1)
        ]
        showDataIntoTableWidget(self.tableRecommend, pd.DataFrame(rows, columns=RECOMMEND_COLUMNS))
        self.tableRecommend.setWordWrap(True)
        self.tableRecommend.resizeRowsToContents()
        header = self.tableRecommend.horizontalHeader()
        for col in range(len(RECOMMEND_COLUMNS) - 1):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(len(RECOMMEND_COLUMNS) - 1, QHeaderView.ResizeMode.Stretch)
        self.lblTracksTitle.setText("Chọn một album ở trên để xem track")
        showDataIntoTableWidget(self.tableTracks, pd.DataFrame(columns=TRACK_COLUMNS))

    def onRecommendationSelected(self):
        row = self.tableRecommend.currentRow()
        if row < 0 or row >= len(self.recommendations):
            return

        rec = self.recommendations[row]
        tracks = rec.tracks
        bars = relativeBars([score for _, score in tracks])
        rows = [
            {
                "Track": t.name,
                "Thể loại": t.genre,
                "Nhạc sĩ": t.composer,
                "Thời lượng (phút)": f"{t.milliseconds / 60000:.2f}",
                "Giá (USD)": f"{t.unit_price:.2f}",
                "Mức phù hợp": bar,
            }
            for (t, _), bar in zip(tracks, bars)
        ]
        self.lblTracksTitle.setText(f"Track của album \"{rec.title}\" (chưa mua, xếp theo mức phù hợp)")
        showDataIntoTableWidget(self.tableTracks, pd.DataFrame(rows, columns=TRACK_COLUMNS))
        if not tracks:
            self.lblStatus.setText("Bạn đã mua hết track của album này.")

    def showHistory(self, history):
        if history is None or history.empty:
            self.historyRows = pd.DataFrame(columns=HISTORY_COLUMNS)
            self.btnHistory.setText("Lịch sử mua: chưa có")
            self.btnHistory.setEnabled(False)
            drawGenreChart(self.canvas, pd.Series(dtype=int))
            return

        dates = pd.to_datetime(history["InvoiceDate"]).dt.strftime("%d/%m/%Y")
        self.historyRows = pd.DataFrame({
            "Ngày mua": dates,
            "Track": history["TrackName"],
            "Album": history["AlbumTitle"],
            "Nghệ sĩ": history["Artist"],
            "Thể loại": history["Genre"],
        })
        self.btnHistory.setText(f"Xem lịch sử mua ({len(self.historyRows)} dòng)")
        self.btnHistory.setEnabled(True)
        drawGenreChart(self.canvas, history["Genre"].value_counts())

    def openHistoryDialog(self):
        dialog = HistoryDialog(self.historyRows, f"Lịch sử mua · {self.cbCustomer.currentText()}", self.window)
        dialog.exec()
