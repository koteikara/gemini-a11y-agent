# sample-input.html レビュー標準手順

`sample-expected-reviewed.html` に到達するため、検出候補に以下の値を入力して適用します。

- IMG-W-02: `title = イベント案内の動画（YouTube）`
- HTML-R-15:
  - 1つ目のtable caption = `イベント案内の日程`
  - 2つ目のtable caption = `資料区分の説明`
- LINK-R-02: `こちら` → `イベント詳細`
- LINK-R-04: `test@example.com` → `メールでお問い合わせ`
- IMG-R-05: `alt="画像"` → `alt="イベント案内ガイド"`
- IMG-R-09: `alt="会場写真"` → `alt="会場写真を拡大して表示"`
- SKIP-04:
  - お問い合わせブロック → 削除する
  - ページトップへブロック → 削除する

HTML-R-08、HTML-R-16、HTML-W-02、HTML-R-21、LINK-R-06、LINK-R-08、LINK-R-09 は検出のみとし、この標準シナリオでは自動変更しません。
