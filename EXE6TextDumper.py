#!/usr/bin/python
# coding: utf-8

'''
    EXE6 Text Dumper by ideal.exe

    EXE6文字コードによってデータをテキストに変換するプログラム
    会話データの解析などに利用可能

    出力用の文字列を+=で連結する方式からリストに入れていって最後にjoin()で連結する方式にしたら一気に早くなった（40sec -> 8sec）

'''

import re
import os
import sys
import binascii
import time
startTime = time.time() # 実行時間計測開始

# 辞書のインポート
import EXE6Dict
CP_EXE6_1 = EXE6Dict.CP_EXE6_1
CP_EXE6_2 = EXE6Dict.CP_EXE6_2
CP_EXE6_1_inv = EXE6Dict.CP_EXE6_1_inv
CP_EXE6_2_inv = EXE6Dict.CP_EXE6_2_inv

'''
main
'''
# 引数が足りないよ！
if len(sys.argv) < 2:
    print "Usage: >python EXE6TextDumper.py ROCKEXE6"
    quit()

file = sys.argv[1]  # 1つめの引数をファイルパスとして格納
L = []  # 出力するデータの配列

# 2つめの引数があれば出力ファイル名として使う
if len(sys.argv) == 3:
    outName = sys.argv[2]
else:
    outName = "out.txt"

# ファイルを開く
with open(file, 'rb') as romFile:   # 読み取り専用、バイナリファイルとして開く
    data = romFile.read()   # データのバイナリ文字列（バイナリエディタのASCIIのとこみたいな感じ）
    size = len(data)    # ファイルサイズ
    print( str(size) + " Bytes" )

# ダンプ
readPos = 0 # 読み取るアドレス
while readPos < size:
    currentChar = data[readPos]

    # 2バイトフラグなら
    if currentChar == "\xE4":
        readPos += 1  # 次の文字を
        L.append(CP_EXE6_2[ data[readPos] ])    # 2バイト文字として出力

    # \xF5 次の2バイトを使う顔グラフィックの変更
    elif currentChar in ["\xF0", "\xF5"]:
        L.append(CP_EXE6_1[currentChar])
        L.append(binascii.hexlify(data[readPos+1] + data[readPos+2]) + "\n")    # 文字コードの値をそのまま文字列として出力（'\xAB' -> "AB"）
        readPos += 2

    # \xE6 リスト要素の終わりに現れるようなので、\xE6が現れたら次の要素の先頭アドレスを確認できるようにする
    elif currentChar == "\xE6":
        L.append(CP_EXE6_1[currentChar])
        L.append("\n" + hex(readPos+1) + ": ")

    # テキストボックスを開く\xE8の次の1バイトは\0x00，\xE7も同様？
    elif currentChar in ["\xE7", '\xE8']:
        L.append(CP_EXE6_1[currentChar])
        readPos += 1
        L.append(binascii.hexlify(data[readPos]) + '\n')

    # 1バイト文字
    else:
        L.append(CP_EXE6_1[ currentChar ])

    readPos += 1

    if readPos % 10000 == 0:
        sys.stdout.write(".")

# ファイル出力
with open(outName, "wb") as outFile:
    out = "".join(L)    # 配列を一つの文字列に連結
    outFile.write(out)
    print "done"

executionTime = time.time() - startTime    # 実行時間計測終了
print( "Execution Time: " + str(executionTime) + " sec" )
