""" EXE Map の設定ファイル
"""
import os
import sys

PROGRAM_NAME = "EXE MAP  ver 0.8"
MEMORY_OFFSET = 0x8000000
MAP_ENTRY_START = 0x339DC  # for Gregar
MAP_ENTRY_END = 0x33F28  # for Gregar
MAP_ENTRY_SIZE = 0xC
COLOR_NUM_16 = 16
COLOR_NUM_256 = 256
BYTE = 1
WORD = 2
DWORD = 4
TILE_DATA_SIZE_16 = 0x20    # 16色タイルのデータサイズ
TILE_DATA_SIZE_256 = 0x40   # 256色タイルのデータサイズ
ICON_PATH = '../resources/bug.png'
sys.path.append(os.path.join(os.path.dirname(__file__), '../common'))
