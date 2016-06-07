# coding:utf-8
import re
import os
import sys

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
    print "Usage: >python EXE6_Text.py ROCKEXE6"
    quit()

file = sys.argv[1]  # 1つめの引数をファイルパスとして格納
out = ""    # 出力するデータ

with open(file, 'rb') as romFile:   # 読み取り専用、バイナリファイルとして開く
    data = romFile.read()   # データのバイナリ文字列（バイナリエディタのASCIIのとこみたいな感じ）
    size = len(data)    # ファイルサイズ
    print str(size) + " Bytes"

    readPos = 0 # 読み取るアドレス
    while readPos < size:
        # 2バイトフラグなら
        if data[readPos] == "\xE4":
            readPos += 1  # 次の文字を
            out += CP_EXE6_2[ data[readPos] ] # 2バイト文字として出力
        elif data[readPos] == "\xF0" or data[readPos] == "\xF5":
            out += CP_EXE6_1[ data[readPos] ]
            out += CP_EXE6_1[ data[readPos+1] ] + CP_EXE6_1[ data[readPos+2] ] + "\n"
            readPos += 2
        # 解析用：\xE6はリスト要素の終わりに現れるようなので、\xE6が現れたら次の要素の先頭アドレスを確認できるようにする
        elif data[readPos] == "\xE6":
            out += CP_EXE6_1[ data[readPos] ]
            out += hex(readPos+1) + ": "
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

with open("out.txt", "wb") as outFile:
    outFile.write(out)
    print "done"
