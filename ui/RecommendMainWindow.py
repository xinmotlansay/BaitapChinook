# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'RecommendMainWindow.ui'
##
## Created by: Qt User Interface Compiler version 6.11.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QGridLayout, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMainWindow, QPushButton, QSizePolicy, QSpacerItem,
    QSpinBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget)

from ui.widgets import CheckComboBox

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1280, 800)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayoutMain = QVBoxLayout(self.centralwidget)
        self.verticalLayoutMain.setObjectName(u"verticalLayoutMain")
        self.horizontalLayoutTop = QHBoxLayout()
        self.horizontalLayoutTop.setObjectName(u"horizontalLayoutTop")
        self.tabCustomer = QTabWidget(self.centralwidget)
        self.tabCustomer.setObjectName(u"tabCustomer")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabCustomer.sizePolicy().hasHeightForWidth())
        self.tabCustomer.setSizePolicy(sizePolicy)
        self.tabCustomer.setMaximumSize(QSize(16777215, 170))
        self.tabExisting = QWidget()
        self.tabExisting.setObjectName(u"tabExisting")
        self.gridLayoutExisting = QGridLayout(self.tabExisting)
        self.gridLayoutExisting.setObjectName(u"gridLayoutExisting")
        self.lblCustomerTitle = QLabel(self.tabExisting)
        self.lblCustomerTitle.setObjectName(u"lblCustomerTitle")

        self.gridLayoutExisting.addWidget(self.lblCustomerTitle, 0, 0, 1, 1)

        self.lblSearchTitle = QLabel(self.tabExisting)
        self.lblSearchTitle.setObjectName(u"lblSearchTitle")

        self.gridLayoutExisting.addWidget(self.lblSearchTitle, 0, 1, 1, 1)

        self.lblModelTitle = QLabel(self.tabExisting)
        self.lblModelTitle.setObjectName(u"lblModelTitle")

        self.gridLayoutExisting.addWidget(self.lblModelTitle, 0, 2, 1, 1)

        self.cbCustomer = QComboBox(self.tabExisting)
        self.cbCustomer.setObjectName(u"cbCustomer")

        self.gridLayoutExisting.addWidget(self.cbCustomer, 1, 0, 1, 1)

        self.txtSearch = QLineEdit(self.tabExisting)
        self.txtSearch.setObjectName(u"txtSearch")

        self.gridLayoutExisting.addWidget(self.txtSearch, 1, 1, 1, 1)

        self.cbModel = QComboBox(self.tabExisting)
        self.cbModel.setObjectName(u"cbModel")

        self.gridLayoutExisting.addWidget(self.cbModel, 1, 2, 1, 1)

        self.verticalSpacerExisting = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayoutExisting.addItem(self.verticalSpacerExisting, 2, 0, 1, 3)

        self.tabCustomer.addTab(self.tabExisting, "")
        self.tabNew = QWidget()
        self.tabNew.setObjectName(u"tabNew")
        self.horizontalLayoutNew = QHBoxLayout(self.tabNew)
        self.horizontalLayoutNew.setObjectName(u"horizontalLayoutNew")
        self.groupCountry = QGroupBox(self.tabNew)
        self.groupCountry.setObjectName(u"groupCountry")
        self.verticalLayoutCountry = QVBoxLayout(self.groupCountry)
        self.verticalLayoutCountry.setObjectName(u"verticalLayoutCountry")
        self.cbCountry = QComboBox(self.groupCountry)
        self.cbCountry.setObjectName(u"cbCountry")

        self.verticalLayoutCountry.addWidget(self.cbCountry)

        self.lblNewHint = QLabel(self.groupCountry)
        self.lblNewHint.setObjectName(u"lblNewHint")
        self.lblNewHint.setWordWrap(True)

        self.verticalLayoutCountry.addWidget(self.lblNewHint)

        self.verticalSpacerNew = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayoutCountry.addItem(self.verticalSpacerNew)


        self.horizontalLayoutNew.addWidget(self.groupCountry)

        self.groupGenres = QGroupBox(self.tabNew)
        self.groupGenres.setObjectName(u"groupGenres")
        self.verticalLayoutGenres = QVBoxLayout(self.groupGenres)
        self.verticalLayoutGenres.setObjectName(u"verticalLayoutGenres")
        self.cbGenres = CheckComboBox(self.groupGenres)
        self.cbGenres.setObjectName(u"cbGenres")

        self.verticalLayoutGenres.addWidget(self.cbGenres)

        self.horizontalLayoutGenreButtons = QHBoxLayout()
        self.horizontalLayoutGenreButtons.setObjectName(u"horizontalLayoutGenreButtons")
        self.btnSelectAllGenres = QPushButton(self.groupGenres)
        self.btnSelectAllGenres.setObjectName(u"btnSelectAllGenres")

        self.horizontalLayoutGenreButtons.addWidget(self.btnSelectAllGenres)

        self.btnClearGenres = QPushButton(self.groupGenres)
        self.btnClearGenres.setObjectName(u"btnClearGenres")

        self.horizontalLayoutGenreButtons.addWidget(self.btnClearGenres)

        self.horizontalSpacerGenres = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayoutGenreButtons.addItem(self.horizontalSpacerGenres)


        self.verticalLayoutGenres.addLayout(self.horizontalLayoutGenreButtons)

        self.verticalSpacerGenres = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayoutGenres.addItem(self.verticalSpacerGenres)


        self.horizontalLayoutNew.addWidget(self.groupGenres)

        self.tabCustomer.addTab(self.tabNew, "")

        self.horizontalLayoutTop.addWidget(self.tabCustomer)

        self.verticalLayoutButton = QVBoxLayout()
        self.verticalLayoutButton.setObjectName(u"verticalLayoutButton")
        self.lblKTitle = QLabel(self.centralwidget)
        self.lblKTitle.setObjectName(u"lblKTitle")

        self.verticalLayoutButton.addWidget(self.lblKTitle)

        self.spinK = QSpinBox(self.centralwidget)
        self.spinK.setObjectName(u"spinK")
        self.spinK.setMinimum(1)
        self.spinK.setMaximum(20)
        self.spinK.setValue(10)

        self.verticalLayoutButton.addWidget(self.spinK)

        self.btnRecommend = QPushButton(self.centralwidget)
        self.btnRecommend.setObjectName(u"btnRecommend")

        self.verticalLayoutButton.addWidget(self.btnRecommend)

        self.verticalSpacerButton = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayoutButton.addItem(self.verticalSpacerButton)


        self.horizontalLayoutTop.addLayout(self.verticalLayoutButton)


        self.verticalLayoutMain.addLayout(self.horizontalLayoutTop)

        self.verticalLayoutResults = QVBoxLayout()
        self.verticalLayoutResults.setObjectName(u"verticalLayoutResults")
        self.lblRecommendTitle = QLabel(self.centralwidget)
        self.lblRecommendTitle.setObjectName(u"lblRecommendTitle")

        self.verticalLayoutResults.addWidget(self.lblRecommendTitle)

        self.tableRecommend = QTableWidget(self.centralwidget)
        self.tableRecommend.setObjectName(u"tableRecommend")

        self.verticalLayoutResults.addWidget(self.tableRecommend)

        self.horizontalLayoutBottom = QHBoxLayout()
        self.horizontalLayoutBottom.setObjectName(u"horizontalLayoutBottom")
        self.verticalLayoutLeft = QVBoxLayout()
        self.verticalLayoutLeft.setObjectName(u"verticalLayoutLeft")
        self.lblTracksTitle = QLabel(self.centralwidget)
        self.lblTracksTitle.setObjectName(u"lblTracksTitle")

        self.verticalLayoutLeft.addWidget(self.lblTracksTitle)

        self.tableTracks = QTableWidget(self.centralwidget)
        self.tableTracks.setObjectName(u"tableTracks")

        self.verticalLayoutLeft.addWidget(self.tableTracks)


        self.horizontalLayoutBottom.addLayout(self.verticalLayoutLeft)

        self.verticalLayoutRight = QVBoxLayout()
        self.verticalLayoutRight.setObjectName(u"verticalLayoutRight")
        self.btnHistory = QPushButton(self.centralwidget)
        self.btnHistory.setObjectName(u"btnHistory")

        self.verticalLayoutRight.addWidget(self.btnHistory)

        self.lblChartTitle = QLabel(self.centralwidget)
        self.lblChartTitle.setObjectName(u"lblChartTitle")

        self.verticalLayoutRight.addWidget(self.lblChartTitle)

        self.chartHost = QWidget(self.centralwidget)
        self.chartHost.setObjectName(u"chartHost")
        self.chartHost.setMinimumSize(QSize(0, 150))
        self.verticalLayoutChart = QVBoxLayout(self.chartHost)
        self.verticalLayoutChart.setObjectName(u"verticalLayoutChart")

        self.verticalLayoutRight.addWidget(self.chartHost)


        self.horizontalLayoutBottom.addLayout(self.verticalLayoutRight)


        self.verticalLayoutResults.addLayout(self.horizontalLayoutBottom)


        self.verticalLayoutMain.addLayout(self.verticalLayoutResults)

        self.lblStatus = QLabel(self.centralwidget)
        self.lblStatus.setObjectName(u"lblStatus")

        self.verticalLayoutMain.addWidget(self.lblStatus)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        self.tabCustomer.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"G\u1ee3i \u00fd album cho kh\u00e1ch h\u00e0ng", None))
        self.lblCustomerTitle.setText(QCoreApplication.translate("MainWindow", u"Kh\u00e1ch h\u00e0ng", None))
        self.lblSearchTitle.setText(QCoreApplication.translate("MainWindow", u"T\u00ecm ki\u1ebfm", None))
        self.lblModelTitle.setText(QCoreApplication.translate("MainWindow", u"M\u00f4 h\u00ecnh album", None))
        self.txtSearch.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Nh\u1eadp t\u00ean ho\u1eb7c m\u00e3 kh\u00e1ch h\u00e0ng", None))
        self.tabCustomer.setTabText(self.tabCustomer.indexOf(self.tabExisting), QCoreApplication.translate("MainWindow", u"Kh\u00e1ch h\u00e0ng \u0111\u00e3 c\u00f3", None))
        self.groupCountry.setTitle(QCoreApplication.translate("MainWindow", u"Qu\u1ed1c gia", None))
        self.lblNewHint.setText(QCoreApplication.translate("MainWindow", u"G\u1ee3i \u00fd theo \u0111\u1ed9 ph\u1ed5 bi\u1ebfn, kh\u00f4ng c\u00e1 nh\u00e2n h\u00f3a.", None))
        self.groupGenres.setTitle(QCoreApplication.translate("MainWindow", u"Th\u1ec3 lo\u1ea1i y\u00eau th\u00edch (ch\u1ecdn nhi\u1ec1u)", None))
        self.btnSelectAllGenres.setText(QCoreApplication.translate("MainWindow", u"Ch\u1ecdn t\u1ea5t c\u1ea3", None))
        self.btnClearGenres.setText(QCoreApplication.translate("MainWindow", u"X\u00f3a h\u1ebft", None))
        self.tabCustomer.setTabText(self.tabCustomer.indexOf(self.tabNew), QCoreApplication.translate("MainWindow", u"Kh\u00e1ch h\u00e0ng m\u1edbi", None))
        self.lblKTitle.setText(QCoreApplication.translate("MainWindow", u"S\u1ed1 album (K)", None))
        self.btnRecommend.setText(QCoreApplication.translate("MainWindow", u"G\u1ee3i \u00fd", None))
        self.lblRecommendTitle.setText(QCoreApplication.translate("MainWindow", u"Top-K album g\u1ee3i \u00fd", None))
        self.lblTracksTitle.setText(QCoreApplication.translate("MainWindow", u"Track c\u1ee7a album \u0111\u00e3 ch\u1ecdn", None))
        self.btnHistory.setText(QCoreApplication.translate("MainWindow", u"Xem l\u1ecbch s\u1eed mua", None))
        self.lblChartTitle.setText(QCoreApplication.translate("MainWindow", u"Th\u1ec3 lo\u1ea1i \u0111\u00e3 mua", None))
        self.lblStatus.setText("")
    # retranslateUi

