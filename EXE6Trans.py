#!/usr/bin/python
# coding: utf-8

'''
    EXE6 Translater by ideal.exe
'''

import re
import os
import sys
import binascii
from PyQt4 import QtGui
from PyQt4 import QtCore

# 辞書のインポート
import EXE6Dict
CP_EXE6_1 = EXE6Dict.CP_EXE6_1
CP_EXE6_2 = EXE6Dict.CP_EXE6_2
CP_EXE6_1_inv = EXE6Dict.CP_EXE6_1_inv
CP_EXE6_2_inv = EXE6Dict.CP_EXE6_2_inv


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
        binary = self.decodeByEXE6Dict(text)
        binary = binascii.hexlify(binary).upper()
        binary = " ".join( [binary[i:i+2] for i in xrange(0, len(binary), 2)] ) # ２文字ごとにスペースを入れて整形
        self.binEdit.setText(binary)

    def bin2txt(self):
        binary = self.binEdit.toPlainText()
        binary = unicode(binary).translate({ord(" "):None, ord("\n"):None}) # 空白，改行を無視
        binary = binascii.unhexlify(binary)
        text = self.encodeByEXE6Dict(binary)
        self.txtEdit.setText(text)

    # 辞書に基づいてバイナリ->テキスト
    def encodeByEXE6Dict(self, string):
        import EXE6TextDumper
        result = EXE6TextDumper.encodeByEXE6Dict(string)

        return result

    # 辞書に基づいてテキスト->バイナリ
    def decodeByEXE6Dict(self, string):
        result = ""
        readPos = 0

        while readPos < len(string):
            currentChar = string[readPos].encode('utf-8')   # Unicode文字列から1文字取り出してString型に変換

            # 改行などは<改行>などのコマンドとして表示している
            if currentChar == "<":
                readPos += 1
                while string[readPos] != ">":
                    currentChar += string[readPos]
                    readPos += 1
                currentChar += string[readPos]
                result += binascii.unhexlify(currentChar[1:3]) # <F5:顔>のF5だけ取り出して数値に戻す
                readPos += 1
                continue

            # 値は[0037]などのパラメータとして表示している
            if currentChar == "[":
                readPos += 1
                while string[readPos] != "]":
                    currentChar += string[readPos]
                    readPos += 1
                currentChar += string[readPos]
                result += binascii.unhexlify(currentChar[3:-1]) # [0xHHHH]のHHHHだけ取り出して数値に戻す
                readPos += 1
                continue

            if currentChar in CP_EXE6_2_inv:    # 2バイト文字なら
                result += "\xE4" + CP_EXE6_2_inv[currentChar]
            elif currentChar in CP_EXE6_1_inv:  # 1バイト文字なら
                result += CP_EXE6_1_inv[currentChar]
            else:   # 辞書に存在しない文字なら
                result += "\x80"    # ■に置き換え
                print u"辞書に" + currentChar + "と一致する文字がありません"

            readPos += 1

        return result


'''
main

'''

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
