#!/usr/bin/python
# coding: utf-8

u"""
    EXE6 Text Dumper by ideal.exe

    EXE6文字コードによってデータをテキストに変換するプログラム
    会話データの解析などに利用可能

    出力用の文字列を+=で連結する方式からリストに入れていって最後にjoin()で連結する方式にしたら一気に早くなった（40sec -> 8sec）

"""

import time
startTime = time.time() # 実行時間計測開始

import binascii
import os
import re
import sys


def encodeByEXE6Dict(data):
    u"""ロックマンエグゼ６のテキストをダンプする
    """

    # 辞書のインポート
    import EXE6Dict
    CP_EXE6_1 = EXE6Dict.CP_EXE6_1
    CP_EXE6_2 = EXE6Dict.CP_EXE6_2
    CP_EXE6_1_inv = EXE6Dict.CP_EXE6_1_inv
    CP_EXE6_2_inv = EXE6Dict.CP_EXE6_2_inv

    readPos = 0 # 読み取るアドレス
    L = []  # 出力するデータの配列

    while readPos < len(data):
        currentChar = data[readPos]

        if currentChar == "\xE4":
            u""" ２バイト文字フラグ
            """
            readPos += 1  # 次の文字を
            L.append( CP_EXE6_2[ data[readPos] ] )  # 2バイト文字として出力

        elif currentChar in ["\xF0", "\xF5"]:
            u""" 次の2バイトを使うコマンド
            """

            #L.append("\n" + hex(readPos) + ": ")
            #L.append("\n\n## ")
            L.append(CP_EXE6_1[currentChar])
            L.append( "[0x" + binascii.hexlify(data[readPos+1] + data[readPos+2]) + "]")    # 文字コードの値をそのまま文字列として出力（'\xAB' -> "AB"）

            if currentChar in ["\xF0", "\xF5"]:
                L.append("\n")

            readPos += 2

        elif currentChar in ["\xEE"]:
            u""" 次の3バイトを使うコマンド
            """

            L.append(CP_EXE6_1[currentChar])
            L.append( "[0x" + binascii.hexlify(data[readPos+1:readPos+4]) + "]")
            readPos += 3

        # \xE6 リスト要素の終わりに現れるようなので、\xE6が現れたら次の要素の先頭アドレスを確認できるようにする
        elif currentChar == "\xE6":
            L.append(CP_EXE6_1[currentChar])
            #L.append("\n" + hex(readPos+1) + ": ")
            #L.append("\n\n---\n")

        # テキストボックスを開く\xE8の次の1バイトは\0x00，\xE7も同様？
        elif currentChar in ["\xE7", "\xE8"]:
            #L.append("\n\n---\n")
            L.append(CP_EXE6_1[currentChar])
            readPos += 1
            L.append( "[0x" + binascii.hexlify(data[readPos]) + "]\n")

        elif currentChar in ["\xE9"]:
            u""" 改行
            """
            L.append(CP_EXE6_1[ currentChar])
            L.append("\n")

        elif currentChar in ["\xF2"]:
            u""" テキストウインドウのクリア
            """
            L.append(CP_EXE6_1[ currentChar])
            #L.append("\n\n---\n")
            L.append("\n")

        # 1バイト文字
        else:
            L.append( CP_EXE6_1[ currentChar ] )

        readPos += 1

        if readPos % 10000 == 0:    # 進捗表示
            sys.stdout.write(".")

    result = "".join(L)    # 配列を一つの文字列に連結
    return result


def main():
    # 引数が足りないよ！
    if len(sys.argv) < 2:
        print "Usage: >python EXE6TextDumper.py ROCKEXE6"
        quit()

    f = sys.argv[1]  # 1つめの引数をファイルパスとして格納
    name, ext = os.path.splitext(f) # ファイル名と拡張子を取得
    L = []  # 出力するデータの配列

    # 2つめの引数があれば出力ファイル名として使う
    if len(sys.argv) == 3:
        outName = sys.argv[2]
    else:
        outName = name + "_text.md"    # 標準の出力ファイル名

    # ファイルを開く
    with open(f, 'rb') as romFile:   # 読み取り専用、バイナリファイルとして開く
        data = romFile.read()   # データのバイナリ文字列（バイナリエディタのASCIIのとこみたいな感じ）
        size = len(data)    # ファイルサイズ
        print( str(size) + " Bytes" )

    result = exe6TextDump(data)

    # ファイル出力
    with open(outName, "wb") as outFile:
        outFile.write(result)
        print "done"

    executionTime = time.time() - startTime    # 実行時間計測終了
    print( "Execution Time: " + str(executionTime) + " sec" )

if __name__ == '__main__':
    main()
