#!/usr/bin/python
# coding: utf-8

u''' EXE Sprite Reader ver 1.2 by ideal.exe


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
COLOR_SIZE  = 2 # 1色あたりのサイズ
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
            logger.info( _(u"ファイルの選択をキャンセルしました") )
            return -1    # 中断

        if self.setSpriteDict(self.romData) == -1:
            u""" 非対応ROMの場合も中断
            """
            return -1

        self.extractSpriteAddr(self.romData)
        self.ui.spriteList.setCurrentRow(0)


    def openSprite(self):
        u""" スプライトファイルを開くときの処理
        """

        filename = QtGui.QFileDialog.getOpenFileName( self, _("Open EXE_Sprite File"), os.path.expanduser('./') )   # ファイル名がQString型で返される
        filename = unicode(filename)

        try:
            with open( filename, 'rb' ) as romFile:
                self.romData = romFile.read()
        except:
            logger.info( _(u"ファイルの選択をキャンセルしました") )
            return -1

        self.spriteList = []
        self.ui.spriteList.clear()
        self.spriteList.append( {"spriteAddr":0, "compFlag":0, "readPos":0} )

        spriteItemStr = "Opened Sprite"  # GUIのリストに表示する文字列
        spriteItem = QtGui.QListWidgetItem( spriteItemStr )  # GUIのスプライトリストに追加するアイテムの生成
        self.ui.spriteList.addItem(spriteItem) # GUIスプライトリストへ追加
        self.ui.spriteList.setCurrentRow(0)  # 1番目のスプライトを自動で選択


    def setSpriteDict(self, romData):
        u""" バージョンを判定し使用する辞書をセットする
        """

        global romName
        romName = romData[0xA0:0xAC]
        global EXE_Addr    # アドレスリストはグローバル変数にする（書き換えないし毎回self.をつけるのが面倒なので）

        if romName == "ROCKEXE6_GXX":
            logger.info( _(u"ロックマンエグゼ6 グレイガ jp としてロードしました") )
            EXE_Addr = SpriteDict.ROCKEXE6_GXX
        elif romName == "MEGAMAN6_GXX":
            logger.info( _(u"ロックマンエグゼ6 グレイガ en としてロードしました") )
            EXE_Addr = SpriteDict.MEGAMAN6_GXX
        elif romName == "ROCKEXE6_RXX":
            logger.info( _(u"ロックマンエグゼ6 ファルザー jp としてロードしました") )
            EXE_Addr = SpriteDict.ROCKEXE6_RXX
        elif romName == "MEGAMAN6_FXX":
            logger.info( _(u"ロックマンエグゼ6 ファルザー en としてロードしました") )
            EXE_Addr = SpriteDict.MEGAMAN6_FXX

        elif romName == "ROCKEXE5_TOB":
            logger.info( _(u"ロックマンエグゼ5 チームオブブルース jp としてロードしました") )
            EXE_Addr = SpriteDict.ROCKEXE5_TOB
        elif romName == "ROCKEXE5_TOC":
            logger.info( _(u"ロックマンエグゼ5 チームオブカーネル jp としてロードしました") )
            EXE_Addr = SpriteDict.ROCKEXE5_TOC

        elif romName == "ROCKEXE4.5RO":
            logger.info( _(u"ロックマンエグゼ4.5 jp としてロードしました") )
            EXE_Addr = SpriteDict.ROCKEXE4_5RO

        elif romName == "ROCK_EXE4_RS":
            logger.info( _(u"ロックマンエグゼ4 トーナメントレッドサン jp としてロードしました") )
            EXE_Addr = SpriteDict.ROCKEXE4_RS
        elif romName == "ROCK_EXE4_BM":
            logger.info( _(u"ロックマンエグゼ4 トーナメントブルームーン jp としてロードしました") )
            EXE_Addr = SpriteDict.ROCKEXE4_BM

        elif romName == "ROCK_EXE3_BK":
            logger.info( _(u"ロックマンエグゼ3 Black jp としてロードしました") )
            EXE_Addr = SpriteDict.ROCK_EXE3_BK
        elif romName == "ROCKMAN_EXE3":
            logger.info(_(u"ロックマンエグゼ3 jp としてロードしました"))
            EXE_Addr = SpriteDict.ROCKMAN_EXE3

        else:
            logger.info( _(u"対応していないバージョンです" ) )
            return -1   # error


    def extractSpriteAddr(self, romData):
        u''' スプライトのアドレスを抽出する

            スプライトリストが作成されます
            スプライトリストはスプライトのアドレス，圧縮状態，スプライトのアドレスを保持しているポインタのアドレスを保持します
            spriteListの各要素は{"spriteAddr":spriteAddr, "compFlag":compFlag, "pointerAddr":readPos}の形式です
        '''

        self.spriteList = []
        self.ui.spriteList.clear() # UIのスプライトリストの初期化

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

                if spriteAddr in EXE_Addr["ignoreAddr"]:
                    readPos += OFFSET_SIZE
                    continue

                self.spriteList.append( {"spriteAddr":spriteAddr, "compFlag":compFlag, "pointerAddr":readPos} )

                spriteAddrStr = ( hex(memByte)[2:].zfill(2) + hex(spriteAddr)[2:].zfill(6) ).upper() + "\t"  # GUIのリストに表示する文字列
                if romName == "ROCKEXE6_GXX":
                    try:
                        spriteAddrStr += unicode( SpriteDict.GXX_Sprite_List[hex(spriteAddr)] )
                    except:
                        pass
                spriteItem = QtGui.QListWidgetItem( spriteAddrStr )  # GUIのスプライトリストに追加するアイテムの生成
                self.ui.spriteList.addItem(spriteItem) # GUIスプライトリストへ追加

            readPos += OFFSET_SIZE


    def guiSpriteItemActivated(self, index):
        u''' GUIでスプライトが選択されたときに行う処理

            描画シーンのクリア，アニメーションリストの生成
        '''

        if index == -1:
            u""" 何らかの原因で無選択状態になったら中断
            """
            return -1

        self.graphicsScene = QtGui.QGraphicsScene() # スプライトを描画するためのシーン
        self.graphicsScene.setSceneRect(-120,-80,240,160)    # gbaの画面を模したシーン（ ビューの中心が(0,0)になる ）
        self.ui.graphicsView.setScene(self.graphicsScene)
        self.ui.palSelect.setValue(0)   # パレットをリセット
        self.ui.animList.clear()

        spriteAddr = self.spriteList[index]["spriteAddr"]
        compFlag = self.spriteList[index]["compFlag"]

        [spriteData, animPtrList, frameDataList, oamDataList] = self.parseAllData(self.romData, spriteAddr, compFlag)
        self.spriteData = spriteData
        self.animPtrList = animPtrList
        self.frameDataList = frameDataList
        self.oamDataList = oamDataList

        self.ui.animLabel.setText(u"アニメーション：" + str(len(animPtrList)))
        for animPtr in animPtrList:
            animPtrStr = hex(animPtr["value"])[2:].zfill(6).upper() # GUIに表示する文字列
            animItem = QtGui.QListWidgetItem( animPtrStr )    # GUIのアニメーションリストに追加するアイテムの生成
            self.ui.animList.addItem(animItem) # アニメーションリストへ追加

        self.ui.animList.setCurrentRow(0)   # self.guiAnimItemActivated(0)  が呼ばれる


    def parseAllData(self, romData, spriteAddr, compFlag):
        u""" スプライトの読み取り

            以下のリストを返す

            spriteData

            animPtrList.append({"animNum":animCount, "addr":readAddr, "value":animPtr})

            frameDataList.append({"animNum":animPtr["animNum"], "frameNum":frameCount, "address":readAddr, "frameData":frameData, \
                "graphSizeAddr":graphSizeAddr, "palSizeAddr":palSizeAddr, "junkDataAddr":junkDataAddr, \
                "oamPtrAddr":oamPtrAddr, "frameDelay":frameDelay, "frameType":frameType})

            oamDataList.append({"animNum":frameData["animNum"], "frameNum":frameData["frameNum"], "address":readAddr, "oamData":oamData})
        """

        if compFlag == 0:
            spriteData = romData[spriteAddr+HEADER_SIZE:]   # スプライトはサイズ情報を持たないので仮の範囲を切り出し
        elif compFlag == 1:
            spriteData = LZ77Util.decompLZ77_10(romData, spriteAddr)[8:]    # ファイルサイズ情報とヘッダー部分を取り除く
        else:
            logger.info(u"不明なエラーです")
            return -1

        readAddr = 0
        animDataStart = spriteData[readAddr:readAddr+OFFSET_SIZE]
        animDataStart = struct.unpack("<L", animDataStart)[0]
        logger.debug("Animation Data Start:\t" + hex(animDataStart))

        u""" アニメーションオフセットのテーブルからアニメーションのアドレスを取得
        """
        animPtrList = []
        animCount = 0
        while readAddr < animDataStart:
            animPtr = spriteData[readAddr:readAddr+OFFSET_SIZE]
            animPtr = struct.unpack("<L", animPtr)[0]
            animPtrList.append({"animNum":animCount, "addr":readAddr, "value":animPtr})
            readAddr += OFFSET_SIZE
            animCount += 1

        u""" アニメーションのアドレスから各フレームのデータを取得
        """
        frameDataList = []
        graphAddrList = []    # グラフィックデータは共有しているフレームも多いので別のリストで保持
        for animPtr in animPtrList:
            readAddr = animPtr["value"]
            logger.debug("Animation at " + hex(readAddr))

            frameCount = 0
            while True: # do while文がないので代わりに無限ループ＋breakを使う
                frameData = spriteData[readAddr:readAddr+FRAME_DATA_SIZE]
                [graphSizeAddr, palSizeAddr, junkDataAddr, oamPtrAddr, frameDelay, frameType] = struct.unpack("<LLLLHH", frameData)   # データ構造に基づいて分解
                if graphSizeAddr not in graphAddrList:
                    graphAddrList.append(graphSizeAddr)
                [graphicSize] = struct.unpack("L", spriteData[graphSizeAddr:graphSizeAddr+OFFSET_SIZE])
                graphicData = spriteData[graphSizeAddr+OFFSET_SIZE:graphSizeAddr+OFFSET_SIZE+graphicSize]

                frameDataList.append({"animNum":animPtr["animNum"], "frameNum":frameCount, "address":readAddr, "frameData":frameData, \
                    "graphSizeAddr":graphSizeAddr, "graphicData":graphicData,"palSizeAddr":palSizeAddr, "junkDataAddr":junkDataAddr, \
                    "oamPtrAddr":oamPtrAddr, "frameDelay":frameDelay, "frameType":frameType})

                readAddr += FRAME_DATA_SIZE
                frameCount += 1

                if frameData[-2:] in ["\x80\x00","\xC0\x00"]: # 終端フレームならループを終了
                    break

        u""" フレームデータからOAMデータを取得
        """
        oamDataList = []
        for frameData in frameDataList:
            logger.debug("Frame at " + hex(frameData["address"]))
            logger.debug("  Animation Number:\t" + str(frameData["animNum"]))
            logger.debug("  Frame Number:\t\t" + str(frameData["frameNum"]))
            logger.debug("  Address of OAM Pointer:\t" + hex(frameData["oamPtrAddr"]))
            oamPtrAddr = frameData["oamPtrAddr"]
            [oamPtr] = struct.unpack("L", spriteData[oamPtrAddr:oamPtrAddr+OFFSET_SIZE])
            readAddr = oamPtrAddr + oamPtr

            while True:
                oamData = spriteData[readAddr:readAddr+OAM_DATA_SIZE]
                if oamData == OAM_DATA_END:
                    break
                logger.debug("OAM at " + hex(readAddr))

                [startTile, posX, posY, flag1, flag2] = struct.unpack("BbbBB", oamData)
                logger.debug("  Start Tile:\t" + str(startTile))
                logger.debug("  Offset X:\t" + str(posX))
                logger.debug("  Offset Y:\t" + str(posY))

                flag1 = bin(flag1)[2:].zfill(8)
                flag2 = bin(flag2)[2:].zfill(8)
                logger.debug("  Flag1 (VHNNNNSS)\t" + flag1)
                logger.debug("  Flag2 (PPPPNNSS)\t" + flag2)

                flipV = int( flag1[0], 2 ) # 垂直反転フラグ
                flipH = int( flag1[1], 2 ) # 水平反転フラグ

                objSize = flag1[-2:]
                objShape = flag2[-2:]
                [sizeX, sizeY] = objDim[objSize+objShape]
                logger.debug("  Size X:\t" + str(sizeX))
                logger.debug("  Size Y:\t" + str(sizeY))

                oamDataList.append({"animNum":frameData["animNum"], "frameNum":frameData["frameNum"], "address":readAddr, "oamData":oamData, \
                    "startTile":startTile, "posX":posX, "posY":posY, "sizeX":sizeX, "sizeY":sizeY, "flipV":flipV, "flipH":flipH})
                readAddr += OAM_DATA_SIZE

        u""" 無圧縮スプライトデータの切り出し
        """
        if compFlag == 0:
            endAddr = oamDataList[-1]["address"] + OAM_DATA_SIZE + len(OAM_DATA_END)
            spriteData = spriteData[:endAddr]

        return [spriteData, animPtrList, frameDataList, oamDataList]


    def guiAnimItemActivated(self, index):
        u''' GUIでアニメーションが選択されたときに行う処理

            フレームリストから選択されたアニメーションのフレームを取り出してリスト化
        '''

        if index == -1: # GUIの選択位置によっては-1が渡されることがある？
            return

        self.ui.frameList.clear()

        currentAnimFrame = [frame for frame in self.frameDataList if frame["animNum"] == index]
        self.ui.frameLabel.setText(u"フレーム：" + str(len(currentAnimFrame)))
        for frame in currentAnimFrame:
            frameStr = hex(frame["address"])[2:].zfill(8).upper()  # GUIに表示する文字列
            frameItem = QtGui.QListWidgetItem( frameStr )    # GUIのフレームリストに追加するアイテムの生成
            self.ui.frameList.addItem(frameItem) # フレームリストへ追加

        self.ui.frameList.setCurrentRow(0)


    def guiFrameItemActivated(self, index):
        u''' GUIでフレームが選択されたときに行う処理

            現在のフレームのOAMを取得してリスト化，パレットの取得
        '''

        if index == -1:
            return

        self.graphicsScene.clear()  # 描画シーンのクリア
        self.ui.oamList.clear()
        animIndex = self.ui.animList.currentRow()

        u""" フレームが指定している色を無視してUIで選択中のパレットで表示する仕様にしています
        """
        palIndex = self.ui.palSelect.value()

        [currentFrame] = [frame for frame in self.frameDataList if frame["animNum"] == animIndex and frame["frameNum"] == index]
        self.parsePaletteData(self.spriteData, currentFrame["palSizeAddr"], palIndex)

        currentFrameOam = [oam for oam in self.oamDataList if oam["animNum"] == animIndex and oam["frameNum"] == index]
        self.ui.oamLabel.setText(u"OAM：" + str(len(currentFrameOam)))

        for oam in currentFrameOam:
            oamAddrStr = ( hex(oam["address"])[2:].zfill(8)).upper()  # GUIのリストに表示する文字列
            oamItem = QtGui.QListWidgetItem( oamAddrStr )   # GUIのOAMリストに追加するアイテムの生成
            self.ui.oamList.addItem(oamItem) # GUIスプライトリストへ追加

            # OAM画像の生成，描画
            graphicData = currentFrame["graphicData"]
            image = self.makeOAMImage(graphicData, oam["startTile"], oam["sizeX"], oam["sizeY"], oam["flipV"], oam["flipH"])
            self.drawOAM(image, oam["sizeX"], oam["sizeY"], oam["posX"], oam["posY"])


    def parsePaletteData(self, spriteData, palSizePtr, palIndex):
        u''' パレットデータの読み取り

            入力：スプライトデータ，パレットサイズのアドレス
            処理：スプライトデータからのパレットサイズ読み込み，パレットデータ読み込み，RGBAカラー化
        '''

        # パレットサイズの読み取り
        palSize = spriteData[palSizePtr:palSizePtr+OFFSET_SIZE]
        palSize = struct.unpack("<L", palSize)[0]
        if palSize != 0x20:  # サイズがおかしい場合は無視→と思ったら自作スプライトとかで0x00にしてることもあったので無視
            palSize = 0x20

        readPos = palSizePtr + OFFSET_SIZE + palIndex * palSize # パレットサイズ情報の後にパレットデータが続く（インデックス番号によって開始位置をずらす）
        endAddr = readPos + palSize

        self.palData = []    # パレットデータを格納するリスト
        self.ui.palList.clear()
        palCount = 0
        while readPos < endAddr:
            color = spriteData[readPos:readPos+COLOR_SIZE]
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
            readPos += COLOR_SIZE


    def changePalet(self, n):
        index = self.ui.frameList.currentRow()
        self.guiFrameItemActivated(index)


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
            logger.info(u"色の選択をキャンセルしました")
            return 0

        r,g,b,a = color.getRgb()    # ダイアログでセットされた色に更新

        binR = bin(r/8)[2:].zfill(5)    # 5bitカラーに変換
        binG = bin(g/8)[2:].zfill(5)
        binB = bin(b/8)[2:].zfill(5)
        gbaColor = int(binB + binG + binR, 2)  # GBAのカラーコードに変換
        colorStr = struct.pack("H", gbaColor)
        self.spriteData = self.spriteData[:writePos] + colorStr + self.spriteData[writePos+COLOR_SIZE:]  # ロード中のスプライトデータの色を書き換える

        frameIndex = self.ui.frameList.currentRow()
        self.guiFrameItemActivated(frameIndex)


    def playAnimData(self):
        u''' アニメーションの再生
        '''

        logger.info(u"現在アニメーションの再生には対応していません")


    def makeOAMImage(self, imgData, startTile, width, height, flipV, flipH):
        u''' OAM情報から画像を生成する

            入力：スプライトのグラフィックデータ，開始タイル，横サイズ，縦サイズ，垂直反転フラグ，水平反転フラグ
            出力：画像データ（QPixmap形式）

            グラフィックデータは4bitで1pxを表現する．アクセス可能な最小単位は8*8pxのタイルでサイズは32byteとなる
        '''

        TILE_WIDTH = 8
        TILE_HEIGHT = 8
        TILE_DATA_SIZE = TILE_WIDTH * TILE_HEIGHT / 2

        logger.debug("Image Width:\t" + str(width))
        logger.debug("Image Height:\t" + str(height))
        logger.debug("Flip V:\t" + str(flipV))
        logger.debug("Flip H:\t" + str(flipH))

        startAddr = startTile * TILE_DATA_SIZE  # 開始タイルから開始アドレスを算出（1タイル8*8px = 32バイト）
        imgData = imgData[startAddr:]   # 使う部分を切り出し
        imgData = binascii.hexlify(imgData).upper()   # バイナリ値をそのまま文字列にしたデータに変換（0xFF -> "FF"）
        imgData = list(imgData) # 1文字ずつのリストに変換
        # ドットの描画順（0x01 0x23 0x45 0x67 -> 10325476）に合わせて入れ替え
        for i in range(0, len(imgData))[0::2]:  # 偶数だけ取り出す（0から+2ずつ）
            imgData[i], imgData[i+1] = imgData[i+1], imgData[i] # これで値を入れ替えられる

        width = width / TILE_WIDTH # サイズからタイルの枚数に変換
        height = height / TILE_HEIGHT

        totalSize = len(imgData)    # 全ドット数
        imgArray = []

        # 色情報に変換する
        readPos = 0
        while readPos < totalSize:
            currentPixel = int(imgData[readPos], 16)    # 1ドット分読み込み，文字列から数値に変換
            imgArray.append(self.palData[currentPixel]["color"])    # 対応する色に変換
            readPos += 1

        imgArray = np.array(imgArray)   # ndarrayに変換
        imgArray = imgArray.reshape( (-1, TILE_WIDTH, 4) )  # 横8ドットのタイルに並べ替える（-1を設定すると自動で縦の値を算出してくれる）
        u""" 現在の状態

            □
            □
            ︙
            □
            □
        """

        tileNum = width * height  # 合計タイル数

        # タイルの切り出し
        tile = []  # pythonのリストとして先に宣言する（ndarrayとごっちゃになりやすい）
        for i in range(0, tileNum):
            tile.append(imgArray[TILE_HEIGHT*i:TILE_HEIGHT*(i+1), 0:TILE_WIDTH, :])    # 8x8のタイルを切り出していく

        # タイルの並び替え
        h = []  # 水平方向に結合したタイルを格納するリスト
        for i in range(0, height):
            h.append( np.zeros_like(tile[0]) )    # タイルを詰めるダミー
            for j in range(0, width):
                h[i] = np.hstack( (h[i], tile[i*width + j]) )
            if i != 0:
                h[0] = np.vstack((h[0], h[i]))
        img = h[0][:, 8:, :]    # ダミー部分を切り取る（ださい）

        dataImg = Image.fromarray( np.uint8(img) )  # 色情報の行列から画像を生成（PILのImage形式）
        if flipH == 1:
            dataImg = dataImg.transpose(Image.FLIP_LEFT_RIGHT)  # PILの機能で水平反転
        if flipV == 1:
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


    def dumpSprite(self):
        u""" スプライトのダンプ
        """

        targetSprite = self.getCurrentSprite()

        if targetSprite["compFlag"] == 0:
            data = self.romData[targetSprite["spriteAddr"]:targetSprite["spriteAddr"]+HEADER_SIZE] + self.spriteData
        else:
            data = LZ77Util.decompLZ77_10(self.romData, targetSprite["spriteAddr"])[4:] # ファイルサイズ情報を取り除く

        filename = QtGui.QFileDialog.getSaveFileName(self, _(u"スプライトを保存する"), os.path.expanduser('./'), _("dump File (*.bin *.dmp)"))
        try:
            with open( unicode(filename), 'wb') as saveFile:
                saveFile.write(data)
                logger.info(u"ファイルを保存しました")
        except:
            logger.info(u"ファイルの保存をキャンセルしました")


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

        output = "" # 出力用のスプライトデータ

        u""" アニメーションオフセットテーブル作成
        """
        animDataStart = ANIMATION_NUM * OFFSET_SIZE
        for i in xrange(ANIMATION_NUM):
            output += struct.pack("L", animDataStart + i * ANIMATION_SIZE)

        u""" グラフィック，OAMなどのコピー

            フレームデータ内で各アドレスを参照するので先にコピーする
        """
        output += "\xFF" * ANIMATION_SIZE * ANIMATION_NUM # アニメーションデータ領域の確保
        writeAddr = ANIMATION_TABLE_SIZE + ANIMATION_SIZE * ANIMATION_NUM
        copyOffset = writeAddr - self.frameDataList[0]["graphSizeAddr"] # グラフィックデータの元の開始位置との差分（フレームデータの修正に使用する）
        # 先頭のフレームが先頭のグラフィックデータを使ってないパターンがあったら死ぬ
        output += self.spriteData[self.frameDataList[0]["graphSizeAddr"]:]  # グラフィックデータ先頭からスプライトの終端までコピー

        u""" フレームデータのコピー
        """
        for frameData in self.frameDataList:
            writeAddr = animDataStart + ANIMATION_SIZE * frameData["animNum"] + FRAME_DATA_SIZE * frameData["frameNum"]
            graphSizeAddr = frameData["graphSizeAddr"] + copyOffset
            palSizeAddr = frameData["palSizeAddr"] + copyOffset
            junkDataAddr = frameData["junkDataAddr"] + copyOffset
            oamPtrAddr = frameData["oamPtrAddr"] + copyOffset
            frameDelay = frameData["frameDelay"]
            frameType = frameData["frameType"]
            data = struct.pack("<LLLLHH", graphSizeAddr, palSizeAddr, junkDataAddr, oamPtrAddr, frameDelay, frameType)
            output = output[:writeAddr] + data + output[writeAddr+len(data):]

        for i in xrange(len(self.animPtrList), ANIMATION_NUM):    # 拡張した分のアニメーション
            writeAddr = animDataStart + ANIMATION_SIZE * i
            data = output[animDataStart:animDataStart+ANIMATION_SIZE] # 1つめのアニメーションをコピーする
            output = output[:writeAddr] + data + output[writeAddr+len(data):]

        output = "\xFF\xFF\xFF\xFF" + output    # ヘッダの追加

        filename = QtGui.QFileDialog.getSaveFileName(self, _(u"スプライトを保存する"), os.path.expanduser('./'), _("dump File (*.bin *.dmp)"))
        try:
            with open( unicode(filename), 'wb') as saveFile:
                saveFile.write(output)
                logger.info(u"ファイルを保存しました")
        except:
            logger.info(u"ファイルの保存をキャンセルしました")


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
                logger.info(u"ファイルを保存しました")
        except:
            logger.info(u"ファイルの保存をキャンセルしました")


    def saveRomFile(self):
        u""" ファイルの保存
        """

        filename = QtGui.QFileDialog.getSaveFileName(self, _(u"ROMを保存する"), os.path.expanduser('./'), _("Rom File (*.gba *.bin)"))
        try:
            with open( unicode(filename), 'wb') as saveFile:
                saveFile.write(self.romData)
                logger.info(u"ファイルを保存しました")
        except:
            logger.info(u"ファイルの保存をキャンセルしました")


    def repoint(self):
        u""" ポインタの書き換え
        """
        index = self.ui.spriteList.currentRow()
        targetAddr = self.spriteList[index]["pointerAddr"]
        logger.info( u"書き換えるアドレス：\t" + hex( targetAddr ) )

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
                self.romData = self.romData[:targetAddr] + data + self.romData[targetAddr+len(data):]
            except:
                logger.info(u"不正な値です")
            # リロード
            self.extractSpriteAddr(self.romData)
            self.ui.spriteList.setCurrentRow(index)
        else:
            logger.info(u"リポイントをキャンセルしました")


    def writePalData(self):
        u""" UI上で編集したパレットのデータをROMに書き込む
        """

        targetSprite = self.getCurrentSprite()
        if targetSprite["compFlag"] == 1:
            logger.info(u"圧縮スプライトは現在非対応です")
            return 0
        else:
            writeAddr = targetSprite["spriteAddr"] + HEADER_SIZE  # ヘッダのぶん4バイト
            self.romData = self.romData[:writeAddr] + self.spriteData + self.romData[writeAddr+len(self.spriteData):]
            logger.info(u"編集したパレットをメモリ上のROMに書き込みました")
            return 0


    def flipSprite(self):
        u""" 選択中のスプライトを水平反転する

            全てのOAMの水平反転フラグを切り替え，描画オフセットXを-X-sizeXにする
        """

        targetSprite = self.getCurrentSprite()
        if targetSprite["compFlag"] == 1:
            print(u"圧縮スプライトは非対応です")
            return -1

        for oam in self.oamDataList:
            writeAddr = oam["address"] + targetSprite["spriteAddr"] + HEADER_SIZE   # ROM内でのアドレス
            logger.debug("OAM at " + hex(writeAddr) )
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
            self.writeDataToRom(writeAddr, flipData)
            sys.stdout.write(".")
        logger.info("done")

        logger.info(u"水平反転したスプライトを書き込みました")
        index = self.ui.spriteList.currentRow()
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
