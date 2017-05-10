#!/usr/bin/python
# coding: utf-8

""" Sappy Transplant Assistant  by ideal.exe

    曲とかボイスセットの移植をサポートするツール
    対話形式になりました．そのうち引数形式にも対応するかもしれません

    ソングテーブルとかのアドレスは他のツールで調べてください
    ソングテーブル以外のアドレスを入力するとどうなるかはわかりません
"""

import argparse
import binascii
import os
import struct
import sys
import time

from logging import getLogger, FileHandler, StreamHandler, DEBUG, INFO
logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(INFO)
fhandler = FileHandler(os.path.join(os.path.dirname(__file__), "SappyTransplantAssistant.log"), "w")
fhandler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.addHandler(fhandler)


""" 定数
"""
PROGRAM_NAME = "Sappy Transplant Assistant ver 1.4.1  by ideal.exe"
OFFSET_SIZE = 4 # オフセットサイズは4バイト
MEMORY_OFFSET = 0x08000000   # ROMがマッピングされるメモリ上のアドレス
SONG_HEADER_SIZE = 4
VOICE_SIZE = 0xC # 音源定義データのサイズ
devices = {
    "0x0":"Direct Sound",
    "0x1":"Square Wave 1",
    "0x2":"Square Wave 2",
    "0x3":"Wave Memory",
    "0x4":"Noise",
    "0x8":"Direct Sound",
    "0x40":"Multi Sample",
    "0x80":"Drum Part"
}


def main():
    """ Main
    """
    startTime = time.time() # 実行時間計測開始
    print(PROGRAM_NAME +"\n")

    parser = argparse.ArgumentParser()  # コマンドラインオプション解析
    parser.add_argument("romFile", help="移植元のファイル")
    #parser.add_argument("-t", "--target", help="移植先のファイル")
    args = parser.parse_args()

    filePath = args.romFile
    name, ext = os.path.splitext(filePath) # ファイル名と拡張子を取得
    romData = openFile(filePath)

    sys.stdout.write(u"ソングテーブルのアドレス（0xXXXXXX）： ")
    songTableAddr = int(input(), 16)
    sys.stdout.write(u"移植オフセット（0xXXXXXX）： ")
    transplantOffs = int(input(), 16)
    print("")
    data = voiceTransplanter(romData, songTableAddr, transplantOffs)

    outName = name + "_Voices_" + hex(transplantOffs) + ext  # 出力ファイル名
    saveFile(data, outName)
    executionTime = time.time() - startTime    # 実行時間計測終了
    logger.info("\nExecution Time:\t" + str(executionTime) + " sec")


def voiceTransplanter(romData, songTableAddr, transplantOffs):
    """ 指定したソングテーブル内の曲が使用しているボイスセットのポインタを調整する

    """
    logger.info(romData[0xA0:0xAC].decode("utf-8"))

    songAddrList = songTableParser(romData, songTableAddr)
    voicesAddrList = []
    for song in songAddrList:
        songData = songDataParser(romData, song)
        if songData != -1:
            voicesAddrList.append(songData["voicesAddr"])

    offsAddrList = []   # 処理すべきポインタが追加されていくリスト
    # 切り出す音源データの仮の範囲
    voiceDataStart = voicesAddrList[0]
    voiceDataEnd = voicesAddrList[0]

    for voices in voicesAddrList:
        # ここの処理がいまいちださい
        [offsAddrList, start, end, drumsAddr] = voiceTableParser(romData, voices, offsAddrList)
        if len(drumsAddr) > 0:  # ドラムパートを使用していれば
            [offsAddrList, start2, end2, drumsAddr] = \
                voiceTableParser(romData, drumsAddr[0], offsAddrList) # ドラムパートは1個だけ分析する
        else:
            start2 = start
            end2 = end
        # コピーする範囲の更新
        if voiceDataStart > min(start, start2):
            voiceDataStart = min(start, start2)
        if voiceDataEnd < max(end, end2) < len(romData):
            voiceDataEnd = max(end, end2)

    # ポインタ書き換え
    for addr in offsAddrList:
        [baseData] = struct.unpack("L", romData[addr:addr+OFFSET_SIZE])   # もともとのポインタ
        data = struct.pack("L", baseData + transplantOffs)
        romData = writeDataToRom(romData, addr, data)
        print(".", end="", flush=True)
    print("done\n")

    print(fmtHex(voiceDataStart) + u"から" + fmtHex(voiceDataEnd) + u"まで切り出しました")
    print(u"出力データを移植先の " + fmtHex(voiceDataStart + transplantOffs) + u" にペーストしてください")
    print(u"各ボイスセットには元のアドレス＋" + fmtHex(transplantOffs) + u"でアクセス出来ます")
    print(u"例）" + fmtHex(voicesAddrList[0]) + u" → " + \
        fmtHex(voicesAddrList[0]+transplantOffs) +"\n")

    return romData[voiceDataStart:voiceDataEnd]


def songTableParser(romData, startAddr):
    """ ソングテーブルから曲のアドレスを抽出する
    """
    songAddrList = []
    dataSize = 8    # 1曲分のデータサイズ
    readAddr = startAddr

    count = 0
    while True:
        [addr, data] = struct.unpack("LL", romData[readAddr:readAddr+dataSize])

        if addr == 0:
            # addr = 0x00000000が終端らしい
            break

        logger.debug("Entry" + str(count) + " at " + fmtHex(readAddr) + "{")

        addr -= MEMORY_OFFSET
        logger.debug("\tAddr:\t" + fmtHex(addr))
        logger.debug("\tData:\t" + fmtHex(data))

        if data != 0 and addr not in songAddrList:   # ここ適当（曲のアドレスとそうじゃないアドレスをどうやって区別すべきか検討中
            songAddrList.append(addr)

        logger.debug("}")
        readAddr += dataSize
        count += 1

    logger.info(str(count) + " entry found\n")
    return songAddrList


def songDataParser(romData, songAddr):
    """ 曲データを解析する

        各データの辞書を返します
        曲データではないと判断した場合は-1を返します
    """

    readAddr = songAddr

    """ ヘッダ

        ヘッダと言いつつ曲データの末尾にある
    """
    logger.debug("Song at " + fmtHex(songAddr))
    [trackNum, x1, x2, x3] = struct.unpack("BBBB", romData[readAddr:readAddr+SONG_HEADER_SIZE])

    if trackNum == 0:
        return -1

    logger.debug("Track Number:\t" + str(trackNum))
    logger.debug([x1, x2, x3])
    readAddr += SONG_HEADER_SIZE

    # ボイステーブルのアドレス
    voicesAddrPtr = readAddr
    voicesAddr = struct.unpack("L", romData[readAddr:readAddr+OFFSET_SIZE])[0] - MEMORY_OFFSET
    readAddr += OFFSET_SIZE
    logger.debug("Voices Addr:\t" + fmtHex(voicesAddr) + "\n")

    # 各トラックのアドレス
    trackList = []
    trackPtrList = []
    for i in range(trackNum):
        trackAddr = struct.unpack("L", romData[readAddr:readAddr+OFFSET_SIZE])[0] - MEMORY_OFFSET
        trackList.append(trackAddr)
        trackPtrList.append(readAddr)
        readAddr += OFFSET_SIZE
        logger.debug("Track" + str(i) + " Addr:\t" + fmtHex(trackAddr))
    logger.debug("---")

    return {"trackNum":trackNum, "voicesAddr":voicesAddr, "voicesAddrPtr":voicesAddrPtr, \
            "trackList":trackList, "trackPtrList":trackPtrList}


def trackDataParser(romData, trackAddr):
    """ トラックデータを解析する

        トラックデータの中もポインタまみれだったので作成
        0xB1が終端？0xB2,B3がポインタとして使われている？（MIDIでは0xBXはXchのコントロールチェンジ）
        0xB2はトラックの最後にあることからループと思われる
    """

    readAddr = trackAddr
    logger.debug("Track at " + fmtHex(readAddr))
    ptrAddrList = []    # トラックデータ内のポインタアドレス

    while romData[readAddr] != "\xB1":
        if romData[readAddr] in ["\xB2", "\xB3"]:
            logger.debug(binascii.hexlify(romData[readAddr]).upper() + ":")
            readAddr += 1
            ptrAddrList.append(readAddr)
            [data] = struct.unpack("L", romData[readAddr:readAddr+OFFSET_SIZE])
            logger.debug("   " + fmtHex(data))
            readAddr += OFFSET_SIZE
        else:
            readAddr += 1
    logger.debug("")

    return ptrAddrList


def voiceTableParser(romData, tableAddr, offsAddrList):
    """ ボイステーブルを解析する

        ボイスセット内のポインタのアドレス，ボイスセットの開始，終了アドレス，使用しているドラムセットのアドレスを返す
    """
    voiceDataStart = tableAddr # コピーすべきボイスセットの開始地点
    voiceDataEnd = tableAddr   # コピーすべきボイスセットの終了地点

    readAddr = tableAddr
    drumsAddr = []  # ドラム音源はボイスセットの構造を内包しているので後で同様の処理を行う

    for i in range(128):
        [device, baseNote, sweepTime, sweepShift, addr, atk, dec, sus, rel] = \
            struct.unpack("BBBBLBBBB", romData[readAddr:readAddr+VOICE_SIZE])
        if addr >= MEMORY_OFFSET and addr - MEMORY_OFFSET < len(romData):  # まともなポインタだったら
            addr -= MEMORY_OFFSET
            if readAddr+4 not in offsAddrList:  # まだリストに追加していないなら
                offsAddrList.append(readAddr+4) # addrの値を保持しているアドレスを記録

            if addr < voiceDataStart:
                voiceDataStart = addr   # ボイステーブルより前に楽器データがあったらそこからコピーしなければいけない

            if device == 0x80 and addr not in drumsAddr:  # 既にリストに追加済みのドラムセットでなければ
                drumsAddr.append(addr)

            elif device in [0x0, 0x8]:
                """ Direct Sound の場合は音源データの終端を探しに行かないといけない

                    データ構造はSampleインポートでインポートしたデータから推測
                """
                [sampleSize] = struct.unpack("L", romData[addr+0xC:addr+0x10])
                sampleEnd = addr + 0x10 + sampleSize
                if voiceDataEnd < sampleEnd:
                    voiceDataEnd = sampleEnd

        readAddr += VOICE_SIZE
        if voiceDataEnd < readAddr:
            voiceDataEnd = readAddr+VOICE_SIZE

    return [offsAddrList, voiceDataStart, voiceDataEnd, drumsAddr]


def songTransplanter(romData, songAddr, targetAddr, voicesAddr):
    """ 指定したアドレスの曲を指定したアドレス，ボイスセットで演奏できるように調整して出力する
    """

    songData = songDataParser(romData, songAddr)
    transplantOffs = targetAddr - songAddr

    # ポインタ書き換え
    data = struct.pack("L", voicesAddr+MEMORY_OFFSET)
    logger.debug(binascii.hexlify(data))
    romData = writeDataToRom(romData, songData["voicesAddrPtr"], data)

    for addr in songData["trackPtrList"]:
        [baseData] = struct.unpack("L", romData[addr:addr+OFFSET_SIZE])
        data = struct.pack("L", baseData + transplantOffs)
        logger.debug(binascii.hexlify(data))
        romData = writeDataToRom(romData, addr, data)

    # トラックデータ内のポインタの書き換え
    for track in songData["trackList"]:
        ptrAddrList = trackDataParser(romData, track)
        for addr in ptrAddrList:
            [baseData] = struct.unpack("L", romData[addr:addr+OFFSET_SIZE])
            data = struct.pack("L", baseData + transplantOffs)
            logger.debug(binascii.hexlify(data))
            romData = writeDataToRom(romData, addr, data)


    # 曲データの切り出し（全てのゲームがこの曲構造かは不明）
    songDataStart = songData["trackList"][0]
    logger.debug("Song Data Start:\t" + fmtHex(songDataStart))
    songDataEnd = songData["trackPtrList"][-1]+OFFSET_SIZE
    logger.debug("Song Data End:\t\t" + fmtHex(songDataEnd))


    print(u"出力データを移植先の " + fmtHex(songDataStart + transplantOffs) + u" にペーストしてください")
    print(u"ソングヘッダのアドレスは" + fmtHex(targetAddr) + u"です")
    print(u"移植先のソングテーブルで" + fmtHex(targetAddr) + u"を指定するとアクセスできます")

    return romData[songDataStart:songDataEnd]


def writeDataToRom(romData, writeAddr, data):
    """ 指定したアドレスから指定したデータを上書きする
    """
    romData = romData[:writeAddr] + data + romData[writeAddr+len(data):]
    return romData


def openFile(filePath):
    """ ファイルを開く
    """

    try:
        with open(filePath, 'rb') as romFile:   # 読み取り専用、バイナリファイルとして開く
            romData = romFile.read()   # データのバイナリ文字列（バイナリエディタのASCIIのとこみたいな感じ）

    except OSError:
        print(u"ファイルを開けませんでした")

    return romData


def saveFile(data, outName):
    """ ファイル出力
    """

    try:
        with open(outName, "wb") as outFile:
            outFile.write(data)
    except OSError:
        print(u"ファイルを正しく出力できませんでした")


def fmtHex(num):
    """ 16進数をいい感じに表示する
    """
    return "0x" + hex(num)[2:].upper()


if __name__ == '__main__':
    main()
