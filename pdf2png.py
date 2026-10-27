#!/usr/bin/env python3
"""PDF を 1 ページずつ PNG 画像に変換するツール。

使用例:
    python pdf2png.py input.pdf
    python pdf2png.py input.pdf -o out -p page_ -s 1 -d 300
    python pdf2png.py secret.pdf --password          # パスワードを対話入力
    python pdf2png.py secret.pdf --password mypass   # パスワードを直接指定
"""

import argparse
import getpass
import sys
from pathlib import Path

import pymupdf


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="PDF を 1 ページずつ PNG に変換します")
    p.add_argument("pdf", type=Path, help="入力 PDF ファイル")
    p.add_argument("-o", "--outdir", type=Path, default=Path("."),
                   help="出力先ディレクトリ (既定: カレントディレクトリ)")
    p.add_argument("-p", "--prefix", default=None,
                   help="出力ファイル名の先頭文字列 (既定: PDF のファイル名 + '_')")
    p.add_argument("-s", "--start", type=int, default=1,
                   help="連番の開始番号 (既定: 1)")
    p.add_argument("-z", "--digits", type=int, default=None,
                   help="連番のゼロ埋め桁数 (既定: 最終番号の桁数に合わせる)")
    p.add_argument("-d", "--dpi", type=int, default=150,
                   help="出力解像度 DPI (既定: 150)")
    p.add_argument("--password", nargs="?", const="", default=None,
                   help="PDF のパスワード。値を省略すると対話入力")
    return p.parse_args(argv)


def open_pdf(path: Path, password):
    doc = pymupdf.open(path)
    if not doc.needs_pass:
        return doc
    # パスワードが未指定・空なら対話入力 (3 回まで)
    if password:
        if doc.authenticate(password):
            return doc
        print("パスワードが正しくありません。", file=sys.stderr)
    for _ in range(3):
        try:
            pw = getpass.getpass(f"'{path.name}' のパスワード: ")
        except (EOFError, KeyboardInterrupt):
            sys.exit("\n中断しました。")
        if doc.authenticate(pw):
            return doc
        print("パスワードが正しくありません。", file=sys.stderr)
    sys.exit("認証に失敗しました。")


def main(argv=None):
    args = parse_args(argv)
    if not args.pdf.is_file():
        sys.exit(f"ファイルが見つかりません: {args.pdf}")
    if args.dpi <= 0:
        sys.exit("--dpi は 1 以上を指定してください。")
    if args.start < 0:
        sys.exit("--start は 0 以上を指定してください。")

    doc = open_pdf(args.pdf, args.password)
    prefix = args.prefix if args.prefix is not None else f"{args.pdf.stem}_"
    last = args.start + doc.page_count - 1
    digits = args.digits if args.digits is not None else len(str(last))
    args.outdir.mkdir(parents=True, exist_ok=True)

    for i, page in enumerate(doc):
        num = args.start + i
        out = args.outdir / f"{prefix}{num:0{digits}d}.png"
        page.get_pixmap(dpi=args.dpi).save(out)
        print(f"[{i + 1}/{doc.page_count}] {out}")

    doc.close()


if __name__ == "__main__":
    main()
