#!/usr/bin/python
# coding: utf-8
# pylint: disable=C0103, E1101

""" Common Action  ver 1.0  by ideal.exe

    共用できる機能をまとめたモジュール
"""

import gettext
import os
import sys
from PIL import Image
from logging import getLogger, StreamHandler, INFO
from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np


logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(INFO)
logger.setLevel(INFO)
logger.addHandler(handler)

_ = gettext.gettext

TILE_WIDTH = 8  # px
TILE_HEIGHT = 8
TILE_DATA_SIZE = TILE_WIDTH * TILE_HEIGHT // 2  # 1タイルあたりのデータサイズ（１バイトで２ドット）


class GbaTile():
    """ GBAのタイル

        20バイトのバイナリデータから8x8(px)、16色のビットマップを作成する
    """

    def __init__(self, binTileData):
        self.binTileData = binTileData

        dotList = list(binTileData.hex().upper())
        dotList = [int(i, 16) for i in dotList]
        # ドットの描画順（0x01 0x23 0x45 0x67 -> 10325476）に合わせて入れ替え
        for i in range(0, len(dotList))[0::2]:  # 偶数だけ取り出す（0から+2ずつ）
            dotList[i], dotList[i+1] = dotList[i+1], dotList[i] # これで値を入れ替えられる

        imgArray = np.array(dotList, dtype=np.uint8).reshape((TILE_WIDTH, TILE_HEIGHT))
        self.imgArray = imgArray
        self.image = QtGui.QImage(imgArray, TILE_WIDTH, TILE_HEIGHT, QtGui.QImage.Format_Indexed8)


    def getBinTileData(self):
        """ タイルのバイナリデータを返す
        """
        return self.binTileData


    def getImgArray(self):
        """ np.array形式のタイルデータを返す
        """
        return self.imgArray
        

    def getQImage(self):
        """ QImage形式のタイル画像を返す
        """
        return self.image


class GbaMap():
    """ GBAのマップ
    """

    def __init__(self, binMapData, tileX, tileY):
        self.binMapData = binMapData

        tileList = []
        readAddr = 0
        while readAddr < len(binMapData):
            tileList.append(GbaTile(binMapData[readAddr:readAddr+TILE_DATA_SIZE]))
            readAddr += TILE_DATA_SIZE

        h = []  # 水平方向に結合したタイルを格納するリスト
        for i in range(tileY):
            h.append(np.hstack([tile.imgArray for tile in tileList[tileX*i:tileX*i+tileX]]))
        self.mapArray = np.vstack(h)
        self.pilImage = Image.fromarray(self.mapArray)  # 色情報の行列から画像を生成（PILのImage形式）
        self.mapImg = QtGui.QImage(self.mapArray, TILE_WIDTH*tileX, TILE_HEIGHT*tileY, QtGui.QImage.Format_Indexed8)


    def getImage(self):
        """ QImage形式のマップ画像を返す
        """
        return self.mapImg


    def getPilImage(self):
        """ PIL形式のマップ画像を返す
        """
        return self.pilImage


def saveSceneImage(graphicsScene):
    """ QGraphicsSceneを画像として保存する
    """

    sourceBounds = graphicsScene.itemsBoundingRect()    # シーン内の全てのアイテムから領域を算出
    image = QtGui.QImage(QtCore.QSize(sourceBounds.width(), sourceBounds.height()), QtGui.QImage.Format_ARGB32)
    image.fill(QtGui.QColor(0, 0, 0, 0).rgba()) # 初期化されていないのでfillしないとノイズが入る（えぇ・・・）
    targetBounds = QtCore.QRectF(image.rect())
    painter = QtGui.QPainter(image)
    graphicsScene.render(painter, targetBounds, sourceBounds)
    painter.end()

    filename = QtWidgets.QFileDialog.getSaveFileName(None, _("シーンを画像として保存"), os.path.expanduser('./'), _("image File (*.png)"))[0]
    try:
        with open(filename, 'wb') as saveFile:
            image.save(filename, "PNG")
            logger.info("ファイルを保存しました")
    except OSError:
        logger.info("ファイルの保存をキャンセルしました")


def gba2rgb(gbaColor):
    """ GBAの色情報からRGB値に変換する
    """

    binColor = bin(int.from_bytes(gbaColor, "little"))[2:].zfill(16) # GBAのオブジェクトは15bitカラー（0BBBBBGGGGGRRRRR）
    logger.debug(binColor)
    b = int(binColor[1:6], 2) * 8  #   文字列化されているので数値に直す（255階調での近似色にするため8倍する）
    g = int(binColor[6:11], 2) * 8
    r = int(binColor[11:16], 2) * 8

    return [r, g, b]


def rgb2gba(r, g, b):
    """ RBGからGBAの16bitカラー情報に変換する
    """

    binR = bin(r//8)[2:].zfill(5)    # 5bitカラーに変換
    binG = bin(g//8)[2:].zfill(5)
    binB = bin(b//8)[2:].zfill(5)
    gbaColor = int(binB + binG + binR, 2).to_bytes(2, "little") # GBAのカラーコードに変換

    return gbaColor


def loadData(message):
    """ ファイルからバイナリデータを読み込む
    """
    filename = QtWidgets.QFileDialog.getOpenFileName(None, _(message), os.path.expanduser('./'))[0]   # ファイル名がQString型で返される

    try:
        with open(filename, 'rb') as openFile:
            data = openFile.read()
        return data
    except OSError:
        logger.info(_("ファイルの選択をキャンセルしました"))
        return -1


def printBinary(binary):
    """ バイナリデータを見やすく出力する
    """
    baseStr = binary.hex().upper()
    for i, c in enumerate(baseStr):
        print(c, end="", flush=True)
        if i % 2 == 1: print(" ", end="")
        if i % 32 == 31: print("")


def parsePaletteData(romData, palAddr):
    """ パレットデータの読み取り

        入力：ROMデータ，パレットのアドレス
        処理：ROMデータからのパレット読み込み、RGBAカラー化
        出力：QImage用のカラーテーブル
    """
    PALETTE_SIZE = 0x20
    COLOR_SIZE = 2

    readAddr = palAddr
    endAddr = readAddr + PALETTE_SIZE

    palData = []
    while readAddr < endAddr:
        color = romData[readAddr:readAddr+COLOR_SIZE]
        logger.debug(hex(int.from_bytes(color, "little")))

        [r, g, b] = gba2rgb(color)
        logger.debug("R:" + str(r) + " G:" + str(g) + " B:" + str(b))

        if len(palData) == 0:
            palData.append(QtGui.qRgba(r, g, b, 0)) # 最初の色は透過色
        else:
            palData.append(QtGui.qRgba(r, g, b, 255))

        readAddr += COLOR_SIZE

    return palData


if __name__ == '__main__':
    filepath = sys.argv[1]
    with open(filepath, "rb") as romFile:
        romData = romFile.read()
    startAddr = 0x708774
    palAddr = 0x709DF4

    tileX = 9   # X方向のタイルの枚数
    tileY = 2
    IMG_DATA_SIZE = tileX * tileY * 0x20

    app = QtWidgets.QApplication(sys.argv)

    binMapData = romData[startAddr:startAddr+IMG_DATA_SIZE]
    gbaMap = GbaMap(binMapData, tileX, tileY)
    colorTable = parsePaletteData(romData, palAddr)

    mapImg = gbaMap.getImage()
    mapImg.setColorTable(colorTable)
    pixmap = QtGui.QPixmap.fromImage(mapImg)
    screen = QtWidgets.QLabel()
    screen.setPixmap(pixmap)
    screen.show()
    sys.exit(app.exec_())
