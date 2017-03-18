#!/usr/bin/python
# coding: utf-8

u""" Common Action

    共用できるアクションをまとめたモジュール
"""

from PyQt5 import QtCore, QtGui, QtWidgets

from logging import getLogger,StreamHandler,INFO
logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(INFO)
logger.setLevel(INFO)
logger.addHandler(handler)

import gettext
_ = gettext.gettext

import os


def saveSceneImage(graphicsScene):
    u""" QGraphicsSceneを画像として保存する
    """

    sourceBounds = graphicsScene.itemsBoundingRect()    # シーン内の全てのアイテムから領域を算出
    image = QtGui.QImage( QtCore.QSize(sourceBounds.width(), sourceBounds.height()), QtGui.QImage.Format_ARGB32)
    image.fill(QtGui.QColor(0, 0, 0, 0).rgba()) # 初期化されていないのでfillしないとノイズが入る（えぇ・・・）
    targetBounds = QtCore.QRectF( image.rect() )
    painter = QtGui.QPainter(image)
    graphicsScene.render(painter, targetBounds, sourceBounds)
    painter.end()

    filename = QtWidgets.QFileDialog.getSaveFileName(None, _(u"シーンを画像として保存"), os.path.expanduser('./'), _("image File (*.png)"))[0]
    try:
        with open( filename, 'wb') as saveFile:
            image.save(filename, "PNG")
            logger.info(u"ファイルを保存しました")
    except:
        logger.info(u"ファイルの保存をキャンセルしました")
        

def gba2rgb(gbaColor):
    """ GBAの色情報からRGB値に変換する
    """

    binColor = bin( int.from_bytes(gbaColor, "little") )[2:].zfill(16) # GBAのオブジェクトは15bitカラー（0BBBBBGGGGGRRRRR）
    logger.debug(binColor)
    b = int( binColor[1:6], 2 ) * 8  #   文字列化されているので数値に直す（255階調での近似色にするため8倍する）
    g = int( binColor[6:11], 2 ) * 8
    r = int( binColor[11:16], 2 ) * 8

    return [r, g, b]
