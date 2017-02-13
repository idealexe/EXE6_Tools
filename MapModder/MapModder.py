#!/usr/bin/python
# coding: utf-8

u""" Map Modder ver 0.3 by ideal.exe
"""

from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt4 import QtCore, QtGui
import binascii
import numpy as np
import os
import pandas as pd
import re
import struct
import sys

import gettext
_ = gettext.gettext # 後の翻訳用

import UI_MapModder as designer
import CommonAction as commonAction

from logging import getLogger,StreamHandler,INFO,DEBUG
logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(INFO)
logger.setLevel(INFO)
logger.addHandler(handler)

import argparse
parser = argparse.ArgumentParser(description=u"入力ファイルに対して指定の処理を行います")
parser.add_argument("file", help=u"処理対象のファイル")
args = parser.parse_args()

LIST_FILE_PATH = os.path.join(os.path.dirname(sys.argv[0]), "lists/") # プログラムと同ディレクトリにあるlistsフォルダ下にリストを保存する


u""" Map Modder
"""
class MapModder(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.ui = designer.Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.graphicsView.scale(2,2)
        self.graphicsScene = QtGui.QGraphicsScene()
        self.graphicsScene.setSceneRect(-120,-80,240,160)    # gbaの画面を模したシーン（ ビューの中心が(0,0)になる ）
        self.ui.graphicsView.setScene(self.graphicsScene)

        u""" 各種パラメータの初期化

            複数の関数で独立して更新されることが多いので全てself下の変数とした
        """
        self.addr = 0
        self.palAddr = 0
        self.tileX = self.ui.xTileBox.value()
        self.tileY = self.ui.yTileBox.value()

    def updateImage(self):
        u""" 画像を更新する
        """
        self.palData = self.parsePaletteData(self.romData, self.palAddr)
        image = self.makeMapImage(self.romData, self.addr, self.tileX, self.tileY)
        self.drawMap(image)

    def openFile(self, *args):
        u""" ファイルを開くときの処理
        """
        if len(args) != 0:
            u""" 引数がある場合はそれをファイル名にする
            """
            filename = args[0]
        else:
            u""" 引数がない場合はファイルを開く
            """
            filename = QtGui.QFileDialog.getOpenFileName( self, _("Open File"), os.path.expanduser('./') )   # ファイル名がQString型で返される
            filename = unicode(filename)
        self.openedFileName = filename  # 保存時にパスを利用したいので


        try:
            with open( filename, 'rb' ) as romFile:
                self.romData = romFile.read()
        except:
            logger.info( _(u"ファイルの選択をキャンセルしました") )
            return -1    # 中断

        [title, code] = self.getRomHeader(self.romData)
        listName = code + "_" + title + ".csv"

        if os.path.exists(LIST_FILE_PATH + listName):
            u""" リストファイルの存在判定
            """
            self.listData = self.loadListFile(listName)
        else:
            df = pd.DataFrame({
            "label":[],
            "addr":[],
            "palAddr":[],
            "width":[],
            "height":[],
            "comp":[]
            },
            columns=['label', 'addr', 'palAddr', 'width', 'height', 'comp'])    # 並び順を指定
            df.to_csv(LIST_FILE_PATH + listName, encoding="utf-8", index=False)
            print(u"リストファイルを作成しました")
            self.listData = df
            self.ui.dataList.clear()

        self.updateImage()

    def loadListFile(self, listName):
        u""" リストファイルの読み込み

            GUIのリストをセットアップしpandas形式のリストを返す
        """
        self.ui.dataList.clear()
        listData = pd.read_csv(LIST_FILE_PATH + listName, encoding="utf-8", index_col=None)
        logger.debug(listData)
        for i, data in listData.iterrows():    # 各行のイテレータ
            logger.debug(data)
            logger.debug(data["label"])

            dataStr = unicode(data["label"])    # GUIのリストに表示する文字列
            item = QtGui.QListWidgetItem(dataStr)  # リストに追加するアイテムの生成
            self.ui.dataList.addItem(item) # リストへ追加
        logger.info(u"リストファイルを読み込みました")
        return listData


    def getRomHeader(self, romData):
        title = romData[0xA0:0xAC].decode("utf-8")
        code = romData[0xAC:0xB0].decode("utf-8")
        print("Title:\t" + title)
        print("Code:\t" + code)
        return [title, code]


    def drawMap(self, image):
        u''' マップ画像を描画する
        '''
        self.graphicsScene.clear()
        item = QtGui.QGraphicsPixmapItem(image)
        item.setOffset(image.width()/2*-1, image.height()/2*-1)
        imageBounds = item.boundingRect()
        self.graphicsScene.addItem(item)
        #self.graphicsScene.addRect(imageBounds)


    def parsePaletteData(self, romData, palAddr):
        u""" パレットデータの読み取り

            入力：ROMデータ，パレットのアドレス
            処理：ROMデータからのパレット読み込み，GUIのパレットリスト更新，RGBAカラー化
        """
        PALETTE_SIZE = 0x20
        COLOR_SIZE = 2

        readAddr = palAddr
        endAddr = readAddr + PALETTE_SIZE

        palData = []    # パレットデータを格納するリスト
        self.ui.palList.clear()
        palCount = 0
        while readAddr < endAddr:
            color = romData[readAddr:readAddr+COLOR_SIZE]
            color = struct.unpack("<H", color)[0]

            binColor = bin(color)[2:].zfill(15) # GBAのオブジェクトは15bitカラー（0BBBBBGGGGGRRRRR）
            b = int( binColor[0:5], 2 ) * 8  #   文字列化されているので数値に直す（255階調での近似色にするため8倍する）
            g = int( binColor[5:10], 2 ) * 8
            r = int( binColor[10:15], 2 ) * 8

            if palCount == 0:
                palData.append( {"color":[r, g, b, 0], "addr":readAddr } ) # 最初の色は透過色
            else:
                palData.append( {"color":[r, g, b, 255], "addr":readAddr } )

            colorStr = hex(color)[2:].zfill(4).upper() + "\t(" + str(r).rjust(3) + ", " + str(g).rjust(3) + ", " + str(b).rjust(3) + ")"  # GUIに表示する文字列
            colorItem = QtGui.QListWidgetItem(colorStr)
            colorItem.setBackgroundColor( QtGui.QColor(r, g, b) )  # 背景色をパレットの色に
            colorItem.setTextColor( QtGui.QColor(255-r, 255-g, 255-b) )    # 文字は反転色
            self.ui.palList.addItem(colorItem) # フレームリストへ追加

            palCount += 1
            readAddr += COLOR_SIZE

        return palData


    def guiDataItemActivated(self):
        u""" 登録データが選択されたときの処理
        """
        [self.label, self.addr, self.palAddr, self.tileX, self.tileY] = self.getCrrentItemData()

        self.ui.labelEdit.setText(self.label)
        self.ui.addrBox.setValue(self.addr)
        self.ui.palAddrBox.setValue(self.palAddr)
        self.ui.xTileBox.setValue(self.tileX)
        self.ui.yTileBox.setValue(self.tileY)

        self.updateImage()


    def getCrrentItemData(self):
        u""" 現在の行のアイテム情報を返す
        """
        index = self.ui.dataList.currentRow()
        logger.debug("index:\t" + str(index))
        logger.debug(self.listData)

        label = self.listData["label"][index]
        addr = int(self.listData["addr"][index], 16)
        palAddr = int(self.listData["palAddr"][index], 16)
        tileX = int(self.listData["width"][index])
        tileY = int(self.listData["height"][index])

        return [label, addr, palAddr, tileX, tileY]


    def guiAddrChanged(self, value):
        u""" アドレスが更新されたときの処理
        """
        self.addr = self.ui.addrBox.value()
        self.updateImage()

    def guiAddrStepChanged(self, n):
        u""" アドレスのステップ数の変更
        """
        self.ui.addrBox.setSingleStep(n)

    def guiNextMapPressed(self):
        u""" 次のマップらしきものを表示する

            現在のマップと同じサイズだけアドレスを移動するだけ（ついでにパレットも切り替える）
        """
        self.addr += self.tileX * self.tileY * 32
        self.ui.addrBox.setValue(self.addr)
        self.palAddr += self.ui.palAddrStep.value()
        self.ui.palAddrBox.setValue(self.palAddr)
        self.updateImage()

    def guiPrevMapPressed(self):
        u""" 前のマップらしきものを表示する

            現在のマップと同じサイズだけアドレスを移動するだけ
        """
        self.addr -= self.tileX * self.tileY * 32
        self.ui.addrBox.setValue(self.addr)
        self.palAddr -= self.ui.palAddrStep.value()
        self.ui.palAddrBox.setValue(self.palAddr)
        self.updateImage()


    def guiPalAddrChanged(self):
        u""" パレットアドレスが更新されたときの処理
        """
        self.palAddr = self.ui.palAddrBox.value()
        self.ui.palAddrBox.setValue(self.palAddr)
        #self.ui.palAddrBox.lineEdit().setText(hex(self.palAddr))
        logger.debug(hex(self.palAddr))
        self.updateImage()


    def guiPalAddrStepChanged(self, n):
        u""" パレットアドレスのステップ数の変更
        """
        self.ui.palAddrBox.setSingleStep(n)


    def guiPalItemActivated(self):
        u""" GUIで色が選択されたときに行う処理
        """
        COLOR_SIZE = 2

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
        self.romData = self.romData[:writePos] + colorStr + self.romData[writePos+COLOR_SIZE:]
        self.updateImage()


    def guiTileXChanged(self, n):
        self.tileX = n
        self.updateImage()

    def guiTileYChanged(self, n):
        self.tileY = n
        self.updateImage()

    def guiRegButtonPressed(self):
        u""" 登録ボタンが押されたときの処理
        """
        [title, code] = self.getRomHeader(self.romData)
        listName = code + "_" + title + ".csv"

        label = self.ui.labelEdit.text()
        addr = self.ui.addrBox.value()
        palAddr = self.ui.palAddrBox.value()
        width = self.ui.xTileBox.value()
        height = self.ui.yTileBox.value()

        se = pd.Series([unicode(label), hex(addr), hex(palAddr), width, height, 0], index=self.listData.columns)
        self.listData = self.listData.append(se, ignore_index=True).sort_values(by=["palAddr"], ascending=True).reset_index(drop=True)   # 追加してソート
        logger.debug(self.listData)
        self.listData.to_csv("./lists/" + listName, encoding="utf-8", index=False)
        logger.info(u"リストに登録しました")
        self.loadListFile(listName)

    def saveFile(self):
        u""" ファイルの保存
        """

        filename = QtGui.QFileDialog.getSaveFileName(self, _(u"ROMを保存する"), \
            os.path.expanduser(os.path.dirname(self.openedFileName)), _("Rom File (*.gba *.bin)"))
        try:
            with open( unicode(filename), 'wb') as saveFile:
                saveFile.write(self.romData)
                logger.info(u"ファイルを保存しました")
        except:
            logger.info(u"ファイルの保存をキャンセルしました")

    def changeViewScale(self, value):
        u""" ビューを拡大縮小する
        """
        self.ui.graphicsView.resetTransform()   # 一度オリジナルサイズに戻す
        scale = pow(2, value/10.0)   # 指数で拡大したほうが自然にスケールしてる感じがする
        self.ui.graphicsView.scale(scale, scale)

    def searchBinary(self):
        u""" データを検索する
        """
        searchText = str(self.ui.searchEdit.text())
        logger.info("Search Text:\t" + searchText)

        try:
            searchValue = binascii.unhexlify(searchText)   # "0a" -> 0x0A
        except:
            logger.warning(u"入力はバイト列として解釈できるテキストのみ受けつけます")
            return -1

        logger.info("Search Value:\t" + searchValue )

        self.ui.searchBrowser.clear()
        pattern = re.compile(re.escape(searchValue) )   # エスケープが必要な文字（0x3f = "?" とか）が含まれている可能性がある
        matchIter = re.finditer(pattern, self.romData)

        count = 0
        for m in matchIter:
            logger.debug(hex( m.start() ))
            resultText = hex(m.start())
            self.ui.searchBrowser.append(resultText)
            count += 1
            if count >= 100:
                logger.info(u"マッチ結果が多すぎます．100件以降は省略しました")
                return -1

    def saveImageFile(self):
        commonAction.saveSceneImage(self.graphicsScene)


    def makeMapImage(self, romData, startAddr, width, height):
        u''' マップ画像を生成する

            グラフィックデータは4bitで1pxを表現する．アクセス可能な最小単位は8*8pxのタイルでデータサイズは32byteとなる
        '''

        TILE_WIDTH = 8  # px
        TILE_HEIGHT = 8
        TILE_DATA_SIZE = TILE_WIDTH * TILE_HEIGHT / 2   # bytes

        logger.debug("Image Width:\t" + str(width) + " Tile")
        logger.debug("Image Height:\t" + str(height) + " Tile")

        imgDataSize = TILE_DATA_SIZE * width * height
        imgData = romData[startAddr:startAddr+imgDataSize]  # 使う部分を切り出し
        imgData = binascii.hexlify(imgData).upper()   # バイナリ値をそのまま文字列にしたデータに変換（0xFF -> "FF"）
        imgData = list(imgData) # 1文字ずつのリストに変換
        # ドットの描画順（0x01 0x23 0x45 0x67 -> 10325476）に合わせて入れ替え
        for i in range(0, len(imgData))[0::2]:  # 偶数だけ取り出す（0から+2ずつ）
            imgData[i], imgData[i+1] = imgData[i+1], imgData[i] # これで値を入れ替えられる

        imgArray = []
        imgDotNum = len(imgData)
        # 色情報に変換する
        readAddr = 0
        while readAddr < imgDotNum:
            currentPixel = int(imgData[readAddr], 16)    # 1ドット分読み込み，文字列から数値に変換
            imgArray.append(self.palData[currentPixel]["color"])    # 対応する色に変換
            readAddr += 1

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
        qImg = ImageQt(dataImg) # QImage形式に変換
        pixmap = QtGui.QPixmap.fromImage(qImg)  # QPixmap形式に変換
        return pixmap


u""" Main
"""
def main():
    reload(sys) # モジュールをリロードしないと文字コードが変更できない
    sys.setdefaultencoding("utf-8") # コンソールの出力をutf-8に設定

    app = QtGui.QApplication(sys.argv)

    mapModder = MapModder();
    mapModder.show()

    if len(sys.argv) >= 2:
        mapModder.openFile(sys.argv[1])

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
