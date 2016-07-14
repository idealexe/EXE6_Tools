#!/usr/bin/python
# coding: utf-8

# ロックマンのスプライトのポインタ周辺をとりあえず使ってみる
# このアドレスの直前にポインタのテーブルっぽいものがある
# テーブルのポインタが示すアドレスには白玉がある．スプライトのまとまりを区切ってるのだろうか
ROCKEXE6_GXX = {
"startAddr":0x032CA8,
"endAddr":0x033963
}

ROCKEXE6_RXX = {
"startAddr":0x032CA8,
"endAddr":0x033963
}

ROCKEXE5_TOB = {
"startAddr":0x0326E8,
"endAddr":0x033147
}

ROCKEXE5_TOC = {
"startAddr":0x0326EC,
"endAddr":0x03314B
}
