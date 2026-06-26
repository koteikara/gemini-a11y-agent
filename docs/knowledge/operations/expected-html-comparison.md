# 期待HTML比較

Google Sheetsサイドバーの「検証」タブで、出力HTMLと期待HTMLを比較する。比較時は `data-a11y-candidate-id` を削除し、タグ間空白・連続空白を正規化する。

- `sample-expected-auto.html`: 解析直後の低リスク自動補正のみを反映する。
- `sample-expected-reviewed.html`: `sample-review-steps.md` の標準値をすべて適用したレビュー済み期待HTML。

不一致の場合は iframe title、table caption、リンク文言、img alt、問い合わせ/ページトップ削除を優先して確認する。
