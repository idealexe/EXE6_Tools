#!/usr/bin/python
# coding: utf-8

u''' EXE6 Translater by ideal.exe
'''

PROGRAM_NAME = "EXE6 Translater  ver1.0  by ideal.exe"

import os
import sys
import binascii
from PyQt5 import QtWidgets

from logging import getLogger,StreamHandler,INFO,DEBUG
logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(INFO)
logger.setLevel(INFO)
logger.addHandler(handler)

import UI_EXE6Trans as designer
# 辞書のインポート
sys.path.append(os.path.join(os.path.dirname(sys.argv[0]), "../common/"))
import EXE6Dict


class Window(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.ui = designer.Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle(PROGRAM_NAME)

    def txt2bin(self):
        text = self.ui.txtEdit.toPlainText()   # QString型になる
        text = text.translate({ord("\n"):None}) # 改行を無視
        logger.debug("元のテキスト：" + text)
        binary = EXE6Dict.decodeByEXE6Dict(text)
        logger.debug(binary)
        binary = str(binary.hex()).upper()
        binary = " ".join( [binary[i:i+2] for i in range(0, len(binary), 2)] ) # ２文字ごとにスペースを入れて整形
        self.ui.binEdit.setPlainText(binary)

    def bin2txt(self):
        binary = self.ui.binEdit.toPlainText()
        binary = binary.translate({ord(" "):None, ord("\n"):None}) # 空白，改行を無視
        binary = binascii.unhexlify(binary)
        text = EXE6Dict.encodeByEXE6Dict(binary)
        self.ui.txtEdit.setPlainText(text)


def main():
    app = QtWidgets.QApplication(sys.argv)

    window = Window()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
