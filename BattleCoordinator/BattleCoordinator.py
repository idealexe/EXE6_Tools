#!/usr/bin/python
# coding: utf-8

""" EXE6 Battle Coordinator  by ideal.exe

    バトルデータの再利用可能なテキストベースでの管理を目指すツール

    使い方
    * DUMP_STARTとDUMP_ENDをバトルデータの範囲にあわせて設定する
    * ダンプする `>Python BattleCoordinator.py [ROMFILE] -d`
    * ダンプしたファイルから編集したいバトルデータを探す
    * バトルデータを編集する（sample.yamlを参照してください）
    * 編集したバトルデータをインポートする `>Python BattleCoordinator.py [ROMFILE] -i [BATTLE_DATA.yaml]`

    バトルデータの構造については以下を参考にしてください
    * https://www65.atwiki.jp/mmnbhack/pages/13.html
    * http://forums.therockmanexezone.com/topic/8831454/1/

"""

PROGRAM_NAME = "EXE6 Battle Coordinator  ver 0.1  by ideal.exe"

import argparse
parser = argparse.ArgumentParser(description="バトル設定を出力します")
parser.add_argument("file", help="開くROMファイル")
parser.add_argument("-d", "--dump", help="ダンプモード", action="store_true")
parser.add_argument("-i", "--importFile", help="インポートモード")
args = parser.parse_args()

from logging import getLogger,StreamHandler,INFO
logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(INFO)
logger.setLevel(INFO)
logger.addHandler(handler)

import os
import struct
import sys
import yaml

sys.path.append(os.path.join(os.path.dirname(sys.argv[0]), "../common/"))
name, ext = os.path.splitext(args.file) # ファイル名と拡張子を取得
import EXE6Dict

""" 定数
"""
BATTLE_DATA_SIZE = 0x10
MEMORY_OFFSET = 0x08000000
OBJECT_DATA_SIZE = 4
OBJECT_SEPARATOR = 0xF0

""" 設定用定数
"""
DUMP_START = 0xB2C00
DUMP_END = 0xB3CD0

""" BattleCoordinator
"""
class BattleCoordinator():
    romData = ""

    def openFile(self, filePath):
        with open( filePath, 'rb' ) as romFile:
            self.romData = romFile.read()

    def dumpBattleData(self, addr):
        comments = []
        logger.debug("@" + hex(addr) + "{")
        battleData = self.romData[addr:addr+BATTLE_DATA_SIZE]
        logger.debug("Raw Battle Data:\t" + str(battleData) )
        [field, x1, bgm, mode, background, count, area, x2, effect, objAddr] = struct.unpack("BBBBBBBBLL", battleData)
        objAddr -= MEMORY_OFFSET
        logger.debug("\t'field':" + str(field) + "," )
        logger.debug("\t'bgm':" + hex(bgm) + "," + "\t# " + EXE6Dict.MUSIC_LIST[bgm] )
        logger.debug("\t'mode':" + hex(mode) + "," )
        logger.debug("\t'bg':" + hex(background) + "," )
        logger.debug("\t'count':" + str(count) + "," )
        logger.debug("\t'area':" + bin(area)[2:] + "," )
        logger.debug("\t'effect':" + hex(effect) + "," )
        logger.debug("\t'objAddr':" + hex(objAddr) + "," )
        logger.debug("\t'objects':[")
        logger.debug("---\n")

        readAddr = objAddr
        objects = []
        while self.romData[readAddr] != OBJECT_SEPARATOR:
            logger.debug("\t\t{")
            objData = self.romData[readAddr:readAddr+OBJECT_DATA_SIZE]
            logger.debug("Raw Object Data:\t" + str(objData) )
            [objType, position, enemy] = struct.unpack("BBH", objData)
            logger.debug("\t\t'objType':" + hex(objType) + "\t# " + EXE6Dict.OBJECT_TYPE_LIST[objType])
            logger.debug("\t\t'position':" + hex(position))
            if objType == 0x11:
                logger.debug("\t\t'enemy':" + hex(enemy) + "\t# " + EXE6Dict.ENEMY_LIST[enemy])
                comments.append(EXE6Dict.ENEMY_LIST[enemy])
            logger.debug("\t\t}")
            objects.append({"objType":hex(objType), "position":hex(position), "value":hex(enemy)})
            readAddr += OBJECT_DATA_SIZE
        logger.debug("}\n")

        output = {
        "_comments":comments,
        "address":hex(addr),
        "field":hex(field),
        "x1":x1,
        "bgm":hex(bgm),
        "mode":hex(mode),
        "bg":hex(background),
        "count":count,
        "area":bin(area)[2:],
        "x2":x2,
        "effect":hex(effect),
        "objAddr":hex(objAddr),
        "objects":objects
        }
        return output

    def importBattleData(self, battleDataSet):
        for d in battleDataSet:
            address = int(d["address"], 16)
            field = int(d["field"], 16)
            x1 = d["x1"]
            bgm = int(d["bgm"], 16)
            mode = int(d["mode"], 16)
            bg = int(d["bg"], 16)
            count = d["count"]
            area = int(d["area"], 2)
            x2 = d["x2"]
            effect = int(d["effect"], 16)
            objAddr = int(d["objAddr"], 16)
            battleData = struct.pack("BBBBBBBBLL", field, x1, bgm, mode, bg, count, area, x2, effect, objAddr+MEMORY_OFFSET)
            logger.debug("Raw Battle Data:\t" + str(battleData) )

            objData = b""
            for obj in d["objects"]:
                objType = int(obj["objType"], 16)
                position = int(obj["position"], 16)
                value = int(obj["value"], 16)
                objData += struct.pack("BBH", objType, position, value)
            objData += b"\xF0"

            self.romData = self.romData[:address] + battleData + self.romData[address+BATTLE_DATA_SIZE:]
            self.romData = self.romData[:objAddr] + objData + self.romData[objAddr+len(objData):]

        with open(name + "_mod" + ext, "wb") as outFile:
            outFile.write(self.romData)


""" main
"""
def main():
    battleCoordinator = BattleCoordinator()
    battleCoordinator.openFile(args.file)

    if args.dump == True:
        """ ダンプモード
        """
        output = []
        readAddr = DUMP_START
        while readAddr < DUMP_END:
            output.append( battleCoordinator.dumpBattleData(readAddr) )
            readAddr += BATTLE_DATA_SIZE
        with open("output.yaml", "w") as outFile:
            yaml.dump(output, outFile, encoding="utf-8", allow_unicode=True)

    elif args.importFile != None:
        """ インポートモード
        """
        with open(args.importFile, "r", encoding="utf-8") as f:
            data = yaml.load(f)

        battleCoordinator.importBattleData(data)

if __name__ == '__main__':
    main()
