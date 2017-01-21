#!/usr/bin/python
# coding: utf-8

u''' EXE6 Talk Editor by ideal.exe

    ロックマンエグゼ６の会話データを編集できるプログラム
    編集したデータのサイズに合わせてオフセットテーブルを再構築するので
    元のデータサイズを超えた会話を作成できます
'''

from PyQt4 import QtGui
from PyQt4 import QtCore
import os
import gettext
import struct
import sys
_ = gettext.gettext # 後の翻訳用

import EXE6Dict


class TalkEditor(QtGui.QMainWindow):
    def __init__(self):
        super(TalkEditor, self).__init__()
        self.setGUI()


    def setGUI(self):
        u""" GUIの初期化
        """

        self.setWindowTitle( _("EXE6 Talk Editor") )
        self.setWindowIcon(QtGui.QIcon("icon.png"))
        self.resize(600, 600)

        # メニューバー
        menuBar = self.menuBar()
        menuBar.setNativeMenuBar(False) # OS XでもWindowsと同じメニューバー形式にする
        # ファイルメニュー
        fileMenu = menuBar.addMenu( _('&ファイル') )

        # ステータスバー
        statusBar = self.statusBar()

        # ファイルを開く
        openAction = QtGui.QAction( _("&ファイルを開く"), self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip( _("ファイルを開く") )
        openAction.triggered.connect( self.openFile )
        fileMenu.addAction(openAction)

        # 名前をつけて保存
        saveAction = QtGui.QAction( _("&名前をつけて保存"), self)
        saveAction.setShortcut('Ctrl+S')
        saveAction.setStatusTip( _("ファイルを保存") )
        saveAction.triggered.connect( self.saveFile )
        fileMenu.addAction(saveAction)

        # 終了
        exitAction = QtGui.QAction( _("&終了"), self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip( _("アプリケーションを終了する") )
        exitAction.triggered.connect( QtGui.qApp.quit )
        fileMenu.addAction(exitAction)

        # ウィジェット
        widget = QtGui.QWidget()
        self.setCentralWidget(widget)

        # レイアウト（水平ボックスをメインにする）
        mainHbox = QtGui.QHBoxLayout()
        widget.setLayout(mainHbox)

        # アイテムリスト
        itemVbox = QtGui.QVBoxLayout()
        mainHbox.addLayout(itemVbox)

        itemLabel = QtGui.QLabel(self)
        itemLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)   # 横：左寄せ，縦：中央
        itemLabel.setText( _("アイテム") )
        itemVbox.addWidget(itemLabel)

        # アイテムリストは後でアクセスするのでselfで作成
        self.guiItemList = QtGui.QListWidget(self) # スプライトのリスト
        self.guiItemList.setMinimumWidth(300)    # 横幅の最小値
        self.guiItemList.currentRowChanged.connect(self.guiItemActivated) # クリックされた時に実行する関数
        #self.guiItemList.itemDoubleClicked.connect(self.guiItemItemWClicked)    # ダブルクリックされたときに実行する関数
        itemVbox.addWidget(self.guiItemList)

        # テキスト
        textVbox = QtGui.QVBoxLayout()
        mainHbox.addLayout(textVbox)

        textLabel = QtGui.QLabel(self)
        textLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)   # 横：左寄せ，縦：中央
        textLabel.setText( _("テキスト") )
        textVbox.addWidget(textLabel)

        self.textEdit = QtGui.QTextEdit(self)
        self.textEdit.setMinimumWidth(400)    # 横幅の最小値
        textVbox.addWidget(self.textEdit)

        writeBtn = QtGui.QPushButton( _("書き込む"), self)
        writeBtn.clicked.connect(self.writeText)   # ボタンを押したときに実行する関数を指定
        textVbox.addWidget(writeBtn)

        # ウインドウの表示
        self.show()


    def openFile(self, *args):
        u''' ファイルを開くときの処理
        '''

        if args[0] == False:
            u""" 引数がなければファイルメニューを開く
            """
            filename = QtGui.QFileDialog.getOpenFileName( self, _("Open EXE6 Talk File"), os.path.expanduser('./') )   # ファイル名がQString型で返される
            filename = unicode(filename)    # QStringからUnicodeになおす
        else:
            u""" 引数があるときはそのファイルを開く
            """
            filename = args[0]

        try:
            with open( filename, 'rb' ) as talkFile:
                self.talkData = talkFile.read()

        except:
            print( _(u"ファイルの選択をキャンセルしました") )
            return 0    # 0を返して関数を抜ける

        self.parseTalkData()


    def parseTalkData(self):
        u""" 会話データを解析してGUIのリストにセットする
        """

        if len(self.talkData) == struct.unpack("H", self.talkData[1:3])[0]:
            u""" ヘッダがついているか判定する（偶然一致する可能性も０ではない）
            """
            self.talkData = self.talkData[4:]

        L = EXE6Dict.exeDataUnpack(self.talkData)
        self.guiItemList.clear()
        self.itemList = L

        for i in xrange( len(L) ):
            item = QtGui.QListWidgetItem( str(i).zfill(3) + ": " + EXE6Dict.encodeByEXE6Dict(L[i]).translate(None, "\n") )
            self.guiItemList.addItem(item)


    def guiItemActivated(self, index):
        u""" GUIでリストアイテムが選択されたときの処理
        """

        #print unicode( EXE6Dict.encodeByEXE6Dict(self.itemList[index]) )

        if index == -1:
            return 0

        text = EXE6Dict.encodeByEXE6Dict(self.itemList[index])
        self.textEdit.setText(text)
        self.serectedItem = index
        print( "Serected Item: " + str(self.serectedItem) )


    def writeText(self):
        u""" 書き込みボタンが押されたときの処理
        """

        text = self.textEdit.toPlainText()   # QString型になる
        text = unicode(text)    # Unicode型に変換
        text = text.translate({ord("\n"):None}) # 改行を無視
        binary = EXE6Dict.decodeByEXE6Dict(text)
        self.itemList[self.serectedItem] = binary
        self.talkData = EXE6Dict.exeDataPack(self.itemList)
        self.parseTalkData() # リロード
        print("Write!")


    def saveFile(self):
        u""" ファイルを保存するときの処理
        """

        filename = QtGui.QFileDialog.getSaveFileName(self, _("Save EXE6 Talk File"), os.path.expanduser('./'))
        try:
            with open( unicode(filename), 'wb') as talkFile:
                talkFile.write(self.talkData)
                print u"ファイルを保存しました"
        except:
            print u"ファイルの保存をキャンセルしました"


def main():
    app = QtGui.QApplication(sys.argv)
    monoFont = QtGui.QFont("MS Gothic", 10) # 等幅フォント
    app.setFont(monoFont)   # 全体のフォントを設定

    # 日本語文字コードを正常表示するための設定
    reload(sys) # モジュールをリロードしないと文字コードが変更できない
    sys.setdefaultencoding("utf-8") # コンソールの出力をutf-8に設定
    QtCore.QTextCodec.setCodecForCStrings( QtCore.QTextCodec.codecForName("utf-8") )    # GUIもutf-8に設定

    talkEditor = TalkEditor()
    # 引数があったら
    if len(sys.argv) >= 2:
        talkEditor.openFile(sys.argv[1])    # 一つ目の引数をファイル名として開く
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
