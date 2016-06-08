#!/usr/bin/python
# coding: utf-8

'''
    EXE6 Text Dumper by ideal.exe

    EXE6文字コードによってデータをテキストに変換するプログラム
    会話データの解析などに利用可能

'''

import re
import os
import sys
import binascii

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
out = ""    # 出力するデータ

if len(sys.argv) == 3:
    outName = sys.argv[2]
else:
    outName = "out.txt"

with open(file, 'rb') as romFile:   # 読み取り専用、バイナリファイルとして開く
    data = romFile.read()   # データのバイナリ文字列（バイナリエディタのASCIIのとこみたいな感じ）
    size = len(data)    # ファイルサイズ
    print str(size) + " Bytes"

    readPos = 0 # 読み取るアドレス
    while readPos < size:
        currentChar = data[readPos]
        # 2バイトフラグなら
        if currentChar == "\xE4":
            readPos += 1  # 次の文字を
            out += CP_EXE6_2[ data[readPos] ] # 2バイト文字として出力

        # \xF5 次の2バイトを使う顔グラフィックの変更
        elif currentChar == "\xF0" or currentChar == "\xF5":
            out += CP_EXE6_1[currentChar]
            out += binascii.hexlify(data[readPos+1] + data[readPos+2]) + "\n" # '\xAB' -> "AB"
            readPos += 2

        # 解析用：\xE6はリスト要素の終わりに現れるようなので、\xE6が現れたら次の要素の先頭アドレスを確認できるようにする
        elif currentChar == "\xE6":
            out += CP_EXE6_1[currentChar]
            out += "\n" + hex(readPos+1) + ": "

        # テキストボックスを開く\xE8の次の1バイトは\0x00，\xE7も同様？
        elif currentChar == "\xE8" or currentChar == '\xE7':
            out += CP_EXE6_1[currentChar]
            readPos += 1
            out += binascii.hexlify(data[readPos]) + '\n'


        else:
            out += CP_EXE6_1[ data[readPos] ]

        readPos += 1

        if readPos % 10000 == 0:
            sys.stdout.write(".")

    '''
    # ASCIIとバイト文字列が一致するかの判定
    if "N" == "\x4e":
        print "true"
    else:
        print "false"
    # 一致した（小文字でも一致する）
    '''

with open(outName, "wb") as outFile:
    outFile.write(out)
    print "done"
