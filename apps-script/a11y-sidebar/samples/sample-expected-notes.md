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

## 手動検証メモ

- サイドバーに「HTML補正」「使い方」タブが表示され、選択中タブが青背景で分かる。
- タブ切替時、非表示タブの内容は `hidden` で隠れ、HTML補正の入力・候補一覧と使い方本文が混ざらない。
- YouTube iframe候補では `title` を入力して対象iframeへ適用できる。
- captionなしtable候補では空captionは適用せず、入力後にtable先頭へ `caption` を追加できる。
- 「こちら」リンク、mailtoリンクは `href` を変更せず表示テキストだけ置換できる。
- リンク画像候補、画像ファイルへの拡大リンク候補は `alt` を追加・更新できる。
- 末尾問い合わせブロックは自動削除せず、「削除する」を選んだ場合だけremoveし、「残す」はスキップ扱いにできる。
- 出力HTMLには `data-a11y-candidate-id` が残らない。
- コピー、リセットが動作する。
