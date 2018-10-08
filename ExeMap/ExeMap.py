""" EXE Map

    今は日本語版グレイガ専用です。
"""
# pylint: disable=c-extension-no-member, import-error

import argparse
import logging
import sys
from PyQt5 import QtWidgets, QtGui, QtCore
import exe_map_settings as settings
import UI_ExeMap as Designer
import CommonAction as Common
import compress
import LZ77Util


""" ロギング設定 """
STREAM_HANDLER = logging.StreamHandler()
STREAM_HANDLER.setLevel(logging.DEBUG)
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
LOGGER.addHandler(STREAM_HANDLER)

""" パーサ設定 """
PARSER = argparse.ArgumentParser(description=settings.PROGRAM_NAME)
PARSER.add_argument('-f', '--file', help='開くROMファイル')
ARGS = PARSER.parse_args()


class ExeMap(QtWidgets.QMainWindow):
    """ EXE Map
    """
    def __init__(self, parent=None):
        """ init
        """
        super(ExeMap, self).__init__(parent)
        self.ui = Designer.Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle(settings.PROGRAM_NAME)
        self.setWindowIcon(QtGui.QIcon('bug.png'))
        self.graphics_scene = QtWidgets.QGraphicsScene(self)
        self.ui.graphicsView.setScene(self.graphics_scene)
        self.ui.graphicsView.scale(1, 1)
        self.graphics_group_bg1 = QtWidgets.QGraphicsItemGroup()
        self.graphics_group_bg2 = QtWidgets.QGraphicsItemGroup()
        self.current_map = None
        self.bin_map_bg = b''

        with open('ROCKEXE6_GXX.gba', 'rb') as bin_file:
            self.bin_data = bin_file.read()

        self.map_entry_list = self.init_map_entry_list()
        self.draw(self.map_entry_list[0])

    def init_map_entry_list(self):
        """ マップリストの初期化
        """
        map_entries = split_by_size(self.bin_data[settings.MAP_ENTRY_START:
                                                  settings.MAP_ENTRY_END], settings.MAP_ENTRY_SIZE)
        map_entry_list = []
        self.ui.mapList.clear()

        for bin_map_entry in map_entries:
            tileset = int.from_bytes(bin_map_entry[0:4], 'little')
            if tileset == 0:  # テーブル内に電脳とインターネットの区切りがあるので除去
                continue

            map_entry = ExeMapEntry(bin_map_entry, self.bin_data)
            map_entry_list.append(map_entry)
            item = QtWidgets.QListWidgetItem(hex(map_entry.tilemap))
            self.ui.mapList.addItem(item)

        return map_entry_list

    def map_entry_selected(self):
        """ マップリストのアイテムがダブルクリックされたときの処理
        """
        index = self.ui.mapList.currentRow()
        self.current_map = self.map_entry_list[index]
        self.ui_map_attribute_update()
        self.draw(self.current_map)

    def ui_map_attribute_update(self):
        self.ui.widthValueLabel.setText(str(self.current_map.width) + ' tile')
        self.ui.heightValueLabel.setText(str(self.current_map.width) + ' tile')
        self.ui.tileMapValueLabel.setText(hex(self.current_map.tilemap_offset))

    def draw(self, map_entry):
        """ マップの描画
        """
        # パレットの更新
        bin_palette = self.bin_data[map_entry.palette_offset: map_entry.palette_offset+0x200]
        palette_list = []
        if map_entry.color_mode == 0:
            for bin_palette in split_by_size(bin_palette, 0x20):
                palette_list.append(Common.GbaPalette(bin_palette))
        elif map_entry.color_mode == 1:
            palette_list.append(Common.GbaPalette(bin_palette, settings.COLOR_NUM_256))

        # GUIのパレットテーブルの更新
        self.ui.paletteTable.clear()
        for row, palette in enumerate(palette_list):
            for col, color in enumerate(palette.color):
                item = QtWidgets.QTableWidgetItem()
                brush = QtGui.QBrush(QtGui.QColor(color.r, color.g, color.b))
                brush.setStyle(QtCore.Qt.SolidPattern)
                item.setBackground(brush)
                if map_entry.color_mode == 0:
                    self.ui.paletteTable.setItem(row, col % settings.COLOR_NUM_16, item)
                elif map_entry.color_mode == 1:
                    self.ui.paletteTable.setItem(col // settings.COLOR_NUM_16,
                                                 col % settings.COLOR_NUM_16, item)

        # タイルの処理
        bin_tileset_1 = LZ77Util.decompLZ77_10(self.bin_data, map_entry.tileset_offset_1)
        bin_tileset_2 = LZ77Util.decompLZ77_10(self.bin_data, map_entry.tileset_offset_2)
        bin_tileset = bin_tileset_1 + bin_tileset_2
        char_base = []

        if map_entry.color_mode == 0:
            for bin_char in split_by_size(bin_tileset, settings.TILE_DATA_SIZE_16):
                char_base.append(Common.GbaTile(bin_char))
        elif map_entry.color_mode == 1:
            for bin_char in split_by_size(bin_tileset, settings.TILE_DATA_SIZE_256):
                char_base.append(Common.GbaTile(bin_char, settings.COLOR_NUM_256))

        for i, char in enumerate(char_base):
            # タイルセットリストの表示
            item = QtWidgets.QTableWidgetItem()
            if map_entry.color_mode == 0:
                char.image.setColorTable(palette_list[1].get_qcolors())
            elif map_entry.color_mode == 1:
                char.image.setColorTable(palette_list[0].get_qcolors())
            tile_image = QtGui.QPixmap.fromImage(char.image)
            item.setIcon(QtGui.QIcon(tile_image))
            self.ui.tilesetTable.setItem(i // settings.COLOR_NUM_16,
                                         i % settings.COLOR_NUM_16, item)

        self.bin_map_bg = LZ77Util.decompLZ77_10(self.bin_data, map_entry.tilemap_offset)
        self.draw_map(map_entry, char_base, palette_list)

    def draw_map(self, map_entry, char_base, palette_list):
        """ GraphicsViewにマップを描画する

        :param map_entry:
        :param char_base:
        :param palette_list:
        :return:
        """
        self.graphics_scene.clear()
        self.graphics_group_bg1 = QtWidgets.QGraphicsItemGroup()
        self.graphics_group_bg2 = QtWidgets.QGraphicsItemGroup()
        for i, tile_entry in enumerate(split_by_size(self.bin_map_bg, 2)):
            # タイルマップに基づいてタイルを描画
            attribute = bin(int.from_bytes(tile_entry, 'little'))[2:].zfill(16)
            palette_num = int(attribute[:4], 2)
            flip_v = int(attribute[4], 2)
            flip_h = int(attribute[5], 2)
            tile_num = int(attribute[6:], 2)

            if map_entry.color_mode == 0:
                char_base[tile_num].image.setColorTable(palette_list[palette_num].get_qcolors())

            tile_image = QtGui.QPixmap.fromImage(char_base[tile_num].image)
            if flip_h == 1:
                tile_image = tile_image.transformed(QtGui.QTransform().scale(-1, 1))
            if flip_v == 1:
                tile_image = tile_image.transformed(QtGui.QTransform().scale(1, -1))
            item = QtWidgets.QGraphicsPixmapItem(tile_image)
            item.ItemIsSelectable = True
            item.ItemIsMovable = True
            item.setOffset(i % map_entry.width * 8, i // map_entry.width % map_entry.height * 8)
            bg = i // (map_entry.width * map_entry.height)
            if bg == 0:
                self.graphics_group_bg1.addToGroup(item)
            elif bg == 1:
                self.graphics_group_bg2.addToGroup(item)

        self.graphics_scene.addItem(self.graphics_group_bg1)
        self.graphics_scene.addItem(self.graphics_group_bg2)

    def bg1_visible_changed(self, state):
        """ BG1の表示切り替え
        """
        self.graphics_group_bg1.setVisible(state)

    def bg2_visible_changed(self, state):
        """ BG2の表示切り替え
        """
        self.graphics_group_bg2.setVisible(state)

    def movement_visible_changed(self):
        """

        :return:
        """
        pass

    def rubber_band_changed(self, select_rect):
        """

        :param select_rect:
        :return:
        """
        items = self.ui.graphicsView.items(select_rect)
        LOGGER.debug(items)


class ExeMapEntry:
    """ EXE Map Entry
    """
    def __init__(self, bin_map_entry, bin_rom_data):
        self.bin_map_entry = bin_map_entry
        tileset, palette, tilemap = [int.from_bytes(offset, 'little')
                                     for offset in split_by_size(bin_map_entry, 4)]

        self.tileset = tileset - settings.MEMORY_OFFSET
        self.tilemap = tilemap - settings.MEMORY_OFFSET
        self.palette = palette - settings.MEMORY_OFFSET

        self.width = bin_rom_data[self.tilemap]
        self.height = bin_rom_data[self.tilemap + 1]
        self.palette_offset = self.palette + 0x4
        self.tileset_offset_1 = self.tileset + 0x18
        self.tileset_offset_2 = self.tileset + int.from_bytes(
            bin_rom_data[self.tileset + 0x10: self.tileset + 0x14], 'little')
        self.color_mode = bin_rom_data[self.tilemap + 2]  # おそらく（0: 16色、1: 256色）
        self.tilemap_offset = self.tilemap + 0xC


def split_by_size(data, size):
    """ 文字列をn文字ずつに分割したリストを返す

    :param data:
    :param size:
    :return:
    """
    return [data[i:i+size] for i in [i for i in range(0, len(data), size)]]


if __name__ == '__main__':
    APP = QtWidgets.QApplication(sys.argv)
    WINDOW = ExeMap()
    WINDOW.show()
    sys.exit(APP.exec_())
