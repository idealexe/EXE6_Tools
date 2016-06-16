#!/usr/bin/python
# coding: utf-8

'''
    EXE6_TextEditor by ideal.exe

    ※開発中のプログラムなので危険です。必ずデータのバックアップを取った状態で使用してください。

    開発環境はWindows10 + Python2.7.11 + PyQt4
    現在対応しているデータは日本語版グレイガ，ファルザーです
    >python EXE6TextEditor.py でGUIが開きます
    File メニューから対応しているROMデータを開きます
    データの先頭アドレスと文字列データが表示されます
    テキストボックス内の文字列を書き換えてWriteボタンを押すとメモリ上のROMデータを書き換えます（元のファイルに影響はありません）
    ※元の文字列に上書きするので容量を超えた書き込みは出来ません。元の容量より少ない場合は左を\x00で埋めます
    Saveボタンを押すと保存メニューが開き、書き換えたデータをファイルに保存できます

'''

import re
import os
import sys
import gettext
from PyQt4 import QtGui
from PyQt4 import QtCore
_ = gettext.gettext # 後の翻訳用

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
        # 終了
        exitAction = QtGui.QAction( _("&Exit"), self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip( _("Exit Application") )
        exitAction.triggered.connect( QtGui.qApp.quit )

        # ファイルを開く
        openAction = QtGui.QAction( _("&Open EXE6 File"), self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip( _("Open GBA File") )
        openAction.triggered.connect( self.openFile )

        # ステータスバー
        statusBar = self.statusBar()
        statusBar.showMessage( _("ファイルを選択してください") )

        # メニューバー
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu( _('&File') )
        fileMenu.addAction(openAction)
        fileMenu.addAction(exitAction)

        self.widget = QtGui.QWidget()
        self.monoFont = QtGui.QFont("MS Gothic")

        self.modeLabel = QtGui.QLabel(self)
        self.modeLabel.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignRight)   # 縦：中央，横：右寄せ
        self.modeLabel.setText( _("編集するデータ") )

        self.modeComb = QtGui.QComboBox(self)   # モード選択用コンボボックス
        self.modeComb.activated.connect(self.modeActivated)

        self.itemList = QtGui.QListWidget(self) # 要素を表示するリスト
        self.itemList.currentRowChanged.connect(self.itemActivated) # クリックされた時に実行する関数

        self.text = QtGui.QTextEdit(self)   # 文字列データを表示するテキストボックス
        #self.text.setFontPointSize(14)
        self.text.setFontFamily("MS Gothic")

        self.btnWrite = QtGui.QPushButton( _("Write"), self)  # テキストを書き込むボタン
        self.btnWrite.clicked.connect(self.writeText)   # ボタンを押したときに実行する関数を指定

        self.capacityLabel = QtGui.QLabel(self) # 書き込める容量を表示するラベル
        self.capacityLabel.setText("")

        self.saveBtn = QtGui.QPushButton( _("Save"), self)  # 保存ボタン
        self.saveBtn.clicked.connect(self.saveFile)

        modeHbox = QtGui.QHBoxLayout()
        modeHbox.addWidget(self.modeLabel)
        modeHbox.addWidget(self.modeComb)

        viewHbox = QtGui.QHBoxLayout()
        viewHbox.addWidget(self.itemList)
        viewHbox.addWidget(self.text)

        btnHbox = QtGui.QHBoxLayout()
        btnHbox.addWidget(self.btnWrite)
        btnHbox.addWidget(self.saveBtn)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(modeHbox)
        vbox.addLayout(viewHbox)
        vbox.addWidget(self.capacityLabel)
        vbox.addLayout(btnHbox)

        self.widget.setLayout(vbox)
        self.setCentralWidget(self.widget)
        self.resize(400, 400)
        self.setWindowTitle( _("EXE6 Text Editor") )
        self.show()

    def openFile(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, _("Open EXE6 File"), os.path.expanduser('~'))   # ファイル名がQString型で返される
        with open( unicode(filename), 'rb') as romFile: # Unicodeにエンコードしないとファイル名に2バイト文字があるときに死ぬ
            self.romData = romFile.read()

            # バージョンの判定（使用する辞書を選択するため）
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
            self.currentMode = 0    # モードの初期化
            self.currentItem = 0

            self.dumpListData(self.romData, EXE6_Addr[0][1], EXE6_Addr[0][2])

    # データからリストを作成（\xE6を区切り文字として使う）
    def dumpListData(self, romData, startAddr, endAddr):
        #print "<dumpListData>"
        startAddr = int(startAddr, 16)  # 読み取り開始位置
        endAddr = int(endAddr, 16)  # 読み取り終了位置
        readPos = startAddr
        self.dataList = []  # リストの初期化
        self.itemList.clear()   # 表示用リストの初期化
        currentData = ""    # データ保持用

        while readPos <= endAddr:
            currentChar = romData[readPos]
            if currentChar != "\xE6":   # 文字列の終端でなければ
                currentData += currentChar
            else:
                if self.currentMode != 1:   # チップ説明文モード以外
                    capacity = readPos - startAddr # 読み込み終了位置から読み込み開始位置を引けばデータ容量
                    #data = [hex(startAddr), currentData, capacity]    # 先頭アドレス，データ文字列，データ容量
                    item = QtGui.QListWidgetItem( self.encodeByEXE6Dict(currentData) )  # 一覧に追加する文字列
                else:   # チップ説明文モード
                    if currentData[0:11] == "\xE8\x07\x01\x01\xE8\x06\x01\x01\xF1\x00\x00": # 一般的なチップなら
                        startAddr += 11 # 実際の文字列の先頭を開始位置にする（書き込むときのため）
                        currentData = currentData[11:-2]    # 後ろの制御文字もカット
                        capacity = readPos - startAddr -2
                    else:
                        capacity = readPos - startAddr # 読み込み終了位置から読み込み開始位置を引けばデータ容量
                    item = QtGui.QListWidgetItem( hex(startAddr) )  # 一覧に追加する先頭アドレス

                item.setFont(self.monoFont)
                self.itemList.addItem(item)
                data = [hex(startAddr), currentData, capacity]    # 先頭アドレス，データ文字列，データ容量
                self.dataList.append(data)
                startAddr = readPos + 1
                currentData = ""

            readPos += 1

        self.itemList.setCurrentRow(self.currentItem)   # 選択位置を保持する

    # リスト内のアイテムがアクティブになったとき実行
    def itemActivated(self, item):    # 第二引数には現在のリストのインデックスが渡される
        #print "<itemActivated>"
        if item != -1:  # リストから選択が外れると-1を返すのでそのときは処理を行わない（保存ボタンなどを押す時のため）
            self.currentItem = item # 現在のアイテムを記憶
            #print self.currentItem

            currentData = self.dataList[self.currentItem]
            txt = currentData[1]
            txt = self.encodeByEXE6Dict(txt)   # 対応するデータをエンコード
            self.text.setText(txt)  # テキストボックスに表示
            self.capacityLabel.setText( "書き込み可能容量: " + str(currentData[2]) + " バイト")
        else:
            pass

    # 書き込みボタンが押されたとき実行
    def writeText(self):
        #print "<writeText>"
        currentData = self.dataList[self.currentItem]
        writeAddr = int(currentData[0], 16)    # 書き込み開始位置
        capacity = currentData[2]  # 書き込み可能容量
        qStr = self.text.toPlainText()  # Python2.xだとQStringという型でデータが返される
        uStr = unicode(qStr)  # 一旦QStringからUnicode文字列に変換しないとダメ（めんどくさい）
        uStr = uStr.replace("\n","")    # 改行文字も取り除く
        #print isinstance(sStr, unicode)
        bStr = self.decodeByEXE6Dict(uStr)  # バイナリ文字列

        if len(bStr) <= capacity: # 新しい文字列データが書き込み可能なサイズなら
            while len(bStr) < capacity: # 文字数が足りない場合は■で埋める
                bStr = "\x80" + bStr

            self.romData = self.romData[0:writeAddr] + bStr + self.romData[writeAddr + capacity:]    # 文字列は上書きできないので切り貼りする
            self.modeActivated(self.currentMode)    # データのリロード
            print u"書き込み成功"
        else:   # 容量オーバー
            print u"書き込み可能な容量を超えています"

    # コンボボックスからモードを変更する処理
    def modeActivated(self, mode):
        #print "<modeActivated>"
        self.currentMode = mode
        self.dumpListData(self.romData, EXE6_Addr[mode][1], EXE6_Addr[mode][2])

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
            elif string[readPos] == "\xE9":
                result += CP_EXE6_1[ string[readPos] ] + "\n"   # 辞書の方に改行を入れると一致検索が面倒
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

    def saveFile(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, _("Save EXE6 File"), os.path.expanduser('~'))
        try:
            with open( unicode(filename), 'wb') as romFile:
                romFile.write(self.romData)
                print u"ファイルを保存しました"
        except:
            print u"ファイルの保存をキャンセルしました"


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
