#!/usr/bin/python
# coding: utf-8

u''' EXE6 Translater by ideal.exe
'''

import re
import os
import sys
import binascii
from PyQt4 import QtGui
from PyQt4 import QtCore

# 辞書のインポート
import EXE6Dict


class Window(QtGui.QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.setMyself()

    def setMyself(self):
        exitAction = QtGui.QAction(QtGui.QIcon('icon.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip("Exit Application")
        exitAction.triggered.connect(QtGui.qApp.quit)

        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(exitAction)

        self.widget = QtGui.QWidget()

        # ラベルは表示した後アクセスしないのでself.はつけない
        txtLabel = QtGui.QLabel(self)
        txtLabel.setText("テキスト")

        binLabel = QtGui.QLabel(self)
        binLabel.setText("バイナリ")

        self.txtEdit = QtGui.QTextEdit(self)
        #self.txtEdit.setFontPointSize(14)
        #self.txtEdit.setFontFamily("MS Gothic")

        self.binEdit = QtGui.QTextEdit(self)
        #self.binEdit.setFontPointSize(14)
        #self.binEdit.setFontFamily("MS Gothic")

        self.txtBtn = QtGui.QPushButton("txt -> bin", self)
        self.txtBtn.clicked.connect(self.txt2bin)   # ボタンを押したときに実行する関数を指定

        self.binBtn = QtGui.QPushButton("bin -> txt", self)
        self.binBtn.clicked.connect(self.bin2txt)

        labelHbox = QtGui.QHBoxLayout()
        labelHbox.addWidget(txtLabel)
        labelHbox.addWidget(binLabel)

        editHbox = QtGui.QHBoxLayout()
        editHbox.addWidget(self.txtEdit)
        editHbox.addWidget(self.binEdit)

        btnHbox = QtGui.QHBoxLayout()
        btnHbox.addWidget(self.txtBtn)
        btnHbox.addWidget(self.binBtn)

        vbox = QtGui.QVBoxLayout()
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
        text = unicode(text)    # Unicode型に変換
        text = text.translate({ord("\n"):None}) # 改行を無視
        binary = EXE6Dict.decodeByEXE6Dict(text)
        binary = binascii.hexlify(binary).upper()
        binary = " ".join( [binary[i:i+2] for i in xrange(0, len(binary), 2)] ) # ２文字ごとにスペースを入れて整形
        self.binEdit.setText(binary)

    def bin2txt(self):
        binary = self.binEdit.toPlainText()
        binary = unicode(binary).translate({ord(" "):None, ord("\n"):None}) # 空白，改行を無視
        binary = binascii.unhexlify(binary)
        text = EXE6Dict.encodeByEXE6Dict(binary)
        self.txtEdit.setText(text)


def main():
    app = QtGui.QApplication(sys.argv)
    monoFont = QtGui.QFont("MS Gothic", 12) # 等幅フォント
    app.setFont(monoFont)   # 全体のフォントを設定

    # 日本語文字コードを正常表示するための設定
    reload(sys) # モジュールをリロードしないと文字コードが変更できない
    sys.setdefaultencoding("utf-8") # コンソールの出力をutf-8に設定
    QtCore.QTextCodec.setCodecForCStrings( QtCore.QTextCodec.codecForName("utf-8") )

    window = Window()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
