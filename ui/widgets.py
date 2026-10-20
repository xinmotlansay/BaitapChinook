from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QComboBox


class CheckComboBox(QComboBox):
    """Ô xổ xuống có checkbox: chọn nhiều mục, popup không đóng sau mỗi lần bấm."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModel(QStandardItemModel(self))
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setPlaceholderText("Chọn thể loại...")
        self.view().pressed.connect(self._toggleItem)

    def addCheckItem(self, text):
        item = QStandardItem(text)
        item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        item.setCheckState(Qt.CheckState.Unchecked)
        self.model().appendRow(item)
        self.setCurrentIndex(-1)
        self._updateText()

    def checkedItems(self):
        model = self.model()
        return [
            model.item(i).text()
            for i in range(model.rowCount())
            if model.item(i).checkState() == Qt.CheckState.Checked
        ]

    def setAllChecked(self, checked):
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        model = self.model()
        for i in range(model.rowCount()):
            model.item(i).setCheckState(state)
        self._updateText()

    def hidePopup(self):
        # Bấm vào mục trong danh sách thì giữ popup mở; chỉ đóng khi bấm ra ngoài
        if self.view().underMouse():
            return
        super().hidePopup()

    def _toggleItem(self, index):
        item = self.model().itemFromIndex(index)
        new_state = Qt.CheckState.Unchecked if item.checkState() == Qt.CheckState.Checked else Qt.CheckState.Checked
        item.setCheckState(new_state)
        self._updateText()

    def _updateText(self):
        self.lineEdit().setText(", ".join(self.checkedItems()))
