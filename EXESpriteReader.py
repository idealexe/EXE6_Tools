#!/usr/bin/python
# coding: utf-8

u''' EXE6 Sprite Reader by ideal.exe


    データ構造仕様

    palData: パレットデータ辞書のリスト．OAMの生成（彩色）に使用する．
    palData[i] := { "color":[赤, 緑, 青, α], "addr":スプライト内のアドレス }

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

import SpriteDict
import LZ77Util
import UI_EXESpriteReader as designer

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

class SpriteReader(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = designer.Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.graphicsView.scale(2,2) # なぜかQt Designer上で設定できない


    def openFile(self, *args):
        u''' ファイルを開くときの処理
        '''

        if len(args) != 0:
            u""" 引数がある場合はそれをファイル名にする
            """
            filename = args[0]
        else:
            u""" 引数がない場合はファイルを開く
            """
            filename = QtGui.QFileDialog.getOpenFileName( self, _("Open EXE6 File"), os.path.expanduser('./') )   # ファイル名がQString型で返される
            filename = unicode(filename)

        try:
            with open( filename, 'rb' ) as romFile:
                self.romData = romFile.read()
        except:
            print( _(u"ファイルの選択をキャンセルしました") )
            return 0    # 中断

        if self.setDict(self.romData) == -1:
            return 0
        self.extractSpriteAddr(self.romData)
        self.guiSpriteItemActivated(0)  # 1番目のスプライトを自動で選択


    def setDict(self, romData):
        u""" バージョンを判定し使用する辞書をセットする
        """

        romName = self.romData[0xA0:0xAC]
        global EXE_Addr    # アドレスリストはグローバル変数にする（書き換えないし毎回self.をつけるのが面倒なので）
        if romName == "ROCKEXE6_GXX":
            print( _(u"ロックマンエグゼ6 グレイガとしてロードしました") )
            EXE_Addr = SpriteDict.ROCKEXE6_GXX
        elif romName == "ROCKEXE6_RXX":
            print( _(u"ロックマンエグゼ6 ファルザーとしてロードしました") )
            EXE_Addr = SpriteDict.ROCKEXE6_RXX
        elif romName == "ROCKEXE5_TOB":
            print( _(u"ロックマンエグゼ5 チームオブブルースとしてロードしました") )
            EXE_Addr = SpriteDict.ROCKEXE5_TOB
        elif romName == "ROCKEXE5_TOC":
            print( _(u"ロックマンエグゼ5 チームオブカーネルとしてロードしました") )
            EXE_Addr = SpriteDict.ROCKEXE5_TOC
        elif romName == "ROCKEXE4.5RO":
            print( _(u"ロックマンエグゼ4.5としてロードしました") )
            EXE_Addr = SpriteDict.ROCKEXE4_5RO
        else:
            print( _(u"対応していないバージョンです" ) )
            return -1   # error


    def extractSpriteAddr(self, romData):
        u''' スプライトのアドレスを抽出する
        '''

        self.spriteAddrList = []    # スプライトの先頭アドレスと圧縮状態を保持するリスト
        self.ui.spriteList.clear() # スプライトリストの初期化

        readPos = EXE_Addr["startAddr"]
        while readPos <= EXE_Addr["endAddr"]:
            spriteAddr = romData[readPos:readPos+4]
            memByte = struct.unpack("B", spriteAddr[3])[0]

            if memByte in [0x08, 0x88]:
                u""" ポインタの最下位バイトはメモリ上の位置を表す0x08

                    0x88の場合は圧縮データとして扱われる模様
                """

                if memByte == 0x88: # ポインタ先頭が0x88なら圧縮スプライトとして扱う
                    compFlag = 1
                else:
                    compFlag = 0

                spriteAddr = spriteAddr[:3] + "\x00"    # ROM内でのアドレスに直す　例）081D8000 -> 001D8000 (00 80 1D 08 -> 00 80 1D 00)
                spriteAddr = struct.unpack("<L", spriteAddr)[0]
                if spriteAddr in [0x4EA2E4, 0x4EA9DC, 0x506328]:    # 白玉等を除く
                    readPos += 4
                    continue

                self.spriteAddrList.append( {"spriteAddr":spriteAddr, "compFlag":compFlag, "readPos":readPos} )

                spriteAddrStr = ( hex(memByte)[2:].zfill(2) + hex(spriteAddr)[2:].zfill(6) ).upper() + "\t(" + hex(readPos)[2:].zfill(6).upper() + ")\t" + \
                                    unicode( SpriteDict.GXX_Sprite_List[hex(spriteAddr)] )  # GUIのリストに表示する文字列
                spriteItem = QtGui.QListWidgetItem( spriteAddrStr )  # GUIのスプライトリストに追加するアイテムの生成
                self.ui.spriteList.addItem(spriteItem) # GUIスプライトリストへ追加

            readPos += 4


    def guiSpriteItemActivated(self, index):
        u''' GUIでスプライトが選択されたときに行う処理
        '''

        self.graphicsScene = QtGui.QGraphicsScene() # スプライトを描画するためのシーン
        self.graphicsScene.setSceneRect(-120,-80,240,160)    # gbaの画面を模したシーン（ ビューの中心が(0,0)になる ）
        self.ui.graphicsView.setScene(self.graphicsScene)
        #self.ui.spriteList.setCurrentRow(index) # GUI以外から呼び出された時のために選択位置を合わせる
        # ↑この変更もハンドリングされてしまうのでダメ
        spriteAddr = self.spriteAddrList[index]["spriteAddr"]
        print( "Serected Sprite:\t" + hex(spriteAddr) )
        compFlag = self.spriteAddrList[index]["compFlag"]
        self.parseSpriteData(self.romData, spriteAddr, compFlag)
        self.guiAnimItemActivated(0)    # 先頭のアニメーションを選択したことにして表示


    def parseSpriteData(self, romData, spriteAddr, compFlag):
        u''' ROMデータから指定された位置にあるスプライトの情報を取り出す

            スプライトリストでアイテムが選択されたら実行する形を想定
        '''

        if compFlag == 0:   # 非圧縮スプライトなら
            startAddr = spriteAddr
            endAddr = startAddr + 0x100000  # スプライトのサイズは得られないのでとりあえず設定
            readPos = startAddr
            #print "Sprite Address:\t" + hex(startAddr) + "\n"

            # 使う部分だけ切り出し
            spriteHeader = romData[startAddr:startAddr+4]   # 初めの４バイトがヘッダ情報
            self.spriteData = romData[startAddr+4:endAddr]   # それ以降がスプライトの内容

        elif compFlag == 1: # 圧縮スプライトなら
            spriteData = LZ77Util.decompLZ77_10(romData, spriteAddr)[8:]    # ファイルサイズ情報とヘッダー部分を取り除く
            self.spriteData = spriteData

        else:
            return

        readPos = 0 # スプライトデータの先頭から読み込む
        animDataStart = self.spriteData[readPos:readPos+4]
        animDataStart = struct.unpack("<L", animDataStart)[0]

        # アニメーションポインタのリスト生成
        self.animPtrList = []
        self.ui.animList.clear()   # 表示用リストの初期化

        while readPos < animDataStart:
            animPtr = self.spriteData[readPos:readPos+4] # ポインタは4バイト
            readPos += 4

            animPtr = struct.unpack("<L", animPtr)[0]   # リトルエンディアンのunsigned longとして読み込む
            self.animPtrList.append(animPtr)
            animPtrStr = hex(animPtr)[2:].zfill(6).upper() # GUIに表示する文字列
            animItem = QtGui.QListWidgetItem( animPtrStr )    # GUIのアニメーションリストに追加するアイテムの生成
            self.ui.animList.addItem(animItem) # アニメーションリストへ追加


    def guiAnimItemActivated(self, index):
        u''' GUIでアニメーションが選択されたときに行う処理
        '''

        if index == -1: # GUIの選択位置によっては-1が渡されることがある？
            return

        #self.guiAnimList.setCurrentRow(index) # GUI以外から呼び出された時のために選択位置を合わせる
        self.graphicsScene.clear()  # 描画シーンのクリア
        animPtr = self.animPtrList[index]
        print( "Serected Anim:\t" + str(index) + " (" + hex(animPtr) + ")" )
        self.parseAnimData(self.spriteData, animPtr)
        self.guiFrameItemActivated(0)


    def parseAnimData(self, spriteData, animPtr):
        u''' 指定されたアニメーションデータを読み込んで処理する

            GUIのアニメーションリストで選択されたアニメーションに対して実行する
            アニメーションデータは20バイトのデータでアニメーションの1フレームを管理する
            この関数ではアニメーションデータが持つフレームデータをリスト化する
            1つのアニメーションのフレーム数は事前に与えられず，アニメーションデータが持つ再生タイプに基づいて逐次的にロードする模様
        '''

        self.framePtrList = []
        self.ui.frameList.clear()   # フレームリストのクリア
        frameCount = 0

        while True: # do while文がないので代わりに無限ループ＋breakを使う
            frameData = spriteData[animPtr:animPtr+20]
            self.framePtrList.append(animPtr)
            animPtrStr = hex(animPtr)[2:].zfill(8).upper()  # GUIに表示する文字列
            frameItem = QtGui.QListWidgetItem( animPtrStr )    # GUIのフレームリストに追加するアイテムの生成
            self.ui.frameList.addItem(frameItem) # フレームリストへ追加

            animPtr += 20
            frameCount += 1

            if frameData[-2:] in ["\x80\x00","\xC0\x00"]: # 終端フレームならループを終了
                break


    def guiFrameItemActivated(self, index):
        u''' GUIでフレームが選択されたときに行う処理
        '''

        if index == -1:
            return

        self.ui.frameList.setCurrentRow(index) # GUI以外から呼び出された時のために選択位置を合わせる
        framePtr = self.framePtrList[index]
        self.parseframeData(self.spriteData, framePtr)


    def parseframeData(self, spriteData, animPtr):
        u''' 1フレーム分の情報を取り出し画像を表示する

            入力：スプライトのデータとアニメーションデータの開始位置
            処理：20バイトのアニメーションデータを読み取って情報を取り出す
            出力：アニメーションデータの情報
        '''

        self.graphicsScene.clear()  # 描画シーンのクリア
        animData = spriteData[animPtr:animPtr+20]   # 1フレーム分ロード
        animData = struct.unpack("<LLLLHH", animData)   # データ構造に基づいて分解

        u'''
            20バイトで1フレーム
            4バイト：画像サイズがあるアドレスへのポインタ
            4バイト：パレットサイズがあるアドレスへのポインタ
            4バイト：OAMデータのポインタがあるアドレスへのポインタ
            4バイト：未使用データへのポインタ（？）
            2バイト：フレーム遅延数
            2バイト：再生タイプ

        '''
        graphSizePtr = animData[0]

        # 画像容量の読み取り
        graphSize = spriteData[graphSizePtr:graphSizePtr+4]
        graphSize = struct.unpack("<L", graphSize)[0]
        #print( "Graphics Size:\t" + hex(graphSize) )

        # 画像データの読み込み
        readPos = graphSizePtr + 4  # ４バイトのサイズ情報の後に画像データが続く
        graphData = spriteData[readPos:readPos+graphSize]   # 画像のロード

        palSizePtr = animData[1]

        ptrToOAMptr = animData[3]

        oamDataPtr = spriteData[ ptrToOAMptr:ptrToOAMptr+4 ]
        oamDataPtr = struct.unpack("<L", oamDataPtr)[0]
        #print( "OAM Data Pointer:\t" + hex(oamDataPtr) )
        oamDataStart = ptrToOAMptr + oamDataPtr # OAMデータの先頭アドレスはOAMポインタの先頭アドレス+ポインタの値
        readPos = oamDataStart

        '''
            OAMの処理
            OAMデータは5バイトで1セット
            FF FF FF FF FF で終端を表す

        '''
        oamCount = 0
        self.oamList = []   # OAMの情報を格納するリスト
        self.ui.oamList.clear() # GUIのOAMリストをクリア
        while spriteData[readPos:readPos+5] != "\xFF\xFF\xFF\xFF\xFF":
            #print( "\nOAM: " + str(oamCount) )

            oamData = spriteData[readPos:readPos+5]
            oamAddrStr = ( hex(readPos)[2:].zfill(8)).upper()  # GUIのリストに表示する文字列
            oamItem = QtGui.QListWidgetItem( oamAddrStr )   # GUIのOAMリストに追加するアイテムの生成
            self.ui.oamList.addItem(oamItem) # GUIスプライトリストへ追加

            readPos += 5
            oamCount += 1


            oamData = struct.unpack("BbbBB", oamData)
            startTile = oamData[0]
            #print( "Starting Tile:\t" + str(startTile) )
            posX = oamData[1]
            #print( "X:\t" + str(posX) )
            posY = oamData[2]
            #print( "Y:\t" + str(posY) )

            flag1 = bin(oamData[3])[2:].zfill(8)    # 2進数にして先頭の0bを取り除いて8桁に0埋め
            '''
                フラグ構造（8bit）
                b b  bbbb   bb
                h v unused size

            '''
            objSize = flag1[-2:]    # 下位2ビット
            hFlip = int( flag1[1], 2 ) # 水平反転フラグ
            vFlip = int( flag1[0], 2 ) # 垂直反転フラグ
            #print( "Horizontal Flip: " + str(hFlip) )
            #print( "Vertical Flip:\t" + str(vFlip) )
            #print("size:\t" + str(objSize) )

            flag2 = bin(oamData[4])[2:].zfill(8)
            objShape = flag2[-2:]
            palIndex = int(flag2[0:4], 2)
            #print("shape:\t" + str(objShape) )
            #print("")

            # パレットの設定
            self.parsePaletteData(spriteData, palSizePtr, palIndex)

            sizeX, sizeY = objDim[objSize+objShape]
            image = self.makeOAMImage(graphData, startTile, sizeX, sizeY, hFlip, vFlip) # PILじゃないと反転出来なそうなので画像生成の時点で反転を適用する

            OAM = {
            "image":image,
            "sizeX":sizeX,
            "sizeY":sizeY,
            "posX":posX,
            "posY":posY
            }
            self.oamList.append(OAM)
            self.drawOAM(OAM["image"], OAM["sizeX"], OAM["sizeY"], OAM["posX"], OAM["posY"])

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
            #self.showOBJ(graphData, startTile, sizeX, sizeY, posX, posY, hFlip, vFlip)

        #print "Animation Flame Delay:\t" + str(animData[4]) + " frame"

        animType = animData[5]
        '''
            アニメーションタイプは再生状態を決定する
            0x00:   遅延フレーム分待った後に次フレームを再生（次のアニメーションデータをロード）
            0x80:   アニメーションの終了（最後のフレーム）
            0xC0:   アニメーションのループ（最初のフレームに戻る）
            アニメーションの最後のフレームは0x80か0xC0

        '''
        #print "Animation Type:\t" + hex(animType)
        #print "\n----------------------------------------\n"


    def guiSpriteItemWClicked(self, item):
        u''' GUIでスプライトがダブルクリックされたときに行う処理（未使用）
        '''

        index = self.ui.spriteList.currentRow() # 選択された行の番号を取得
        ptrAddr = self.spriteAddrList[index][2]


    def guiOAMItemActivated(self, item):
        u''' GUIでOAMが選択されたときに行う処理
        '''

        index = self.guiOAMList.currentRow()  # 渡されるのはアイテムなのでインデックス番号は現在の行から取得する
        if self.graphicsScene.items()[index].isVisible():
            self.graphicsScene.items()[index].hide()    # 非表示にする
        else:
            self.graphicsScene.items()[index].show()    # 表示する

        '''
        oam = self.oamList[index]
        image = oam["image"]
        item = QtGui.QGraphicsPixmapItem(image)
        item.setOffset(oam["posX"], oam["posY"])
        imageBounds = item.boundingRect()
        print( self.graphicsScene.items()[index] )
        #self.graphicsScene.addRect(imageBounds)
        #self.graphicsScene.addItem(item)
        '''

    def guiPalItemActivated(self, item):
        u''' GUIで色が選択されたときに行う処理
        '''

        index = self.guiPalList.currentRow()
        r,g,b,a = self.palData[index]["color"]   # 選択された色の値をセット
        writePos = self.palData[index]["addr"]  # 色データを書き込む位置
        color = QtGui.QColorDialog.getColor( QtGui.QColor(r, g, b) )    # カラーダイアログを開く
        r,g,b,a = color.getRgb()    # ダイアログでセットされた色に更新

        binR = bin(r/8)[2:].zfill(5)    # 5bitカラーに変換
        binG = bin(g/8)[2:].zfill(5)
        binB = bin(b/8)[2:].zfill(5)
        gbaColor = int(binB + binG + binR, 2)  # GBAのカラーコードに変換
        colorStr = struct.pack("H", gbaColor)
        self.spriteData = self.spriteData[:writePos] + colorStr + self.spriteData[writePos+2:]  # ロード中のスプライトデータの色を書き換える
        #self.romData = self.romData[:writePos] + colorStr + self.romData[writePos+2:]  # ROM内の色を書き換える

        animIndex = self.guiAnimList.currentRow()
        print("animIndex: " + str(animIndex) )
        self.guiAnimItemActivated(animIndex)


    '''
        アニメーションの再生

    '''
    def playAnimData(self):
        pass


    def makeOAMImage(self, imgData, startTile, width, hight, hFlip, vFlip):
        u''' OAM情報から画像を生成する

            入力：スプライトのグラフィック，開始タイル，横サイズ，縦サイズ
            出力：画像データ（QPixmap形式）
        '''

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
            imgArray.append(self.palData[currentPixel]["color"])
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

        dataImg = Image.fromarray( np.uint8(img) )  # 色情報の行列から画像を生成（PILのImage形式）
        if hFlip == 1:
            dataImg = dataImg.transpose(Image.FLIP_LEFT_RIGHT)  # PILの機能で水平反転

        if vFlip == 1:
            dataImg = dataImg.transpose(Image.FLIP_TOP_BOTTOM)
        qImg = ImageQt(dataImg) # QImage形式に変換
        pixmap = QtGui.QPixmap.fromImage(qImg)  # QPixmap形式に変換
        return pixmap


    def drawOAM(self, image, sizeX, sizeY, posX, posY):
        u''' OAMを描画する
        '''

        item = QtGui.QGraphicsPixmapItem(image)
        item.setOffset(posX , posY)
        imageBounds = item.boundingRect()
        self.graphicsScene.addItem(item)
        #self.graphicsScene.addRect(imageBounds)


    def parsePaletteData(self, spriteData, palSizePtr, palIndex):
        u''' パレットデータの読み取り

            入力：スプライトデータ，パレットサイズのアドレス
            処理：スプライトデータからのパレットサイズ読み込み，パレットデータ読み込み，RGBAカラー化
        '''

        # パレットサイズの読み取り
        palSize = spriteData[palSizePtr:palSizePtr+4]
        palSize = struct.unpack("<L", palSize)[0]
        #print( "Palette Size:\t" + hex(palSize) )
        if palSize != 0x20:  # サイズがおかしい場合は無視
            return

        readPos = palSizePtr + 4 + palIndex * palSize # パレットサイズ情報の後にパレットデータが続く（インデックス番号によって開始位置をずらす）
        endAddr = readPos + palSize

        self.palData = []    # パレットデータを格納するリスト
        self.ui.palList.clear()
        palCount = 0
        while readPos < endAddr:
            color = spriteData[readPos:readPos+2]   # 1色あたり16bit（2バイト）
            color = struct.unpack("<H", color)[0]

            binColor = bin(color)[2:].zfill(15) # GBAのオブジェクトは15bitカラー（0BBBBBGGGGGRRRRR）
            binB = int( binColor[0:5], 2 ) * 8  #   文字列化されているので数値に直す（255階調での近似色にするため8倍する）
            binG = int( binColor[5:10], 2 ) * 8
            binR = int( binColor[10:15], 2 ) * 8
            #print "R: " + hex(binR) + "\tG: " + hex(binG) + "\tB: " + hex(binB)
            if palCount == 0:
                self.palData.append( {"color":[binR, binG, binB, 0], "addr":readPos } ) # 最初の色は透過色
            else:
                self.palData.append( {"color":[binR, binG, binB, 255], "addr":readPos } )

            colorStr = hex(color)[2:].zfill(4).upper() + "\t(" + str(binR).rjust(3) + ", " + str(binG).rjust(3) + ", " + str(binB).rjust(3) + ")"  # GUIに表示する文字列
            colorItem = QtGui.QListWidgetItem(colorStr)
            colorItem.setBackgroundColor( QtGui.QColor(binR, binG, binB) )  # 背景色をパレットの色に
            colorItem.setTextColor( QtGui.QColor(255-binR, 255-binG, 255-binB) )    # 文字は反転色
            self.ui.palList.addItem(colorItem) # フレームリストへ追加

            palCount += 1
            readPos += 2


'''
main

'''
def main():
    app = QtGui.QApplication(sys.argv)

    # 日本語文字コードを正常表示するための設定
    reload(sys) # モジュールをリロードしないと文字コードが変更できない
    sys.setdefaultencoding("utf-8") # コンソールの出力をutf-8に設定

    spriteReader = SpriteReader();
    spriteReader.show()
    if len(sys.argv) >= 2:
        spriteReader.openFile(sys.argv[1])

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
