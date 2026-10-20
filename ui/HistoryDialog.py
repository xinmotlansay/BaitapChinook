from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QTableWidget,
    QVBoxLayout,
)

from ui.utils import showDataIntoTableWidget


class HistoryDialog(QDialog):
    """Popup hiển thị toàn bộ lịch sử mua của một khách hàng."""

    def __init__(self, rows, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(900, 600)

        table = QTableWidget()
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        showDataIntoTableWidget(table, rows)

        layout = QVBoxLayout(self)
        layout.addWidget(table)
