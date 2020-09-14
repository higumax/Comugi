# Comugi 
Pythonによる日本語形態素解析エンジン

## Setup
### 1.  辞書のインストール
Comugiは形態素解析ための辞書としてmecab-ipadicを使用します．  
こちらから[mecab-ipadic-2.7.0-20070801.tar.gz](https://taku910.github.io/mecab/#download)をダウンロードし，解凍したディレクトリを`./data` ディレクトリに配置して下さい．


### 2.  辞書データの変換
トップディレクトリで以下のコマンドを実行
```python
python build.py
```
ダブル配列辞書など，Comugiの実行に必要なデータが`./data` 内に生成されます．


## Usage
`main.py` ファイルを実行
```python
python main.py
```
続けて標準入力に入力した文章が分かち書きされて出力されます．  
以下は「吾輩は猫である」と入力したときの結果です．

~~~
> input sentence (press 'exit' to exit)

吾輩は猫である

> 表層型  品詞    品詞1   原型    発音
> __BOS__ None    None    None    None
> 吾輩    名詞    代名詞  吾輩    ワガハイ
> は      助詞    係助詞  は      ワ
> 猫      名詞    一般    猫      ネコ
> で      助動詞  *       だ      デ
> ある    助動詞  *       ある    アル
> __EOS__ None    None    None    None
~~~
### N-best解析
`-n` オプションにつづけて自然数を与えるとN-bestの解析結果が出力されます．（ただしいまのところ実験的機能）