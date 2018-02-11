#!/usr/bin/python
# coding: utf-8

""" Sappy Transplant Assistant  by ideal.exe

    ボイスセットの移植をサポートするツール
    対話形式になりました．そのうち引数形式にも対応するかもしれません

    ソングテーブルとかのアドレスは他のツールで調べてください
    ソングテーブル以外のアドレスを入力するとどうなるかはわかりません
"""

import argparse
import binascii
import os
import struct
import sys
import time

from logging import getLogger, FileHandler, StreamHandler, DEBUG, INFO
logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(INFO)
file_handler = FileHandler(os.path.join(os.path.dirname(__file__), "SappyTransplantAssistant.log"), "w")
file_handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.addHandler(file_handler)


""" 定数
"""
PROGRAM_NAME = "Sappy Transplant Assistant ver 1.5  by ideal.exe"
OFFSET_SIZE = 4  # オフセットサイズは4バイト
MEMORY_OFFSET = 0x08000000  # ROMがマッピングされるメモリ上のアドレス
SONG_HEADER_SIZE = 4
VOICE_SIZE = 0xC  # 音源定義データのサイズ
DEVICES = {
    "0x0": "Direct Sound",
    "0x1": "Square Wave 1",
    "0x2": "Square Wave 2",
    "0x3": "Wave Memory",
    "0x4": "Noise",
    "0x8": "Direct Sound",
    "0x40": "Multi Sample",
    "0x80": "Drum Part"
}


def main():
    """ Main
    """
    start_time = time.time()  # 実行時間計測開始
    print(PROGRAM_NAME + "\n")

    parser = argparse.ArgumentParser()   # コマンドラインオプション解析
    parser.add_argument("romFile", help="移植元のファイル")
    # parser.add_argument("-t", "--target", help="移植先のファイル")
    args = parser.parse_args()

    file_path = args.romFile
    name, ext = os.path.splitext(file_path)  # ファイル名と拡張子を取得
    rom_data = openFile(file_path)

    sys.stdout.write("ソングテーブルのアドレス（0xXXXXXX）： ")
    song_tb_addr = int(input(), 16)
    sys.stdout.write("移植オフセット（0xXXXXXX）： ")
    transplant_offs = int(input(), 16)
    print("")
    data = voiceTransplanter(rom_data, song_tb_addr, transplant_offs)

    output_name = name + "_Voices_" + hex(transplant_offs) + ext   # 出力ファイル名
    saveFile(data, output_name)
    execution_time = time.time() - start_time     # 実行時間計測終了
    logger.info("\nExecution Time:\t" + str(execution_time) + " sec")


def voiceTransplanter(rom_data, song_tb_addr, transplant_offs):
    """ 指定したソングテーブル内の曲が使用しているボイスセットのポインタを調整する

    """
    logger.info(rom_data[0xA0:0xAC].decode("utf-8"))

    song_addr_list = songTableParser(rom_data, song_tb_addr)
    voices_addr_list = []
    for song in song_addr_list:
        song_data = song_dataParser(rom_data, song)
        if song_data != -1:
            voices_addr_list.append(song_data["voicesAddr"])

    offsAddrList = []   # 処理すべきポインタが追加されていくリスト
    # 切り出す音源データの仮の範囲
    voiceDataStart = voices_addr_list[0]
    voiceDataEnd = voices_addr_list[0]

    for voices in voices_addr_list:
        # ここの処理がいまいちださい
        [offsAddrList, start, end, drumsAddr] = voiceTableParser(rom_data, voices, offsAddrList)
        if len(drumsAddr) > 0:  # ドラムパートを使用していれば
            [offsAddrList, start2, end2, drumsAddr] = \
                voiceTableParser(rom_data, drumsAddr[0], offsAddrList)  # ドラムパートは1個だけ分析する
        else:
            start2 = start
            end2 = end
        # コピーする範囲の更新
        if voiceDataStart > min(start, start2):
            voiceDataStart = min(start, start2)
        if voiceDataEnd < max(end, end2) < len(rom_data):
            voiceDataEnd = max(end, end2)

    # ポインタ書き換え
    for addr in offsAddrList:
        [baseData] = struct.unpack("L", rom_data[addr:addr+OFFSET_SIZE])   # もともとのポインタ
        data = struct.pack("L", baseData + transplant_offs)
        rom_data = writeDataToRom(rom_data, addr, data)
        print(".", end='', flush=True)
    print("done\n")

    print(fmt_hex(voiceDataStart) + "から" + fmt_hex(voiceDataEnd) + "までを音源データとして切り出しました")
    print("出力データを移植先ROMの " + fmt_hex(voiceDataStart + transplant_offs) + " にペーストしてください")
    print("各ボイスセットには元のアドレス＋" + fmt_hex(transplant_offs) + "でアクセス出来ます")
    print("例）" + fmt_hex(voices_addr_list[0]) + " → " + fmt_hex(voices_addr_list[0]+transplant_offs) + "\n")

    return rom_data[voiceDataStart:voiceDataEnd]


def songTableParser(rom_data, startAddr):
    """ ソングテーブルから曲のアドレスを抽出する
    """
    song_addr_list = []
    dataSize = 8    # 1曲分のデータサイズ
    readAddr = startAddr

    count = 0
    while True:
        [addr, data] = struct.unpack("LL", rom_data[readAddr:readAddr+dataSize])
        # dataの詳細は不明だけどエグゼの音源は1F 00 1F 00にしないと音が抜ける（Sappyだと曲グループとして表示されている。1F 00 1F 00 -> 31, 31）

        if addr == 0:
            # addr = 0x00000000が終端らしい
            break

        logger.debug("Entry" + str(count) + " at " + fmt_hex(readAddr) + "{")

        addr -= MEMORY_OFFSET
        logger.debug("\tAddr:\t" + fmt_hex(addr))
        logger.debug("\tData:\t" + fmt_hex(data))

        if data != 0 and addr not in song_addr_list:   # ここ適当（曲のアドレスとそうじゃないアドレスをどうやって区別すべきか検討中
            song_addr_list.append(addr)

        logger.debug("}")
        readAddr += dataSize
        count += 1

    logger.info(str(count) + " entry found\n")
    return song_addr_list


def song_dataParser(rom_data, songAddr):
    """ 曲データを解析する

        各データの辞書を返します
        曲データではないと判断した場合は-1を返します
    """

    readAddr = songAddr

    """ ヘッダ

        ヘッダと言いつつ曲データの末尾にある
    """
    logger.debug("Song at " + fmt_hex(songAddr))
    [trackNum, x1, x2, x3] = struct.unpack("BBBB", rom_data[readAddr:readAddr+SONG_HEADER_SIZE])

    if trackNum == 0:
        return -1

    logger.debug("Track Number:\t" + str(trackNum))
    logger.debug([x1, x2, x3])
    readAddr += SONG_HEADER_SIZE

    # ボイステーブルのアドレス
    voicesAddrPtr = readAddr
    voicesAddr = struct.unpack("L", rom_data[readAddr:readAddr+OFFSET_SIZE])[0] - MEMORY_OFFSET
    readAddr += OFFSET_SIZE
    logger.debug("Voices Addr:\t" + fmt_hex(voicesAddr) + "\n")

    # 各トラックのアドレス
    trackList = []
    trackPtrList = []
    for i in range(trackNum):
        trackAddr = struct.unpack("L", rom_data[readAddr:readAddr+OFFSET_SIZE])[0] - MEMORY_OFFSET
        trackList.append(trackAddr)
        trackPtrList.append(readAddr)
        readAddr += OFFSET_SIZE
        logger.debug("Track" + str(i) + " Addr:\t" + fmt_hex(trackAddr))
    logger.debug("---")

    return {"trackNum": trackNum, "voicesAddr": voicesAddr, "voicesAddrPtr": voicesAddrPtr,
            "trackList": trackList, "trackPtrList": trackPtrList}


def voiceTableParser(rom_data, tableAddr, offsAddrList):
    """ ボイステーブルを解析する

        ボイスセット内のポインタのアドレス，ボイスセットの開始，終了アドレス，使用しているドラムセットのアドレスを返す
    """
    voiceDataStart = tableAddr  # コピーすべきボイスセットの開始地点
    voiceDataEnd = tableAddr   # コピーすべきボイスセットの終了地点

    readAddr = tableAddr
    drumsAddr = []  # ドラム音源はボイスセットの構造を内包しているので後で同様の処理を行う

    for i in range(128):
        [device, baseNote, sweepTime, sweepShift, addr, atk, dec, sus, rel] = \
            struct.unpack("BBBBLBBBB", rom_data[readAddr:readAddr+VOICE_SIZE])
        if addr >= MEMORY_OFFSET and addr - MEMORY_OFFSET < len(rom_data):  # まともなポインタだったら
            addr -= MEMORY_OFFSET
            if readAddr+4 not in offsAddrList:  # まだリストに追加していないなら
                offsAddrList.append(readAddr+4)  # addrの値を保持しているアドレスを記録

            if addr < voiceDataStart:
                voiceDataStart = addr   # ボイステーブルより前に楽器データがあったらそこからコピーしなければいけない

            if device == 0x80 and addr not in drumsAddr:  # 既にリストに追加済みのドラムセットでなければ
                drumsAddr.append(addr)

            elif device in [0x0, 0x8]:
                """ Direct Sound の場合は音源データの終端を探しに行かないといけない

                    データ構造はSampleインポートでインポートしたデータから推測
                """
                [sampleSize] = struct.unpack("L", rom_data[addr+0xC:addr+0x10])
                sampleEnd = addr + 0x10 + sampleSize
                if voiceDataEnd < sampleEnd:
                    voiceDataEnd = sampleEnd

            elif device in [0x40]:
                """ Multi Sampleは複数ポインタを持ってるのでそっちもリストに入れる
                """
                if readAddr + 8 not in offsAddrList:  # まだリストに追加していないなら
                    offsAddrList.append(readAddr + 8)  # addrの値を保持しているアドレスを記録

        readAddr += VOICE_SIZE
        if voiceDataEnd < readAddr:
            voiceDataEnd = readAddr+VOICE_SIZE

    return [offsAddrList, voiceDataStart, voiceDataEnd, drumsAddr]


def writeDataToRom(rom_data, writeAddr, data):
    """ 指定したアドレスから指定したデータを上書きする
    """
    rom_data = rom_data[:writeAddr] + data + rom_data[writeAddr+len(data):]
    return rom_data


def openFile(file_path):
    """ ファイルを開く
    """
    rom_data = b''

    try:
        with open(file_path, 'rb') as romFile:   # 読み取り専用、バイナリファイルとして開く
            rom_data = romFile.read()   # データのバイナリ文字列（バイナリエディタのASCIIのとこみたいな感じ）

    except OSError:
        print("ファイルを開けませんでした")

    return rom_data


def saveFile(data, output_name):
    """ ファイル出力
    """

    try:
        with open(output_name, "wb") as outFile:
            outFile.write(data)
    except OSError:
        print("ファイルを正しく出力できませんでした")


def fmt_hex(num):
    """ 16進数をいい感じに表示する
    """
    return "0x" + hex(num)[2:].upper()


if __name__ == '__main__':
    main()
