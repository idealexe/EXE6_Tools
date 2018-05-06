#!/usr/bin/python
# coding: utf-8
# pylint: disable=C0103, E1101

""" Common Action  by ideal.exe

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
TILE_DATA_SIZE = TILE_WIDTH * TILE_HEIGHT // 2  # 1タイルあたりのデータサイズ（1バイトで2ドット）


class GbaTile:
    """ GBAのタイル

        20バイトのバイナリデータから8x8(px)、16色のビットマップを作成する
    """

    def __init__(self, bin_tile_data):
        self.bin_tile_data = bin_tile_data

        dot_list = list(bin_tile_data.hex().upper())
        dot_list = [int(i, 16) for i in dot_list]
        # ドットの描画順（0x01 0x23 0x45 0x67 -> 10325476）に合わせて入れ替え
        for i in range(0, len(dot_list))[0::2]:  # 偶数だけ取り出す（0から+2ずつ）
            dot_list[i], dot_list[i+1] = dot_list[i+1], dot_list[i]  # これで値を入れ替えられる

        img_array = np.array(dot_list, dtype=np.uint8).reshape((TILE_WIDTH, TILE_HEIGHT))
        self.img_array = img_array
        self.image = QtGui.QImage(img_array, TILE_WIDTH, TILE_HEIGHT, QtGui.QImage.Format_Indexed8)

    def get_bin_tile_data(self):
        """ タイルのバイナリデータを返す
        """
        return self.bin_tile_data

    def get_img_array(self):
        """ np.array形式のタイルデータを返す
        """
        return self.img_array
        
    def get_qimage(self):
        """ QImage形式のタイル画像を返す
        """
        return self.image


class GbaMap:
    """ GBAのマップ
    """

    def __init__(self, bin_map_data, tile_num_x, tile_num_y):
        self.bin_map_data = bin_map_data

        tile_list = []
        read_addr = 0
        while read_addr < len(bin_map_data):
            tile_list.append(GbaTile(bin_map_data[read_addr:read_addr+TILE_DATA_SIZE]))
            read_addr += TILE_DATA_SIZE

        h = []  # 水平方向に結合したタイルを格納するリスト
        for i in range(tile_num_y):
            h.append(np.hstack([tile.img_array for tile in tile_list[tile_num_x * i:tile_num_x * i + tile_num_x]]))
        self.mapArray = np.vstack(h)
        self.pilImage = Image.fromarray(self.mapArray)  # 色情報の行列から画像を生成（PILのImage形式）
        self.mapImg = QtGui.QImage(self.mapArray, TILE_WIDTH * tile_num_x, TILE_HEIGHT * tile_num_y, QtGui.QImage.Format_Indexed8)

    def getImage(self):
        """ QImage形式のマップ画像を返す
        """
        return self.mapImg

    def getPilImage(self):
        """ PIL形式のマップ画像を返す
        """
        return self.pilImage


class GbaOam:
    """ GBAのOAM

        6バイト（16ビットx3）のデータをOAMとして解析する
    """
    def __init__(self, bin_oam_data):
        self.bin_oam_data = bin_oam_data

        attribute = list()
        attribute.append(bin_oam_data[0:2])
        attribute.append(bin_oam_data[2:4])
        attribute.append(bin_oam_data[4:6])

        self.y = bit_val(attribute[0], 0, 7)
        self.rot_scale_flag = bit_val(attribute[0], 8)  # 0=Off, 1=On
        self.size_visible_flag = bit_val(attribute[0], 9)
        self.mode = bit_val(attribute[0], 10, 11)  # 0=Normal, 1=Semi-Transparent, 2=OBJ Window, 3=Prohibited
        self.mosaic = bit_val(attribute[0], 12)
        self.color = bit_val(attribute[0], 13)  # 0=16color, 1=256color
        self.shape = bit_val(attribute[0], 14, 15)

        self.x = bit_val(attribute[1], 0, 8)
        self.flip_h = bit_val(attribute[1], 12)
        self.flip_v = bit_val(attribute[1], 13)
        self.size = bit_val(attribute[1], 14, 15)

        self.tile_num = bit_val(attribute[2], 0, 9)
        self.priority = bit_val(attribute[2], 10, 11)
        self.palette_num = bit_val(attribute[2], 12, 15)

        logger.info("X: " + str(self.x))
        logger.info("Y: " + str(self.y))
        logger.info("Tile No: " + hex(self.tile_num))
        logger.info("Flip H: " + str(self.flip_h))
        logger.info("Flip V: " + str(self.flip_v))
        logger.info("Color: " + str(self.color))
        logger.info("Palette: " + str(self.palette_num))
        logger.info("Priority: " + str(self.priority))


def bit_val(byte_num, lsb, msb=None):
    """ バイト列から指定したビットの値を取得する

    :param byte_num:
    :param lsb:
    :param msb:
    :return:
    """
    size = 8 * len(byte_num)
    bin_num = bin(int.from_bytes(byte_num, 'little'))[2:].zfill(size)

    lsb_index = size - lsb

    if msb is not None:
        msb_index = size - 1 - msb
        return int(bin_num[msb_index:lsb_index], 2)

    return int(bin_num[lsb_index-1:lsb_index], 2)


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

    filename = QtWidgets.QFileDialog.getSaveFileName(None, _("シーンを画像として保存"),
                                                     os.path.expanduser('./'), _("image File (*.png)"))[0]
    try:
        with open(filename, 'wb') as saveFile:
            image.save(filename, "PNG")
            logger.info("ファイルを保存しました")
    except OSError:
        logger.info("ファイルの保存をキャンセルしました")


def gba2rgb(gbaColor):
    """ GBAの色情報からRGB値に変換する
    """

    binColor = bin(int.from_bytes(gbaColor, "little"))[2:].zfill(16)  # GBAのオブジェクトは15bitカラー（0BBBBBGGGGGRRRRR）
    logger.debug(binColor)
    b = int(binColor[1:6], 2) * 8  # 文字列化されているので数値に直す（255階調での近似色にするため8倍する）
    g = int(binColor[6:11], 2) * 8
    r = int(binColor[11:16], 2) * 8

    return [r, g, b]


def rgb2gba(r, g, b):
    """ RBGからGBAの16bitカラー情報に変換する
    """

    binR = bin(r//8)[2:].zfill(5)    # 5bitカラーに変換
    binG = bin(g//8)[2:].zfill(5)
    binB = bin(b//8)[2:].zfill(5)
    gbaColor = int(binB + binG + binR, 2).to_bytes(2, "little")  # GBAのカラーコードに変換

    return gbaColor


def loadData(message):
    """ ファイルからバイナリデータを読み込む
    """
    filename = QtWidgets.QFileDialog.getOpenFileName(None, _(message), os.path.expanduser('./'))[0]  # ファイル名がQString型で返される

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
        if i % 2 == 1:
            print(" ", end="")
        if i % 32 == 31:
            print("")


def parsePaletteData(romData, palAddr):
    """ パレットデータの読み取り

        入力：ROMデータ，パレットのアドレス
        処理：ROMデータからのパレット読み込み、RGBAカラー化
        出力：QImage用のカラーテーブル
    """
    PALETTE_SIZE = 0x20
    COLOR_SIZE = 2

    read_addr = palAddr
    endAddr = read_addr + PALETTE_SIZE

    palData = []
    while read_addr < endAddr:
        color = romData[read_addr:read_addr+COLOR_SIZE]
        logger.debug(hex(int.from_bytes(color, "little")))

        [r, g, b] = gba2rgb(color)
        logger.debug("R:" + str(r) + " G:" + str(g) + " B:" + str(b))

        if len(palData) == 0:
            palData.append(QtGui.qRgba(r, g, b, 0))  # 最初の色は透過色
        else:
            palData.append(QtGui.qRgba(r, g, b, 255))

        read_addr += COLOR_SIZE

    return palData


if __name__ == '__main__':
    file_path = sys.argv[1]
    with open(file_path, "rb") as data:
        memory = data.read()

    GbaOam(b'\x06\x00\x12\x40\x9c\xc7')
