# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'EXE6Trans.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.verticalLayout_2.addWidget(self.label)
        self.txtEdit = QtWidgets.QPlainTextEdit(self.centralwidget)
        self.txtEdit.setObjectName("txtEdit")
        self.verticalLayout_2.addWidget(self.txtEdit)
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setObjectName("pushButton")
        self.verticalLayout_2.addWidget(self.pushButton)
        self.horizontalLayout_2.addLayout(self.verticalLayout_2)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.binEdit = QtWidgets.QPlainTextEdit(self.centralwidget)
        self.binEdit.setObjectName("binEdit")
        self.verticalLayout.addWidget(self.binEdit)
        self.pushButton_2 = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_2.setObjectName("pushButton_2")
        self.verticalLayout.addWidget(self.pushButton_2)
        self.horizontalLayout_2.addLayout(self.verticalLayout)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 24))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionExit = QtWidgets.QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.menu.addAction(self.actionExit)
        self.menubar.addAction(self.menu.menuAction())

        self.retranslateUi(MainWindow)
        self.actionExit.triggered.connect(MainWindow.close)
        self.pushButton.clicked.connect(MainWindow.txt2bin)
        self.pushButton_2.clicked.connect(MainWindow.bin2txt)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.label.setText(_translate("MainWindow", "テキスト"))
        self.pushButton.setText(_translate("MainWindow", "txt -> bin"))
        self.label_2.setText(_translate("MainWindow", "バイナリ"))
        self.pushButton_2.setText(_translate("MainWindow", "bin -> txt"))
        self.menu.setTitle(_translate("MainWindow", "ファイル"))
        self.actionExit.setText(_translate("MainWindow", "終了"))
        self.actionExit.setShortcut(_translate("MainWindow", "Ctrl+Q"))

