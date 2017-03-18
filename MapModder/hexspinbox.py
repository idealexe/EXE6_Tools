#!/usr/bin/python
# coding: utf-8

from PyQt5 import QtGui, QtWidgets

u""" Hex Spin Box

    QSpinBoxを16進数表示にしたやつ
"""
class HexSpinBox(QtWidgets.QSpinBox):
    def __init__(self, parent=None):
        super(HexSpinBox, self).__init__(parent)    # HexSpinBoxが継承しているQSpinBoxのコンストラクタを呼ぶ

    def textFromValue(self, value):
        return hex(value)[2:].upper()

    def valueFromText(self, text):
        value = int(str(text), 16)
        return value
    """
    def validate(self, input, pos):
        return (QtGui.QValidator.Acceptable, pos)
        """
