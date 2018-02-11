#!/usr/bin/python
# coding: utf-8

""" GBA MIDI Corrector by ideal.exe

    Sappyで書き出した標準形式のMIDIデータをmid2agb.exeで正しく変換できるようにするプログラム
    （ループは手作業で・・・）
"""

import time
import os
import re
import struct
import argparse
from logging import getLogger, StreamHandler, INFO

parser = argparse.ArgumentParser(description='Sappyで書き出した標準形式のMIDIデータをmid2agb.exeで正しく変換できるようにします')
parser.add_argument("file", help="修正するMIDIファイル")
parser.add_argument("-o", "--output", help="出力するファイルの名前")
args = parser.parse_args()

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(INFO)
logger.setLevel(INFO)
logger.addHandler(handler)


HEADER_CHUNK_SIZE = 14  # ヘッダーチャンクは14バイト
TRACK_CHUNK_SIZE = 8  # トラックチャンクは8バイト

startTime = time.time()  # 実行時間計測開始
f = args.file  # 1つめの引数をファイルパスとして格納
name, ext = os.path.splitext(f)  # ファイル名と拡張子を取得

if args.output is not None:
    OUTPUT_NAME = args.output
else:
    OUTPUT_NAME = name + "_corr" + ext  # 標準の出力ファイル名

# ファイルを開く
data = b''
try:
    with open(f, 'rb') as midFile:   # 読み取り専用、バイナリファイルとして開く
        data = midFile.read()
except OSError:
    print("ファイルを開けませんでした")

readPos = 0  # 読み取り位置

# ヘッダーの読み取り
header = struct.unpack(">4sLHHH", data[0: HEADER_CHUNK_SIZE])
# chunkType = header[0]
# chunkSize = header[1]
# midFormat = header[2]
trackNum = header[3]
# timeUnit = header[4]
header = data[0: HEADER_CHUNK_SIZE]  # あとで結合するのでとっておく
readPos += HEADER_CHUNK_SIZE

# 各トラックの読み取り
tracks = [] * trackNum
for i in range(trackNum):
    trackChunk = struct.unpack(">4sL", data[readPos: readPos + TRACK_CHUNK_SIZE])
    dataSize = trackChunk[1]
    readPos += TRACK_CHUNK_SIZE
    tracks.append(data[readPos: readPos + dataSize])
    readPos += dataSize

# 各イベントをコントロールチェンジに書き換える
reEvent = re.compile(b"LFOS|LFODL|MODT|XCMD xIECV|XCMD xIECL")  # 検索パターンをコンパイル
for i in range(trackNum):
    while True:
        m = reEvent.search(tracks[i])
        if m is None:   # マッチするパターンがなくなったらおわり
            break

        eventStart = m.start() - 3  # マッチした位置の3バイト前がテキストイベントの開始位置
        n = tracks[i][m.start()-1]  # マッチした位置の1バイト前がデータ長
        eventSize = n + 3  # イベント全体のサイズ

        code = struct.pack("B", 0xB0 + i)
        value = tracks[i][m.end()+1:m.end()+3]  # かなり決め打ち（文字列の後１つスペースを開けて値があることを仮定している）
        value = re.match(b"\d*", value).group()  # 数字部分のみ取り出し

        if value == b"":  # 値が数字ではない場合（MODTを想定）
            value = b"\x00"
        else:
            value = int(value).to_bytes(1, "little")    # b"28" -> (int)28 -> b"0x1C"

        cc = b""
        if m.group() == b"LFOS":
            cc += code + b"\x15" + value   # LFOSのコントロールチェンジは BX 15 VV （Xはチャンネル）
        elif m.group() == b"LFODL":
            cc += code + b"\x1A" + value
        elif m.group() == b"MODT":
            cc += code + b"\x16" + value
        elif m.group() == b"XCMD xIECV":
            cc += code + b"\x1E\x08\x00" + code + b"\x1F" + value
        elif m.group() == b"XCMD xIECL":
            cc += code + b"\x1E\x09\x00" + code + b"\x1F" + value

        tracks[i] = tracks[i][0:eventStart] + cc + \
            tracks[i][eventStart+eventSize:]  # ここで長さが変わってしまうため以前のマッチ位置が使えなくなる->whileで回す方式にした

    dataSizeStr = struct.pack(">L", len(tracks[i]))    # データサイズを更新
    tracks[i] = b"MTrk" + dataSizeStr + tracks[i]   # トラックチャンクを結合

output = b"".join(tracks)
output = b"".join([header, output])

# ファイル出力
try:
    with open(OUTPUT_NAME, "wb") as outFile:
        outFile.write(output)
except OSError:
    print("ファイルを正しく出力できませんでした")

executionTime = time.time() - startTime    # 実行時間計測終了
print("Execution Time:\t" + str(round(executionTime, 3)) + " sec")
