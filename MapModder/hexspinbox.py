#!/usr/bin/python
# coding: utf-8

from PyQt5 import QtCore, QtGui, QtWidgets

u""" Hex Spin Box

    QSpinBoxを16進数表示にしたやつ
"""
class HexSpinBox(QtWidgets.QSpinBox):
    def __init__(self, parent=None):
        super(HexSpinBox, self).__init__(parent)    # HexSpinBoxが継承しているQSpinBoxのコンストラクタを呼ぶ
        self.validator = QtGui.QRegExpValidator(QtCore.QRegExp('0x[0-9A-Fa-f]{1,8}'))   # 8ケタまでの16進数を入力として許可

    def textFromValue(self, value):
        return hex(value)[2:].upper()

    def valueFromText(self, text):
        value = int(str(text), 16)
        return value

    def validate(self, text, pos):
        return self.validator.validate(text, pos)
