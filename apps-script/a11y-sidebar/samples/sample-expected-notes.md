# sample-input.html 期待メモ

- iframe: 1
- img: 2
- table: 2
- a: 7
- form: 0

## 主な期待結果

- `IMG-W-02`: titleなしYouTube iframeを要確認候補にする。
- `HTML-R-15`: captionなしtable 2件を候補にする。
- `HTML-R-16`: rowspanありtableを検出する。
- `LINK-R-02`: 「こちら」リンクを検出する。
- `LINK-R-04`: mailtoおよびメールアドレスラベルを検出する。
- `LINK-R-08`: `other.html#section1` を検出する。
- `LINK-R-09`: `#missing-id` を要確認、`#exists` は対象外。
- `IMG-R-05`: 汎用altのリンク画像を検出する。
- `IMG-R-09`: `large.jpg` への画像リンクを検出する。
- `SKIP-04`: 末尾の問い合わせ・ページトップ風ブロックを候補にする。
