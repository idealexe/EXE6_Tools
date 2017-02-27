#!/usr/bin/python
# coding: utf-8

u"""
    ロックマンエグゼ６の文字コードや各種アドレスの辞書

    ロックマンエグゼ６用文字コード対応表（http://www65.atwiki.jp/mmnbhack/pages/17.html）を少し改変
    エンコードでは文字コード対応表に基づく変換に加えて，解析のために独自の整形を行います．
    デコードではこれらの整形を行ったテキストが正しく元のバイナリと一致するように変換されます．

"""

import binascii
import struct
import sys

# 1バイト文字
CP_EXE6_1 = {
b"\x00":"　",  b"\x01":"０", b"\x02":"１", b"\x03":"２", b"\x04":"３", b"\x05":"４", b"\x06":"５", b"\x07":"６",
b"\x08":"７", b"\x09":"８", b"\x0A":"９", b"\x0B":"ウ", b"\x0C":"ア", b"\x0D":"イ", b"\x0E":"オ", b"\x0F":"エ",
b"\x10":"ケ", b"\x11":"コ", b"\x12":"カ", b"\x13":"ク", b"\x14":"キ", b"\x15":"セ", b"\x16":"サ", b"\x17":"ソ",
b"\x18":"シ", b"\x19":"ス", b"\x1A":"テ", b"\x1B":"ト", b"\x1C":"ツ", b"\x1D":"タ", b"\x1E":"チ", b"\x1F":"ネ",
b"\x20":"ノ", b"\x21":"ヌ", b"\x22":"ナ", b"\x23":"ニ", b"\x24":"ヒ", b"\x25":"ヘ", b"\x26":"ホ", b"\x27":"ハ",
b"\x28":"フ", b"\x29":"ミ", b"\x2A":"マ", b"\x2B":"メ", b"\x2C":"ム", b"\x2D":"モ", b"\x2E":"ヤ", b"\x2F":"ヨ",
b"\x30":"ユ", b"\x31":"ロ", b"\x32":"ル", b"\x33":"リ", b"\x34":"レ", b"\x35":"ラ", b"\x36":"ン", b"\x37":"熱",
b"\x38":"斗", b"\x39":"ワ", b"\x3A":"ヲ", b"\x3B":"ギ", b"\x3C":"ガ", b"\x3D":"ゲ", b"\x3E":"ゴ", b"\x3F":"グ",
b"\x40":"ゾ", b"\x41":"ジ", b"\x42":"ゼ", b"\x43":"ズ", b"\x44":"ザ", b"\x45":"デ", b"\x46":"ド", b"\x47":"ヅ",
b"\x48":"ダ", b"\x49":"ヂ", b"\x4A":"ベ", b"\x4B":"ビ", b"\x4C":"ボ", b"\x4D":"バ", b"\x4E":"ブ", b"\x4F":"ピ",
b"\x50":"パ", b"\x51":"ペ", b"\x52":"プ", b"\x53":"ポ", b"\x54":"ゥ", b"\x55":"ァ", b"\x56":"ィ", b"\x57":"ォ",
b"\x58":"ェ", b"\x59":"ュ", b"\x5A":"ヴ", b"\x5B":"ッ", b"\x5C":"ョ", b"\x5D":"ャ", b"\x5E":"Ａ", b"\x5F":"Ｂ",
b"\x60":"Ｃ", b"\x61":"Ｄ", b"\x62":"Ｅ", b"\x63":"Ｆ", b"\x64":"Ｇ", b"\x65":"Ｈ", b"\x66":"Ｉ", b"\x67":"Ｊ",
b"\x68":"Ｋ", b"\x69":"Ｌ", b"\x6A":"Ｍ", b"\x6B":"Ｎ", b"\x6C":"Ｏ", b"\x6D":"Ｐ", b"\x6E":"Ｑ", b"\x6F":"Ｒ",
b"\x70":"Ｓ", b"\x71":"Ｔ", b"\x72":"Ｕ", b"\x73":"Ｖ", b"\x74":"Ｗ", b"\x75":"Ｘ", b"\x76":"Ｙ", b"\x77":"Ｚ",
b"\x78":"＊", b"\x79":"－", b"\x7A":"×", b"\x7B":"＝", b"\x7C":"：", b"\x7D":"％", b"\x7E":"？", b"\x7F":"＋",
b"\x80":"■", b"\x81":"(ｺｳﾓﾘ)", b"\x82":"ー", b"\x83":"！", b"\x84":"(RV)", b"\x85":"(BX)", b"\x86":"＆", b"\x87":"、",
b"\x88":"。", b"\x89":"．", b"\x8A":"・", b"\x8B":"；", b"\x8C":"’", b"\x8D":"”", b"\x8E":"～", b"\x8F":"／",
b"\x90":"（", b"\x91":"）", b"\x92":"「", b"\x93":"」", b"\x94":"(EX)", b"\x95":"(SP)", b"\x96":"(FZ)", b"\x97":"□",
b"\x98":"＿", b"\x99":"ｚ", b"\x9A":"周", b"\x9B":"え", b"\x9C":"お", b"\x9D":"う", b"\x9E":"あ", b"\x9F":"い",
b"\xA0":"け", b"\xA1":"く", b"\xA2":"き", b"\xA3":"こ", b"\xA4":"か", b"\xA5":"せ", b"\xA6":"そ", b"\xA7":"す",
b"\xA8":"さ", b"\xA9":"し", b"\xAA":"つ", b"\xAB":"と", b"\xAC":"て", b"\xAD":"た", b"\xAE":"ち", b"\xAF":"ね",
b"\xB0":"の", b"\xB1":"な", b"\xB2":"ぬ", b"\xB3":"に", b"\xB4":"へ", b"\xB5":"ふ", b"\xB6":"ほ", b"\xB7":"は",
b"\xB8":"ひ", b"\xB9":"め", b"\xBA":"む", b"\xBB":"み", b"\xBC":"も", b"\xBD":"ま", b"\xBE":"ゆ", b"\xBF":"よ",
b"\xC0":"や", b"\xC1":"る", b"\xC2":"ら", b"\xC3":"り", b"\xC4":"ろ", b"\xC5":"れ", b"\xC6":"究", b"\xC7":"ん",
b"\xC8":"を", b"\xC9":"わ", b"\xCA":"研", b"\xCB":"げ", b"\xCC":"ぐ", b"\xCD":"ご", b"\xCE":"が", b"\xCF":"ぎ",
b"\xD0":"ぜ", b"\xD1":"ず", b"\xD2":"じ", b"\xD3":"ぞ", b"\xD4":"ざ", b"\xD5":"で", b"\xD6":"ど", b"\xD7":"づ",
b"\xD8":"だ", b"\xD9":"ぢ", b"\xDA":"べ", b"\xDB":"ば", b"\xDC":"び", b"\xDD":"ぼ", b"\xDE":"ぶ", b"\xDF":"ぽ",
b"\xE0":"ぷ", b"\xE1":"ぴ", b"\xE2":"ぺ", b"\xE3":"ぱ",
b"\xE4":"<E4>",    b"\xE5":"<E5>",    b"\xE6":"<E6:閉>",    b"\xE7":"<E7:終端>",
b"\xE8":"<E8:開>",    b"\xE9":"<E9:改行>",    b"\xEA":"<EA>",    b"\xEB":"<EB>",
b"\xEC":"<EC:Cursor>",    b"\xED":"<ED:Select>",    b"\xEE":"<EE:Pause>",    b"\xEF":"<skip?>",
b"\xF0":"<F0:ch_speaker>",    b"\xF1":"<F1:Speed>",    b"\xF2":"<F2:消去>",    b"\xF3":"<F3>",
b"\xF4":"<F4:Sound>",    b"\xF5":"<F5:顔>",    b"\xF6":"<F6>",    b"\xF7":"<F7>",
b"\xF8":"<F8>",    b"\xF9":"<F9>",    b"\xFA":"<FA>",    b"\xFB":"<FB>",
b"\xFC":"<FC>",    b"\xFD":"<FD>",    b"\xFE":"<FE>",    b"\xFF":"<FF>"
}

# 2バイト文字（\xE4 + \xXX）
CP_EXE6_2 = {
b"\x00":"ぅ",    b"\x01":"ぁ",    b"\x02":"ぃ",    b"\x03":"ぉ",    b"\x04":"ぇ",    b"\x05":"ゅ",    b"\x06":"ょ",    b"\x07":"っ",
b"\x08":"ゃ",    b"\x09":"a",    b"\x0A":"b",    b"\x0B":"c",    b"\x0C":"d",    b"\x0D":"e",    b"\x0E":"f",    b"\x0F":"g",
b"\x10":"h",    b"\x11":"i",    b"\x12":"j",    b"\x13":"k",    b"\x14":"l",    b"\x15":"m",    b"\x16":"n",    b"\x17":"o",
b"\x18":"p",    b"\x19":"q",    b"\x1A":"r",    b"\x1B":"s",    b"\x1C":"t",    b"\x1D":"u",    b"\x1E":"v",    b"\x1F":"w",
b"\x20":"x",    b"\x21":"y",    b"\x22":"z",    b"\x23":"容",    b"\x24":"量",    b"\x25":"全",    b"\x26":"木",    b"\x27":"(MB)",
b"\x28":"無",    b"\x29":"現",    b"\x2A":"実",    b"\x2B":"○",    b"\x2C":"×",    b"\x2D":"緑",    b"\x2E":"道",    b"\x2F":"不",
b"\x30":"止",    b"\x31":"彩",    b"\x32":"起",    b"\x33":"父",    b"\x34":"集",    b"\x35":"院",    b"\x36":"一",    b"\x37":"二",
b"\x38":"三",    b"\x39":"四",    b"\x3A":"五",    b"\x3B":"六",    b"\x3C":"七",    b"\x3D":"八",    b"\x3E":"陽",    b"\x3F":"十",
b"\x40":"百",    b"\x41":"千",    b"\x42":"万",    b"\x43":"脳",    b"\x44":"上",    b"\x45":"下",    b"\x46":"左",    b"\x47":"右",
b"\x48":"手",    b"\x49":"来",    b"\x4A":"日",    b"\x4B":"目",    b"\x4C":"月",    b"\x4D":"獣",    b"\x4E":"名",    b"\x4F":"人",
b"\x50":"入",    b"\x51":"出",    b"\x52":"山",    b"\x53":"口",    b"\x54":"光",    b"\x55":"電",    b"\x56":"気",    b"\x57":"綾",
b"\x58":"科",    b"\x59":"次",    b"\x5A":"名",    b"\x5B":"前",    b"\x5C":"学",    b"\x5D":"校",    b"\x5E":"省",    b"\x5F":"祐",
b"\x60":"室",    b"\x61":"世",    b"\x62":"界",    b"\x63":"高",    b"\x64":"朗",    b"\x65":"枚",    b"\x66":"野",    b"\x67":"悪",
b"\x68":"路",    b"\x69":"闇",    b"\x6A":"大",    b"\x6B":"小",    b"\x6C":"中",    b"\x6D":"自",    b"\x6E":"分",    b"\x6F":"間",
b"\x70":"系",    b"\x71":"鼻",    b"\x72":"問",    b"\x73":"究",    b"\x74":"門",    b"\x75":"城",    b"\x76":"王",    b"\x77":"兄",
b"\x78":"化",    b"\x79":"葉",    b"\x7A":"行",    b"\x7B":"街",    b"\x7C":"屋",    b"\x7D":"水",    b"\x7E":"見",    b"\x7F":"終",
b"\x80":"新",    b"\x81":"桜",    b"\x82":"先",    b"\x83":"生",    b"\x84":"長",    b"\x85":"今",    b"\x86":"了",    b"\x87":"点",
b"\x88":"井",    b"\x89":"子",    b"\x8A":"言",    b"\x8B":"太",    b"\x8C":"属",    b"\x8D":"風",    b"\x8E":"会",    b"\x8F":"性",
b"\x90":"持",    b"\x91":"時",    b"\x92":"勝",    b"\x93":"赤",    b"\x94":"毎",    b"\x95":"年",    b"\x96":"火",    b"\x97":"改",
b"\x98":"計",    b"\x99":"画",    b"\x9A":"職",    b"\x9B":"体",    b"\x9C":"波",    b"\x9D":"回",    b"\x9E":"外",    b"\x9F":"地",
b"\xA0":"員",    b"\xA1":"正",    b"\xA2":"造",    b"\xA3":"値",    b"\xA4":"合",    b"\xA5":"戦",    b"\xA6":"川",    b"\xA7":"秋",
b"\xA8":"原",    b"\xA9":"町",    b"\xAA":"晴",    b"\xAB":"用",    b"\xAC":"金",    b"\xAD":"郎",    b"\xAE":"作",    b"\xAF":"数",
b"\xB0":"方",    b"\xB1":"社",    b"\xB2":"攻",    b"\xB3":"撃",    b"\xB4":"力",    b"\xB5":"同",    b"\xB6":"武",    b"\xB7":"何",
b"\xB8":"発",    b"\xB9":"少",    b"\xBA":"教",    b"\xBB":"以",    b"\xBC":"白",    b"\xBD":"早",    b"\xBE":"暮",    b"\xBF":"面",
b"\xC0":"組",    b"\xC1":"後",    b"\xC2":"文",    b"\xC3":"字",    b"\xC4":"本",    b"\xC5":"階",    b"\xC6":"明",    b"\xC7":"才",
b"\xC8":"者",    b"\xC9":"向",    b"\xCA":"犬",    b"\xCB":"々",    b"\xCC":"ヶ",    b"\xCD":"連",    b"\xCE":"射",    b"\xCF":"舟",
b"\xD0":"戸",    b"\xD1":"切",    b"\xD2":"土",    b"\xD3":"炎",    b"\xD4":"伊",    b"\xD5":"夫",    b"\xD6":"鉄",    b"\xD7":"国",
b"\xD8":"男",    b"\xD9":"天",    b"\xDA":"老",    b"\xDB":"師",    b"\xDC":"xDC",    b"\xDD":"xDD",    b"\xDE":"xDE",    b"\xDF":"xDF",
b"\xE0":"xE0",    b"\xE1":"xE1",    b"\xE2":"xE2",    b"\xE3":"xE3",    b"\xE4":"xE4",    b"\xE5":"xE5",    b"\xE6":"xE6",    b"\xE7":"xE7",
b"\xE8":"xE8",    b"\xE9":"xE9",    b"\xEA":"xEA",    b"\xEB":"xEB",    b"\xEC":"xEC",    b"\xED":"xED",    b"\xEE":"xEE",    b"\xEF":"xEF",
b"\xF0":"xF0",    b"\xF1":"xF1",    b"\xF2":"xF2",    b"\xF3":"xF3",    b"\xF4":"xF4",    b"\xF5":"xF5",    b"\xF6":"xF6",    b"\xF7":"xF7",
b"\xF8":"xF8",    b"\xF9":"xF9",    b"\xFA":"xFA",    b"\xFB":"xFB",    b"\xFC":"xFC",    b"\xFD":"xFD",    b"\xFE":"xFE",    b"\xFF":"xFF"
}

# 逆引き辞書
CP_EXE6_1_inv = { v:k for k, v in CP_EXE6_1.items() }
CP_EXE6_2_inv = { v:k for k, v in CP_EXE6_2.items() }

# テキストからバイナリに変換するときに半角にも対応する
half = {
"0":b"\x01",    "1":b"\x02",    "2":b"\x03",    "3":b"\x04",    "4":b"\x05",
"5":b"\x06",    "6":b"\x07",    "7":b"\x08",    "8":b"\x09",    "9":b"\x0A",
"A":b"\x5E",    "B":b"\x5F",    "C":b"\x60",    "D":b"\x61",    "E":b"\x62",
"F":b"\x63",    "G":b"\x64",    "H":b"\x65",    "I":b"\x66",    "J":b"\x67",
"K":b"\x68",    "L":b"\x69",    "M":b"\x6A",    "N":b"\x6B",    "O":b"\x6C",
"P":b"\x6D",    "Q":b"\x6E",    "R":b"\x6F",    "S":b"\x70",    "T":b"\x71",
"U":b"\x72",    "V":b"\x73",    "W":b"\x74",    "X":b"\x75",    "Y":b"\x76",
"Z":b"\x77",    "*":b"\x78",    "-":b"\x79",    "=":b"\x7B",    ":":b"\x7C",
"%":b"\x7D",    "?":b"\x7E",    "+":b"\x7F",    "!":b"\x83",    "&":b"\x86",
" ":b"\x00"
}
CP_EXE6_1_inv.update(half)

# グレイガ版の各種アドレス[名前, 先頭アドレス, 終端アドレス]
GXX_Addr_List = [
["マップ名",      "0x6EB560", "0x6EBC09"],
["チップテキスト", "0x70C36E", "0x7102A2"],
["エネミー名",    "0x710FFE", "0x71163F"],
["ナビ名",     "0x7117B0", "0x711B7F"],
["キーアイテム名",  "0x75F094", "0x75F37A"],
["ナビカス名",  "0x75FF39", "0x7600A0"]
]

GXX_TextDataList = [
{"description":"オープニング１", "addr":0x7B27E4, "pointerAddr":0x846C0},
{"description":"オープニング２", "addr":0x7B2D5C, "pointerAddr":0x847E4},
{"description":"オープニング３", "addr":0x7B33F4, "pointerAddr":0x84934},
{"description":"アイリスとロボット犬１", "addr":0x7B3514, "pointerAddr":0x849F3},
{"description":"チュートリアル戦闘前", "addr":0x7B3658, "pointerAddr":0x84B1C},
{"description":"チュートリアル戦闘１", "addr":0x7135E0, "pointerAddr":0x27FE4},
{"description":"チュートリアル戦闘１勝利", "addr":0x7B3774, "pointerAddr":0x84C5B},
{"description":"チュートリアル戦闘２", "addr":0x713D30, "pointerAddr":0x27FE8},
{"description":"チュートリアル戦闘２勝利", "addr":0x7B37EC, "pointerAddr":0x84D27},
{"description":"チュートリアル戦闘３", "addr":0x71428C, "pointerAddr":0x27FEC},
{"description":"チュートリアル戦闘３勝利", "addr":0x7B3868, "pointerAddr":0x84DFF},
{"description":"アイリスとロボット犬２", "addr":0x7B394C, "pointerAddr":0x84EB4},
{"description":"", "addr":0, "pointerAddr":0},
{"description":"", "addr":0, "pointerAddr":0},
{"description":"", "addr":0, "pointerAddr":0},
{"description":"", "addr":0, "pointerAddr":0},
{"description":"マップ名", "addr":0x6EB378, "pointerAddr":0},
{"description":"チップ名１", "addr":0x70B2F4, "pointerAddr":0},
{"description":"チップ名２", "addr":0x70BC4C, "pointerAddr":0},
{"description":"チップ説明１", "addr":0x70C164, "pointerAddr":0},
{"description":"チップ説明２", "addr":0x70EBF0, "pointerAddr":0},
{"description":"クロス能力", "addr":0x710064, "pointerAddr":0},
{"description":"ナビカス名", "addr":0x75FEA0, "pointerAddr":0},
{"description":"", "addr":0, "pointerAddr":0},
{"description":"", "addr":0, "pointerAddr":0}
]

# ファルザー版の各種アドレス
RXX_Addr_List = [
["Map",      "0x6ED62C", "0x6EDCD6"],
["ChipText", "0x70E40E", "0x712342"],
["Enemy",    "0x71309E", "0x7136DF"],
["Navi",     "0x713850", "0x713C1F"],
["KeyItem",  "0x761160", "0x761446"],
["NaviCus",  "0x762005", "0x76216C"]
]

def encodeByEXE6Dict(data):
    u""" バイナリ文字列をエグゼ６のテキストとしてエンコード
    """

    readPos = 0 # 読み取るアドレス
    L = []  # 出力するデータの配列

    while readPos < len(data):
        currentChar = data[readPos].to_bytes(1, "little")

        if currentChar == b"\xE4":
            u""" ２バイト文字フラグ
            """
            readPos += 1  # 次の文字を
            L.append( CP_EXE6_2[ data[readPos].to_bytes(1, "little") ] )  # 2バイト文字として出力

        elif currentChar in [b"\xF0", b"\xF1", b"\xF5"]:
            u""" 次の2バイトを使うコマンド
            """

            if currentChar in [b"\xF5"]:
                L.append("\n")

            #L.append("\n" + hex(readPos) + ": ")
            #L.append("\n\n## ")
            L.append(CP_EXE6_1[currentChar])
            L.append( "[0x" + binascii.hexlify(data[readPos+1:readPos+1+2]) + "]")    # 文字コードの値をそのまま文字列として出力（'\xAB' -> "AB"）
            L.append("\n")

            readPos += 2

        elif currentChar in [b"\xEE"]:
            u""" 次の3バイトを使うコマンド
            """
            L.append(CP_EXE6_1[currentChar])
            L.append( "[0x" + binascii.hexlify(data[readPos+1:readPos+1+3]) + "]")
            L.append("\n")

            readPos += 3

        # \xE6 リスト要素の終わりに現れるようなので、\xE6が現れたら次の要素の先頭アドレスを確認できるようにする
        elif currentChar == b"\xE6":
            L.append(CP_EXE6_1[currentChar])
            #L.append("\n" + hex(readPos+1) + ": ")
            L.append("\n\n@ "  + hex(readPos+1) + " @\n")

        # テキストボックスを開く\xE8の次の1バイトは\0x00，\xE7も同様？
        elif currentChar in [b"\xE7", b"\xE8"]:
            #L.append("\n\n---\n")
            L.append(CP_EXE6_1[currentChar])
            readPos += 1
            L.append( "[0x" + binascii.hexlify(data[readPos]) + "]")
            if currentChar in [b"\xE7"]:
                L.append("\n")
            elif currentChar in [b"\xE8"]:
                L.append("\n")

        elif currentChar in [b"\xE9", b"\xF2"]:
            u""" 改行，テキストウインドウのクリア
            """
            L.append(CP_EXE6_1[ currentChar])
            L.append("\n")

        # 1バイト文字
        else:
            L.append( CP_EXE6_1[ currentChar ] )

        readPos += 1

        if readPos % 10000 == 0:    # 進捗表示
            sys.stdout.write(".")

    result = "".join(L)    # 配列を一つの文字列に連結
    return result


def decodeByEXE6Dict(string):
    u""" エグゼ６のテキストをバイナリ文字列にデコード
    """

    result = b""
    readPos = 0

    while readPos < len(string):
        currentChar = string[readPos]

        if currentChar == "@":
            u""" コメントは@で囲んでいる
            """
            #print "detect @ " + str(readPos)
            readPos += 1
            while string[readPos] != "@":
                readPos += 1
            #print "close @ " + str(readPos)
            readPos += 1
            continue

        # BXなどは(BX)と表記している
        if currentChar == "(":
            readPos += 1
            while string[readPos] != ")":
                currentChar += string[readPos]
                readPos += 1
            currentChar += string[readPos]

        # 改行などは<改行>などのコマンドとして表示している
        if currentChar == "<":
            readPos += 1
            while string[readPos] != ">":
                currentChar += string[readPos]
                readPos += 1
            currentChar += string[readPos]
            result += binascii.unhexlify(currentChar[1:3]) # <F5:顔>のF5だけ取り出して数値に戻す
            readPos += 1
            continue

        # 値は[0037]などのパラメータとして表示している
        if currentChar == "[":
            readPos += 1
            while string[readPos] != "]":
                currentChar += string[readPos]
                readPos += 1
            currentChar += string[readPos]
            result += binascii.unhexlify(currentChar[3:-1]) # [0xHHHH]のHHHHだけ取り出して数値に戻す
            readPos += 1
            continue

        if currentChar in CP_EXE6_2_inv:    # 2バイト文字なら
            result += b"\xE4" + CP_EXE6_2_inv[currentChar]

        elif currentChar in CP_EXE6_1_inv:  # 1バイト文字なら
            result += CP_EXE6_1_inv[currentChar]

        else:   # 辞書に存在しない文字なら
            result += b"\x80"    # ■に置き換え
            print(u"辞書に「" + currentChar + "」と一致する文字がありません")

        readPos += 1

    return result


def exeDataUnpack(data):
    u""" ロックマンエグゼでよく使われてる形式のデータをアンパックする

        [2Byte:１コ目のデータのオフセット][2Byte:２コ目のデータのオフセット]・・・・
        ・
        ・
        ・
        ・
        [nByte:１コ目のデータ]・・・・
    """

    offs = []   # データのオフセット
    firstDataOffs = struct.unpack('H', data[0:2])[0]    # １つ目のデータの開始位置（オフセットテーブルの終端＋１）

    for i in range(0, firstDataOffs, 2):
        offs.append( struct.unpack('H', data[i:i+2])[0] )   # オフセットは２バイト

    L = []
    for j in range(0, len(offs)):
        if j < len(offs)-1:
            L.append(data[offs[j]:offs[j+1]])
        else:
            L.append(data[offs[j]:])    # 最後のデータはオフセットからデータ末尾まで

    return L


def exeDataPack(L):
    u""" データ配列をロックマンエグゼでよく使われてる形式にパックする
    """

    offs = []

    for i in range(0, len(L)):
        if i == 0:
            offs.append( len(L) * 2 )   # １つ目のオフセット値はテーブルサイズ（データ数ｘ２バイト）
        else:
            offs.append( offs[i-1] + len(L[i-1]) )

    offsTable = "".join( [struct.pack('H', o) for o in offs] )
    data = offsTable + "".join(L)
    return data
