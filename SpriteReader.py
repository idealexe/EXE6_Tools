#!/usr/bin/python
# coding: utf-8

'''
    EXE6 Sprite Reader by ideal.exe

'''

import binascii
import gettext
import os
import re
import sys
import struct
import numpy as np
from PyQt4 import QtGui
from PyQt4 import QtCore
from PIL import Image
from PIL.ImageQt import ImageQt
_ = gettext.gettext # 後の翻訳用

# 辞書のインポート
import EXE6Dict
CP_EXE6_1 = EXE6Dict.CP_EXE6_1
CP_EXE6_2 = EXE6Dict.CP_EXE6_2
CP_EXE6_1_inv = EXE6Dict.CP_EXE6_1_inv
CP_EXE6_2_inv = EXE6Dict.CP_EXE6_2_inv

# フラグと形状の対応を取る辞書[size+shape]:[x,y]
# キーにリストが使えないのでこんなことに・・・
objDim = {
"0000":[8,8],
"0001":[16,8],
"0010":[8,16],
"0100":[16,16],
"0101":[32,8],
"0110":[8,32],
"1000":[32,32],
"1001":[32,16],
"1010":[16,32],
"1100":[64,64],
"1101":[64,32],
"1110":[32,64]
}

class SpriteViewer(QtGui.QMainWindow):
    def __init__(self):
        super(SpriteViewer, self).__init__()
        self.setGUI()

    '''
        GUIの初期化

    '''
    def setGUI(self):
        self.setWindowTitle( _("EXE6 Sprite Viewer") )
        self.resize(800, 450)

        # メニューバー
        menuBar = self.menuBar()
        menuBar.setNativeMenuBar(False) # OS XでもWindowsと同じメニューバー形式にする
        # ファイルメニュー
        fileMenu = menuBar.addMenu( _('&ファイル') )
        # ヘルプメニュー
        helpMenu = menuBar.addMenu( _('&ヘルプ') )

        # ステータスバー
        statusBar = self.statusBar()
        #statusBar.showMessage( _("ファイルを選択してください") )

        # ファイルを開く
        openAction = QtGui.QAction( _("&ファイルを開く"), self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip( _("ファイルを開く") )
        openAction.triggered.connect( self.openFile )
        fileMenu.addAction(openAction)

        # 終了
        exitAction = QtGui.QAction( _("&終了"), self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip( _("アプリケーションを終了する") )
        exitAction.triggered.connect( QtGui.qApp.quit )
        fileMenu.addAction(exitAction)

        # ウィジェット
        self.widget = QtGui.QWidget()
        self.setCentralWidget(self.widget)

        # レイアウト
        mainHbox = QtGui.QHBoxLayout()
        self.widget.setLayout(mainHbox)

        # スプライトリスト
        spriteVbox = QtGui.QVBoxLayout()
        mainHbox.addLayout(spriteVbox)

        self.spriteLabel = QtGui.QLabel(self)
        self.spriteLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)   # 横：左寄せ，縦：中央
        self.spriteLabel.setText( _("スプライトリスト") )
        spriteVbox.addWidget(self.spriteLabel)

        self.guiSpriteList = QtGui.QListWidget(self) # スプライトのリスト
        self.guiSpriteList.setMaximumWidth(120)    # 横幅の最大値
        self.guiSpriteList.currentRowChanged.connect(self.guiSpriteItemActivated) # クリックされた時に実行する関数
        spriteVbox.addWidget(self.guiSpriteList)

        # グラフィック
        viewVbox = QtGui.QVBoxLayout()
        mainHbox.addLayout(viewVbox)

        viewLabel = QtGui.QLabel(self)
        viewLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)   # 横：左寄せ，縦：中央
        viewLabel.setText( _("スプライトビュー") )
        viewVbox.addWidget(viewLabel)

        # スプライトを表示するためのビュー
        graphicsView = QtGui.QGraphicsView()    # シーンを表示するためのビュー
        graphicsView.setCacheMode( QtGui.QGraphicsView.CacheBackground )
        graphicsView.setBackgroundBrush( QtGui.QBrush(QtCore.Qt.lightGray, QtCore.Qt.CrossPattern) ) # ビュー背景の設定
        self.graphicsScene = QtGui.QGraphicsScene() # スプライトを描画するためのシーン
        self.graphicsScene.setSceneRect(-120,-80,240,160)    # gbaの画面を模したシーン（ ビューの中心が(0,0)になる ）
        graphicsView.setScene(self.graphicsScene)
        viewVbox.addWidget(graphicsView)

        # アニメーションリスト
        animVbox = QtGui.QVBoxLayout()
        mainHbox.addLayout(animVbox)

        self.animLabel = QtGui.QLabel(self)
        self.animLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)   # 横：左寄せ，縦：中央
        self.animLabel.setText( _("アニメーションリスト") )
        animVbox.addWidget(self.animLabel)

        self.guiAnimList = QtGui.QListWidget(self) # アニメーションのリスト
        self.guiAnimList.setMaximumWidth(120)    # 横幅の最大値
        self.guiAnimList.currentRowChanged.connect(self.guiAnimItemActivated) # クリックされた時に実行する関数
        animVbox.addWidget(self.guiAnimList)

        self.frameLabel = QtGui.QLabel(self)
        self.frameLabel.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.frameLabel.setText( _("フレームリスト") )
        animVbox.addWidget(self.frameLabel)

        self.guiFrameList = QtGui.QListWidget(self)
        self.guiFrameList.setMaximumWidth(120)
        self.guiFrameList.currentRowChanged.connect(self.guiFrameItemActivated) # クリックされた時に実行する関数
        animVbox.addWidget(self.guiFrameList)

        self.show()


    '''
        GUIでスプライトが選択されたときに行う処理

    '''
    def guiSpriteItemActivated(self, index):
        spriteAddr = self.spriteAddrList[index]
        self.parseSpriteData(self.romData, spriteAddr)
        self.guiAnimItemActivated(0)    # 先頭のアニメーションを選択したことにして表示

    '''
        GUIでアニメーションが選択されたときに行う処理

    '''
    def guiAnimItemActivated(self, index):
        animPtr = self.animPtrList[index]
        print "Selected Animation:\t" + hex(animPtr)
        self.parseAnimData(self.spriteData, animPtr)
        self.parseframeData(self.spriteData, animPtr)   # 先頭フレームのオブジェクトを描画

    '''
        GUIでフレームが選択されたときに行う処理

    '''
    def guiFrameItemActivated(self, index):
        framePtr = self.framePtrList[index]
        self.parseframeData(self.spriteData, framePtr)

    '''
        ファイルを開くときの処理

    '''
    def openFile(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, _("Open EXE6 File"), os.path.expanduser('~'))   # ファイル名がQString型で返される
        try:
            with open( unicode(filename), 'rb') as romFile: # Unicodeにエンコードしないとファイル名に2バイト文字があるときに死ぬ
                self.romData = romFile.read()

        except:
            print( _(u"ファイルの選択をキャンセルしました") )
            return 0    # 0を返して関数を抜ける

        # バージョンの判定（使用する辞書を選択するため）
        romName = self.romData[0xA0:0xAC]
        global EXE6_Addr    # アドレスリストはグローバル変数にする（書き換えないし毎回self.をつけるのが面倒）
        if romName == "ROCKEXE6_GXX":
            print( _(u"グレイガ版としてロードしました") )
            EXE6_Addr = EXE6Dict.GXX_Sprite_Table
        elif romName == "ROCKEXE6_RXX":
            print( _(u"ファルザー版としてロードしました") )
            EXE6_Addr = EXE6Dict.RXX_Addr_List
        else:
            print( _(u"ROMタイトルが識別出来ませんでした") )
            EXE6_Addr = EXE6Dict.GXX_Addr_List # 一応グレイガ版の辞書に設定する

        self.extractSpriteAddr(self.romData)

    '''
        スプライトのアドレスを抽出する

    '''
    def extractSpriteAddr(self, romData):
        self.spriteAddrList = []    # スプライトの先頭アドレスを保持するリスト
        self.guiSpriteList.clear() # スプライトリストの初期化

        readPos = EXE6_Addr["startAddr"]
        while readPos <= EXE6_Addr["endAddr"]:
            spriteAddr = romData[readPos:readPos+4]
            # ポインタの最下位バイトはメモリ上の位置を表す08なのでROM内の位置に変換するために00にする
            # 88の場合もある模様，圧縮データを表してるっぽい？
            if spriteAddr[3] == "\x08":
                spriteAddr = spriteAddr[:3] + "\x00"
                spriteAddr = struct.unpack("<L", spriteAddr)[0]

                self.spriteAddrList.append(spriteAddr)
                spriteItem = QtGui.QListWidgetItem( hex(spriteAddr) )    # GUIのスプライトリストに追加するアイテムの生成
                self.guiSpriteList.addItem(spriteItem) # スプライトリストへ追加

            readPos += 4

    '''
        ROMデータから指定された位置にあるスプライトの情報を取り出す
        スプライトリストでアイテムが選択されたら実行する形を想定

    '''
    def parseSpriteData(self, romData, spriteAddr):
        startAddr = spriteAddr
        endAddr = startAddr + 0x100000  # スプライトの容量は得られないのでとりあえず設定
        readPos = startAddr
        #print "Sprite Address:\t" + hex(startAddr) + "\n"

        # 使う部分だけ切り出し
        spriteHeader = romData[startAddr:startAddr+4]   # 初めの４バイトがヘッダ情報
        self.spriteData = romData[startAddr+4:endAddr]   # それ以降がスプライトの内容（ポインタもこのデータの先頭を00としている）
        self.gbaAddrOffset = 0x08000000 + startAddr + 4    # データのメモリ上での位置を表示するとき用のオフセット

        '''
        # ヘッダ情報の表示
        header = struct.unpack("BBBB", spriteHeader)
        print "[header]"
        print "Random: " + hex(header[0])
        print "Const1: " + hex(header[1])
        print "Const2: " + hex(header[2])
        print "Number of Animations: " + str(header[3])
        print "\n"
        '''

        readPos = 0 # スプライトデータの先頭から読み込む
        # ポインタ領域の長さは最初のポインタ-4（最初のポインタからそのポインタが示すアニメーションデータの開始アドレスまでがポインタ領域になる）
        # ↑普通に最初のポインタと同じ値になると思う
        #print "[Animation Pointers]"
        animDataStart = self.spriteData[readPos:readPos+4]
        animDataStart = readPos + struct.unpack("<L", animDataStart)[0]

        # アニメーションポインタのリスト生成
        self.animPtrList = []
        self.guiAnimList.clear()   # 表示用リストの初期化
        while readPos < animDataStart:
            animPtr = self.spriteData[readPos:readPos+4] # ポインタは4バイト
            readPos += 4

            animPtr = struct.unpack("<L", animPtr)[0]   # リトルエンディアンのunsigned longとして読み込む
            self.animPtrList.append(animPtr)
            animItem = QtGui.QListWidgetItem( hex(animPtr) )    # GUIのアニメーションリストに追加するアイテムの生成
            self.guiAnimList.addItem(animItem) # アニメーションリストへ追加


    '''
        指定されたアニメーションデータを読み込んで処理する
        GUIのアニメーションリストで選択されたアニメーションに対して実行する
        アニメーションデータは20バイトのデータでアニメーションの1フレームを管理する
        1つのアニメーションのフレーム数は事前に与えられず，アニメーションデータが持つ再生タイプに基づいて逐次的にロードする模様

    '''
    def parseAnimData(self, spriteData, animPtr):
        self.graphicsScene.clear()   # 描画シーンのクリア
        self.guiFrameList.clear()   # フレームリストのクリア
        frameCount = 0
        self.framePtrList = []
        while True: # do while文がないので代わりに無限ループ＋breakを使う
            frameData = spriteData[animPtr:animPtr+20]
            self.framePtrList.append(animPtr)
            frameItem = QtGui.QListWidgetItem( hex(animPtr) )    # GUIのフレームリストに追加するアイテムの生成
            self.guiFrameList.addItem(frameItem) # フレームリストへ追加

            animPtr += 20
            frameCount += 1

            if frameData[-2:] in ["\x80\x00","\xC0\x00"]: # 終端フレームならループを終了
                break

    '''
        入力：スプライトのデータとアニメーションデータの開始位置
        処理：20バイトのアニメーションデータを読み取って情報を取り出す
        出力：アニメーションデータの情報

    '''
    def parseframeData(self, spriteData, animPtr):
        self.graphicsScene.clear()  # 描画シーンのクリア
        #print( "Animation Data Address:\t" + hex(animPtr) )    # スプライトファイル内でのアドレス
        print( "Frame Data Address:\t" + hex(animPtr + self.gbaAddrOffset) ) # メモリ上のアドレス
        animData = spriteData[animPtr:animPtr+20]   # 1フレーム分ロード
        animData = struct.unpack("<LLLLHH", animData)   # データ構造に基づいて分解
        '''
            20バイトで1フレーム
            4バイト：画像サイズがあるアドレスへのポインタ
            4バイト：パレットサイズがあるアドレスへのポインタ
            4バイト：OAMデータのポインタがあるアドレスへのポインタ
            4バイト：未使用データへのポインタ（？）
            2バイト：フレーム遅延数
            2バイト：再生タイプ

        '''
        graphSizePtr = animData[0]
        print( "Graphics Size Address:\t" + hex(graphSizePtr + self.gbaAddrOffset) )
        # 画像容量の読み取り
        graphSize = spriteData[graphSizePtr:graphSizePtr+4]
        graphSize = struct.unpack("<L", graphSize)[0]
        print( "Graphics Size:\t" + hex(graphSize) )

        # 画像データの読み込み
        readPos = graphSizePtr + 4  # ４バイトのサイズ情報の後に画像データが続く
        graphData = spriteData[readPos:readPos+graphSize]   # 画像のロード

        palSizePtr = animData[1]
        print( "Palette Size Address:\t" + hex(palSizePtr + self.gbaAddrOffset) )

        ptrToOAMptr = animData[3]
        print( "Address of OAM Data Pointer:\t" + hex(ptrToOAMptr + self.gbaAddrOffset) )
        oamDataPtr = spriteData[ ptrToOAMptr:ptrToOAMptr+4 ]
        oamDataPtr = struct.unpack("<L", oamDataPtr)[0]
        print( "OAM Data Pointer:\t" + hex(oamDataPtr) )
        oamDataStart = ptrToOAMptr + oamDataPtr
        readPos = oamDataStart

        '''
            OAMの処理
            OAMデータは5バイトで1セット
            FF FF FF FF FF で終端を表す

        '''
        oamCount = 0
        while spriteData[readPos:readPos+5] != "\xFF\xFF\xFF\xFF\xFF":
            print( "\nOAM: " + str(oamCount) )
            oamCount += 1

            oamData = spriteData[readPos:readPos+5]
            readPos += 5
            oamData = struct.unpack("BbbBB", oamData)
            startTile = oamData[0]
            print( "Starting Tile:\t" + str(startTile) )
            posX = oamData[1]
            print( "X:\t" + str(posX) )
            posY = oamData[2]
            print( "Y:\t" + str(posY) )

            flag1 = bin(oamData[3])[2:].zfill(8)    # 2進数にして先頭の0bを取り除いて8桁に0埋め
            '''
                フラグ構造（8bit）
                B B  BBBB   BB
                h v unused size

            '''
            objSize = flag1[-2:]    # 下位2ビット
            hFlip = int( flag1[1], 2 ) # 水平反転フラグ
            vFlip = int( flag1[0], 2 ) # 垂直反転フラグ
            print( "Horizontal Flip: " + str(hFlip) )
            print( "Vertical Flip:\t" + str(vFlip) )
            print("size:\t" + str(objSize) )

            flag2 = bin(oamData[4])[2:].zfill(8)
            objShape = flag2[-2:]
            palIndex = int(flag2[0:4], 2)
            print("shape:\t" + str(objShape) )
            print("")

            # パレットの設定
            self.parsePaletteData(spriteData, palSizePtr, palIndex)

            '''
                フラグとサイズの関係．わかりづらい・・・

                shape:
                    b00: 正方形
                    b01: 長方形（横長）
                    b10: 長方形（縦長）
                    b11: 未使用

                size 0, shape 0: 8x8
                □
                size 0, shape 1: 16x8
                □□
                size 0, shape 2: 8x16
                □
                □
                size 1, shape 0: 16x16
                □□
                □□
                size 1, shape 1: 32x8
                □□□□
                size 1, shape 2: 8x32
                □
                □
                □
                □
                size 2, shape 0: 32x32
                □□□□
                □□□□
                □□□□
                □□□□
                size 2, shape 1: 32x16
                □□□□
                □□□□
                size 2, shape 2: 16x32
                □□
                □□
                □□
                □□
                size 3, shape 0: 64x64
                size 3, shape 1: 64x32
                size 3, shape 2: 32x64
            '''
            sizeX, sizeY = objDim[objSize+objShape]
            self.showOBJ(graphData, startTile, sizeX, sizeY, posX, posY, hFlip, vFlip)

        print "Animation Flame Delay:\t" + str(animData[4]) + " frame"

        animType = animData[5]
        '''
            アニメーションタイプは再生状態を決定する
            0x00:   遅延フレーム分待った後に次フレームを再生（次のアニメーションデータをロード）
            0x80:   アニメーションの終了（最後のフレーム）
            0xC0:   アニメーションのループ（最初のフレームに戻る）
            アニメーションの最後のフレームは0x80か0xC0

        '''
        print "Animation Type:\t" + hex(animType)
        print "\n----------------------------------------\n"


    '''
        バイナリデータからタイルセットに変換する

    '''
    def bin2tilesets(self, imgData):
        imgData = binascii.hexlify(imgData).upper()   # バイナリ値をそのまま文字にしたデータに変換
        imgData = list(imgData) # 1文字ずつのリストに変換（入れ替えのため）

        # ドットの描画順（0x01 0x23 0x45 0x67 -> 10325476）に合わせて入れ替え
        for i in range(0, len(imgData))[0::2]:  # 偶数だけ取り出す（0から+2ずつ）
            imgData[i], imgData[i+1] = imgData[i+1], imgData[i] # これで値を入れ替えられる

        totalSize = len(imgData)    # 全ドット数
        imgArray = []
        # 色情報に変換する
        sys.stdout.write("Loading...")
        readPos = 0
        while readPos < totalSize:
            imgArray.append(glay[imgData[readPos]])
            readPos += 1

            if readPos % 20000 == 0:
                sys.stdout.write(".")
        sys.stdout.write("done\n")

        imgArray = np.array(imgArray)   # ndarrayに変換
        imgArray = imgArray.reshape( (-1, 8, 4) )
        tileNum = width * hight  # 合計タイル数

        # タイルの切り出し
        tile = []  # pythonのリストとして先に宣言する（ndarrayとごっちゃになりやすい）
        for i in range(0, tileNum):
            tile.append(imgArray[i*8:i*8+8, 0:8, :])    # 8x8のタイルを切り出していく


    '''
        OAMを表示する
        入力：スプライトのグラフィック，開始タイル，横サイズ，縦サイズ，水平反転，垂直反転

    '''
    def showOBJ(self, imgData, startTile, width, hight, posX, posY, hFlip, vFlip):
        startAddr = startTile * 32  # 開始タイルから開始アドレスを算出（1タイル8*8px = 32バイト）
        width = width/8 # サイズからタイルの枚数に変換
        hight = hight/8
        imgData = imgData[startAddr:]   # 使う部分を切り出し
        imgData = binascii.hexlify(imgData).upper()   # バイナリ値をそのまま文字列にしたデータに変換
        imgData = list(imgData) # 1文字ずつのリストに変換

        # ドットの描画順（0x01 0x23 0x45 0x67 -> 10325476）に合わせて入れ替え
        for i in range(0, len(imgData))[0::2]:  # 偶数だけ取り出す（0から+2ずつ）
            imgData[i], imgData[i+1] = imgData[i+1], imgData[i] # これで値を入れ替えられる

        totalSize = len(imgData)    # 全ドット数
        imgArray = []
        # 色情報に変換する
        readPos = 0
        while readPos < totalSize:
            currentPixel = int(imgData[readPos], 16)    # 1ドット分読み込み，文字列から数値に変換
            imgArray.append(self.palData[currentPixel])
            readPos += 1

        imgArray = np.array(imgArray)   # ndarrayに変換
        imgArray = imgArray.reshape( (-1, 8, 4) )  # 横8ドットのタイルに並べ替える（-1を設定すると自動で縦の値を算出してくれる）

        tileNum = width * hight  # 合計タイル数

        # タイルの切り出し
        tile = []  # pythonのリストとして先に宣言する（ndarrayとごっちゃになりやすい）
        for i in range(0, tileNum):
            tile.append(imgArray[i*8:i*8+8, 0:8, :])    # 8x8のタイルを切り出していく

        # タイルの並び替え
        h = []  # 水平方向に結合したタイルを格納するリスト
        for i in range(0, hight):
            h.append( np.zeros_like(tile[0]) )    # タイルを詰めるダミー
            for j in range(0, width):
                h[i] = np.hstack((h[i], tile[i*width + j]))
            if i != 0:
                h[0] = np.vstack((h[0], h[i]))
        img = h[0][:, 8:, :]    # ダミー部分を切り取る（ださい）

        dataImg = Image.fromarray( np.uint8(img) )  # 色情報の行列から画像を生成
        if hFlip == 1:
            dataImg = dataImg.transpose(Image.FLIP_LEFT_RIGHT)  # PILの機能で水平反転
            print "H flip!"

        if vFlip == 1:
            dataImg = dataImg.transpose(Image.FLIP_TOP_BOTTOM)
            print "V Flip!"

        qImg = ImageQt(dataImg)
        pixmap = QtGui.QPixmap.fromImage(qImg)
        item = QtGui.QGraphicsPixmapItem(pixmap)
        item.setOffset(posX,posY)
        self.graphicsScene.addItem(item)
        #dataImg.show()

    '''
        パレットデータの読み取り
        入力：スプライトデータ，パレットサイズのアドレス
        処理：スプライトデータからのパレットサイズ読み込み，パレットデータ読み込み，RGBAカラー化

    '''
    def parsePaletteData(self, spriteData, palSizePtr, palIndex):
        # パレットサイズの読み取り
        palSize = spriteData[palSizePtr:palSizePtr+4]
        palSize = struct.unpack("<L", palSize)[0]
        print( "Palette Size:\t" + hex(palSize) )

        readPos = palSizePtr + 4 + palIndex * palSize # パレットサイズ情報の後にパレットデータが続く（インデックス番号によって開始位置をずらす）
        endAddr = readPos + palSize

        self.palData = []    # パレットデータを格納するリスト
        palCount = 0
        while readPos < endAddr:
            color = spriteData[readPos:readPos+2]   # 1色あたり16bit（2バイト）
            color = struct.unpack("<H", color)[0]
            readPos += 2

            binColor = bin(color)[2:].zfill(15) # GBAのオブジェクトは15bitカラー（0BBBBBGGGGGRRRRR）
            binB = int( binColor[0:5], 2 ) * 8  #   文字列化されているので数値に直す（255階調での近似色にするため8倍する）
            binG = int( binColor[5:10], 2 ) * 8
            binR = int( binColor[10:15], 2 ) * 8
            #print "R: " + hex(binR) + "\tG: " + hex(binG) + "\tB: " + hex(binB)
            if palCount == 0:
                self.palData.append( [binR, binG, binB, 0] ) # 最初の色は透過色
            else:
                self.palData.append( [binR, binG, binB, 255] )

            palCount += 1

        #print palData

'''
main

'''
def main():
    app = QtGui.QApplication(sys.argv)

    # 日本語文字コードを正常表示するための設定
    reload(sys) # モジュールをリロードしないと文字コードが変更できない
    sys.setdefaultencoding("utf-8") # コンソールの出力をutf-8に設定
    QtCore.QTextCodec.setCodecForCStrings( QtCore.QTextCodec.codecForName("utf-8") )    # GUIもutf-8に設定

    spriteViewer = SpriteViewer()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
