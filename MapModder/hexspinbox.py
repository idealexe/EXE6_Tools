#!/usr/bin/python
# coding: utf-8

from PyQt4 import QtGui

u""" Hex Spin Box

    QSpinBoxを16進数表示にしたやつ
"""
class HexSpinBox(QtGui.QSpinBox):
    def __init__(self, parent=None):
        super(HexSpinBox, self).__init__(parent)    # HexSpinBoxが継承しているQSpinBoxのコンストラクタを呼ぶ

    def textFromValue(self, value):
        return hex(value)

    def valueFromText(self, text):
        return int(16, text)
