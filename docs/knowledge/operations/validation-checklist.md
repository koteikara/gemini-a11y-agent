---
type: Validation Checklist
title: 検証チェックリスト
description: タブ、件数サマリー、候補適用、手動LLM、出力クリーンアップ、コピー・リセットを確認する。
tags: [a11y, sidebar, operations]
timestamp: 2026-06-25T00:00:00+09:00
---

# 検証チェックリスト

`samples/sample-input.html` を使い、サイドバーのタブ、候補適用、手動LLM、出力HTMLを確認する。

## タブUI

- 「HTML補正」「使い方」タブが表示される。
- タブ切替が動作する。
- 選択中タブが視覚的に分かる。
- 非表示タブの内容が混ざって表示されない。
- 使い方タブは仮置き本文を表示し、今後の操作説明、LLM連携説明、検証手順、FAQを増やせる。

## 解析と件数

- iframe 件数が表示される。
- img 件数が表示される。
- table 件数が表示される。
- a 件数が表示される。
- form 件数が表示される。

## 候補適用

- titleなしYouTube iframeが候補になり、titleを入力して適用できる。
- captionなしtableが候補になり、captionを入力して適用できる。
- 「こちら」リンクが候補になり、hrefを変更せずリンク文言を置換できる。
- mailtoリンクが候補になり、mailto hrefを削除せず表示文言を置換できる。
- alt不足または汎用altのリンク画像が候補になり、altを入力して適用できる。
- 画像ファイルへの拡大リンク候補でaltを補正できる。
- 末尾問い合わせブロックが候補になり、「削除する / 残す」を選べる。
- 対象なし、スキップ、要確認、適用済み、一部適用済みの状態遷移を確認できる。

## 手動LLM

- 候補ごとにLLM用プロンプトを生成できる。
- プロンプトをコピーできる。
- LLM回答JSONを貼り戻せる。
- 検証OKの場合だけ入力欄へ反映する。
- 検証NGの場合はHTMLへ適用しない。

## 出力HTML

- iframe の `frameborder` が削除される。
- iframe の `allowfullscreen` は保持される。
- 出力HTMLから `data-a11y-candidate-id` が削除される。
- コピーできる。
- リセットできる。

## 関連

- [ナレッジ索引](../index.md)
