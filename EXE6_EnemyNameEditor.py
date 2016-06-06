#!/usr/bin/python
# coding: utf-8

'''
    EXE6_TextEditor by ideal.exe

    ※開発中のプログラムなので危険です。必ずデータのバックアップを取った状態で使用してください。

    開発環境はWindows10 + Python2.7.11 + PyQt4
    現在対応しているデータはグレイガ版のみです
    >python EXE6_TextEditor.py でGUIが開きます
    File メニューからグレイガ版のROMデータを開きます
    敵の名前とデータの先頭アドレスが表示されます
    テキストボックス内の文字列を書き換えてWriteボタンを押すとメモリ上のROMデータを書き換えます（元のファイルに影響はありません）
    ※元の敵の名前に上書きするので容量を超えた書き込みは出来ません。元の容量より少ない場合は左を\x00で埋めます
    Saveボタンを押すと保存メニューが開き、書き換えたデータをファイルに保存できます
'''

import re
import os
import sys
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

        openAction = QtGui.QAction(QtGui.QIcon('icon.png'), "&Open EXE6 File", self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip("Open GBA File")
        openAction.triggered.connect(self.openFile)

        statusBar = self.statusBar()
        statusBar.showMessage("Choose File")

        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(openAction)
        fileMenu.addAction(exitAction)

        self.widget = QtGui.QWidget()

        self.text = QtGui.QTextEdit(self)   # 説明文を表示するテキストボックス
        self.comb = QtGui.QComboBox(self)   # リストを表示するコンボボックス
        self.comb.activated.connect(self.onActivated)   # コンボボックス内の要素が選択されたときに実行する関数を指定

        self.btnWrite = QtGui.QPushButton("Write", self)  # テキストを書き込むボタン
        self.btnWrite.clicked.connect(self.writeText)   # ボタンを押したときに実行する関数を指定

        self.capacityLabel = QtGui.QLabel(self) # 書き込める容量を表示するラベル
        self.capacityLabel.setText("")

        self.saveBtn = QtGui.QPushButton("Save", self)  # 保存ボタン
        self.saveBtn.clicked.connect(self.saveFile)

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.comb)
        vbox.addWidget(self.text)
        vbox.addWidget(self.capacityLabel)
        vbox.addWidget(self.btnWrite)
        vbox.addWidget(self.saveBtn)

        self.widget.setLayout(vbox)
        self.setCentralWidget(self.widget)
        self.resize(400, 300)
        self.setWindowTitle("EXE6 Text Editor")
        self.show()

    # 辞書に基づいてバイナリ->テキスト
    def encodeByEXE6Dict(self, string):
        result = ""
        readPos = 0

        while readPos < len(string):
            # 2バイトフラグなら
            if string[readPos] == "\xE4":
                readPos += 1  # 次の文字を
                result += CP_EXE6_2[ string[readPos] ] # 2バイト文字として出力
            elif string[readPos] == "\xF0" or string[readPos] == "\xF5":
                result += CP_EXE6_1[ string[readPos] ]
                result += CP_EXE6_1[ string[readPos+1] ] + CP_EXE6_1[ string[readPos+2] ] + "\n"
                readPos += 2
            elif string[readPos] == "\xE6":
                result += CP_EXE6_1[ string[readPos] ]
            else:
                result += CP_EXE6_1[ string[readPos] ]

            readPos += 1
        return result

    # 辞書に基づいてテキスト->バイナリ
    def decodeByEXE6Dict(self, string):
        result = ""
        readPos = 0

        while readPos < len(string):
            currentChar = string[readPos].encode('utf-8')   # Unicode文字列から1文字取り出した後にString型に変換
            # 改行などは<改行>などのコマンドとして表示している
            if currentChar == "<":
                readPos += 1
                while string[readPos] != ">":
                    currentChar += string[readPos]
                    readPos += 1
                readPos += 1
                currentChar += string[readPos]

            if currentChar in CP_EXE6_2_inv:    # 2バイト文字なら
                result += "\xE4" + CP_EXE6_2_inv[currentChar]
            elif currentChar in CP_EXE6_1_inv:  # 1バイト文字なら
                result += CP_EXE6_1_inv[currentChar]
            else:   # 辞書に存在しない文字なら
                result += "\x80"    # ■に置き換え
                print "Key Not Found"

            readPos += 1

        return result

    def dumpEnemyName(self, romData):
        startAddr = int("0x710FFE", 16) # メットールの先頭アドレス
        endAddr = int("0x71163F", 16)
        readPos = startAddr
        self.enemyList = []
        currentEnemy = ""

        while readPos <= endAddr:
            currentChar = romData[readPos]
            if currentChar != "\xE6":   # 文字列の終端でなければ
                currentEnemy += currentChar
            else:
                capacity = readPos - startAddr # 読み込み終了位置から読み込み開始位置を引けばデータ容量
                enemyData = [hex(startAddr), currentEnemy, capacity]    # エネミー名の先頭アドレス，エネミー名，データ容量
                self.enemyList.append(enemyData)
                self.comb.addItem( hex(startAddr) )
                startAddr = readPos + 1
                currentEnemy = ""

            readPos += 1
        self.currentItem = 0
        self.onActivated(self.currentItem)


    def openFile(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, "Open EXE6 File", os.path.expanduser('~'))   # ファイル名がQString型で返される
        with open( unicode(filename), 'rb') as romFile: # Unicodeにエンコードしないとファイル名に2バイト文字があるときに死ぬ
            self.romData = romFile.read()
            self.dumpEnemyName(self.romData)

    def saveFile(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, "Save EXE6 File", os.path.expanduser('~'))
        with open( unicode(filename), 'wb') as romFile:
            romFile.write(self.romData)
            print "Save"

    # コンボボックスがアクティブになったとき実行
    def onActivated(self, item):    # 第二引数にはインデックスが渡される
        self.currentItem = item # 現在のアイテムを記憶
        data = self.enemyList[item][1]
        txt = self.encodeByEXE6Dict(data)   # 対応するデータをエンコード
        self.text.setText(txt)  # テキストボックスに表示
        self.capacityLabel.setText( "書き込み可能容量: " + str(self.enemyList[item][2]) + " バイト")

    def writeText(self):
        currentEnemy = self.enemyList[self.currentItem]
        writeAddr = int(currentEnemy[0], 16)    # 書き込み開始位置
        capacity = currentEnemy[2]  # 書き込み可能容量
        qStr = self.text.toPlainText()  # Python2.xだとQStringという型でデータが返される
        uStr = unicode(qStr)  # 一旦QStringからUnicode文字列に変換しないとダメ（めんどくさい）
        #print isinstance(sStr, unicode)
        bStr = self.decodeByEXE6Dict(uStr)  # バイナリ文字列

        if len(bStr) <= capacity: # 新しい文字列データが書き込み可能なサイズなら
            while len(bStr) < capacity: # 文字数が足りない場合は0埋め（もっとマシな書き方は・・・）
                bStr = "\x00" + bStr

            self.romData = self.romData[0:writeAddr] + bStr + self.romData[writeAddr + capacity:]    # 文字列は上書きできないので切り貼りする
            self.dumpEnemyName(self.romData)    # エネミーリストをリロード
            print u"書き込み成功"
        else:   # 容量オーバー
            print u"書き込み可能な容量を超えています"


'''
main
'''
def main():
    app = QtGui.QApplication(sys.argv)
    # 日本語文字コードを正常表示するための設定
    QtCore.QTextCodec.setCodecForCStrings( QtCore.QTextCodec.codecForName("utf8") )
    window = Window()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
