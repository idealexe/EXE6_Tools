#!/usr/bin/python
# coding: utf-8

u''' EXE6 Translater by ideal.exe
'''

import re
import os
import sys
import binascii
from PyQt5 import QtGui, QtCore, QtWidgets

from logging import getLogger,StreamHandler,INFO,DEBUG
logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(INFO)
logger.setLevel(INFO)
logger.addHandler(handler)

# 辞書のインポート
sys.path.append(os.path.join(os.path.dirname(sys.argv[0]), "../common/"))
import EXE6Dict


class Window(QtWidgets.QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.setMyself()

    def setMyself(self):
        exitAction = QtWidgets.QAction(QtGui.QIcon('icon.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip("Exit Application")
        exitAction.triggered.connect(QtWidgets.qApp.quit)

        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(exitAction)

        self.widget = QtWidgets.QWidget()

        # ラベルは表示した後アクセスしないのでself.はつけない
        txtLabel = QtWidgets.QLabel(self)
        txtLabel.setText("テキスト")

        binLabel = QtWidgets.QLabel(self)
        binLabel.setText("バイナリ")

        self.txtEdit = QtWidgets.QTextEdit(self)
        #self.txtEdit.setFontPointSize(14)
        #self.txtEdit.setFontFamily("MS Gothic")

        self.binEdit = QtWidgets.QTextEdit(self)
        #self.binEdit.setFontPointSize(14)
        #self.binEdit.setFontFamily("MS Gothic")

        self.txtBtn = QtWidgets.QPushButton("txt -> bin", self)
        self.txtBtn.clicked.connect(self.txt2bin)   # ボタンを押したときに実行する関数を指定

        self.binBtn = QtWidgets.QPushButton("bin -> txt", self)
        self.binBtn.clicked.connect(self.bin2txt)

        labelHbox = QtWidgets.QHBoxLayout()
        labelHbox.addWidget(txtLabel)
        labelHbox.addWidget(binLabel)

        editHbox = QtWidgets.QHBoxLayout()
        editHbox.addWidget(self.txtEdit)
        editHbox.addWidget(self.binEdit)

        btnHbox = QtWidgets.QHBoxLayout()
        btnHbox.addWidget(self.txtBtn)
        btnHbox.addWidget(self.binBtn)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(labelHbox)
        vbox.addLayout(editHbox)
        vbox.addLayout(btnHbox)

        self.widget.setLayout(vbox)
        self.setCentralWidget(self.widget)
        self.resize(800, 600)
        self.setWindowTitle("EXE6 Translater")
        self.show()

    def txt2bin(self):
        text = self.txtEdit.toPlainText()   # QString型になる
        text = text.translate({ord("\n"):None}) # 改行を無視
        logger.info("元のテキスト：" + text)
        binary = EXE6Dict.decodeByEXE6Dict(text)
        logger.info(binary)
        binary = str(binary.hex()).upper()
        binary = " ".join( [binary[i:i+2] for i in range(0, len(binary), 2)] ) # ２文字ごとにスペースを入れて整形
        self.binEdit.setText(binary)

    def bin2txt(self):
        binary = self.binEdit.toPlainText()
        binary = binary.translate({ord(" "):None, ord("\n"):None}) # 空白，改行を無視
        binary = binascii.unhexlify(binary)
        text = EXE6Dict.encodeByEXE6Dict(binary)
        self.txtEdit.setText(text)


def main():
    app = QtWidgets.QApplication(sys.argv)
    monoFont = QtGui.QFont("MS Gothic", 12) # 等幅フォント
    app.setFont(monoFont)   # 全体のフォントを設定

    window = Window()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
