#!/usr/bin/python
# coding: utf-8

u""" Sappy Transplant Assistant ver 1.1 by ideal.exe

    与えられたソングテーブル内の曲が使用しているボイスセットを
    元のアドレス＋指定オフセットでアクセス出来るようにポインタを書き換えるツール

    ソングテーブルのアドレスは他のツールで調べてください
    ソングテーブル以外のアドレスを入力するとどうなるかはわかりません
"""

import os
import struct
import sys
import time


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

    # 引数が足りないよ！
    if len(sys.argv) < 4:
        print(u"usage:\n\t第1引数：ボイスセットを持つファイル\n\
        第2引数：ソングテーブルのアドレス（16進数0xXXXXXX）\n\
        第3引数：移植オフセット（16進数0xXXXXXX）")
        sys.exit()

    filePath = sys.argv[1]  # 1つめの引数をファイルパスとして格納
    name, ext = os.path.splitext(filePath) # ファイル名と拡張子を取得
    outName = name + "_forTransplant" + ext  # 標準の出力ファイル名
    songTableAddr = int(sys.argv[2], 16)
    transplantOffs = int(sys.argv[3], 16)

    romData = openFile(filePath)
    data = voiceTransplanter(romData, songTableAddr, transplantOffs )
    #data = voiceTransplanter(romData, 0x1494A0, 0x700000 )
    saveFile(data, outName)

    executionTime = time.time() - startTime    # 実行時間計測終了
    print( "Execution Time:\t" + str(executionTime) + " sec" )


def songTableParser(romData, startAddr):
    u""" ソングテーブルから曲のアドレスを抽出する
    """
    songAddrList = []
    dataSize = 8    # 1曲分のデータサイズ
    readAddr = startAddr
    endAddr = startAddr + dataSize*100 # 実際の曲の数によらず100曲分のスペースが確保されている？

    while readAddr < endAddr:
        [addr, data] = struct.unpack("LL", romData[readAddr:readAddr+dataSize])
        if data != 0:
            addr -= memoryOffs
            #print( hex(addr) )
            songAddrList.append(addr)
        readAddr += dataSize

    return songAddrList


def songDataParser(romData, songAddr):
    u""" 曲データを解析する

        移植に使うためボイステーブルのアドレスを返します
    """

    readAddr = songAddr

    u""" ヘッダ
    """
    #print("Song at " + hex(songAddr))
    [trackNum, x1, x2, x3] = struct.unpack("BBBB", romData[readAddr:readAddr+4])
    #print("Track Number:\t" + str(trackNum) )
    #print([x1, x2, x3])
    readAddr += 4

    u""" ボイステーブルのアドレス
    """
    voicesAddr = struct.unpack("L", romData[readAddr:readAddr+offsSize])[0] - memoryOffs
    #print(hex(readAddr))
    readAddr += offsSize
    #print( "Voices Addr:\t" + hex(voicesAddr) + "\n")

    u""" 各トラックのアドレス
    """
    trackList = []
    for i in xrange(trackNum):
        trackAddr = struct.unpack("L", romData[readAddr:readAddr+offsSize])[0] - memoryOffs
        trackList.append(trackAddr)
        #print(hex(readAddr))
        readAddr += offsSize
        #print("Track" + str(i) + " Addr:\t" + hex(trackAddr))
    #print("\n---\n")

    return voicesAddr


def voiceTransplanter(romData, songTableAddr, transplantOffs):
    u""" 指定したソングテーブル内の曲が使用しているボイスセットのポインタを調整する

    """

    songAddrList = songTableParser(romData, songTableAddr)
    voicesAddrList = []
    for song in songAddrList:
        voicesAddrList.append( songDataParser(romData, song) )

    offsAddrList = []   # 処理すべきポインタが追加されていくリスト
    voiceDataStart = voicesAddrList[0]
    voiceDataEnd = voicesAddrList[0]

    for voices in voicesAddrList:
        # ここの処理がいまいちださい
        [offsAddrList, start, end, drumsAddr] = voiceTableParser(romData, voices, offsAddrList)
        [offsAddrList, start2, end2, drumsAddr] = voiceTableParser(romData, drumsAddr[0], offsAddrList) # ドラムパートは1個だけ分析する
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


def voiceTableParser(romData, tableAddr, offsAddrList):
    voiceDataStart = tableAddr # コピーすべきボイスセットの開始地点
    voiceDataEnd = tableAddr   # コピーすべきボイスセットの終了地点

    readAddr = tableAddr
    drumsAddr = []  # ドラム音源はボイスセットの構造を内包しているので後で同様の処理を行う

    #print("## Voices at " + hex(tableAddr) + "\n")
    #print("| Sound | Device | Address |\n|----:|:---:|----:|")
    for i in xrange(128):
        [device, baseNote, st, ss, addr, atk, dec, sus, rel] = struct.unpack("BBBBLBBBB", romData[readAddr:readAddr+voiceSize])
        if addr >= memoryOffs:  # ポインタだったら
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
