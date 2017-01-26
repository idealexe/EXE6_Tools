#!/usr/bin/python
# coding: utf-8

u""" Sappy Transplant Assistant ver 1.0 by ideal.exe

    与えられたファイル内のvoicesAddrにあるボイスセットをtargetAddrに移植したとき正しく鳴るようにポインタを書き換えるツール
    ボイスセットのアドレスはSappyで調べてください．ボイスセット以外のアドレスを入力するとどうなるかはわかりません．
"""

import os
import struct
import sys
import time


def main():
    startTime = time.time() # 実行時間計測開始

    # 引数が足りないよ！
    if len(sys.argv) < 4:
        print(u"usage:\n\t第1引数：ボイスセットを持つファイル\n\t第2引数：移植するボイスセットのアドレス（16進数0xXXXXXX）\n\t第3引数：移植後のアドレス（16進数0xXXXXXX）")
        sys.exit()

    filePath = sys.argv[1]  # 1つめの引数をファイルパスとして格納
    name, ext = os.path.splitext(filePath) # ファイル名と拡張子を取得
    outName = name + "_forTransplant" + ext  # 標準の出力ファイル名
    voicesAddr = int(sys.argv[2], 16)
    targetAddr = int(sys.argv[3], 16)

    # ファイルを開く
    try:
        with open(filePath, 'rb') as romFile:   # 読み取り専用、バイナリファイルとして開く
            romData = romFile.read()   # データのバイナリ文字列（バイナリエディタのASCIIのとこみたいな感じ）
            size = len(romData)    # ファイルサイズ
            print( str(size) + " Bytes" )
    except:
        print(u"ファイルを開けませんでした")

    #data = voiceTransplanter(romData, 0x1438ac, 0x8438ac)
    data = voiceTransplanter(romData, voicesAddr, targetAddr)
    saveFile(data, outName)

    executionTime = time.time() - startTime    # 実行時間計測終了
    print( "Execution Time:\t" + str(executionTime) + " sec" )


def voiceTransplanter(romData, voicesAddr, targetAddr):
    u""" ROM内のvoicesAddrで定義されているボイスセットをtargetAddrに移植したとき正しく鳴るようにポインタを書き換えて出力する
    """

    offsLen = 4 # オフセットは4バイト
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
    offsAddrList = []   # 移植の際に書き換えるべきポインタ
    voiceDataStart = voicesAddr # コピーすべきボイスセットの開始地点
    voiceDataEnd = voicesAddr   # コピーすべきボイスセットの終了地点

    u""" 楽器データ
    """
    readAddr = voicesAddr
    drumsAddr = []  # ドラム音源はボイスセットの構造を内包しているので後で同様の処理を行う
    for i in xrange(128):
        [device, baseNote, st, ss, addr, atk, dec, sus, rel] = struct.unpack("BBBBLBBBB", romData[readAddr:readAddr+voiceSize])
        if addr >= memoryOffs:  # ポインタだったら
            offsAddrList.append(readAddr+4) # addrの値を保持しているアドレス
            addr -= memoryOffs
            if addr < voiceDataStart:
                voiceDataStart = addr   # ボイステーブルより前に楽器データがあったらそこからコピーしなければいけない
            #print(hex(readAddr+4))
        if device == 0x80:  # ドラムセットだったら
            if addr not in drumsAddr:  # 既にリストに追加済みのアドレスでなければ
                drumsAddr.append(addr)
        elif device in [0x0, 0x8]:
            u""" Direct Sound だと音源データの終端を探しに行かないといけない
            """
            [sampleSize] = struct.unpack("L", romData[addr+0xC:addr+0x10])
            sampleEnd = addr + 0x10 + sampleSize
            if voiceDataEnd < sampleEnd:
                voiceDataEnd = sampleEnd

        readAddr += voiceSize
        if voiceDataEnd < readAddr:
            voiceDataEnd = readAddr+voiceSize

        try:
            print( "Sound " + str(i) + "\t" + devices[hex(device)] + "\tAddr:" + hex(addr) )
        except:
            print( "Sound " + str(i) + "\t???(" + hex(device) + ")\tAddr:" + hex(addr) )


    u""" ドラムデータ
    """
    for drumAddr in drumsAddr:
        print("\n---\nDrums:\t" + hex(drumAddr))
        readAddr = drumAddr

        for i in xrange(128):
            [device, baseNote, st, ss, addr, atk, dec, sus, rel] = struct.unpack("BBBBLBBBB", romData[readAddr:readAddr+voiceSize])
            if addr >= memoryOffs and readAddr+4 not in offsAddrList:  # まだリストに追加していないポインタだったら（ボイスセットと共通の楽器もあるので）
                offsAddrList.append(readAddr+4)
                addr -= memoryOffs
                if addr < voiceDataStart:
                    voiceDataStart = addr
                if device in [0x0, 0x8]:
                    u""" Direct Sound だと音源データの終端を探しに行かないといけない
                    """
                    [sampleSize] = struct.unpack("L", romData[addr+0xC:addr+0x10])
                    sampleEnd = addr + 0x10 + sampleSize
                    if voiceDataEnd < sampleEnd:
                        voiceDataEnd = sampleEnd
                #print(hex(readAddr+4))
            readAddr += voiceSize
            if voiceDataEnd < readAddr:
                voiceDataEnd = readAddr+voiceSize

            try:
                print( "Sound " + str(i) + "\t" + devices[hex(device)] + "\tAddr:" + hex(addr) )
            except:
                print( "Sound " + str(i) + "\t???(" + hex(device) + ")\tAddr:" + hex(addr) )

    u""" ポインタ書き換え
    """
    for addr in offsAddrList:
        [baseData] = struct.unpack("L", romData[addr:addr+4])
        data = struct.pack("L", baseData + (targetAddr - voicesAddr) )
        romData = writeDataToRom(romData, addr, data)

    print( hex(voicesAddr) + u" のボイスセットを " + hex(targetAddr) + u" に移植するには")
    print( u"出力データを移植先の " + hex(voiceDataStart + (targetAddr - voicesAddr)) + u" にペーストしてください")
    return romData[voiceDataStart:voiceDataEnd]


def writeDataToRom(romData, writeAddr, data):
    u""" 指定したアドレスから指定したデータを上書きする
    """
    romData = romData[:writeAddr] + data + romData[writeAddr+len(data):]
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
