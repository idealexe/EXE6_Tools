# GBA MIDI Corrector
## 概要
Sappyで書き出したMIDIデータをmid2agb.exeで正しく変換できるようにするツールです。

## 説明
SappyのMIDI書き出し機能で出力した標準形式のMIDIデータは、GBAのハードウェア特有のコントロールチェンジ情報が適切に変換されていません。
このツールではそれらの情報をmid2agb.exeで正しく変換できるように修正します。

## 使用方法
* `>python GBA_MIDI_Corrector.py <MIDI FILE>`
* `>python GBA_MIDI_Corrector.py <MIDI FILE> -o <OUTPUT FILE>`

# Sappy Transplant Assistant
## 概要
音源データの移植をサポートするツールです。

## 説明
