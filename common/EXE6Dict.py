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

OBJECT_TYPE_LIST = {
0x00:"Player-Controlled Navi",
0x01:"Opponent Player-Controlled Navi",
0x10:"Fight on Red Side",
0x11:"Fight on Blue Side",
0x20:"Mystery Data",
0x30:"Rock",
0x70:"Flag",
0x80:"Rock Cube",
0x90:"Guardian",
0xA0:"Metal Cube"
}

ENEMY_LIST={
0x00:"テストウィルス",
0x01:"メットール",
0x02:"メットール2",
0x03:"メットール3",
0x04:"メットールSP",
0x05:"レアットール",
0x06:"レアットール2",
0x07:"アーバルボーイ",
0x08:"アーバルボーイ2",
0x09:"アーバルボーイ3",
0x0A:"アーバルボーイSP",
0x0B:"レアーバルボーイ",
0x0C:"レアーバルボーイ2",
0x0D:"メガリアA",
0x0E:"メガリアH",
0x0F:"メガリアW",
0x10:"メガリアE",
0x11:"レアガリア",
0x12:"レアガリア2",
0x13:"スウォーディン",
0x14:"スウォードラ",
0x15:"スウォータル",
0x16:"スウォーディンSP",
0x17:"レアスウォードラ",
0x18:"レアスウォータル",
0x19:"キラーズアイ",
0x1A:"デモンズアイ",
0x1B:"ジョーカーズアイ",
0x1C:"キラーズアイSP",
0x1D:"レアラージアイ",
0x1E:"レアラーズアイ2",
0x1F:"クエイカー",
0x20:"クエイクドム",
0x21:"クエイクダバ",
0x22:"クエイカーSP",
0x23:"レアクエイカー",
0x24:"レアクエイカー2",
0x25:"キャタック",
0x26:"キャターリン",
0x27:"キャタパルド",
0x28:"キャタックSP",
0x29:"レアャタック",
0x2A:"レアャタック2",
0x2B:"チャンプル",
0x2C:"チャンパー",
0x2D:"チャンプラナ",
0x2E:"チャンプルSP",
0x2F:"レアャンプル",
0x30:"レアャンプル2",
0x31:"ウインドボックス",
0x32:"バキュームファン",
0x33:"ウインドボックス2",
0x34:"バキュームファン2",
0x35:"レアボックス",
0x36:"レアファン",
0x37:"ララパッパ",
0x38:"ララチューバ",
0x39:"ララボーン",
0x3A:"ララミュート",
0x3B:"ララホルン",
0x3C:"ララパッパSP",
0x3D:"ダルスト",
0x3E:"ダルヒータ",
0x3F:"ダルバーナ",
0x40:"ダルストSP",
0x41:"レアダルスト",
0x42:"レアダルスト2",
0x43:"ドルダーラ",
0x44:"ドルデーラ",
0x45:"ドルドーラ",
0x46:"ドルダーラSP",
0x47:"レアドルダーラ",
0x48:"レアドルダーラ2",
0x49:"ヤカーン",
0x4A:"ヤカーン",
0x4B:"スーパーヤカーン",
0x4C:"ヤカーンDX",
0x4D:"ヤカーンSP",
0x4E:"ヤカーンSP",
0x4F:"センボン",
0x50:"マンボン",
0x51:"オクボン",
0x52:"センボンSP",
0x53:"レアセンボン",
0x54:"レアセンボン2",
0x55:"ヒトデスタ",
0x56:"ヒトデキラ",
0x57:"ヒトデット",
0x58:"ヒトデスタSP",
0x59:"レアヒトデスタ",
0x5A:"レアヒトデスタ2",
0x5B:"ツボリュウ",
0x5C:"ライリュウ",
0x5D:"スイリュウ",
0x5E:"モクリュウ",
0x5F:"ハクリュウ",
0x60:"コウリュウ",
0x61:"カカジー",
0x62:"カカダス",
0x63:"カカダッペ",
0x64:"カカジーSP",
0x65:"レアカカジー",
0x66:"レアカカジー2",
0x67:"パルフォロン",
0x68:"パルフォート",
0x69:"パルフォルグ",
0x6A:"パルフォロンSP",
0x6B:"レアパルフォロン",
0x6C:"レアパルフォロン2",
0x6D:"グラサン",
0x6E:"ギャングサン",
0x6F:"ヒットサン",
0x70:"グラサンSP",
0x71:"レアグラサン",
0x72:"レアグラサン2",
0x73:"ボムコーン",
0x74:"メガコーン",
0x75:"ギガコーン",
0x76:"ボムコーンSP",
0x77:"レアコーン",
0x78:"レアコーン2",
0x79:"モリキュー",
0x7A:"モリッチャ",
0x7B:"モリブル",
0x7C:"モリキューSP",
0x7D:"レアモリキュー",
0x7E:"レアモリキュー2",
0x7F:"ハニホー",
0x80:"ハニブーン",
0x81:"ハニバッチ",
0x82:"ハニホーSP",
0x83:"レアハニホー",
0x84:"レアハニホー2",
0x85:"ガンナー",
0x86:"シューター",
0x87:"スナイパー",
0x88:"ガンナーSP",
0x89:"レアガンナー",
0x8A:"レアガンナー2",
0x8B:"ゼロプレーン",
0x8C:"グリーンプレーン",
0x8D:"レッドプレーン",
0x8E:"ブラックプレーン",
0x8F:"レアプレーン",
0x90:"レアプレーン2",
0x91:"アサシンメカ",
0x92:"エレキクラッシャー",
0x93:"デスボルト",
0x94:"アサシンメカSP",
0x95:"アサシンレア",
0x96:"アサシンレア2",
0x97:"スナーム",
0x98:"ジャリーム",
0x99:"デザーム",
0x9A:"スナームSP",
0x9B:"レアスナーム",
0x9C:"レアスナーム2",
0x9D:"アルマン",
0x9E:"アルマッハ",
0x9F:"アルマックス",
0xA0:"アルマンSP",
0xA1:"レアアルマン",
0xA2:"レアアルマン2",
0xA3:"レムゴン",
0xA4:"メタルレムゴン",
0xA5:"ビッグレムゴン",
0xA6:"レムゴンSP",
0xA7:"レアレムゴン",
0xA8:"レアレムゴン2",
0xA9:"ナイトメア",
0xAA:"ブラックメア",
0xAB:"ダークメア",
0xAC:"ナイトメアSP",
0xAD:"ナイトレア",
0xAE:"ナイトレア2",
0xAF:"Flyingarbage",
0xB0:"Flyingarbage",
0xB1:"Flyingarbage",
0xB2:"Nothing",
0xB3:"Nothing",
0xB4:"Nothing",
0xB5:"Totemole",
0xB6:"Totemole",
0xB7:"Totemole",
0xB8:"Totemole",
0xB9:"Totemole",
0xBA:"Totemole",
0xBB:"メットール",
0xBC:"メットール",
0xBD:"メットール",
0xBE:"メットールSP",
0xBF:"レアットール",
0xC0:"レアットール2",
0xC1:"メットール1",
0xC2:"メットール1X",
0xC3:"メットール2",
0xC4:"メットール2X",
0xC5:"メットール3",
0xC6:"メットール3X",
0xC7:"Tuby",
0xC8:"TubyX",
0xC9:"Tuby2",
0xCA:"Tuby2X",
0xCB:"Tuby3",
0xCC:"Tuby3X",
0xCD:"Flag",
0xCE:"Rock",
0xCF:"Otenko",
0xD0:"RockCube",
0xD1:"IceCube",
0xD2:"Nothing",
0xD3:"Nothing",
0xD4:"BombCube",
0xD5:"BlackBomb",
0xD6:"Wind",
0xD7:"Fan",
0xD8:"TimeBomb",
0xD9:"TimeBomb+",
0xDA:"Nothing",
0xDB:"Anubis",
0xDC:"PoisonPharoah",
0xDD:"Fanfare",
0xDE:"Discord",
0xDF:"Timpani",
0xE0:"Silence",
0xE1:"DarkSonic",
0xE2:"VDoll",
0xE3:"Guradian",
0xE4:"Voltz",
0xE5:"AirSpin",
0xE6:"ChaosLord",
0xE7:"RedFruit",
0xE8:"ChemicalFlash",
0xE9:"かいぞうロックマン",
0xEA:"フォルテクロスロックマン",
0x0101:"ヒートマン",
0x0102:"ヒートマンEX",
0x0103:"ヒートマンSP",
0x0104:"ヒートマンRV",
0x0105:"ヒートマンBX",
0x0106:"",
0x0107:"エレキマン",
0x0108:"エレキマンEX",
0x0109:"エレキマンSP",
0x010A:"エレキマンRV",
0x010B:"エレキマンBX",
0x010C:"",
0x010D:"スラッシュマン",
0x010E:"スラッシュマンEX",
0x010F:"スラッシュマンSP",
0x0110:"スラッシュマンRV",
0x0111:"スラッシュマンBX",
0x0112:"",
0x0113:"キラーマン",
0x0114:"キラーマンEX",
0x0115:"キラーマンSP",
0x0116:"キラーマンRV",
0x0117:"キラーマンBX",
0x0118:"",
0x0119:"チャージマン",
0x011A:"チャージマンEX",
0x011B:"チャージマンSP",
0x011C:"チャージマンRV",
0x011D:"チャージマンBX",
0x011E:"",
0x011F:"アクアマン",
0x0120:"アクアマンEX",
0x0121:"アクアマンSP",
0x0122:"アクアマンRV",
0x0123:"アクアマンBX",
0x0124:"",
0x0125:"トマホークマン",
0x0126:"トマホークマンEX",
0x0127:"トマホークマンSP",
0x0128:"トマホークマンRV",
0x0129:"トマホークマンBX",
0x012A:"",
0x012B:"テングマン",
0x012C:"テングマンEX",
0x012D:"テングマンSP",
0x012E:"テングマンRV",
0x012F:"テングマンBX",
0x0130:"",
0x0131:"グランドマン",
0x0132:"グランドマンEX",
0x0133:"グランドマンSP",
0x0134:"グランドマンRV",
0x0135:"グランドマンBX",
0x0136:"",
0x0137:"ダストマン",
0x0138:"ダストマンEX",
0x0139:"ダストマンSP",
0x013A:"ダストマンRV",
0x013B:"ダストマンBX",
0x013C:"",
0x013D:"ブルース",
0x013E:"ブルースEX",
0x013F:"ブルースSP",
0x0140:"ブルースFZ",
0x0141:"ブルースBX",
0x0142:"",
0x0143:"ブラストマン",
0x0144:"ブラストマンEX",
0x0145:"ブラストマンSP",
0x0146:"ブラストマンRV",
0x0147:"ブラストマンBX",
0x0148:"",
0x0149:"ダイブマン",
0x014A:"ダイブマンEX",
0x014B:"ダイブマンSP",
0x014C:"ダイブマンRV",
0x014D:"ダイブマンBX",
0x014E:"",
0x014F:"サーカスマン",
0x0150:"サーカスマンEX",
0x0151:"サーカスマンSP",
0x0152:"サーカスマンRV",
0x0153:"サーカスマンBX",
0x0154:"",
0x0155:"ジャッジマン",
0x0156:"ジャッジマンEX",
0x0157:"ジャッジマンSP",
0x0158:"ジャッジマンRV",
0x0159:"ジャッジマンBX",
0x015A:"",
0x015B:"エレメントマン",
0x015C:"エレメントマンEX",
0x015D:"エレメントマンSP",
0x015E:"エレメントマンRV",
0x015F:"エレメントマンBX",
0x0160:"",
0x0161:"ハクシャク",
0x0162:"ハクシャクEX",
0x0163:"ハクシャクSP",
0x0164:"ハクシャクRV",
0x0165:"ハクシャクBX",
0x0166:"",
0x0167:"カーネル",
0x0168:"カーネルEX",
0x0169:"カーネルSP",
0x016A:"カーネルRV",
0x016B:"カーネルBX",
0x016C:"",
0x016D:"フォルテ",
0x016E:"フォルテBX",
0x016F:"フォルテSP",
0x0170:"フォルテSP",
0x0171:"フォルテBX",
0x0172:"フォルテXX",
0x0173:"グレイガ",
0x0174:"グレイガEX",
0x0175:"グレイガSP",
0x0176:"グレイガRV",
0x0177:"グレイガBX",
0x0178:"",
0x0179:"ファルザー",
0x017A:"ファルザーEX",
0x017B:"ファルザーSP",
0x017C:"ファルザーRV",
0x017D:"ファルザーBX",
0x017E:"",
0x017F:"ハクシャク",
0x0180:"ハクシャクEX",
0x0181:"ハクシャクSP",
0x0182:"ハクシャクRV",
0x0183:"ハクシャクBX",
0x0184:"",
0x0185:"グレイガビースト",
0x0186:"グレイガビーストEX",
0x0187:"グレイガビーストSP",
0x0188:"グレイガビーストRV",
0x0189:"グレイガビーストBX",
0x018A:"",
0x018B:"ファルザービースト",
0x018C:"ファルザービーストEX",
0x018D:"ファルザービーストSP",
0x018E:"ファルザービーストRV",
0x018F:"ファルザービーストBX",
0x0190:"",
0x0191:"ロックマン",
0x0192:"ロックマン",
0x0193:"ロックマン",
0x0194:"ロックマン",
0x0195:"ロックマン",
0x0196:"ロックマン",
0x0197:"ロックマン",
0x0198:"ロックマン",
0x0199:"ロックマン",
0x019A:"ロックマン",
0x019B:"ロックマン",
0x019C:"ロックマン",
0x019D:"ロックマン",
0x019E:"ロックマン",
0x019F:"ロックマン",
0x01A0:"ロックマン",
0x01A1:"ヒートマン",
0x01A2:"エレキマン",
0x01A3:"スラッシュマン",
0x01A4:"キラーマン",
0x01A5:"チャージマン",
0x01A6:"アクアマン",
0x01A7:"トマホークマン",
0x01A8:"テングマン",
0x01A9:"グランドマン",
0x01AA:"ダストマン",
0x01AB:"ブルース"
}

# 逆引き辞書
ENEMY_LIST_INV = { v:k for k, v in ENEMY_LIST.items() }

MUSIC_LIST = {
0x00:"No Music",
0x01:"Title Screen",
0x02:"WWW Theme",
0x03:"Cyber City Theme",
0x04:"Indoors Theme",
0x05:"School Theme",
0x06:"Seaside Town Theme",
0x07:"Sky Town Theme",
0x08:"Green Town Theme",
0x09:"Graveyard Area Theme",
0x0A:"Mr. Weather Comp Theme",
0x0B:"Event Occurance",
0x0C:"Crisis Theme",
0x0D:"Sad Theme",
0x0E:"Hero Theme",
0x0F:"Transmission",
0x10:"Robo Control Comp",
0x11:"Aquarium Comp",
0x12:"Judge Tree Comp",
0x13:"Network Theme",
0x14:"Undernet Theme",
0x15:"Virus Battle",
0x16:"Boss Battle",
0x17:"Final Battle",
0x18:"Pavilion Theme",
0x19:"Winner Theme",
0x1A:"Loser Theme",
0x1B:"Game Over",
0x1C:"Boss Prelude",
0x1D:"Credits",
0x1E:"Navi Customizer Theme",
0x1F:"Winnter Theme (short version)",
0x20:"Pavilion Comp",
0x21:"Theme of the CyberBeasts",
0x22:"Crossover Battle Theme",
0x23:"Shark Chase Theme",
0x24:"ACDC Town",
0x25:"Expo Theme"
}
