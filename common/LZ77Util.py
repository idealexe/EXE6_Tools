#!/usr/bin/python
# coding: utf-8

u""" LZ77 decompressor by ideal.exe

    LZ77圧縮されたデータを検索したり解凍するモジュールです．
    ファイル名と圧縮されたデータの開始アドレスを渡して実行すると解凍します．
"""


import os
import re
import struct
import sys
import time


def detectLZ77(romData):
    u"""
        LZ77(0x10)圧縮されてそうなデータの検索

    """

    minSize = 0x100  # bytes
    maxSize = 0x10000
    searchStep = 0x4

    matchList = []
    candidateIter = re.finditer("\x10(?P<size>...)\x00\x00(?P=size)", romData)    # LZ77圧縮データの先頭は10 XX YY ZZ 00 00 XX YY ZZになる
    for match in candidateIter:
        matchAddr = match.start()
        uncompSize = struct.unpack('l', romData[matchAddr+1 : matchAddr+4] + "\x00")[0] # 次3バイトが展開後のサイズ（4バイトに合わせないとunpack出来ないので"\x00"をつけている）
        # キリが良い位置にあってサイズが妥当なものを抽出
        if (matchAddr >= 0x600000 and matchAddr % searchStep == 0 and minSize <= uncompSize <= maxSize):
            print( hex(matchAddr) + "\t" + str(uncompSize) + " Bytes" )
            matchList.append( {"startAddr":matchAddr, "uncompSize":uncompSize} )

    return matchList


def decompLZ77_10(data, startAddr):
    u"""
        LZ77(0x10)圧縮されたデータの復号
        参考：http://florian.nouwt.com/wiki/index.php/LZ77_(Compression_Format)

    """

    uncompSize = int.from_bytes(data[startAddr+1:startAddr+4], "little")

    def ascii2bit(a):
        u"""
            ASCII文字列を2進数文字列に変換（1文字8ケタ）
            ※現在未使用
        """

        b = ""
        for c in list(a):   # ASCII文字列の各文字に対して
            b += bin( struct.unpack("B", c)[0] )[2:].zfill(8)
        return b

    def byte2bit(byte):
        u""" byte列を2進数文字列に変換（1バイト8ケタ）
        """

        bit = ""

        if isinstance(byte, int):
            bit = bin(byte)[2:].zfill(8)
        else:
            for b in byte:
                bit += bin(b)[2:].zfill(8)
        return bit

    output = b"" # 復号結果を格納するバイト列
    writePos = 0    # 復号データの書き込み位置
    readPos = startAddr+4 # 圧縮データの読み取り開始位置

    while len(output) < uncompSize:
        currentChar = data[readPos] # ブロックヘッダ（１バイト）の読み込み
        blockHeader = byte2bit(currentChar)    # ブロックヘッダを2進数文字列に変換
        for i in range(8):  # 8ブロックで1セット
            if blockHeader[i] == str(0):
                u"""
                    非圧縮ブロックの処理

                """
                readPos += 1    # 次の読み取り位置へ
                if readPos >= len(data):    # ここ適当
                    break
                currentChar = data[readPos:readPos+1] # 1バイト読み込み（data[readPos]だとbytes型ではなく整数値になる）
                output += currentChar   # そのまま出力
                writePos += 1   # 次の書き込み位置へ
            else:
                u"""
                    圧縮ブロックの処理

                """
                readPos += 2
                blockData = data[readPos-1:readPos+1]   # 2バイトをブロック情報として読み込み
                blockData = byte2bit(blockData)    # ブロック情報を2進数文字列に変換
                #print "Block Data: " + blockData

                offs = int(blockData[4:16], 2) + 1
                #print "Backwards Offset: " + str(offs) + " bytes"

                leng = int(blockData[0:4], 2) + 3
                #print "Copy Length: " + str(leng) + " bytes"
                currentChar = output[writePos - offs : writePos - offs + leng]
                if len(currentChar) < leng: # ここで引っかかった
                    #print "Block Data: " + blockData
                    #print "Backwards Offset: " + str(offs) + " bytes"
                    #print "Copy Length: " + str(leng) + " bytes"
                    # 存在する範囲を超えてコピーするときは直前のパターンを繰り返すことになる
                    #currentChar = "{0:{s}<{N}}".format(currentChar, s=currentChar[0], N = leng)
                    currentChar = currentChar * leng # ここ適当
                    currentChar = currentChar[0:leng]
                    #print binascii.hexlify(currentChar)
                #print currentChar
                #print binascii.hexlify(currentChar)
                output += currentChar
                writePos += leng    # 書き込んだバイト数だけずらす
        readPos += 1

    output = output[0:uncompSize]   # 必要な部分だけ切り出し
    return output

def saveFile(data, outName):
    u""" ファイル出力
    """

    try:
        with open(outName, "wb") as outFile:
            outFile.write(data)
    except:
        print(u"ファイルを正しく出力できませんでした")


def main():
    startTime = time.time() # 実行時間計測開始

    # 引数が足りないよ！
    if len(sys.argv) < 3:
        print(u"引数が足りません")
        sys.exit()

    filePath = sys.argv[1]  # 1つめの引数をファイルパスとして格納
    startAddr = int(sys.argv[2], 16)
    name, ext = os.path.splitext(filePath) # ファイル名と拡張子を取得
    outName = name + "_" + hex(startAddr) + ".bin"  # 出力ファイル名

    # ファイルを開く
    try:
        with open(filePath, 'rb') as romFile:   # 読み取り専用、バイナリファイルとして開く
            romData = romFile.read()   # データのバイナリ文字列（バイナリエディタのASCIIのとこみたいな感じ）
            size = len(romData)    # ファイルサイズ
            print( str(size) + " Bytes" )
    except:
        print(u"ファイルを開けませんでした")

    output = decompLZ77_10(romData, startAddr)
    saveFile(output, outName)


    executionTime = time.time() - startTime    # 実行時間計測終了
    print( "Execution Time:\t" + str(executionTime) + " sec" )


if __name__ == '__main__':
    main()
