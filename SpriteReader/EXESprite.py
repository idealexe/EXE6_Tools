#!/usr/bin/python
# coding: utf-8
# pylint: disable=C0103

""" EXE Sprite  by ideal.exe

    EXESpriteReaderのコードが煩雑化してきたのでスプライトデータに関する処理をクラス化する
"""

import os
import struct
import sys

from logging import getLogger, StreamHandler, INFO
logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(INFO)
logger.setLevel(INFO)
logger.addHandler(handler)

sys.path.append(os.path.join(os.path.dirname(sys.argv[0]), "../common/"))
import LZ77Util


HEADER_SIZE = 4
OFFSET_SIZE = 4
COLOR_SIZE = 2 # 1色あたりのサイズ（byte）
FRAME_DATA_SIZE = 20
OAM_DATA_SIZE = 5
OAM_DATA_END = [b"\xFF\xFF\xFF\xFF\xFF", b"\xFF\xFF\xFF\xFF\x00"]

# フラグと形状の対応を取る辞書[size+shape]:[x,y]
OAM_DIMENSION = {
    "0000":[8, 8],
    "0001":[16, 8],
    "0010":[8, 16],
    "0100":[16, 16],
    "0101":[32, 8],
    "0110":[8, 32],
    "1000":[32, 32],
    "1001":[32, 16],
    "1010":[16, 32],
    "1100":[64, 64],
    "1101":[64, 32],
    "1110":[32, 64]
}

class EXEFrame:
    """ Frame
    """

    binFrameData = b""
    graphSizeAddr = 0
    palSizeAddr = 0
    oamPtrAddr = 0
    frameDelay = 0
    frameType = 0

    def __init__(self, binFrameData):
        self.binFrameData = binFrameData

        [self.graphSizeAddr, self.palSizeAddr, junkDataAddr, \
            self.oamPtrAddr, self.frameDelay, self.frameType] = struct.unpack("<LLLLHH", binFrameData)


class EXEOAM:
    """ OAM
    """

    binOamData = b""
    startTile = 0
    posX = 0
    posY = 0
    sizeX = 0
    sizeY = 0
    flipV = 0
    flipH = 0
    palIndex = 0


    def __init__(self, binOamData):
        self.binOamData = binOamData

        [self.startTile, self.posX, self.posY, flag1, flag2] = struct.unpack("BbbBB", binOamData)

        flag1 = bin(flag1)[2:].zfill(8)
        flag2 = bin(flag2)[2:].zfill(8)

        self.flipV = int(flag1[0], 2) # 垂直反転フラグ
        self.flipH = int(flag1[1], 2) # 水平反転フラグ

        self.palIndex = int(flag2[0:4], 2)

        objSize = flag1[-2:]
        objShape = flag2[-2:]
        [self.sizeX, self.sizeY] = OAM_DIMENSION[objSize+objShape]


class EXESprite:
    """ ロックマンエグゼシリーズのスプライトデータを扱うクラス
    """

    binAnimPtrTable = b""
    animPtrList = []
    binSpriteData = b""

    def __init__(self, data, spriteAddr, compFlag):
        """ スプライトデータを読み込んでオブジェクトを初期化する

            data内のspriteAddrをスプライトデータの先頭アドレスとして処理します。
            compFlag=1の場合圧縮スプライトとして扱います。
            スプライトデータのみのファイルを読み込む場合はspriteAddr=0, compFlag=0とすることで同様に扱えます。
        """

        if compFlag == 0:
            spriteData = data[spriteAddr+HEADER_SIZE:]   # スプライトはサイズ情報を持たないので仮の範囲を切り出し
        elif compFlag == 1:
            spriteData = LZ77Util.decompLZ77_10(data, spriteAddr)[8:]    # ファイルサイズ情報とヘッダー部分を取り除く

        readAddr = 0
        animDataStart = int.from_bytes(spriteData[readAddr:readAddr+OFFSET_SIZE], "little")
        logger.debug("Animation Data Start:\t" + hex(animDataStart))
        self.binAnimPtrTable = spriteData[readAddr:readAddr+animDataStart]

        u""" アニメーションオフセットのテーブルからアニメーションのアドレスを取得
        """
        animPtrList = []
        animCount = 0
        while readAddr < animDataStart:
            animPtr = int.from_bytes(spriteData[readAddr:readAddr+OFFSET_SIZE], "little")
            logger.debug("Animation Pointer:\t" + hex(animPtr))
            #animPtr = struct.unpack("<L", animPtr)[0]
            animPtrList.append({"animNum":animCount, "addr":readAddr, "value":animPtr})
            readAddr += OFFSET_SIZE
            animCount += 1
        self.animPtrList = animPtrList

        u""" アニメーションのアドレスから各フレームのデータを取得
        """
        frameDataList = []
        graphAddrList = []    # グラフィックデータは共有しているフレームも多いので別のリストで保持
        for i, animPtr in enumerate(animPtrList):
            readAddr = animPtr["value"]
            logger.debug("Animation " + str(i) + " at " + hex(readAddr))

            frameCount = 0
            while True: # do while文がないので代わりに無限ループ＋breakを使う
                frameData = spriteData[readAddr:readAddr+FRAME_DATA_SIZE]
                frame = EXEFrame(frameData)

                logger.debug("Frame Type:\t" + hex(frame.frameType))
                if frame.graphSizeAddr in [0x0000, 0x2000]:  # 流星のロックマンのスプライトを表示するための応急処置
                    logger.warning(u"不正なアドレスをロードしました．終端フレームが指定されていない可能性があります")
                    break

                if frame.graphSizeAddr not in graphAddrList:
                    graphAddrList.append(frame.graphSizeAddr)
                logger.debug("Graphics Size Address:\t" + hex(frame.graphSizeAddr))

                try:
                    [graphicSize] = \
                        struct.unpack("L", spriteData[frame.graphSizeAddr:frame.graphSizeAddr+OFFSET_SIZE])
                except struct.error:
                    logger.warning(u"不正なアドレスをロードしました．終端フレームが指定されていない可能性があります")
                    break
                graphicData = \
                    spriteData[frame.graphSizeAddr+OFFSET_SIZE:frame.graphSizeAddr+OFFSET_SIZE+graphicSize]

                frameDataList.append({\
                    "animNum":animPtr["animNum"], "frameNum":frameCount, \
                    "address":readAddr, "graphicData":graphicData, "frame":frame})

                readAddr += FRAME_DATA_SIZE
                frameCount += 1

                if frame.frameType in [0x80, 0xC0]: # 終端フレームならループを終了
                    break
        self.frameDataList = frameDataList

        u""" フレームデータからOAMデータを取得
        """
        oamDataList = []
        for frameData in frameDataList:
            logger.debug("Frame at " + hex(frameData["address"]))
            logger.debug("  Animation Number:\t" + str(frameData["animNum"]))
            logger.debug("  Frame Number:\t\t" + str(frameData["frameNum"]))
            logger.debug("  Address of OAM Pointer:\t" + hex(frameData["frame"].oamPtrAddr))
            oamPtrAddr = frameData["frame"].oamPtrAddr
            [oamPtr] = struct.unpack("L", spriteData[oamPtrAddr:oamPtrAddr+OFFSET_SIZE])
            readAddr = oamPtrAddr + oamPtr

            while True:
                oamData = spriteData[readAddr:readAddr+OAM_DATA_SIZE]
                if oamData in OAM_DATA_END:
                    break

                oam = EXEOAM(oamData)

                oamDataList.append({\
                    "animNum":frameData["animNum"], "frameNum":frameData["frameNum"], \
                    "address":readAddr, "oam":oam})
                readAddr += OAM_DATA_SIZE
        self.oamDataList = oamDataList

        u""" 無圧縮スプライトの場合は余分なデータを切り離す
        """
        if compFlag == 0:
            endAddr = oamDataList[-1]["address"] + OAM_DATA_SIZE + len(OAM_DATA_END[0])
            spriteData = spriteData[:endAddr]

        self.binSpriteData = spriteData


    def getBinSpriteData(self):
        """ スプライトのバイナリデータを返す
        """
        return self.binSpriteData


    def getSpriteDataSize(self):
        """ スプライトデータのサイズを返す
        """
        return len(self.binSpriteData)


    def getBinAnimPtrTable(self):
        """ スプライトのアニメーションテーブルを返す
        """
        animDataStart = int.from_bytes(self.binSpriteData[0:OFFSET_SIZE], "little")
        binAnimPtrTable = self.binSpriteData[0:animDataStart]
        return binAnimPtrTable


    def getAnimPtrTableSize(self):
        """ アニメーションテーブルのサイズを返す
        """
        animDataStart = int.from_bytes(self.binSpriteData[0:OFFSET_SIZE], "little")
        return animDataStart


    def getOffsetAnimPtrTable(self, offset):
        """ アニメーションテーブル内のポインタに指定した数値を足したものを返す
        """
        offsetAnimPtrTable = b""
        for animPtr in self.animPtrList:
            offsetAnimPtrTable += (animPtr["value"] + offset).to_bytes(OFFSET_SIZE, "little")
        return offsetAnimPtrTable


    def getOffsetFrameData(self, offset):
        """ フレームデータ内のすべてのポインタに指定した数値を足したものを返す
        """
        offsetFrameData = b""
        for frameData in self.frameDataList:
            graphSizeAddr = frameData["graphSizeAddr"] + offset
            palSizeAddr = frameData["palSizeAddr"] + offset
            junkDataAddr = frameData["junkDataAddr"] + offset
            oamPtrAddr = frameData["oamPtrAddr"] + offset
            frameDelay = frameData["frameDelay"]
            frameType = frameData["frameType"]
            data = struct.pack("<LLLLHH", \
                graphSizeAddr, palSizeAddr, junkDataAddr, oamPtrAddr, frameDelay, frameType)
            offsetFrameData += data
        return offsetFrameData


    def getBaseData(self):
        """ グラフィック、OAM、パレットデータを返す

            （つまりスプライトのうちポインタを含まないデータすべて）
        """
        baseData = self.binSpriteData[self.frameDataList[0]["graphSizeAddr"]:]  # グラフィックデータ先頭からスプライトの終端までコピー
        return baseData
