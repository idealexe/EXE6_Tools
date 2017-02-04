#!/usr/bin/python
# coding: utf-8

u''' EXE Sprite Reader ver 1.1 by ideal.exe


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

from logging import getLogger,StreamHandler,INFO,DEBUG
logger = getLogger(__name__)    # 出力元の明確化
handler = StreamHandler()
handler.setLevel(INFO)
logger.setLevel(INFO)
logger.addHandler(handler)

HEADER_SIZE = 4 # スプライトヘッダのサイズ
OFFSET_SIZE = 4
FRAME_DATA_SIZE = 20
OAM_DATA_SIZE = 5
OAM_DATA_END = "\xFF\xFF\xFF\xFF\xFF"

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

        self.romData = ""   # ファイルを読み込んだ時点でその内容がコピーされる．このデータを読み書きする．


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
            filename = QtGui.QFileDialog.getOpenFileName( self, _("Open EXE_ROM File"), os.path.expanduser('./') )   # ファイル名がQString型で返される
            filename = unicode(filename)

        try:
            with open( filename, 'rb' ) as romFile:
                self.romData = romFile.read()
        except:
            print( _(u"ファイルの選択をキャンセルしました") )
            return -1    # 中断

        if self.setDict(self.romData) == -1:
            u""" 非対応ROMの場合も中断
            """
            return -1

        self.extractSpriteAddr(self.romData)
        self.guiSpriteItemActivated(0)  # 1番目のスプライトを自動で選択


    def openSprite(self):
        u""" スプライトファイルを開くときの処理
        """
        filename = QtGui.QFileDialog.getOpenFileName( self, _("Open EXE Sprite File"), os.path.expanduser('./') )   # ファイル名がQString型で返される
        filename = unicode(filename)

        try:
            with open( filename, 'rb' ) as romFile:
                self.romData = romFile.read()
        except:
            print( _(u"ファイルの選択をキャンセルしました") )
            return -1

        self.spriteList = []
        self.ui.spriteList.clear()
        self.spriteList.append( {"spriteAddr":0, "compFlag":0, "readPos":0} )

        spriteItemStr = "Opend Sprite"  # GUIのリストに表示する文字列
        spriteItem = QtGui.QListWidgetItem( spriteItemStr )  # GUIのスプライトリストに追加するアイテムの生成
        self.ui.spriteList.addItem(spriteItem) # GUIスプライトリストへ追加
        self.guiSpriteItemActivated(0)  # 1番目のスプライトを自動で選択


    def setDict(self, romData):
        u""" バージョンを判定し使用する辞書をセットする
        """

        self.romName = self.romData[0xA0:0xAC]
        global EXE_Addr    # アドレスリストはグローバル変数にする（書き換えないし毎回self.をつけるのが面倒なので）
        if self.romName == "ROCKEXE6_GXX":
            print( _(u"ロックマンエグゼ6 グレイガ jp としてロードしました") )
            EXE_Addr = SpriteDict.ROCKEXE6_GXX
        elif self.romName == "MEGAMAN6_GXX":
            print( _(u"ロックマンエグゼ6 グレイガ en としてロードしました") )
            EXE_Addr = SpriteDict.MEGAMAN6_GXX
        elif self.romName == "ROCKEXE6_RXX":
            print( _(u"ロックマンエグゼ6 ファルザー jp としてロードしました") )
            EXE_Addr = SpriteDict.ROCKEXE6_RXX
        elif self.romName == "MEGAMAN6_FXX":
            print( _(u"ロックマンエグゼ6 ファルザー en としてロードしました") )
            EXE_Addr = SpriteDict.MEGAMAN6_FXX

        elif self.romName == "ROCKEXE5_TOB":
            print( _(u"ロックマンエグゼ5 チームオブブルース jp としてロードしました") )
            EXE_Addr = SpriteDict.ROCKEXE5_TOB
        elif self.romName == "ROCKEXE5_TOC":
            print( _(u"ロックマンエグゼ5 チームオブカーネル jp としてロードしました") )
            EXE_Addr = SpriteDict.ROCKEXE5_TOC

        elif self.romName == "ROCKEXE4.5RO":
            print( _(u"ロックマンエグゼ4.5 jp としてロードしました") )
            EXE_Addr = SpriteDict.ROCKEXE4_5RO

        elif self.romName == "ROCK_EXE4_RS":
            print( _(u"ロックマンエグゼ4 トーナメントレッドサン jp としてロードしました") )
            EXE_Addr = SpriteDict.ROCKEXE4_RS
        elif self.romName == "ROCK_EXE4_BM":
            print( _(u"ロックマンエグゼ4 トーナメントブルームーン jp としてロードしました") )
            EXE_Addr = SpriteDict.ROCKEXE4_BM

        elif self.romName == "ROCK_EXE3_BK":
            print( _(u"ロックマンエグゼ3 Black jp としてロードしました") )
            EXE_Addr = SpriteDict.ROCK_EXE3_BK
        elif self.romName == "ROCKMAN_EXE3":
            print(_(u"ロックマンエグゼ3 jp としてロードしました"))
            EXE_Addr = SpriteDict.ROCKMAN_EXE3

        else:
            print( _(u"対応していないバージョンです" ) )
            return -1   # error


    def extractSpriteAddr(self, romData):
        u''' スプライトのアドレスを抽出する
        '''

        self.spriteList = []    # スプライトの先頭アドレスと圧縮状態を保持するリスト
        self.ui.spriteList.clear() # スプライトリストの初期化

        readPos = EXE_Addr["startAddr"]
        while readPos <= EXE_Addr["endAddr"] - OFFSET_SIZE:
            u""" スプライトテーブルの読み込み

            テーブルの最後のアドレスはスプライトデータではなくデータの終端と思われる
            """

            spriteAddr = romData[readPos:readPos+OFFSET_SIZE]
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
                [spriteAddr] = struct.unpack("<L", spriteAddr)

                """
                if readPos in EXE_Addr["classHeadAddr"]:
                    print hex(spriteAddr)
                """

                if spriteAddr in EXE_Addr["ignoreAddr"]:
                    readPos += OFFSET_SIZE
                    continue


                u""" スプライトの先頭から次のデータまでの間はそのスプライトが利用可能な空間

                nextDataAddr = romData[readPos+4:readPos+8]
                [nextDataAddr] = struct.unpack("<L", nextDataAddr[:3]+"\x00")

                spriteSpace = nextDataAddr - spriteAddr

                パディングがついていることがあるので必ずしもスプライトのサイズとは一致しないが近い値
                ↑と思ったがデータ的に連続していないスプライトを参照していることがあるので意味がなかった
                """

                self.spriteList.append( {"spriteAddr":spriteAddr, "compFlag":compFlag, "pointerAddr":readPos} )

                spriteAddrStr = ( hex(memByte)[2:].zfill(2) + hex(spriteAddr)[2:].zfill(6) ).upper() + "\t"  # GUIのリストに表示する文字列
                if self.romName == "ROCKEXE6_GXX":
                    try:
                        spriteAddrStr += unicode( SpriteDict.GXX_Sprite_List[hex(spriteAddr)] )
                    except:
                        pass

                spriteItem = QtGui.QListWidgetItem( spriteAddrStr )  # GUIのスプライトリストに追加するアイテムの生成
                self.ui.spriteList.addItem(spriteItem) # GUIスプライトリストへ追加

            readPos += OFFSET_SIZE


    def guiSpriteItemActivated(self, index):
        u''' GUIでスプライトが選択されたときに行う処理
        '''

        if index == -1:
            u""" 何らかの原因で無選択状態になったら中断
            """
            return

        self.graphicsScene = QtGui.QGraphicsScene() # スプライトを描画するためのシーン
        self.graphicsScene.setSceneRect(-120,-80,240,160)    # gbaの画面を模したシーン（ ビューの中心が(0,0)になる ）
        self.ui.graphicsView.setScene(self.graphicsScene)
        self.ui.palSelect.setValue(0)
        #self.ui.spriteList.setCurrentRow(index) # GUI以外から呼び出された時のために選択位置を合わせる
        # ↑この変更もハンドリングされてしまうのでダメ
        spriteAddr = self.spriteList[index]["spriteAddr"]
        #print( "Serected Sprite:\t" + hex(spriteAddr) )
        compFlag = self.spriteList[index]["compFlag"]
        self.parseSpriteData(self.romData, spriteAddr, compFlag)
        self.guiAnimItemActivated(0)


    def parseSpriteData(self, romData, spriteAddr, compFlag):
        u''' ROMデータから指定された位置にあるスプライトの情報を取り出す

            スプライトリストでアイテムが選択されたら実行する形を想定
        '''

        if compFlag == 0:   # 非圧縮スプライトなら
            startAddr = spriteAddr
            endAddr = startAddr + 0x100000  # スプライトはサイズ情報を持たないので仮の値を設定
            readPos = startAddr
            #print "Sprite Address:\t" + hex(startAddr) + "\n"

            # 使う部分だけ切り出し
            spriteHeader = romData[startAddr:startAddr+HEADER_SIZE]   # 初めの４バイトがヘッダ情報
            self.spriteData = romData[startAddr+HEADER_SIZE:endAddr]   # それ以降がスプライトの内容

        elif compFlag == 1: # 圧縮スプライトなら
            spriteData = LZ77Util.decompLZ77_10(romData, spriteAddr)[8:]    # ファイルサイズ情報とヘッダー部分を取り除く
            self.spriteData = spriteData

        else:
            return

        readPos = 0 # スプライトデータの先頭から読み込む
        animDataStart = self.spriteData[readPos:readPos+OFFSET_SIZE]
        animDataStart = struct.unpack("<L", animDataStart)[0]

        # アニメーションポインタのリスト生成
        self.animPtrList = []
        self.ui.animList.clear()   # 表示用リストの初期化

        while readPos < animDataStart:
            u""" アニメーションポインタのリスト化
            """
            animPtr = self.spriteData[readPos:readPos+OFFSET_SIZE]
            readPos += OFFSET_SIZE

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

        self.ui.animList.setCurrentRow(index) # GUI以外から呼び出された時のために選択位置を合わせる
        animPtr = self.animPtrList[index]
        #print( "Serected Anim:\t" + str(index) + " (" + hex(animPtr) + ")" )
        self.parseAnimData(self.spriteData, animPtr)
        self.guiFrameItemActivated(0)


    def parseAnimData(self, spriteData, animPtr):
        u''' 指定されたアニメーションデータを読み込んで処理する

            GUIのアニメーションリストで選択されたアニメーションに対して実行する
            アニメーションデータは複数のフレームデータで構成されており，1フレームは20バイトの情報で管理する
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

            animPtr += FRAME_DATA_SIZE
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
        palIndex = self.ui.palSelect.value()
        self.parseframeData(self.spriteData, framePtr)


    def parseframeData(self, spriteData, framePtr):
        u''' 1フレーム分の情報を取り出し画像を表示する

            入力：スプライトのデータとフレームデータの開始位置
            処理：20バイトのアニメーションデータを読み取って情報を取り出す
        '''

        self.graphicsScene.clear()  # 描画シーンのクリア
        frameData = spriteData[framePtr:framePtr+FRAME_DATA_SIZE]   # 1フレーム分ロード
        [graphSizePtr, palSizePtr, junkDataPtr, ptrToOAMptr, frameDelay, animType] = struct.unpack("<LLLLHH", frameData)   # データ構造に基づいて分解

        u"""
            20バイトで1フレーム
            4バイト：画像サイズがあるアドレスへのポインタ
            4バイト：パレットサイズがあるアドレスへのポインタ
            4バイト：未使用データへのポインタ（？）
            4バイト：OAMデータのポインタがあるアドレスへのポインタ
            2バイト：フレーム遅延数
            2バイト：再生タイプ
        """

        graphSize = spriteData[graphSizePtr:graphSizePtr+OFFSET_SIZE]
        #print("Graphics Size Pointer:\t" + hex(graphSizePtr))
        graphSize = struct.unpack("<L", graphSize)[0]
        #print( "Graphics Size:\t" + hex(graphSize) )

        # 画像データの読み込み
        readPos = graphSizePtr + OFFSET_SIZE  # ４バイトのサイズ情報の後に画像データが続く
        graphData = spriteData[readPos:readPos+graphSize]   # 画像のロード

        u""" フレームが指定している色を無視してUIで選択中のパレットで表示する仕様にしています
        """
        palIndex = self.ui.palSelect.value()
        self.parsePaletteData(spriteData, palSizePtr, palIndex)

        oamDataPtr = spriteData[ ptrToOAMptr:ptrToOAMptr+OFFSET_SIZE ]
        oamDataPtr = struct.unpack("<L", oamDataPtr)[0]
        #print( "OAM Data Pointer:\t" + hex(oamDataPtr) )
        oamDataStart = ptrToOAMptr + oamDataPtr # OAMデータの先頭アドレスはOAMポインタの先頭アドレス+ポインタの値
        self.parseOamData(spriteData, graphData, oamDataStart)


    def parseOamData(self, spriteData, graphData, oamDataStart):
        u''' OAMの処理

            OAMデータを読み取って生成した画像とサイズ，描画オフセットを取得する
            OAMデータは5バイトで1セット
            FF FF FF FF FF で終端を表す
        '''

        oamCount = 0
        OAM_DATA_END = "\xFF\xFF\xFF\xFF\xFF"
        readPos = oamDataStart

        self.oamList = []   # OAMの情報を格納するリスト
        self.ui.oamList.clear() # GUIのOAMリストをクリア
        while spriteData[readPos:readPos+OAM_DATA_SIZE] != OAM_DATA_END:

            oamData = spriteData[readPos:readPos+OAM_DATA_SIZE]
            oamAddrStr = ( hex(readPos)[2:].zfill(8)).upper()  # GUIのリストに表示する文字列
            oamItem = QtGui.QListWidgetItem( oamAddrStr )   # GUIのOAMリストに追加するアイテムの生成
            self.ui.oamList.addItem(oamItem) # GUIスプライトリストへ追加

            readPos += OAM_DATA_SIZE
            oamCount += 1


            [startTile, posX, posY, flag1, flag2] = struct.unpack("BbbBB", oamData)
            logger.debug( "Starting Tile:\t" + str(startTile) )
            logger.debug( "X: " + str(posX) )
            logger.debug( "Y: " + str(posY) )

            flag1 = bin(flag1)[2:].zfill(8)    # 2進数にして先頭の0bを取り除いて8桁に0埋め
            u''' フラグ構造（8bit）

                b b  bbbb   bb
                v h unused size
            '''

            objSize = flag1[-2:]    # 下位2ビット
            hFlip = int( flag1[1], 2 ) # 水平反転フラグ
            vFlip = int( flag1[0], 2 ) # 垂直反転フラグ

            logger.debug( "Horizontal Flip: " + str(hFlip) )
            logger.debug( "Vertical Flip:   " + str(vFlip) )
            logger.debug( "Size Flag:\t" + str(objSize) )

            flag2 = bin(flag2)[2:].zfill(8)
            objShape = flag2[-2:]
            logger.debug( "Shape Flag:\t" + str(objShape) )

            sizeX, sizeY = objDim[objSize+objShape]
            image = self.makeOAMImage(graphData, startTile, sizeX, sizeY, hFlip, vFlip)

            OAM = {
            "image":image,
            "sizeX":sizeX,
            "sizeY":sizeY,
            "posX":posX,
            "posY":posY
            }
            self.oamList.append(OAM)
            self.drawOAM(OAM["image"], OAM["sizeX"], OAM["sizeY"], OAM["posX"], OAM["posY"])
            logger.debug("---\n")
        self.endAddr = readPos + len("\xFF\xFF\xFF\xFF\xFF")


    def guiOAMItemActivated(self, item):
        u''' GUIでOAMが選択されたときに行う処理
        '''

        index = self.ui.oamList.currentRow()  # 渡されるのはアイテムなのでインデックス番号は現在の行から取得する
        oam = self.oamList[index]
        image = oam["image"]
        item = QtGui.QGraphicsPixmapItem(image)
        item.setOffset(oam["posX"], oam["posY"])
        imageBounds = item.boundingRect()
        self.graphicsScene.addRect(imageBounds)


    def guiPalItemActivated(self, item):
        u''' GUIで色が選択されたときに行う処理
        '''

        index = self.ui.palList.currentRow()
        if index == -1:
            return -1

        r,g,b,a = self.palData[index]["color"]   # 選択された色の値をセット
        writePos = self.palData[index]["addr"]  # 色データを書き込む位置
        color = QtGui.QColorDialog.getColor( QtGui.QColor(r, g, b) )    # カラーダイアログを開く
        if color.isValid() == False: # キャンセルしたとき
            print(u"色の選択をキャンセルしました")
            return 0

        r,g,b,a = color.getRgb()    # ダイアログでセットされた色に更新

        binR = bin(r/8)[2:].zfill(5)    # 5bitカラーに変換
        binG = bin(g/8)[2:].zfill(5)
        binB = bin(b/8)[2:].zfill(5)
        gbaColor = int(binB + binG + binR, 2)  # GBAのカラーコードに変換
        colorStr = struct.pack("H", gbaColor)
        self.spriteData = self.spriteData[:writePos] + colorStr + self.spriteData[writePos+2:]  # ロード中のスプライトデータの色を書き換える

        frameIndex = self.ui.frameList.currentRow()
        framePtr = self.framePtrList[frameIndex]
        self.parseframeData(self.spriteData, framePtr)


    '''
        アニメーションの再生

    '''
    def playAnimData(self):
        print(u"現在アニメーションの再生には対応していません")


    def makeOAMImage(self, imgData, startTile, width, hight, hFlip, vFlip):
        u''' OAM情報から画像を生成する

            入力：スプライトのグラフィックデータ，開始タイル，横サイズ，縦サイズ
            出力：画像データ（QPixmap形式）

            グラフィックデータは4bitで1pxを表現する．アクセス可能な最小単位は8*8pxのタイルでサイズは32byteとなる
        '''

        startAddr = startTile * 32  # 開始タイルから開始アドレスを算出（1タイル8*8px = 32バイト）
        width = width/8 # サイズからタイルの枚数に変換
        hight = hight/8
        imgData = imgData[startAddr:]   # 使う部分を切り出し
        imgData = binascii.hexlify(imgData).upper()   # バイナリ値をそのまま文字列にしたデータに変換（0xFF -> "FF"）
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
                h[i] = np.hstack( (h[i], tile[i*width + j]) )
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
        palSize = spriteData[palSizePtr:palSizePtr+OFFSET_SIZE]
        palSize = struct.unpack("<L", palSize)[0]
        #print( "Palette Size:\t" + hex(palSize) )
        if palSize != 0x20:  # サイズがおかしい場合は無視→と思ったら自作スプライトとかで0x00にしてることもあったので無視
            #return
            palSize = 0x20

        readPos = palSizePtr + OFFSET_SIZE + palIndex * palSize # パレットサイズ情報の後にパレットデータが続く（インデックス番号によって開始位置をずらす）
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

    def changePalet(self, n):
        index = self.ui.frameList.currentRow()
        framePtr = self.framePtrList[index]
        self.parseframeData(self.spriteData, framePtr)
        """
        try:
            self.parsePaletteData(self.spriteData, palSizePtr, n)
        except:
            print(u"スプライトが読み込まれていません")
            """


    def getSpriteSize(self):
        u""" スプライトデータのサイズを検出する

        スプライトの一番最後のアニメーションの一番最後のフレームの一番最後のOAMの終端がそのアドレス
        """
        #print len(self.animPtrList)
        self.guiAnimItemActivated( len(self.animPtrList)-1 )    # 最後のアニメーション
        #print len(self.framePtrList)
        self.guiFrameItemActivated( len(self.framePtrList)-1 )  # 最後のフレーム
        return self.endAddr+HEADER_SIZE   # ヘッダサイズぶん


    def dumpSprite(self):
        u""" スプライトのダンプ
        """

        targetSprite = self.getCurrentSprite()

        if targetSprite["compFlag"] == 0:
            data = self.romData[targetSprite["spriteAddr"]:targetSprite["spriteAddr"]+self.getSpriteSize()]
        else:
            data = LZ77Util.decompLZ77_10(self.romData, targetSprite["spriteAddr"])[4:] # ファイルサイズ情報を取り除く

        filename = QtGui.QFileDialog.getSaveFileName(self, _(u"スプライトを保存する"), os.path.expanduser('./'), _("dump File (*.bin *.dmp)"))
        try:
            with open( unicode(filename), 'wb') as saveFile:
                saveFile.write(data)
                print u"ファイルを保存しました"
        except:
            print u"ファイルの保存をキャンセルしました"


    def exDumpSprite(self):
        u""" スプライトを拡張してダンプ

            スプライトを32アニメーション，各16フレームのスペースを確保したスプライトに変換して保存する
            拡張した部分には１個めのアニメーションをコピーする
            アニメーション数が少ないスプライトを移植するときも安心
        """

        ANIMATION_NUM = 32   # アニメーション数は32に固定する
        FRAME_NUM = 16   # フレーム数は16枚分確保する
        ANIMATION_TABLE_SIZE = ANIMATION_NUM * OFFSET_SIZE
        ANIMATION_SIZE = FRAME_NUM * FRAME_DATA_SIZE


    def saveFrameImage(self):
        u""" フレーム画像の保存
        """

        sourceBounds = self.graphicsScene.itemsBoundingRect()    # シーン内の全てのアイテムから領域を算出
        image = QtGui.QImage( QtCore.QSize(sourceBounds.width(), sourceBounds.height()), 12)
        targetBounds = QtCore.QRectF(image.rect() )
        painter = QtGui.QPainter(image)
        self.graphicsScene.render(painter, targetBounds, sourceBounds)
        painter.end()

        filename = QtGui.QFileDialog.getSaveFileName(self, _(u"フレーム画像を保存する"), os.path.expanduser('./'), _("image File (*.png)"))
        try:
            with open( unicode(filename), 'wb') as saveFile:
                image.save(filename, "PNG")
                print u"ファイルを保存しました"
        except:
            print u"ファイルの保存をキャンセルしました"


    def saveRomFile(self):
        u""" ファイルの保存
        """

        filename = QtGui.QFileDialog.getSaveFileName(self, _(u"ROMを保存する"), os.path.expanduser('./'), _("Rom File (*.gba *.bin)"))
        try:
            with open( unicode(filename), 'wb') as saveFile:
                saveFile.write(self.romData)
                print u"ファイルを保存しました"
        except:
            print u"ファイルの保存をキャンセルしました"


    def repoint(self):
        u""" ポインタの書き換え
        """
        targetAddr = self.getCurrentSprite()
        print( u"書き換えるアドレス：\t" + hex( targetAddr ) )

        dialog = QtGui.QDialog()
        dialog.ui = repointDialog()
        dialog.ui.setupUi(dialog)
        dialog.show()
        dialog.exec_()

        if dialog.result() == 1:
            addrText = dialog.ui.addrText.text()
            try:
                addr = int(str(addrText), 16)   # QStringから戻さないとダメ
                data = struct.pack("L", addr + 0x08000000)
                print binascii.hexlify(data)
                self.romData = self.romData[:targetAddr] + data + self.romData[targetAddr+len(data):]
            except:
                print(u"不正な値です")
            # リロード
            self.extractSpriteAddr(self.romData)
            self.guiSpriteItemActivated(0)  # 1番目のスプライトを自動で選択
        else:
            print(u"リポイントをキャンセルしました")

    def writePalData(self):
        u""" UI上で編集したパレットのデータをROMに書き込む
        """

        targetSprite = self.getCurrentSprite()
        if targetSprite["compFlag"] == 1:
            print(u"圧縮スプライトは現在非対応です")
            return 0
        else:
            writeAddr = targetSprite["spriteAddr"] + HEADER_SIZE  # ヘッダのぶん4バイト
            self.romData = self.romData[:writeAddr] + self.spriteData + self.romData[writeAddr+len(self.spriteData):]
            print(u"編集したパレットをメモリ上のROMに書き込みました")
            return 0


    def flipSprite(self):
        u""" 選択中のスプライトを水平反転する

            全てのOAMの水平反転フラグを切り替え，描画オフセットXを-X-sizeXにする
        """

        targetSprite = self.getCurrentSprite()
        spriteAddr = targetSprite["spriteAddr"]
        logger.debug("Current Sprite Address:\t" + hex(spriteAddr))

        if targetSprite["compFlag"] == 1:
            print(u"圧縮スプライトは現在非対応です")
            return -1

        spriteAddr += HEADER_SIZE # ヘッダは無視
        readAddr = spriteAddr
        animPtrList = []
        animDataStart = self.romData[readAddr:readAddr+OFFSET_SIZE]
        animDataStart = struct.unpack("<L", animDataStart)[0] + readAddr
        logger.debug("Animation Data Start:\t" + hex(animDataStart))

        animCount = 0
        while readAddr < animDataStart:
            animPtr = self.romData[readAddr:readAddr+OFFSET_SIZE]
            animPtr = struct.unpack("<L", animPtr)[0] + spriteAddr
            animPtrList.append({"animNum":animCount, "addr":readAddr, "value":animPtr})
            readAddr += OFFSET_SIZE
            animCount += 1

        frameDataList = []
        for animPtr in animPtrList:
            readAddr = animPtr["value"]
            logger.debug("Animation at " + hex(readAddr))

            frameCount = 0
            while True: # do while文がないので代わりに無限ループ＋breakを使う
                frameData = self.romData[readAddr:readAddr+FRAME_DATA_SIZE]
                [graphSizePtr, palSizePtr, junkDataPtr, ptrToOAMptr, frameDelay, frameType] = struct.unpack("<LLLLHH", frameData)   # データ構造に基づいて分解
                ptrToOAMptr += spriteAddr
                u"""
                    20バイトで1フレーム
                    4バイト：画像サイズがあるアドレスへのポインタ
                    4バイト：パレットサイズがあるアドレスへのポインタ
                    4バイト：未使用データへのポインタ（？）
                    4バイト：OAMデータのポインタがあるアドレスへのポインタ
                    2バイト：フレーム遅延数
                    2バイト：再生タイプ
                """
                frameDataList.append({"animNum":animPtr["animNum"], "frameNum":frameCount, "address":readAddr, "oamPtrAddr":ptrToOAMptr})
                readAddr += FRAME_DATA_SIZE
                frameCount += 1

                if frameData[-2:] in ["\x80\x00","\xC0\x00"]: # 終端フレームならループを終了
                    break

        oamDataList = []
        for frameData in frameDataList:
            logger.debug("Frame at " + hex(frameData["address"]))
            logger.debug("  Animation Number:\t" + str(frameData["animNum"]))
            logger.debug("  Frame Number:\t\t" + str(frameData["frameNum"]))
            logger.debug("  Address of OAM Pointer:\t" + hex(frameData["oamPtrAddr"]))
            oamPtrAddr = frameData["oamPtrAddr"]
            [oamPtr] = struct.unpack("L", self.romData[oamPtrAddr:oamPtrAddr+OFFSET_SIZE])
            readAddr = oamPtrAddr + oamPtr

            while True:
                oamData = self.romData[readAddr:readAddr+OAM_DATA_SIZE]
                if oamData == OAM_DATA_END:
                    break
                oamDataList.append({"animNum":frameData["animNum"], "frameNum":frameData["frameNum"], "address":readAddr, "oamData":oamData})
                readAddr += OAM_DATA_SIZE

        for oam in oamDataList:
            logger.debug("OAM at " + hex(oam["address"]))
            oamData = oam["oamData"]
            [startTile, posX, posY, flag1, flag2] = struct.unpack("BbbBB", oamData)
            logger.debug("  Start Tile:\t" + str(startTile))
            logger.debug("  Offset X:\t" + str(posX))
            logger.debug("  Offset Y:\t" + str(posY))
            logger.debug("  Flag1 (VHNNNNSS)\t" + bin(flag1)[2:].zfill(8))
            logger.debug("  Flag2 (PPPPNNSS)\t" + bin(flag2)[2:].zfill(8))

            objSize = bin(flag1)[2:].zfill(8)[-2:]
            objShape = bin(flag2)[2:].zfill(8)[-2:]
            [sizeX, sizeY] = objDim[objSize+objShape]
            logger.debug("  Size X:\t" + str(sizeX))
            logger.debug("  Size Y:\t" + str(sizeY))

            posX = posX * -1 -sizeX # 水平方向の描画座標を反転
            flag1 ^= 0b01000000 # 水平反転フラグをビット反転

            flipData = struct.pack("BbbBB", startTile, posX, posY, flag1, flag2)
            self.writeDataToRom(oam["address"], flipData)
            sys.stdout.write(".")
        logger.info("done")

        logger.info(u"水平反転したスプライトを書き込みました")
        self.guiSpriteItemActivated(index)


    def getCurrentSprite(self):
        u""" 選択中のスプライトを取得する
        """
        index = self.ui.spriteList.currentRow()
        if index == -1:
            return -1
        return self.spriteList[index]


    def writeDataToRom(self, writeAddr, data):
        u""" 指定したアドレスから指定したデータを上書きする
        """
        self.romData = self.romData[:writeAddr] + data + self.romData[writeAddr+len(data):]


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class repointDialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        Dialog.resize(300, 100)
        self.verticalLayout = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(Dialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.addrText = QtGui.QLineEdit(Dialog)
        self.addrText.setObjectName(_fromUtf8("addrText"))
        self.verticalLayout.addWidget(self.addrText)
        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Dialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "リポイント", None))
        self.label.setText(_translate("Dialog", "アドレス（16進数で指定してください）", None))



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

u'''
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
