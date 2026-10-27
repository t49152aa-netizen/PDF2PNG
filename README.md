# pdf2png

PDF を 1 ページずつ PNG に変換する CLI ツール。

## インストール
```
pip install -r requirements.txt
```

## GUI 版
```
python pdf2png_gui.py
```
1. 「参照…」で PDF を選択（パスワード付きなら入力ダイアログが出ます）
2. 出力先・ファイル名の文字列・開始番号・桁数・DPI を設定（「出力例」で確認できます）
3. 「変換開始」

※ tkinter を使います。Windows / macOS の公式 Python には同梱。Linux では `sudo apt install python3-tk` などが必要です。

## exe 化 (Windows)
`build.bat` をダブルクリックすると `dist\pdf2png.exe` ができます（Python 3.9 以上が必要）。
できた exe は Python が入っていない PC でもそのまま動きます。

GitHub に push している場合は、Actions の「Build exe」を手動実行（または `v*` タグを push）すると、
Windows 上でビルドされた exe を Artifacts からダウンロードできます。

> PyMuPDF 2.0 以降は、レイアウト解析用モジュール（AI モデル）がインストールされているとそれも読み込みます。
> 画像変換には不要で、exe に含めると起動に失敗するため、`--exclude-module` で除外しています。

## 使い方 (コマンドライン版)
```
python pdf2png.py input.pdf [-o 出力先] [-p 接頭辞] [-s 開始番号] [-z 桁数] [-d DPI] [--password [PW]]
```

| オプション | 説明 | 既定値 |
|---|---|---|
| `-o, --outdir` | 出力ディレクトリ | `.` |
| `-p, --prefix` | ファイル名の先頭文字列 | `PDF名_` |
| `-s, --start` | 連番の開始番号 | `1` |
| `-z, --digits` | 連番のゼロ埋め桁数 | 最終番号の桁数 |
| `-d, --dpi` | 解像度 (DPI) | `150` |
| `--password` | パスワード。値省略で対話入力 | なし |

暗号化 PDF で `--password` を付けなかった場合も、自動でパスワード入力を求めます（3 回まで）。

## 例
```
python pdf2png.py report.pdf -o out -p page_ -s 10 -d 300
# → out/page_10.png, out/page_11.png, ...
python pdf2png.py secret.pdf --password
```
