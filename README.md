# EXE6_Tools
各種データを編集できるかもしれないツール群
* ※開発中のプログラムなので危険です。必ずデータのバックアップを取った状態で使用してください
* コードはだいたいPythonで書いているので実行にはPythonの環境が必要です
* 動作確認環境はWindows10 (64bit) + Python2.7.13 + PyQt4です

## 各プログラムの説明
### EXE6Dict.py
* 文字コード，各種アドレスの辞書とエンコード，デコードモジュール

### EXE6TalkEditor.py
* 頑張り次第で自由な会話を作成できるかもしれないツール
  * 会話データのアドレス特定，LZ77展開，独特のフォーマットに沿ってテキストを編集出来る場合は可能です
* ※きちんと名前をつけて保存しないとファイルが書き出されないのでご注意ください
* 使用法：`>Python EXE6TalkEditor.py`

### EXE6TextDumper.py
* 辞書に基づいて全データをテキストに変換するプログラム
* 会話データの解析などに利用可能

### EXE6TextEditor.py
* 各種テキストを編集できるようになるかもしれないツール
* 現在対応しているデータ
  * マップ名
  * チップ説明文
  * エネミー名
  * ナビ名
  * キーアイテム名
  * ナビカス名
* 使用法：`>Python EXE6TextEditor.py`
  * Fileメニューから対応しているデータを開きます
  * テキストボックス内の文字列を書き換えてWriteボタンを押すとメモリ上のデータを書き換えます（元のファイルに影響はありません）
    * 元のデータ部分に上書きするので容量を超えた書き込みは出来ません。
    * 書き込むデータが元の容量より少ない場合は文字列の左を\x00で埋めます
  * Saveボタンを押すと保存メニューが開き、書き換えたデータをファイルに保存できます

### EXE6Trans.py
* 辞書に基づいてバイナリとテキストを相互変換するツール

### LZ77Util.py
* LZ77圧縮されたデータの検索，展開モジュール
* 使用例：`>Python LZ77Util.py <ROMFILE> 0x75ACBC`
  * ROMFILE内のアドレス`0x75ACBC`からLZ77圧縮されたデータと解釈して展開します

### SappyTransplantAssistant.py
* 音源移植をサポートするツール
* 使用例：`>Python SappyTransplantAssistant.py <ROMFILE> 0x1494A0 0x700000`
  * ROMFILEの0x1494A0をソングテーブルとして読み取り，ソングテーブル内の曲が使用しているボイスセットを元のアドレス+0x700000でアクセス出来るように調整します

### EXESpriteReader.py
* スプライトを閲覧するツール

### SpriteDict.py
* SpriteReader用の辞書データ

### GBA_MIDI_Corrector.py
* Sappyで出力した標準形式のMIDIデータをmid2agb.exeで正しく変換できるようにするプログラム
