#!/usr/bin/python
# coding: utf-8

""" 各ROMにおけるスプライトのアドレスを示すオフセットテーブル

    このオフセットテーブルの直前にもテーブルが存在し，その一つ目のデータがオフセットテーブルの先頭アドレスになっている
    続くデータは各タイプ（ナビ，攻撃エフェクト，置物，etc.）の先頭スプライトのアドレス？

    ROMによってはマイナーバージョンが存在し、それによってアドレスが微妙に異なる場合があるので要チェック
"""

ROCKEXE6_GXX = {
"startAddr":0x032CA8,
"endAddr":0x033967,
"classHeadAddr":[0x032CE0, 0x032D60, 0x032DBC, 0x032F60, 0x0330D0, 0x033150, 0x0332D0, 0x033554, 0x0336D8],
"ignoreAddr":[0x4EA2E4, 0x4EA9DC, 0x506328]
}

MEGAMAN6_GXX = {
"startAddr":0x31CEC,
"endAddr":0x329A8,
"classHeadAddr":[],
"ignoreAddr":[]
}

ROCKEXE6_RXX = {
"startAddr":0x032CA8,
"endAddr":0x033964,
"classHeadAddr":[],
"ignoreAddr":[]
}

MEGAMAN6_FXX = {
"startAddr":0x31CEC,
"endAddr":0x329A4,
"classHeadAddr":[],
"ignoreAddr":[]
}

ROCKEXE5_TOB = {
"startAddr":0x0326E8,
"endAddr":0x033147,
"classHeadAddr":[],
"ignoreAddr":[]
}

ROCKEXE5_TOC = {
"startAddr":0x0326EC,
"endAddr":0x03314B,
"classHeadAddr":[],
"ignoreAddr":[]
}

ROCKEXE4_5RO = {
"startAddr":0x02B39C,
"endAddr":0x02BC73,
"classHeadAddr":[],
"ignoreAddr":[0x50B268]
}

ROCKEXE4_RS = {
"startAddr":0x02787C,
"endAddr":0x028218,
"classHeadAddr":[],
"ignoreAddr":[0x4B5478, 0x4E6684]
}

ROCKEXE4_BM = {
"startAddr":0x027880,
"endAddr":0x02821F,
"classHeadAddr":[],
"ignoreAddr":[]
}

ROCKMAN_EXE3 = {
"startAddr":0,
"endAddr":0,
"classHeadAddr":[],
"ignoreAddr":[]
}

ROCK_EXE3_BK = {
"startAddr":0x248E0,
"endAddr":0x251B4,
"classHeadAddr":[],
"ignoreAddr":[0x441060, 0x6A5F20]
}

ROCKMAN_EXE2 = {
"startAddr":0x1E9D4,
"endAddr":0x1F1A8,
"classHeadAddr":[],
"ignoreAddr":[0x3E9DE0, 0x6C03E4]
}

ROCKMAN_EXE = {
"startAddr":0x12614,
"endAddr":0x12B74,
"classHeadAddr":[],
"ignoreAddr":[]
}

ROCK = {
"startAddr":0,
"endAddr":0,
"classHeadAddr":[],
"ignoreAddr":[]
}
