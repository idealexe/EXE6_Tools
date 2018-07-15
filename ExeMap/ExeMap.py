import os
import sys
import UI_ExeMap as designer
from PyQt5 import QtWidgets, QtGui, QtCore

sys.path.append(os.path.join(os.path.dirname(__file__), "../common/"))
import CommonAction as common
import LZ77Util


PROGRAM_NAME = "EXE MAP  ver 0.2"
TILESET = 0x60a834
TILEMAP = 0x60e054
PALETTE = 0x60dea8
MAP_SIZE = 168
""" タイルセットのアドレスはメモリに展開されたタイルセットデータをLZ77圧縮し、その一部をROM内を検索して特定
    特定したタイルセットアドレスを使ってタイルセットを読み込む処理を特定（r0 = 0x5E0724）
        タイルセットアドレスはr0: 0x18 + r6: 0x85E070Cで作られている
    タイルセットのLZ77展開は0x0815A2D8（ブレーク位置からF7で特定）
    タイルセットを展開した後タイルコントロールも展開するだろうと見てLZ77展開をブレークポイントに設定、
    ブレーク時のr0を確認してタイルセットのアドレスに近いものをタイルコントロールのアドレスとして設定してみていくつか試行して特定成功
    →現時点での特定方法：0x0815A2D8をブレークポイントに設定、エリアを移動して4回目のブレーク時のr0がタイルセットのアドレス、6回目のブレーク時のr0がタイルコントロール
"""


class ExeMap(QtWidgets.QMainWindow):
    """ EXE Map
    """
    def __init__(self, parent=None):
        super(ExeMap, self).__init__(parent)
        self.ui = designer.Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle(PROGRAM_NAME)
        self.graphicsScene = QtWidgets.QGraphicsScene(self)
        self.ui.graphicsView.setScene(self.graphicsScene)
        self.ui.graphicsView.scale(1, 1)

        with open('ROCKEXE6_GXX.gba', 'rb') as bin_file:
            self.bin_data = bin_file.read()

        bin_palette_background = self.bin_data[PALETTE:PALETTE+0x200]
        palette_background = []
        for bin_palette in split_by_size(bin_palette_background, 0x20):
            palette_background.append(common.GbaPalette(bin_palette))

        for row, palette in enumerate(palette_background):
            for col, color in enumerate(palette.color):
                item = QtWidgets.QTableWidgetItem()
                brush = QtGui.QBrush(QtGui.QColor(color.r, color.g, color.b))
                brush.setStyle(QtCore.Qt.SolidPattern)
                item.setBackground(brush)
                self.ui.backgroundPaletteTable.setItem(row, col % 16, item)

        bin_char_base = LZ77Util.decompLZ77_10(self.bin_data, TILESET)
        char_base = []
        for bin_char in split_by_size(bin_char_base, 0x20):
            char_base.append(common.GbaTile(bin_char))

        for i, char in enumerate(char_base):
            item = QtWidgets.QTableWidgetItem()
            char.image.setColorTable(palette_background[1].get_qcolors())
            tile_image = QtGui.QPixmap.fromImage(char.image)
            item.setIcon(QtGui.QIcon(tile_image))
            self.ui.tilesetTable.setItem(i // 16, i % 16, item)

        bin_map_bg1 = LZ77Util.decompLZ77_10(self.bin_data, TILEMAP)
        for i, map_entry in enumerate(split_by_size(bin_map_bg1, 2)):
            attribute = bin(int.from_bytes(map_entry, 'little'))[2:].zfill(16)
            palette_num = int(attribute[:4], 2)
            flip_v = int(attribute[4], 2)
            flip_h = int(attribute[5], 2)
            tile_num = int(attribute[6:], 2)
            if tile_num >= len(char_base):
                # TODO: 存在しないタイル番号を指定しているマップデータの調査
                tile_num = 0
            char_base[tile_num].image.setColorTable(palette_background[palette_num].get_qcolors())
            tile_image = QtGui.QPixmap.fromImage(char_base[tile_num].image)
            if flip_h == 1:
                tile_image = tile_image.transformed(QtGui.QTransform().scale(-1, 1))
            if flip_v == 1:
                tile_image = tile_image.transformed(QtGui.QTransform().scale(1, -1))
            item = QtWidgets.QGraphicsPixmapItem(tile_image)
            item.setOffset(i % MAP_SIZE * 8, i // MAP_SIZE * 8)
            self.graphicsScene.addItem(item)


def split_by_size(data, size):
    """ 文字列をn文字ずつに分割したリストを返す

    :param data:
    :param size:
    :return:
    """
    return [data[i:i+size] for i in [i for i in range(0, len(data), size)]]


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = ExeMap()
    window.show()
    sys.exit(app.exec_())
