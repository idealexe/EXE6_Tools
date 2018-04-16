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

# sys.argv[0]だと実行しているスクリプトのディレクトリしかとれないので__file__に変更
sys.path.append(os.path.join(os.path.dirname(__file__), "../common/"))
import LZ77Util

PROGRAM_NAME = "EXE Sprite  ver 1.1  by ideal.exe"
HEADER_SIZE = 4
OFFSET_SIZE = 4
COLOR_SIZE = 2  # 1色あたりのサイズ（byte）
FRAME_DATA_SIZE = 20
OAM_DATA_SIZE = 5
OAM_DATA_END = [b"\xFF\xFF\xFF\xFF\xFF", b"\xFF\xFF\xFF\xFF\x00"]

# フラグと形状の対応を取る辞書[size+shape]:[x,y]
OAM_DIMENSION = {
    "0000": [8, 8],
    "0001": [16, 8],
    "0010": [8, 16],
    "0100": [16, 16],
    "0101": [32, 8],
    "0110": [8, 32],
    "1000": [32, 32],
    "1001": [32, 16],
    "1010": [16, 32],
    "1100": [64, 64],
    "1101": [64, 32],
    "1110": [32, 64]
}


class EXEAnimation:
    """ Animation

        複数のフレームデータの集まり
    """

    frameList = []
    binAnimData = b""

    def __init__(self, spriteData, animAddr):
        u""" アニメーションのアドレスから各フレームのデータを取得
        """

        graphAddrList = []    # グラフィックデータは共有しているフレームも多いので別のリストで保持
        frameCount = 0
        frameList = []
        readAddr = animAddr

        while True: # do while文がないので代わりに無限ループ＋breakを使う
            binFrameData = spriteData[readAddr:readAddr+FRAME_DATA_SIZE]
            self.binAnimData += binFrameData
            frame = EXEFrame(spriteData, binFrameData)

            logger.debug("Frame Type:\t" + hex(frame.frameType))
            if frame.graphSizeAddr in [0x0000, 0x2000]:  # 流星のロックマンのスプライトを表示するための応急処置
                logger.warning("不正なアドレスをロードしました．終端フレームが指定されていない可能性があります")
                break

            if frame.graphSizeAddr not in graphAddrList:
                graphAddrList.append(frame.graphSizeAddr)
            logger.debug("Graphics Size Address:\t" + hex(frame.graphSizeAddr))

            try:
                [graphicSize] = \
                    struct.unpack("L", spriteData[frame.graphSizeAddr:frame.graphSizeAddr+OFFSET_SIZE])
            except struct.error:
                logger.warning("不正なアドレスをロードしました．終端フレームが指定されていない可能性があります")
                break
            graphicData = \
                spriteData[frame.graphSizeAddr+OFFSET_SIZE:frame.graphSizeAddr+OFFSET_SIZE+graphicSize]

            frameList.append({"frameNum":frameCount, "address":readAddr, "graphicData":graphicData, "frame":frame})

            readAddr += FRAME_DATA_SIZE
            frameCount += 1

            if frame.frameType in [0x80, 0xC0]: # 終端フレームならループを終了
                break
        self.frameList = frameList

    def getFrameNum(self):
        """ フレーム枚数を返す
        """
        return len(self.frameList)


class EXEFrame:
    """ Frame
    """

    binFrameData = b""
    graphSizeAddr = 0
    palSizeAddr = 0
    oamPtrAddr = 0
    frameDelay = 0
    frameType = 0
    oamList = []

    def __init__(self, binSpriteData, binFrameData):
        self.binFrameData = binFrameData

        [self.graphSizeAddr, self.palSizeAddr, self.junkDataAddr,
            self.oamPtrAddr, self.frameDelay, self.frameType] = struct.unpack("<LLLLHH", binFrameData)

        [oamPtr] = struct.unpack("L", binSpriteData[self.oamPtrAddr:self.oamPtrAddr+OFFSET_SIZE])
        readAddr = self.oamPtrAddr + oamPtr

        oamList = []
        while True:
            binOamData = binSpriteData[readAddr:readAddr+OAM_DATA_SIZE]
            if binOamData in OAM_DATA_END:
                break
            oam = EXEOAM(binOamData)
            oamList.append({"address":readAddr, "oam":oam})
            readAddr += OAM_DATA_SIZE
        self.oamList = oamList


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

    def printData(self):
        """ OAM情報表示
        """
        logger.info("Start Tile:\t" + str(self.startTile))
        logger.info("Pos X:\t" + str(self.posX))
        logger.info("Pos Y:\t" + str(self.posY))
        logger.info("Size X:\t" + str(self.sizeX))
        logger.info("Size Y:\t" + str(self.sizeY))
        logger.info("Flip V:\t" + str(self.flipV))
        logger.info("Flip H:\t" + str(self.flipH))
        logger.info("Palette Index:\t" + str(self.palIndex))
        logger.info("===\n")


class EXESprite:
    """ ロックマンエグゼシリーズのスプライトデータを扱うクラス
    """

    binSpriteHeader = b""
    binSpriteData = b""
    binAnimPtrTable = b""
    animPtrList = []
    animList = []
    binGraphicsData = b""

    def __init__(self, data, spriteAddr, compFlag):
        """ スプライトデータを読み込んでオブジェクトを初期化する

            data内のspriteAddrをスプライトデータの先頭アドレスとして処理します。
            compFlag=1の場合圧縮スプライトとして扱います。
            スプライトデータのみのファイルを読み込む場合はspriteAddr=0, compFlag=0とすることで同様に扱えます。
        """

        if compFlag == 0:
            self.binSpriteHeader = data[spriteAddr:spriteAddr+HEADER_SIZE]
            spriteData = data[spriteAddr+HEADER_SIZE:]   # スプライトはサイズ情報を持たないので仮の範囲を切り出し
        elif compFlag == 1:
            data = LZ77Util.decompLZ77_10(data, spriteAddr)[4:]    # ファイルサイズ情報とヘッダー部分を取り除く
            self.binSpriteHeader = data[0:HEADER_SIZE]
            spriteData = data[HEADER_SIZE:]

        readAddr = 0
        animDataStart = int.from_bytes(spriteData[readAddr:readAddr+OFFSET_SIZE], "little")
        logger.debug("Animation Data Start:\t" + hex(animDataStart))
        self.binAnimPtrTable = spriteData[readAddr:readAddr+animDataStart]

        """ アニメーションオフセットのテーブルからアニメーションのアドレスを取得
        """
        animPtrList = []
        animCount = 0
        while readAddr < animDataStart:
            animPtr = int.from_bytes(spriteData[readAddr:readAddr+OFFSET_SIZE], "little")
            logger.debug("Animation Pointer:\t" + hex(animPtr))
            animPtrList.append({"animNum":animCount, "addr":readAddr, "value":animPtr})
            readAddr += OFFSET_SIZE
            animCount += 1
        self.animPtrList = animPtrList

        """ アニメーション取得
        """
        animList = []
        for animPtr in animPtrList:
            animAddr = animPtr["value"]
            anim = EXEAnimation(spriteData, animAddr)
            animList.append(anim)
        self.animList = animList

        """ 無圧縮スプライトの場合は余分なデータを切り離す
        """
        if compFlag == 0:
            endAddr = animList[-1].frameList[-1]["frame"].oamList[-1]["address"] + OAM_DATA_SIZE + len(OAM_DATA_END[0])
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
        for anim in self.animList:
            for frame in anim.frameList:
                frameData = frame["frame"]
                graphSizeAddr = frameData.graphSizeAddr + offset
                palSizeAddr = frameData.palSizeAddr + offset
                junkDataAddr = frameData.junkDataAddr + offset
                oamPtrAddr = frameData.oamPtrAddr + offset
                frameDelay = frameData.frameDelay
                frameType = frameData.frameType
                data = struct.pack("<LLLLHH",
                    graphSizeAddr, palSizeAddr, junkDataAddr, oamPtrAddr, frameDelay, frameType)
                offsetFrameData += data
        return offsetFrameData

    def getAnimNum(self):
        """ アニメーション数を返す
        """
        return len(self.animList)

    def getBaseData(self):
        """ グラフィック、OAM、パレットデータを返す

            （つまりスプライトのうちポインタを含まないデータすべて）
        """
        baseData = self.binSpriteData[self.animList[0].frameList[0]["frame"].graphSizeAddr:]  # グラフィックデータ先頭からスプライトの終端までコピー
        return baseData

    def getAllFrame(self):
        """ 全てのFrameオブジェクトを返す
        """
        allFrameList = []
        for anim in self.animList:
            allFrameList += [frame["frame"] for frame in anim.frameList]
        return allFrameList

    def getAllOam(self):
        """ 全てのOAMオブジェクトを返す
        """
        allOamList = []
        for frame in self.getAllFrame():
            allOamList += [oam for oam in frame.oamList]
        return allOamList
