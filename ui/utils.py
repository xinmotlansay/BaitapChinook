import pandas as pd
from PySide6.QtWidgets import QHeaderView, QTableWidgetItem


def relativeBars(values, width=10):
    """Chuỗi thanh ●○ và phần trăm, tương đối trong danh sách: 100% là cao nhất, 0% là thấp nhất."""
    values = [float(v) for v in values]
    if not values:
        return []
    low, high = min(values), max(values)
    span = high - low
    bars = []
    for v in values:
        share = 1.0 if span == 0 else (v - low) / span
        filled = round(share * width)
        bars.append(f"{'●' * filled}{'○' * (width - filled)}  {share * 100:.0f}%")
    return bars


def showDataIntoTableWidget(table, df):
    """Đổ DataFrame vào QTableWidget. Dùng chung cho mọi bảng trên màn hình."""
    table.clearContents()
    table.setRowCount(len(df))
    table.setColumnCount(len(df.columns))
    table.setHorizontalHeaderLabels([str(c) for c in df.columns])

    for r, row in enumerate(df.itertuples(index=False)):
        for c, value in enumerate(row):
            text = "" if pd.isna(value) else str(value)
            table.setItem(r, c, QTableWidgetItem(text))

    table.resizeColumnsToContents()
    table.horizontalHeader().setStretchLastSection(True)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)


def drawGenreChart(canvas, counts):
    """Vẽ biểu đồ cột ngang số lượt mua theo thể loại. counts: pandas Series, index là tên thể loại."""
    figure = canvas.figure
    figure.clear()
    ax = figure.add_subplot(111)

    if counts.empty:
        ax.text(0.5, 0.5, "Chưa có lịch sử mua", ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
    else:
        counts = counts.sort_values()
        ax.barh(counts.index.tolist(), counts.to_numpy(), color="#4C78A8")
        ax.set_xlabel("Số lượt mua")
        ax.tick_params(axis="y", labelsize=8)
        ax.grid(axis="x", alpha=0.3)

    figure.tight_layout()
    canvas.draw()
