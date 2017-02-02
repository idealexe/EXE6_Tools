#!/usr/bin/python
# coding: utf-8

u""" Sappy Transplant Assistant ver 1.3 by ideal.exe

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

from logging import getLogger,StreamHandler,WARNING,INFO,DEBUG
logger = getLogger(__name__)    # 出力元の明確化
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)


offsSize = 4 # オフセットサイズは4バイト
memoryOffs = 0x08000000   # ROMがマッピングされるアドレス
voiceSize = 0xC # 音源定義データのサイズ
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
    startTime = time.time() # 実行時間計測開始
    parser = argparse.ArgumentParser()  # コマンドラインオプション解析
    parser.add_argument("romFile", help=u"処理対象のファイル")
    """
    parser.add_argument("-m", "--mode", required=True, help=u"実行する処理（song=曲の移植, voice=ボイスセットの移植）")
    parser.add_argument("address", help=u"song mode では移植する曲のアドレス，voice mode ではソングテーブルのアドレスを指定")
    parser.add_argument("transplantOffs", help=u"移植オフセット")
    """
    args = parser.parse_args()

    filePath = args.romFile
    name, ext = os.path.splitext(filePath) # ファイル名と拡張子を取得
    outName = name + "_forTransplant" + ext  # 標準の出力ファイル名

    romData = openFile(filePath)
    print(u"モード選択（song=曲の移植, voice=ボイスセットの移植）")
    sys.stdout.write("Mode: ")
    mode = raw_input()
    if mode == "song":
        sys.stdout.write(u"移植する曲のヘッダアドレス（0xXXXXXX）： ")
        songAddr = raw_input()
        songAddr = int(songAddr, 16)
        sys.stdout.write(u"移植後のヘッダアドレス（0xXXXXXX）： ")
        targetAddr = raw_input()
        targetAddr = int(targetAddr, 16)
        sys.stdout.write(u"使用するボイスセットのアドレス（0xXXXXXX）： ")
        voicesAddr = raw_input()
        voicesAddr = int(voicesAddr, 16)
        print("---")
        data = songTransplanter(romData, songAddr, targetAddr, voicesAddr)
    elif mode == "voice":
        sys.stdout.write(u"ソングテーブルのアドレス（0xXXXXXX）： ")
        songTableAddr = raw_input()
        songTableAddr = int(songTableAddr, 16)
        sys.stdout.write(u"移植オフセット（0xXXXXXX）： ")
        transplantOffs = raw_input()
        transplantOffs = int(transplantOffs, 16)
        print("---")
        data = voiceTransplanter(romData, songTableAddr, transplantOffs)
    else:
        print(u"不正なオプションです")
        return -1

    saveFile(data, outName)
    executionTime = time.time() - startTime    # 実行時間計測終了
    print( "\nExecution Time:\t" + str(executionTime) + " sec" )


def voiceTransplanter(romData, songTableAddr, transplantOffs):
    u""" 指定したソングテーブル内の曲が使用しているボイスセットのポインタを調整する

    """

    songAddrList = songTableParser(romData, songTableAddr)
    voicesAddrList = []
    for song in songAddrList:
        if songDataParser(romData, song) != -1:
            voicesAddrList.append( songDataParser(romData, song)["voicesAddr"] )

    offsAddrList = []   # 処理すべきポインタが追加されていくリスト
    voiceDataStart = voicesAddrList[0]
    voiceDataEnd = voicesAddrList[0]

    for voices in voicesAddrList:
        if voices == -1:
            continue

        # ここの処理がいまいちださい
        [offsAddrList, start, end, drumsAddr] = voiceTableParser(romData, voices, offsAddrList)
        if len(drumsAddr) > 0:
            [offsAddrList, start2, end2, drumsAddr] = voiceTableParser(romData, drumsAddr[0], offsAddrList) # ドラムパートは1個だけ分析する
        else:
            start2 = start
            end2 = end
        # コピーする範囲の更新
        if voiceDataStart > min(start, start2):
            voiceDataStart = min(start, start2)
        if voiceDataEnd < max(end, end2):
            voiceDataEnd = max(end, end2)

    u""" ポインタ書き換え
    """
    for addr in offsAddrList:
        [baseData] = struct.unpack("L", romData[addr:addr+4])   # もともとのポインタ
        data = struct.pack("L", baseData + transplantOffs )
        romData = writeDataToRom(romData, addr, data)
        sys.stdout.write(".")
    print("done\n")

    print(hex(voiceDataStart) + u"から" + hex(voiceDataEnd) + u"まで切り出しました")
    print( u"出力データを移植先の " + hex(voiceDataStart + transplantOffs) + u" にペーストしてください")
    print( u"各ボイスセットには元のアドレス＋" + hex(transplantOffs) + u"でアクセス出来ます" )
    print( u"例）" + hex(voicesAddrList[0]) + u" → " + hex(voicesAddrList[0]+transplantOffs) +"\n" )

    return romData[voiceDataStart:voiceDataEnd]


def songTableParser(romData, startAddr):
    u""" ソングテーブルから曲のアドレスを抽出する
    """
    songAddrList = []
    dataSize = 8    # 1曲分のデータサイズ
    readAddr = startAddr
    endAddr = startAddr + dataSize*100 # 実際の曲の数によらず100曲分のスペースが確保されている？

    while readAddr < endAddr:
        [addr, data] = struct.unpack("LL", romData[readAddr:readAddr+dataSize])
        if data != -1:   # ここ適当（曲のアドレスとそうじゃないアドレスをどうやって区別すべきか検討中）
            addr -= memoryOffs
            #print( hex(addr) )
            if addr not in songAddrList:
                songAddrList.append(addr)
        readAddr += dataSize

    return songAddrList


def songDataParser(romData, songAddr):
    u""" 曲データを解析する

        各データの辞書を返します
        曲データではないと判断した場合は-1を返します
    """

    readAddr = songAddr

    u""" ヘッダ

        ヘッダと言いつつ曲データの末尾にある
    """
    logger.debug("Song at " + hex(songAddr))
    [trackNum, x1, x2, x3] = struct.unpack("BBBB", romData[readAddr:readAddr+4])
    if trackNum == 0:
        return -1
    logger.debug("Track Number:\t" + str(trackNum) )
    #print([x1, x2, x3])
    readAddr += 4

    u""" ボイステーブルのアドレス
    """
    voicesAddrPtr = readAddr
    voicesAddr = struct.unpack("L", romData[readAddr:readAddr+offsSize])[0] - memoryOffs
    #print(hex(readAddr))
    readAddr += offsSize
    logger.debug( "Voices Addr:\t" + hex(voicesAddr) + "\n")

    u""" 各トラックのアドレス
    """
    trackList = []
    trackPtrList = []
    for i in xrange(trackNum):
        trackAddr = struct.unpack("L", romData[readAddr:readAddr+offsSize])[0] - memoryOffs
        trackList.append(trackAddr)
        trackPtrList.append(readAddr)
        #(hex(readAddr))
        readAddr += offsSize
        logger.debug("Track" + str(i) + " Addr:\t" + hex(trackAddr))
    logger.debug("---")

    return {"trackNum":trackNum, "voicesAddr":voicesAddr, "voicesAddrPtr":voicesAddrPtr, "trackList":trackList, "trackPtrList":trackPtrList}

def trackDataParser(romData, trackAddr):
    u""" トラックデータを解析する

        トラックデータの中もポインタまみれだったので作成
        0xB1が終端？0xB2,B3がポインタとして使われている？（MIDIでは0xBXはXchのコントロールチェンジ）
        0xB2はトラックの最後にあることからループと思われる
    """

    readAddr = trackAddr
    logger.debug( "Track at " + hex(readAddr) )
    ptrAddrList = []    # トラックデータ内のポインタアドレス

    while romData[readAddr] != "\xB1":
        if romData[readAddr] in ["\xB2","\xB3"]:
            logger.debug(binascii.hexlify(romData[readAddr]).upper() + ":")
            readAddr += 1
            ptrAddrList.append(readAddr)
            [data] = struct.unpack("L", romData[readAddr:readAddr+offsSize])
            logger.debug("   " + hex(data))
            readAddr += offsSize
        else:
            readAddr += 1
    logger.debug("")

    return ptrAddrList


def voiceTableParser(romData, tableAddr, offsAddrList):
    voiceDataStart = tableAddr # コピーすべきボイスセットの開始地点
    voiceDataEnd = tableAddr   # コピーすべきボイスセットの終了地点

    readAddr = tableAddr
    drumsAddr = []  # ドラム音源はボイスセットの構造を内包しているので後で同様の処理を行う

    #print("## Voices at " + hex(tableAddr) + "\n")
    #print("| Sound | Device | Address |\n|----:|:---:|----:|")
    for i in xrange(128):
        [device, baseNote, st, ss, addr, atk, dec, sus, rel] = struct.unpack("BBBBLBBBB", romData[readAddr:readAddr+voiceSize])
        if addr >= memoryOffs and addr - memoryOffs < len(romData):  # まともなポインタだったら
            addr -= memoryOffs
            if readAddr+4 not in offsAddrList:  # まだリストに追加していないなら
                offsAddrList.append(readAddr+4) # addrの値を保持しているアドレスを記録

            if addr < voiceDataStart:
                voiceDataStart = addr   # ボイステーブルより前に楽器データがあったらそこからコピーしなければいけない
            #print(hex(readAddr+4))
            if device == 0x80 and addr not in drumsAddr:  # 既にリストに追加済みのドラムセットでなければ
                drumsAddr.append(addr)

            elif device in [0x0, 0x8]:
                u""" Direct Sound の場合は音源データの終端を探しに行かないといけない
                """
                [sampleSize] = struct.unpack("L", romData[addr+0xC:addr+0x10])
                sampleEnd = addr + 0x10 + sampleSize
                if voiceDataEnd < sampleEnd:
                    voiceDataEnd = sampleEnd

        readAddr += voiceSize
        if voiceDataEnd < readAddr:
            voiceDataEnd = readAddr+voiceSize

            """
        try:
            print( "| Sound " + str(i).zfill(3) + " |\t" + devices[hex(device)] + "\t| " + hex(addr) + " |" )
        except:
            print( "| Sound " + str(i).zfill(3) + " |\t??? (" + hex(device) + ")\t|" + hex(addr) + " |")
    print("\n---\n")
    """

    return [offsAddrList, voiceDataStart, voiceDataEnd, drumsAddr]


def songTransplanter(romData, songAddr, targetAddr, voicesAddr):
    u""" 指定したアドレスの曲を指定したアドレス，ボイスセットで演奏できるように調整して出力する
    """

    songData = songDataParser(romData, songAddr)
    transplantOffs = targetAddr - songAddr

    # ポインタ書き換え
    data = struct.pack("L", voicesAddr+memoryOffs )
    logger.debug(binascii.hexlify(data))
    romData = writeDataToRom(romData, songData["voicesAddrPtr"], data)

    for addr in songData["trackPtrList"]:
        [baseData] = struct.unpack("L", romData[addr:addr+offsSize])
        data = struct.pack("L", baseData + transplantOffs )
        logger.debug(binascii.hexlify(data))
        romData = writeDataToRom(romData, addr, data)

    # トラックデータ内のポインタの書き換え
    for track in songData["trackList"]:
        ptrAddrList = trackDataParser(romData, track)
        for addr in ptrAddrList:
            [baseData] = struct.unpack("L", romData[addr:addr+offsSize])
            data = struct.pack("L", baseData + transplantOffs )
            logger.debug(binascii.hexlify(data))
            romData = writeDataToRom(romData, addr, data)


    # 曲データの切り出し（全てのゲームがこの曲構造かは不明）
    songDataStart = songData["trackList"][0]
    logger.debug("Song Data Start:\t" + hex(songDataStart))
    songDataEnd = songData["trackPtrList"][-1]+offsSize
    logger.debug("Song Data End:\t\t" + hex(songDataEnd))


    print( u"出力データを移植先の " + hex(songDataStart + transplantOffs) + u" にペーストしてください")
    print( u"ソングヘッダのアドレスは" + hex(targetAddr) + u"です" )

    return romData[songDataStart:songDataEnd]


def writeDataToRom(romData, writeAddr, data):
    u""" 指定したアドレスから指定したデータを上書きする
    """
    romData = romData[:writeAddr] + data + romData[writeAddr+len(data):]
    return romData


def openFile(filePath):
    u""" ファイルを開く
    """

    try:
        with open(filePath, 'rb') as romFile:   # 読み取り専用、バイナリファイルとして開く
            romData = romFile.read()   # データのバイナリ文字列（バイナリエディタのASCIIのとこみたいな感じ）
            size = len(romData)    # ファイルサイズ
            print( str(size) + " Bytes\n" )
    except:
        print(u"ファイルを開けませんでした")

    return romData


def saveFile(data, outName):
    u""" ファイル出力
    """

    try:
        with open(outName, "wb") as outFile:
            outFile.write(data)
    except:
        print(u"ファイルを正しく出力できませんでした")



if __name__ == '__main__':
    main()
