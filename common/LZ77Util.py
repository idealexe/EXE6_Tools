#!/usr/bin/python
# coding: utf-8
# pylint: disable=C0103, E1101

""" LZ77 Utility  ver 1.0  by ideal.exe

    LZ77圧縮されたデータを検索したり解凍するモジュールです．
"""
import logging
import os
import re
import struct
import sys
import time


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
logger.addHandler(stream_handler)


def detectLZ77(romData, minSize=0x1000, maxSize=0x100000, searchStep=0x4, checkRef=False):
    """ LZ77(0x10)圧縮されてそうなデータの検索

        LZ77圧縮データの先頭はだいたい 10 XX YY ZZ 00 00 XX YY ZZ になる
            10 = LZ77圧縮を示す
            XX YY ZZ = 展開後のファイルサイズ
            00 = 展開後データの先頭、非圧縮を示す
            00 = １つめのフラグバイト（先頭なので必然的に全ビット0となる）
    """
    match_list = []
    candidate_iter = re.finditer(b"\x10(?P<size>...)\x00\x00(?P=size)", romData)

    for match in candidate_iter:
        match_addr = match.start()
        uncompressed_size = struct.unpack('l', romData[match_addr+1:match_addr+4] + b"\x00")[0]  # 次3バイトが展開後のサイズ（4バイトに合わせないとunpack出来ないので"\x00"をつけている）

        # キリが良い位置にあってサイズが妥当なものを抽出
        if match_addr % searchStep == 0 and minSize <= uncompressed_size <= maxSize:
            if checkRef is True:
                # ROM内に圧縮データへのポインタがあるかダブルチェック
                pointer = match_addr.to_bytes(3, "little") + b"\x88"
                pattern = re.compile(re.escape(pointer))
                if re.search(pattern, romData) is None:
                    # ポインタがなかったら無視
                    continue
            match_list.append({"start_addr": match_addr, "uncompressed_size": uncompressed_size})

    for i, item in enumerate(match_list):
        print(str(i) + ":\t" + hex(item["start_addr"]) + "\t" + hex(item["uncompressed_size"]) + " bytes")
    return match_list


def decompLZ77_10(data, start_addr):
    """
        LZ77(0x10)圧縮されたデータの復号
        参考：http://florian.nouwt.com/wiki/index.php/LZ77_(Compression_Format)

    """

    if data[start_addr] != 0x10:
        logging.info("指定したアドレスに圧縮データがありません")
        return False

    uncompressed_size = int.from_bytes(data[start_addr+1:start_addr+4], "little")

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

    output = b""  # 復号結果を格納するバイト列
    writePos = 0    # 復号データの書き込み位置
    read_addr = start_addr + 4  # 圧縮データの読み取り開始位置

    while len(output) < uncompressed_size:
        currentChar = data[read_addr]  # ブロックヘッダ（１バイト）の読み込み
        blockHeader = byte2bit(currentChar)    # ブロックヘッダを2進数文字列に変換
        for i in range(8):  # 8ブロックで1セット
            if blockHeader[i] == str(0):
                """ 非圧縮ブロックの処理
                """
                read_addr += 1    # 次の読み取り位置へ
                if read_addr >= len(data):    # ここ適当
                    break
                currentChar = data[read_addr:read_addr+1]  # 1バイト読み込み（data[read_addr]だとbytes型ではなく整数値になる）
                output += currentChar   # そのまま出力
                writePos += 1   # 次の書き込み位置へ
            else:
                """ 圧縮ブロックの処理
                """
                read_addr += 2
                blockData = data[read_addr-1:read_addr+1]   # 2バイトをブロック情報として読み込み（ビッグエンディアン）
                blockData = byte2bit(blockData)    # ブロック情報を2進数文字列に変換
                logger.debug("Block Data: " + blockData)

                offs = int(blockData[4:16], 2) + 1
                logger.debug("Backwards Offset: " + str(offs) + " bytes")

                leng = int(blockData[0:4], 2) + 3
                logger.debug("Copy Length: " + str(leng) + " bytes")
                currentChar = output[writePos - offs: writePos - offs + leng]
                if len(currentChar) < leng:  # ここで引っかかった
                    # print "Block Data: " + blockData
                    # print "Backwards Offset: " + str(offs) + " bytes"
                    # print "Copy Length: " + str(leng) + " bytes"
                    # 存在する範囲を超えてコピーするときは直前のパターンを繰り返すことになる
                    # currentChar = "{0:{s}<{N}}".format(currentChar, s=currentChar[0], N = leng)
                    currentChar = currentChar * leng  # ここ適当
                    currentChar = currentChar[0:leng]
                    # print binascii.hexlify(currentChar)
                # print currentChar
                # print binascii.hexlify(currentChar)
                output += currentChar
                writePos += leng    # 書き込んだバイト数だけずらす
        read_addr += 1

    output = output[0:uncompressed_size]   # 必要な部分だけ切り出し
    return output


def compress_lz77_0x10(bin_data):
    """
    :param bin_data:
    :return:
    """
    output = b""

    """ ヘッダ
    """
    uncompressed_size = len(bin_data)
    output += b"\x10" + uncompressed_size.to_bytes(3, 'little')

    """ ボディ
    """
    flag_byte = b"\xFF"
    output += flag_byte

    read_addr = 0
    output += bin_data[read_addr: read_addr + 1]
    read_addr += 1
    output += bin_data[read_addr: read_addr + 1]

    return output


def save_file(data, output):
    """ ファイル出力
    """

    try:
        with open(output, "wb") as output_file:
            output_file.write(data)
    except OSError:
        print("ファイルを正しく出力できませんでした")


def main():
    # file_path = "ROCKEXE6_GXX.gba"
    file_path = "tileset_uncomped.bin"
    with open(file_path, "rb") as bin_file:
        bin_data = bin_file.read()
    # detectLZ77(bin_data)
    # save_file(decompLZ77_10(bin_data, 0x5e0724), "tileset_uncomped.bin")
    save_file(compress_lz77_0x10(bin_data), "tileset_uncomped_poc.bin")


if __name__ == '__main__':
    main()
