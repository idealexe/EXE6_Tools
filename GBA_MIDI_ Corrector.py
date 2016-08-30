#!/usr/bin/python
# coding: utf-8

'''
    GBA MIDI Corrector by idealexe
    Sappyで出力した標準形式のMIDIデータをmid2agb.exeで正しく変換できるようにするプログラム
    （ループは手作業で・・・）

'''

import time
startTime = time.time() # 実行時間計測開始

import binascii
import os.path
import re
import sys
import struct

# 引数が足りないよ！
if len(sys.argv) < 2:
    print("引数が足りません")
    sys.exit()

f = sys.argv[1]  # 1つめの引数をファイルパスとして格納
name, ext = os.path.splitext(f) # ファイル名と拡張子を取得

# 2つめの引数があれば出力ファイル名として使う
if len(sys.argv) == 3:
    outName = sys.argv[2]
else:
    outName = name + "_corr" + ext  # 標準の出力ファイル名

# ファイルを開く
try:
    with open(f, 'rb') as midFile:   # 読み取り専用、バイナリファイルとして開く
        data = midFile.read()   # データのバイナリ文字列（バイナリエディタのASCIIのとこみたいな感じ）
except:
    print("ファイルを開けませんでした")

readPos = 0 # 読み取り位置

# ヘッダーの読み取り
headerChunkSize = 14 # ヘッダーチャンクは１４バイト
header = struct.unpack(">4sLHHH", data[0 : headerChunkSize])
#print(header)
#chunkType = header[0]
#chunkSize = header[1]
#midFormat = header[2]
trackNum = header[3]
#timeUnit = header[4]
header = data[0 : headerChunkSize]  # あとで結合するのでとっておく
readPos += headerChunkSize

# トラックの読み取り
tracks = [] * trackNum
for i in range(trackNum):
    trackChunkSize = 8  # トラックチャンクは８バイト
    trackChunk = struct.unpack(">4sL", data[readPos : readPos + trackChunkSize])
    dataSize = trackChunk[1]
    readPos += trackChunkSize
    tracks.append( data[readPos : readPos + dataSize] )
    readPos += dataSize

# 各イベントをコントロールチェンジに書き換える
reEvent = re.compile("LFOS|LFODL|MODT|XCMD xIECV|XCMD xIECL") # 検索パターンをコンパイル
for i in range(trackNum):
    while True:
        m = reEvent.search(tracks[i])
        if m == None:   # マッチするパターンがなくなったらおわり
            break

        eventStart = m.start() - 3  # マッチした位置の３バイト前がテキストイベントの開始位置
        n = struct.unpack("B", tracks[i][m.start()-1])[0]   # マッチした位置の１バイト前がデータ長
        eventSize = n + 3;  # イベント全体のサイズ

        code = struct.pack("B", 0xB0 + i)
        value = tracks[i][m.end()+1:m.end()+3]  # かなり決め打ち（文字列の後１つスペースを開けて値があることを仮定している）
        value = re.match("\d*", value).group()  # 数字部分のみ取り出し
        if value == "": # 値が数字ではない場合（MODTを想定）
            value = "0"
        value = struct.pack( "B", int(value) )

        if m.group() == "LFOS":
            cc = code + "\x15" + value   # LFOSのコントロールチェンジは BX 15 VV （Xはチャンネル）
        elif m.group() == "LFODL":
            cc = code + "\x1A" + value
        elif m.group() == "MODT":
            cc = code + "\x16" + value
        elif m.group() == "XCMD xIECV":
            cc = code + "\x1E\x08\x00" + code + "\x1F" + value
        elif m.group() == "XCMD xIECL":
            cc = code + "\x1E\x09\x00" + code + "\x1F" + value

        tracks[i] = tracks[i][0:eventStart] + cc + tracks[i][eventStart+eventSize:] # ここで長さが変わってしまうため以前のマッチ位置が使えなくなる->whileで回す方式にした

    dataSizeStr = struct.pack(">L", len(tracks[i]) )    # データサイズを更新
    tracks[i] = "".join( ["MTrk", dataSizeStr, tracks[i]] ) # トラックチャンクを結合

output = "".join(tracks)
output = "".join( [header, output] )

# ファイル出力
try:
    with open(outName, "wb") as outFile:
        outFile.write(output)
except:
    print("ファイルを正しく出力できませんでした")

executionTime = time.time() - startTime    # 実行時間計測終了
print( "Execution Time:\t" + str( round(executionTime, 3) ) + " sec" )
