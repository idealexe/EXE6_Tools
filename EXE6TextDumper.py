#!/usr/bin/python
# coding: utf-8

u"""
    EXE6 Text Dumper by ideal.exe

    EXE6文字コードによってデータをテキストに変換するプログラム
    会話データの解析などに利用可能

    出力用の文字列を+=で連結する方式からリストに入れていって最後にjoin()で連結する方式にしたら一気に早くなった（40sec -> 8sec）

"""

import binascii
import os
import re
import sys
import time

import EXE6Dict

def main():
    startTime = time.time() # 実行時間計測開始

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

    result = EXE6Dict.encodeByEXE6Dict(data)

    # ファイル出力
    with open(outName, "wb") as outFile:
        outFile.write(result)
        print "done"

    executionTime = time.time() - startTime    # 実行時間計測終了
    print( "Execution Time: " + str(executionTime) + " sec" )

if __name__ == '__main__':
    main()
