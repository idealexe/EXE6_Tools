#!/usr/bin/python
# coding: utf-8
# pylint: disable=C0103, E1101

""" LZ77 Utility  ver 1.0  by ideal.exe

    LZ77圧縮されたデータを検索したり解凍するモジュールです．
"""
import os
import re
import struct
import sys
import time


def detectLZ77(romData, minSize=0x100, maxSize=0x100000, searchStep=0x4, checkRef=False):
    """ LZ77(0x10)圧縮されてそうなデータの検索

        LZ77圧縮データの先頭はだいたい 10 XX YY ZZ 00 00 XX YY ZZ になる
            10 = LZ77圧縮を示す
            XX YY ZZ = 展開後のファイルサイズ
            00 = 展開後データの先頭、非圧縮を示す
            00 = １つめのフラグバイト（先頭なので必然的に全ビット0となる）
    """
    matchList = []
    candidateIter = re.finditer(b"\x10(?P<size>...)\x00\x00(?P=size)", romData)

    for match in candidateIter:
        matchAddr = match.start()
        uncompSize = struct.unpack('l', romData[matchAddr+1:matchAddr+4] + b"\x00")[0]  # 次3バイトが展開後のサイズ（4バイトに合わせないとunpack出来ないので"\x00"をつけている）

        # キリが良い位置にあってサイズが妥当なものを抽出
        if matchAddr % searchStep == 0 and minSize <= uncompSize <= maxSize:
            if checkRef is True:
                # ROM内に圧縮データへのポインタがあるかダブルチェック
                pointer = matchAddr.to_bytes(3, "little") + b"\x88"
                pattern = re.compile(re.escape(pointer))
                if re.search(pattern, romData) is None:
                    # ポインタがなかったら無視
                    continue
            matchList.append({"startAddr": matchAddr, "uncompSize": uncompSize})

    for i, item in enumerate(matchList):
        print(str(i) + ":\t" + hex(item["startAddr"]) + "\t" + hex(item["uncompSize"]) + " bytes")
    return matchList


def decompLZ77_10(data, startAddr):
    """
        LZ77(0x10)圧縮されたデータの復号
        参考：http://florian.nouwt.com/wiki/index.php/LZ77_(Compression_Format)

    """

    if data[startAddr] != 0x10:
        print("指定したアドレスに圧縮データがありません")
        return False

    uncompSize = int.from_bytes(data[startAddr+1:startAddr+4], "little")

    def byte2bit(byte):
        """ byte列を2進数文字列に変換（1バイト8ケタ）
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
                """ 非圧縮ブロックの処理
                """
                readPos += 1    # 次の読み取り位置へ
                if readPos >= len(data):    # ここ適当
                    break
                currentChar = data[readPos:readPos+1] # 1バイト読み込み（data[readPos]だとbytes型ではなく整数値になる）
                output += currentChar   # そのまま出力
                writePos += 1   # 次の書き込み位置へ
            else:
                """ 圧縮ブロックの処理
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
    """ ファイル出力
    """

    try:
        with open(outName, "wb") as outFile:
            outFile.write(data)
    except OSError:
        print("ファイルを正しく出力できませんでした")


def main():
    file_path = sys.argv[1]
    with open(file_path, "rb") as bin_file:
        bin_data = bin_file.read()
    detectLZ77(bin_data)


if __name__ == '__main__':
    main()
