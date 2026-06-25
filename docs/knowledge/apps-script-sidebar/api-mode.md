# API連携モード

Google SheetsサイドバーのAPI連携モードは、候補カード単位でGemini APIへ最小限の候補情報だけを送信し、`replacementText`、`alt`、`caption`、`title` のいずれかを含むJSON回答を候補入力欄へ反映する方式です。HTML全文は送信しません。

## 対応provider

MVPの対応providerはGeminiです。provider差し替えに備え、設定保存、リクエスト生成、レスポンス検証、usage取得、料金計算を分けています。

## APIキー

APIキーは `PropertiesService.getUserProperties()` の `A11Y_GEMINI_API_KEY` にユーザ単位で保存します。シート本文や使用履歴シートには保存しません。

## 対象ルール

- `HTML-R-15`: table caption案
- `LINK-R-02`: 曖昧リンク文言の改善案
- `LINK-R-04`: メールアドレスリンク表示文言案
- `IMG-R-05`: リンク画像alt案
- `IMG-W-02`: iframe title案
- `IMG-W-01`: 画像alt案（画像内容そのものは送信せず、srcや周辺情報ベース）

## ユーザー確認

API候補生成ボタンを押すと、外部APIへ送信する確認ダイアログを表示します。ユーザー操作なしの自動送信はしません。
