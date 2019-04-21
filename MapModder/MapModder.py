#!/usr/bin/python
# coding: utf-8
# pylint: disable=C0103, E1101, I1101

""" Map Modder by ideal.exe
"""

import argparse
import binascii
import os
import re
import sys
import gettext
from logging import getLogger, StreamHandler, INFO
from PyQt5 import QtGui, QtWidgets
import pandas as pd
import UI_MapModder as designer

sys.path.append(os.path.join(os.path.dirname(__file__), "../common"))
import CommonAction as commonAction

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(INFO)
logger.setLevel(INFO)
logger.addHandler(handler)

parser = argparse.ArgumentParser(description="")
parser.add_argument("-f", "--file", help="処理対象のファイル")
args = parser.parse_args()

PROGRAM_NAME = "Map Modder  ver 0.5  by ideal.exe"
LIST_FILE_PATH = \
    os.path.join(os.path.dirname(__file__), "lists/")  # プログラムと同ディレクトリにあるlistsフォルダ下にリストを保存する
_ = gettext.gettext  # 後の翻訳用


class MapModder(QtWidgets.QMainWindow):
    """ Map Modder
    """
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.ui = designer.Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle(PROGRAM_NAME)
        self.ui.graphicsView.scale(2, 2)
        self.graphicsScene = QtWidgets.QGraphicsScene(self)
        self.graphicsScene.setSceneRect(-120, -80, 240, 160)    # gbaの画面を模したシーン（ ビューの中心が(0,0)になる ）
        self.ui.graphicsView.setScene(self.graphicsScene)
        self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__),
                                                    "../resources/bug.png")))

        self.romData = b""
        self.label = ""
        self.addr = 0
        self.palAddr = 0
        self.tileX = self.ui.xTileBox.value()
        self.tileY = self.ui.yTileBox.value()

    def update_image(self):
        """ 画像を更新する
        """
        self.palData = self.parsePaletteData(self.romData, self.palAddr)
        self.colorTable = commonAction.parsePaletteData(self.romData, self.palAddr)
        image = self.make_map_image(self.romData, self.addr,
                                    self.tileX, self.tileY, self.colorTable)
        self.drawMap(image)

    def open_file(self, filename=""):
        """ ファイルを開くときの処理
        """

        if filename is False:
            filename = QtWidgets.QFileDialog.getOpenFileName(self, _("Open File"),
                                                             os.path.expanduser('./'))[0]   # ファイル名がQString型で返される
        self.openedFileName = filename  # 保存時にパスを利用したいので

        try:
            with open(filename, 'rb') as romFile:
                self.romData = romFile.read()
        except OSError:
            logger.info(_("ファイルの選択をキャンセルしました"))
            return -1    # 中断

        [title, code] = self.getRomHeader(self.romData)
        list_name = code + "_" + title + ".csv"

        if os.path.exists(LIST_FILE_PATH + list_name):
            self.list_data = self.loadListFile(list_name)
        else:
            df = pd.DataFrame({
                "label":[],
                "addr":[],
                "palAddr":[],
                "width":[],
                "height":[],
                "comp":[]
            }, columns=['label', 'addr', 'palAddr', 'width', 'height', 'comp'])    # 並び順を指定
            df.to_csv(LIST_FILE_PATH + list_name, encoding="utf-8", index=False)
            print("リストファイルを作成しました")
            self.list_data = df
            self.ui.dataList.clear()

    def loadListFile(self, listName):
        """ リストファイルの読み込み

            GUIのリストをセットアップしpandas形式のリストを返す
        """
        self.ui.dataList.clear()
        list_data = pd.read_csv(LIST_FILE_PATH + listName, encoding="utf-8", index_col=None)
        logger.debug(list_data)

        for i, data in list_data.iterrows():
            data_str = str(i) + ". " + data["label"]    # GUIのリストに表示する文字列
            item = QtWidgets.QListWidgetItem(data_str)  # リストに追加するアイテムの生成
            self.ui.dataList.addItem(item)  # リストへ追加

        logger.info("リストファイルを読み込みました")
        return list_data

    def getRomHeader(self, rom_data):
        """ ヘッダ情報の取得
        """
        title = rom_data[0xA0:0xAC].decode("utf-8")
        code = rom_data[0xAC:0xB0].decode("utf-8")
        print("Title:\t" + title)
        print("Code:\t" + code)
        return [title, code]

    def drawMap(self, image):
        """ マップ画像を描画する
        """
        self.graphicsScene.clear()
        item = QtWidgets.QGraphicsPixmapItem(image)
        item.setOffset(image.width()/2*-1, image.height()/2*-1)
        #imageBounds = item.boundingRect()
        self.graphicsScene.addItem(item)
        #self.graphicsScene.addRect(imageBounds)

    def parsePaletteData(self, rom_data, palAddr):
        """ パレットデータの読み取り

            入力：ROMデータ，パレットのアドレス
            処理：ROMデータからのパレット読み込み，GUIのパレットリスト更新，RGBAカラー化
        """
        PALETTE_SIZE = 0x20
        COLOR_SIZE = 2

        readAddr = palAddr
        endAddr = readAddr + PALETTE_SIZE

        pal_data = []    # パレットデータを格納するリスト
        self.ui.palList.clear()
        pal_count = 0
        while readAddr < endAddr:
            color = rom_data[readAddr:readAddr + COLOR_SIZE]

            [r, g, b] = commonAction.gba2rgb(color)

            if pal_count == 0:
                pal_data.append({"color": [r, g, b, 0], "addr": readAddr})  # 最初の色は透過色
            else:
                pal_data.append({"color": [r, g, b, 255], "addr": readAddr})

            color_str = hex(int.from_bytes(color, "little"))[2:].zfill(4).upper() + \
                            "\t(" + str(r).rjust(3) + \
                            ", " + str(g).rjust(3) + \
                            ", " + str(b).rjust(3) + ")"  # GUIに表示する文字列
            color_item = QtWidgets.QListWidgetItem(color_str)
            color_item.setBackground(QtGui.QColor(r, g, b))  # 背景色をパレットの色に
            color_item.setForeground(QtGui.QColor(255-r, 255-g, 255-b))    # 文字は反転色
            self.ui.palList.addItem(color_item)  # フレームリストへ追加

            pal_count += 1
            readAddr += COLOR_SIZE

        return pal_data

    def guiDataItemActivated(self):
        """ 登録データが選択されたときの処理
        """
        if self.getCrrentItemData() is False:
            return

        [self.label, self.addr, self.palAddr, self.tileX, self.tileY] = self.getCrrentItemData()

        self.ui.labelEdit.setText(self.label)
        self.ui.addrBox.setValue(self.addr)
        self.ui.palAddrBox.setValue(self.palAddr)
        self.ui.xTileBox.setValue(self.tileX)
        self.ui.yTileBox.setValue(self.tileY)

        self.update_image()

    def getCrrentItemData(self):
        """ 現在の行のアイテム情報を返す
        """
        index = self.ui.dataList.currentRow()
        if index == -1:
            return False

        logger.debug("index:\t" + str(index))
        logger.debug(self.list_data)

        label = self.list_data["label"][index]
        addr = int(self.list_data["addr"][index], 16)
        palAddr = int(self.list_data["palAddr"][index], 16)
        tile_x = int(self.list_data["width"][index])
        tile_y = int(self.list_data["height"][index])

        return [label, addr, palAddr, tile_x, tile_y]

    def guiAddrChanged(self, value):
        """ アドレスが更新されたときの処理
        """
        logger.debug("Addr Changed")
        self.addr = self.ui.addrBox.value()
        self.update_image()

    def guiAddrStepChanged(self, n):
        """ アドレスのステップ数の変更
        """
        self.ui.addrBox.setSingleStep(n)

    def guiNextMapPressed(self):
        """ 次のマップらしきものを表示する

            現在のマップと同じサイズだけアドレスを移動するだけ（ついでにパレットも切り替える）
        """
        self.addr += self.tileX * self.tileY * 32
        self.ui.addrBox.setValue(self.addr)
        self.palAddr += self.ui.palAddrStep.value()
        self.ui.palAddrBox.setValue(self.palAddr)
        self.update_image()

    def guiPrevMapPressed(self):
        """ 前のマップらしきものを表示する

            現在のマップと同じサイズだけアドレスを移動するだけ
        """
        self.addr -= self.tileX * self.tileY * 32
        self.ui.addrBox.setValue(self.addr)
        self.palAddr -= self.ui.palAddrStep.value()
        self.ui.palAddrBox.setValue(self.palAddr)
        self.update_image()

    def guiPalAddrChanged(self):
        """ パレットアドレスが更新されたときの処理
        """
        logger.debug("Palette Addr Changed")
        self.palAddr = self.ui.palAddrBox.value()
        self.ui.palAddrBox.setValue(self.palAddr)
        #self.ui.palAddrBox.lineEdit().setText(hex(self.palAddr))
        logger.debug(hex(self.palAddr))
        self.update_image()

    def guiPalAddrStepChanged(self, n):
        """ パレットアドレスのステップ数の変更
        """
        self.ui.palAddrBox.setSingleStep(n)

    def guiPalItemActivated(self):
        """ GUIで色が選択されたときに行う処理
        """
        COLOR_SIZE = 2

        index = self.ui.palList.currentRow()
        if index == -1:
            return -1

        r, g, b, a = self.palData[index]["color"]   # 選択された色の値をセット
        writePos = self.palData[index]["addr"]  # 色データを書き込む位置
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(r, g, b))    # カラーダイアログを開く
        if color.isValid() is False: # キャンセルしたとき
            logger.info("色の選択をキャンセルしました")
            return 0

        r, g, b, a = color.getRgb()    # ダイアログでセットされた色に更新

        gbaColor = commonAction.rgb2gba(r, g, b)
        self.romData = self.romData[:writePos] + gbaColor + self.romData[writePos+COLOR_SIZE:]
        self.update_image()

    def guiTileXChanged(self, n):
        """ GUIでタイルXが変更されたとき
        """
        self.tileX = n
        self.update_image()

    def guiTileYChanged(self, n):
        """ GUIでタイルYが変更されたとき
        """
        self.tileY = n
        self.update_image()

    def guiRegButtonPressed(self):
        """ 登録ボタンが押されたときの処理
        """
        [title, code] = self.getRomHeader(self.romData)
        list_name = code + "_" + title + ".csv"

        label = self.ui.labelEdit.text()
        addr = self.ui.addrBox.value()
        palAddr = self.ui.palAddrBox.value()
        width = self.ui.xTileBox.value()
        height = self.ui.yTileBox.value()

        se = pd.Series([label, hex(addr), hex(palAddr), width, height, 0],
                       index=self.list_data.columns)
        self.list_data = self.list_data.append(se, ignore_index=True).sort_values(by=["palAddr"], ascending=True).reset_index(drop=True)  # 追加してソート
        logger.debug(self.list_data)
        self.list_data.to_csv(LIST_FILE_PATH + list_name, encoding="utf-8", index=False)
        logger.info("リストに登録しました")
        self.loadListFile(list_name)

    def save_file(self):
        """ ファイルの保存
        """
        filename = QtWidgets.QFileDialog.getSaveFileName(self, _("ROMを保存する"), os.path.expanduser(os.path.dirname(self.openedFileName)), _("Rom File (*.gba *.bin)"))[0]
        try:
            with open(filename, 'wb') as saveFile:
                saveFile.write(self.romData)
                logger.info("ファイルを保存しました")
        except OSError:
            logger.info("ファイルの保存をキャンセルしました")

    def change_view_scale(self, value):
        """ ビューを拡大縮小する
        """
        self.ui.graphicsView.resetTransform()   # 一度オリジナルサイズに戻す
        scale = pow(2, value/10.0)   # 指数で拡大したほうが自然にスケールしてる感じがする
        self.ui.graphicsView.scale(scale, scale)

    def search_binary(self):
        """ データを検索する
        """
        search_text = str(self.ui.searchEdit.text())
        logger.info("Search Text:\t" + search_text)

        try:
            search_value = binascii.unhexlify(search_text)   # "0a" -> 0x0A
        except:
            logger.warning("入力はバイト列として解釈できるテキストのみ受けつけます")
            return -1

        logger.info("Search Value:\t" + str(search_value))

        self.ui.searchBrowser.clear()
        pattern = re.compile(re.escape(search_value))   # エスケープが必要な文字（0x3f = "?" とか）が含まれている可能性がある
        match_iter = re.finditer(pattern, self.romData)

        count = 0
        for m in match_iter:
            logger.debug(hex(m.start()))
            result_text = hex(m.start())
            self.ui.searchBrowser.append(result_text)
            count += 1
            if count >= 100:
                logger.info("マッチ結果が多すぎます．100件以降は省略しました")
                return -1

    def save_image_file(self):
        """ 画像を保存する
        """
        commonAction.saveSceneImage(self.graphicsScene)

    def make_map_image(self, rom_data, start_addr, tile_x, tile_y, color_table, flip_v=0, flip_h=0):
        """ QPixmap形式の画像を生成する
        """
        TILE_WIDTH = 8  # px
        TILE_HEIGHT = 8
        TILE_DATA_SIZE = TILE_WIDTH * TILE_HEIGHT // 2  # 1タイルあたりのデータサイズ（python3で整数値の除算結果を得るには//を使う）

        logger.debug("Image Width:\t" + str(tile_x * TILE_WIDTH) + "px")
        logger.debug("Image Height:\t" + str(tile_y * TILE_HEIGHT) + "px")

        imgDataSize = TILE_DATA_SIZE * tile_x * tile_y

        imgData = rom_data[start_addr:start_addr + imgDataSize]   # 使う部分を切り出し
        gbaMap = commonAction.GbaMap(imgData, tile_x, tile_y)
        """
        dataImg = Image.fromarray(np.uint8(img))  # 色情報の行列から画像を生成（PILのImage形式）
        if flipH == 1:
            dataImg = dataImg.transpose(Image.FLIP_LEFT_RIGHT)  # PILの機能で水平反転
        if flipV == 1:
            dataImg = dataImg.transpose(Image.FLIP_TOP_BOTTOM)
        """
        qimage = gbaMap.getImage()
        qimage.setColorTable(color_table)
        pixmap = QtGui.QPixmap.fromImage(qimage)  # QPixmap形式に変換
        return pixmap


def main():
    """ Main
    """
    app = QtWidgets.QApplication(sys.argv)

    map_modder = MapModder()
    map_modder.show()

    logger.debug(args.file)
    if args.file is not None:
        map_modder.open_file(args.file)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
