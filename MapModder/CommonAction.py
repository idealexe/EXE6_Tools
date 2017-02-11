#!/usr/bin/python
# coding: utf-8

u""" Common Action

    共用できるアクションをまとめたモジュール
"""

from PyQt4 import QtCore, QtGui

from logging import getLogger,StreamHandler,INFO,DEBUG
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

    filename = QtGui.QFileDialog.getSaveFileName(None, _(u"シーンを画像として保存"), os.path.expanduser('./'), _("image File (*.png)"))
    try:
        with open( unicode(filename), 'wb') as saveFile:
            image.save(filename, "PNG")
            logger.info(u"ファイルを保存しました")
    except:
        logger.info(u"ファイルの保存をキャンセルしました")
