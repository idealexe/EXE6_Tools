# EXE6_Tools
![ロゴ](resources/logo.png)

各種データを編集できるかもしれないツール群
* ※開発中のプログラムなので危険です．必ずデータのバックアップを取った状態で使用してください
* コードはだいたいPythonで書いているので実行にはPythonの環境が必要です
* 実行時にインポートエラーが出た場合は適宜該当のライブラリをインストールしてください
* 動作確認環境はWindows10 (64bit) + Python3.6 + PyQt5です

## 実行環境の用意
Windows向けの手順です．他のOSはすんなりインストールできると思います
* AnacondaのPython3系をインストール（現時点では3.6）
  * https://www.continuum.io/downloads#windows
* PyQt5用の仮想環境を作成
  * `conda create -n pyqt5`
  * `activate pyqt5`
* 必要なものをインストール
  * `conda install python=3.5 anaconda`
  * `conda install --channel https://conda.anaconda.org/bpentz pyqt5`

## 各プログラムの説明
詳細は各プログラムのREADMEを参照してください

### EXESpriteReader.py
* スプライトを閲覧するツール
* パレット編集，水平反転，アニメーション数拡張，スプライト結合などの機能付き
* 使用法：`>Python EXESpriteReader.py`でGUIが開きます
  * 引数-fでファイルを指定するとそのファイルを開きます

### GBA_MIDI_Corrector.py
* Sappyで出力した標準形式のMIDIデータをmid2agb.exeで正しく変換できるようにするプログラム
* 使用法：`>Python GBA_MIDI_Corrector.py <MIDIFILE>`

### SappyTransplantAssistant.py
* 音源移植をサポートするツール
* ソングテーブルのアドレスを受け取り，各曲が使用しているボイスセットのポインタを調整することで任意のアドレスに移植可能な音源データを出力します
* 使用例：`>Python SappyTransplantAssistant.py <ROMFILE>`

## その他のプログラムの説明
* テキストデータの編集には[Prof.9氏のTextPet](https://github.com/Prof9/TextPet)を使用することをおすすめします．
* 以下はあまり使い道のない古いテキスト編集プログラムです．

### EXE6Dict.py
* 文字コード，各種アドレスの辞書とエンコード，デコードモジュール

### EXE6TalkEditor.py
* 頑張り次第で自由な会話を作成できるかもしれないツール
  * 会話データのアドレス特定，LZ77展開，独特のフォーマットに沿ってテキストを編集出来る場合は可能です
* ※きちんと名前をつけて保存しないとファイルが書き出されないのでご注意ください
* 使用法：`>Python EXE6TalkEditor.py`でGUIが開きます

### EXE6TextDumper.py
* 辞書に基づいて全データをテキストに変換するプログラム
* 会話データの解析などに利用可能
* 使用法：`>Python EXE6TextDumper.py <ROMFILE>`

### EXE6TextEditor.py
* 各種テキストを編集できるようになるかもしれないツール
* 現在対応しているデータ
  * マップ名
  * チップ説明文
  * エネミー名
  * ナビ名
  * キーアイテム名
  * ナビカス名
* 使用法：`>Python EXE6TextEditor.py`でGUIが開きます
  * Fileメニューから対応しているデータを開きます
  * テキストボックス内の文字列を書き換えてWriteボタンを押すとメモリ上のデータを書き換えます（元のファイルに影響はありません）
    * 元のデータ部分に上書きするので容量を超えた書き込みは出来ません。
    * 書き込むデータが元の容量より少ない場合は文字列の左を\x00で埋めます
  * Saveボタンを押すと保存メニューが開き、書き換えたデータをファイルに保存できます

### EXE6Trans.py
* 辞書に基づいてバイナリとテキストを相互変換するツール
* 使用法：`>Python EXE6Trans.py`でGUIが開きます

### LZ77Util.py
* LZ77圧縮されたデータの検索，展開モジュール
* 使用例：`>Python LZ77Util.py <ROMFILE> 0x75ACBC`
  * ROMFILE内のアドレス`0x75ACBC`からLZ77圧縮されたデータと解釈して展開します

### SpriteDict.py
* EXESpriteReader用の辞書データ
