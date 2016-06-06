# coding:utf-8
'''
    EXE6_EnemyNameEditor by ideal.exe

    ※開発中のプログラムなので危険です。必ずデータのバックアップを取った状態で使用してください。

    開発環境はWindows10 + Python2.7.11 + PyQt4
    現在対応しているデータはグレイガ版のみです
    >python EXE6_EnemyNameEditor.py でGUIが開きます
    File メニューからグレイガ版のROMデータを開きます
    敵の名前とデータの先頭アドレスが表示されます
    テキストボックス内の文字列を書き換えてWriteボタンを押すとメモリ上のROMデータを書き換えます（元のファイルに影響はありません）
    Saveボタンを押すと保存メニューが開き、書き換えたデータをファイルに保存できます
'''

import re
import os
import sys
from PyQt4 import QtGui
from PyQt4 import QtCore

# ロックマンエグゼ6用文字コード対応表（http://www65.atwiki.jp/mmnbhack/pages/17.html）を少し改変
# E4は2バイト文字フラグ，E9はテキストの改行，E7はテキストのページ終わり（？）
# 1バイト文字
CP_EXE6_1 = {
"\x00":" ",  "\x01":"０", "\x02":"１", "\x03":"２", "\x04":"３", "\x05":"４", "\x06":"５", "\x07":"６",
"\x08":"７", "\x09":"８", "\x0A":"９", "\x0B":"ウ", "\x0C":"ア", "\x0D":"イ", "\x0E":"オ", "\x0F":"エ",
"\x10":"ケ", "\x11":"コ", "\x12":"カ", "\x13":"ク", "\x14":"キ", "\x15":"セ", "\x16":"サ", "\x17":"ソ",
"\x18":"シ", "\x19":"ス", "\x1A":"テ", "\x1B":"ト", "\x1C":"ツ", "\x1D":"タ", "\x1E":"チ", "\x1F":"ネ",
"\x20":"ノ", "\x21":"ヌ", "\x22":"ナ", "\x23":"ニ", "\x24":"ヒ", "\x25":"ヘ", "\x26":"ホ", "\x27":"ハ",
"\x28":"フ", "\x29":"ミ", "\x2A":"マ", "\x2B":"メ", "\x2C":"ム", "\x2D":"モ", "\x2E":"ヤ", "\x2F":"ヨ",
"\x30":"ユ", "\x31":"ロ", "\x32":"ル", "\x33":"リ", "\x34":"レ", "\x35":"ラ", "\x36":"ン", "\x37":"熱",
"\x38":"斗", "\x39":"ワ", "\x3A":"ヲ", "\x3B":"ギ", "\x3C":"ガ", "\x3D":"ゲ", "\x3E":"ゴ", "\x3F":"グ",
"\x40":"ゾ", "\x41":"ジ", "\x42":"ゼ", "\x43":"ズ", "\x44":"ザ", "\x45":"デ", "\x46":"ド", "\x47":"ヅ",
"\x48":"ダ", "\x49":"ヂ", "\x4A":"ベ", "\x4B":"ビ", "\x4C":"ボ", "\x4D":"バ", "\x4E":"ブ", "\x4F":"ピ",
"\x50":"パ", "\x51":"ペ", "\x52":"プ", "\x53":"ポ", "\x54":"ゥ", "\x55":"ァ", "\x56":"ィ", "\x57":"ォ",
"\x58":"ェ", "\x59":"ュ", "\x5A":"ヴ", "\x5B":"ッ", "\x5C":"ョ", "\x5D":"ャ", "\x5E":"Ａ", "\x5F":"Ｂ",
"\x60":"Ｃ", "\x61":"Ｄ", "\x62":"Ｅ", "\x63":"Ｆ", "\x64":"Ｇ", "\x65":"Ｈ", "\x66":"Ｉ", "\x67":"Ｊ",
"\x68":"Ｋ", "\x69":"Ｌ", "\x6A":"Ｍ", "\x6B":"Ｎ", "\x6C":"Ｏ", "\x6D":"Ｐ", "\x6E":"Ｑ", "\x6F":"Ｒ",
"\x70":"Ｓ", "\x71":"Ｔ", "\x72":"Ｕ", "\x73":"Ｖ", "\x74":"Ｗ", "\x75":"Ｘ", "\x76":"Ｙ", "\x77":"Ｚ",
"\x78":"＊", "\x79":"－", "\x7A":"×", "\x7B":"＝", "\x7C":"：", "\x7D":"％", "\x7E":"？", "\x7F":"＋",
"\x80":"■", "\x81":"<ｺｳﾓﾘ>", "\x82":"ー", "\x83":"！", "\x84":"<RV>", "\x85":"<BX>", "\x86":"＆", "\x87":"、",
"\x88":"。", "\x89":"．", "\x8A":"・", "\x8B":"；", "\x8C":"’", "\x8D":"”", "\x8E":"～", "\x8F":"／",
"\x90":"（", "\x91":"）", "\x92":"「", "\x93":"」", "\x94":"<EX>", "\x95":"<SP>", "\x96":"<FZ>", "\x97":"□",
"\x98":"＿", "\x99":"ｚ", "\x9A":"周", "\x9B":"え", "\x9C":"お", "\x9D":"う", "\x9E":"あ", "\x9F":"い",
"\xA0":"け", "\xA1":"く", "\xA2":"き", "\xA3":"こ", "\xA4":"か", "\xA5":"せ", "\xA6":"そ", "\xA7":"す",
"\xA8":"さ", "\xA9":"し", "\xAA":"つ", "\xAB":"と", "\xAC":"て", "\xAD":"た", "\xAE":"ち", "\xAF":"ね",
"\xB0":"の", "\xB1":"な", "\xB2":"ぬ", "\xB3":"に", "\xB4":"へ", "\xB5":"ふ", "\xB6":"ほ", "\xB7":"は",
"\xB8":"ひ", "\xB9":"め", "\xBA":"む", "\xBB":"み", "\xBC":"も", "\xBD":"ま", "\xBE":"ゆ", "\xBF":"よ",
"\xC0":"や", "\xC1":"る", "\xC2":"ら", "\xC3":"り", "\xC4":"ろ", "\xC5":"れ", "\xC6":"究", "\xC7":"ん",
"\xC8":"を", "\xC9":"わ", "\xCA":"研", "\xCB":"げ", "\xCC":"ぐ", "\xCD":"ご", "\xCE":"が", "\xCF":"ぎ",
"\xD0":"ぜ", "\xD1":"ず", "\xD2":"じ", "\xD3":"ぞ", "\xD4":"ざ", "\xD5":"で", "\xD6":"ど", "\xD7":"づ",
"\xD8":"だ", "\xD9":"ぢ", "\xDA":"べ", "\xDB":"ば", "\xDC":"び", "\xDD":"ぼ", "\xDE":"ぶ", "\xDF":"ぽ",
"\xE0":"ぷ", "\xE1":"ぴ", "\xE2":"ぺ", "\xE3":"ぱ", "\xE4":"xE4",    "\xE5":"xE5",    "\xE6":"<close>\n",    "\xE7":"<end>\n",
"\xE8":"<テキスト>",    "\xE9":"<改行>\n",    "\xEA":"xEA",    "\xEB":"xEB",    "\xEC":"xEC",    "\xED":"xED",    "\xEE":"xEE",    "\xEF":"xEF",
"\xF0":"<ch_speaker>",    "\xF1":"xF1",    "\xF2":"<update>\n",    "\xF3":"xF3",    "\xF4":"xF4",    "\xF5":"<open>",    "\xF6":"xF6",    "\xF7":"xF7",
"\xF8":"xF8",    "\xF9":"xF9",    "\xFA":"xFA",    "\xFB":"xFB",    "\xFC":"xFC",    "\xFD":"xFD",    "\xFE":"xFE",    "\xFF":"xFF",
}
# 2バイト文字（\xE4 + \xXX）
CP_EXE6_2 = {
"\x00":"ぅ",    "\x01":"ぁ",    "\x02":"ぃ",    "\x03":"ぉ",    "\x04":"ぇ",    "\x05":"ゅ",    "\x06":"ょ",    "\x07":"っ",
"\x08":"ゃ",    "\x09":"a",    "\x0A":"b",    "\x0B":"c",    "\x0C":"d",    "\x0D":"e",    "\x0E":"f",    "\x0F":"g",
"\x10":"h",    "\x11":"i",    "\x12":"j",    "\x13":"k",    "\x14":"l",    "\x15":"m",    "\x16":"n",    "\x17":"o",
"\x18":"p",    "\x19":"q",    "\x1A":"r",    "\x1B":"s",    "\x1C":"t",    "\x1D":"u",    "\x1E":"v",    "\x1F":"w",
"\x20":"x",    "\x21":"y",    "\x22":"z",    "\x23":"容",    "\x24":"量",    "\x25":"全",    "\x26":"木",    "\x27":"<MB>",
"\x28":"無",    "\x29":"現",    "\x2A":"実",    "\x2B":"○",    "\x2C":"×",    "\x2D":"緑",    "\x2E":"道",    "\x2F":"不",
"\x30":"止",    "\x31":"彩",    "\x32":"起",    "\x33":"父",    "\x34":"集",    "\x35":"院",    "\x36":"一",    "\x37":"二",
"\x38":"三",    "\x39":"四",    "\x3A":"五",    "\x3B":"六",    "\x3C":"七",    "\x3D":"八",    "\x3E":"陽",    "\x3F":"十",
"\x40":"百",    "\x41":"千",    "\x42":"万",    "\x43":"脳",    "\x44":"上",    "\x45":"下",    "\x46":"左",    "\x47":"右",
"\x48":"手",    "\x49":"来",    "\x4A":"日",    "\x4B":"目",    "\x4C":"月",    "\x4D":"獣",    "\x4E":"名",    "\x4F":"人",
"\x50":"入",    "\x51":"出",    "\x52":"山",    "\x53":"口",    "\x54":"光",    "\x55":"電",    "\x56":"気",    "\x57":"綾",
"\x58":"科",    "\x59":"次",    "\x5A":"名",    "\x5B":"前",    "\x5C":"学",    "\x5D":"校",    "\x5E":"省",    "\x5F":"祐",
"\x60":"室",    "\x61":"世",    "\x62":"界",    "\x63":"高",    "\x64":"朗",    "\x65":"枚",    "\x66":"野",    "\x67":"悪",
"\x68":"路",    "\x69":"闇",    "\x6A":"大",    "\x6B":"小",    "\x6C":"中",    "\x6D":"自",    "\x6E":"分",    "\x6F":"間",
"\x70":"系",    "\x71":"鼻",    "\x72":"問",    "\x73":"究",    "\x74":"門",    "\x75":"城",    "\x76":"王",    "\x77":"兄",
"\x78":"化",    "\x79":"葉",    "\x7A":"行",    "\x7B":"街",    "\x7C":"屋",    "\x7D":"水",    "\x7E":"見",    "\x7F":"終",
"\x80":"新",    "\x81":"桜",    "\x82":"先",    "\x83":"生",    "\x84":"長",    "\x85":"今",    "\x86":"了",    "\x87":"点",
"\x88":"井",    "\x89":"子",    "\x8A":"言",    "\x8B":"太",    "\x8C":"属",    "\x8D":"風",    "\x8E":"会",    "\x8F":"性",
"\x90":"持",    "\x91":"時",    "\x92":"勝",    "\x93":"赤",    "\x94":"毎",    "\x95":"年",    "\x96":"火",    "\x97":"改",
"\x98":"計",    "\x99":"画",    "\x9A":"職",    "\x9B":"体",    "\x9C":"波",    "\x9D":"回",    "\x9E":"外",    "\x9F":"地",
"\xA0":"員",    "\xA1":"正",    "\xA2":"造",    "\xA3":"値",    "\xA4":"合",    "\xA5":"戦",    "\xA6":"川",    "\xA7":"秋",
"\xA8":"原",    "\xA9":"町",    "\xAA":"晴",    "\xAB":"用",    "\xAC":"金",    "\xAD":"郎",    "\xAE":"作",    "\xAF":"数",
"\xB0":"方",    "\xB1":"社",    "\xB2":"攻",    "\xB3":"撃",    "\xB4":"力",    "\xB5":"同",    "\xB6":"武",    "\xB7":"何",
"\xB8":"発",    "\xB9":"少",    "\xBA":"教",    "\xBB":"以",    "\xBC":"白",    "\xBD":"早",    "\xBE":"暮",    "\xBF":"面",
"\xC0":"組",    "\xC1":"後",    "\xC2":"文",    "\xC3":"字",    "\xC4":"本",    "\xC5":"階",    "\xC6":"明",    "\xC7":"才",
"\xC8":"者",    "\xC9":"向",    "\xCA":"犬",    "\xCB":"々",    "\xCC":"ヶ",    "\xCD":"連",    "\xCE":"射",    "\xCF":"舟",
"\xD0":"戸",    "\xD1":"切",    "\xD2":"土",    "\xD3":"炎",    "\xD4":"伊",    "\xD5":"夫",    "\xD6":"鉄",    "\xD7":"国",
"\xD8":"男",    "\xD9":"天",    "\xDA":"老",    "\xDB":"師",    "\xDC":"xDC",    "\xDD":"xDD",    "\xDE":"xDE",    "\xDF":"xDF",
"\xE0":"xE0",    "\xE1":"xE1",    "\xE2":"xE2",    "\xE3":"xE3",    "\xE4":"xE4",    "\xE5":"xE5",    "\xE6":"xE6",    "\xE7":"xE7",
"\xE8":"xE8",    "\xE9":"xE9",    "\xEA":"xEA",    "\xEB":"xEB",    "\xEC":"xEC",    "\xED":"xED",    "\xEE":"xEE",    "\xEF":"xEF",
"\xF0":"xF0",    "\xF1":"xF1",    "\xF2":"xF2",    "\xF3":"xF3",    "\xF4":"xF4",    "\xF5":"xF5",    "\xF6":"xF6",    "\xF7":"xF7",
"\xF8":"xF8",    "\xF9":"xF9",    "\xFA":"xFA",    "\xFB":"xFB",    "\xFC":"xFC",    "\xFD":"xFD",    "\xFE":"xFE",    "\xFF":"xFF"
}

# 逆引き辞書
CP_EXE6_1_inv = {v:k for k, v in CP_EXE6_1.items()}
CP_EXE6_2_inv = {v:k for k, v in CP_EXE6_2.items()}

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
        self.comb = QtGui.QComboBox(self)   # チップリストを表示するコンボボックス
        #self.comb.activated[str].connect(self.onActivatedstr)
        self.comb.activated.connect(self.onActivated)
        self.btnWrite = QtGui.QPushButton("Write", self)  # テキストを書き込むボタン
        self.btnWrite.clicked.connect(self.writeText)
        self.capacityLabel = QtGui.QLabel(self) # 書き込める容量を表示するラベル
        self.capacityLabel.setText("Capacity: Bytes")
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
        filename = QtGui.QFileDialog.getOpenFileName(self, "Open EXE6 File", os.path.expanduser('~'))
        with open(filename, 'rb') as romFile:
            self.romData = romFile.read()
            self.dumpEnemyName(self.romData)

    def saveFile(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, "Open EXE6 File", os.path.expanduser('~'))
        with open(filename, 'wb') as romFile:
            romFile.write(self.romData)
            print "Save"

    # コンボボックスがアクティブになったとき実行
    def onActivated(self, item):    # 第二引数にはインデックスが渡される
        self.currentItem = item # 現在のアイテムを記憶
        data = self.enemyList[item][1]
        txt = self.encodeByEXE6Dict(data)   # 対応するデータをエンコード
        self.text.setText(txt)  # テキストボックスに表示
        self.capacityLabel.setText( "Capacity: " + str(self.enemyList[item][2]) + " Bytes")

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
            print "write"
        else:   # 容量オーバー
            print "Over Capacity"


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
