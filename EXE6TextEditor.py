#!/usr/bin/python
# coding: utf-8

'''
    EXE6_TextEditor by ideal.exe

    ※開発中のプログラムなので危険です。必ずデータのバックアップを取った状態で使用してください。

    開発環境はWindows10 + Python2.7.11 + PyQt4
    現在対応しているデータは日本語版グレイガ，ファルザーです
    >python EXE6TextEditor.py でGUIが開きます
    File メニューから対応しているROMデータを開きます
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
        statusBar.showMessage("ファイルを選択してください")

        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        fileMenu.addAction(openAction)
        fileMenu.addAction(exitAction)

        self.widget = QtGui.QWidget()

        self.modeLabel = QtGui.QLabel(self)
        self.modeLabel.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignRight)   # 縦：中央，横：右寄せ
        self.modeLabel.setText("編集するデータ")

        self.modeComb = QtGui.QComboBox(self)   # モード選択用コンボボックス
        self.modeComb.activated.connect(self.modeActivated)

        self.comb = QtGui.QComboBox(self)   # リストを表示するコンボボックス
        self.comb.activated.connect(self.onActivated)   # コンボボックス内の要素が選択されたときに実行する関数を指定

        self.text = QtGui.QTextEdit(self)   # 説明文を表示するテキストボックス
        self.text.setFontPointSize(14)
        self.text.setFontFamily("MS Gothic")

        self.btnWrite = QtGui.QPushButton("Write", self)  # テキストを書き込むボタン
        self.btnWrite.clicked.connect(self.writeText)   # ボタンを押したときに実行する関数を指定

        self.addrLabel = QtGui.QLabel(self)
        self.addrLabel.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignRight)   # 縦：中央，横：右寄せ
        self.addrLabel.setText("データの先頭アドレス")

        self.capacityLabel = QtGui.QLabel(self) # 書き込める容量を表示するラベル
        self.capacityLabel.setText("")

        self.saveBtn = QtGui.QPushButton("Save", self)  # 保存ボタン
        self.saveBtn.clicked.connect(self.saveFile)

        modeHbox = QtGui.QHBoxLayout()
        modeHbox.addWidget(self.modeLabel)
        modeHbox.addWidget(self.modeComb)

        addrHbox = QtGui.QHBoxLayout()
        addrHbox.addWidget(self.addrLabel)
        addrHbox.addWidget(self.comb)

        btnHbox = QtGui.QHBoxLayout()
        btnHbox.addWidget(self.btnWrite)
        btnHbox.addWidget(self.saveBtn)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(modeHbox)
        vbox.addLayout(addrHbox)
        vbox.addWidget(self.text)
        vbox.addWidget(self.capacityLabel)
        vbox.addLayout(btnHbox)

        self.widget.setLayout(vbox)
        self.setCentralWidget(self.widget)
        self.resize(800, 450)
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
            # 会話文解析用
            elif string[readPos] == "\xF0" or string[readPos] == "\xF5":
                result += CP_EXE6_1[ string[readPos] ]
                result += CP_EXE6_1[ string[readPos+1] ] + CP_EXE6_1[ string[readPos+2] ] + "\n"
                readPos += 2
            elif string[readPos] == "\xE6":
                result += CP_EXE6_1[ string[readPos] ]
            # 通常の1バイト文字
            else:
                result += CP_EXE6_1[ string[readPos] ]

            readPos += 1
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

            if currentChar in CP_EXE6_2_inv:    # 2バイト文字なら
                result += "\xE4" + CP_EXE6_2_inv[currentChar]
            elif currentChar in CP_EXE6_1_inv:  # 1バイト文字なら
                result += CP_EXE6_1_inv[currentChar]
            else:   # 辞書に存在しない文字なら
                result += "\x80"    # ■に置き換え
                print u"辞書に一致する文字がありません"

            readPos += 1

        return result

    # データからリストを作成（\xE6を区切り文字として使う）
    def dumpListData(self, romData, startAddr, endAddr):
        startAddr = int(startAddr, 16)  # 読み取り開始位置
        endAddr = int(endAddr, 16)  # 読み取り終了位置
        readPos = startAddr
        self.enemyList = []
        currentEnemy = ""
        self.comb.clear()

        while readPos <= endAddr:
            currentChar = romData[readPos]
            if currentChar != "\xE6":   # 文字列の終端でなければ
                currentEnemy += currentChar
            else:
                capacity = readPos - startAddr # 読み込み終了位置から読み込み開始位置を引けばデータ容量
                enemyData = [hex(startAddr), currentEnemy, capacity]    # 先頭アドレス，データ文字列，データ容量
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

            # バージョンの判定
            romName = self.romData[0xA0:0xAC]
            global EXE6_Addr    # アドレスリストをグローバル変数にする（書き換えないし毎回self.をつけるのが面倒）
            if romName == "ROCKEXE6_GXX":
                print u"グレイガ版としてロードしました"
                EXE6_Addr = EXE6Dict.GXX_Addr_List
            elif romName == "ROCKEXE6_RXX":
                print u"ファルザー版としてロードしました"
                EXE6_Addr = EXE6Dict.RXX_Addr_List
            else:
                print u"ROMタイトルが識別出来ませんでした"
                EXE6_Addr = EXE6Dict.GXX_Addr_List # 一応グレイガ版の辞書に設定する

            # コンボボックスにモードを追加
            self.modeComb.clear()   # ROMを二回読み込んだ場合などのためにクリアする
            for item in range( 0, len(EXE6_Addr) ):
                self.modeComb.addItem(EXE6_Addr[item][0])

            self.dumpListData(self.romData, EXE6_Addr[0][1], EXE6_Addr[0][2])

    def saveFile(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, "Save EXE6 File", os.path.expanduser('~'))
        with open( unicode(filename), 'wb') as romFile:
            romFile.write(self.romData)
            print u"ファイルを保存しました"

    # コンボボックスからモードを変更する処理
    def modeActivated(self, mode):
        self.currentMode = mode
        self.dumpListData(self.romData, EXE6_Addr[mode][1], EXE6_Addr[mode][2])

    # コンボボックスがアクティブになったとき実行
    def onActivated(self, item):    # 第二引数にはインデックスが渡される
        self.currentItem = item # 現在のアイテムを記憶
        data = self.enemyList[item][1]
        txt = self.encodeByEXE6Dict(data)   # 対応するデータをエンコード
        self.text.setText(txt)  # テキストボックスに表示
        self.capacityLabel.setText( "書き込み可能容量: " + str(self.enemyList[item][2]) + " バイト")

    # 書き込みボタンが押されたとき実行
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
            self.modeActivated(self.currentMode)    # データのリロード
            print u"書き込み成功"
        else:   # 容量オーバー
            print u"書き込み可能な容量を超えています"


'''
main
'''
def main():
    app = QtGui.QApplication(sys.argv)
    # 日本語文字コードを正常表示するための設定
    QtCore.QTextCodec.setCodecForCStrings( QtCore.QTextCodec.codecForName("utf-8") )
    window = Window()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
