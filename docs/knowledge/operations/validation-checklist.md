---
type: Validation Checklist
title: 検証チェックリスト
description: タブ、件数サマリー、候補適用、手動LLM、出力クリーンアップ、コピー・リセットを確認する。
tags: [a11y, sidebar, operations]
timestamp: 2026-06-25T00:00:00+09:00
---

# 検証チェックリスト

`samples/sample-input.html` を使い、サイドバーのタブ、候補適用、手動LLM、出力HTMLを確認する。


## Apps Script起動

- `Code.gs` / `Rules.gs` / `RuleEngine.gs` / `ManualLlm.gs` / `Sidebar.html` をGoogle SheetsコンテナバインドApps Scriptへ同名ファイルとして配置する。
- `showA11ySidebar()` が `HtmlService.createTemplateFromFile('Sidebar').evaluate()` でサイドバーを作ることを確認する。
- `Sidebar.html` の `const RULES = <?!= JSON.stringify(normalizeA11ySidebarRulesForClient()) ?>;` がテンプレート評価され、ブラウザ上に未展開scriptletとして残らないことを確認する。
- スプレッドシートを再読み込みし、メニュー「アクセシビリティ補正」>「HTML補正サイドバーを開く」からサイドバーが開くことを確認する。
- このリポジトリ内の静的確認だけでは実機起動を保証できないため、Google Sheets上でサイドバー表示まで確認する。

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


## sample-input.html 手動確認手順

1. Google Sheetsを開く。
2. 拡張機能 > Apps Script を開く。
3. `Code.gs` / `Rules.gs` / `RuleEngine.gs` / `ManualLlm.gs` / `Sidebar.html` を同名ファイルとして配置する。
4. スプレッドシートを再読み込みする。
5. メニュー「アクセシビリティ補正」>「HTML補正サイドバーを開く」を選ぶ。
6. サイドバーが開くことを確認する。
7. 「HTML補正」「使い方」タブが表示されることを確認する。
8. `samples/sample-input.html` を入力HTMLに貼り付ける。
9. 「HTML解析」を押す。
10. iframe / img / table / a / form の件数が表示されることを確認する。
11. 16ルールが処理一覧に表示されることを確認する。
12. 「上から順に実行」を押し、候補が表示されることを確認する。
13. 候補を1つ適用し、出力HTMLが変わることを確認する。
14. 出力HTMLに `data-a11y-candidate-id` が残らないことを確認する。
15. 出力HTMLをコピーできることを確認する。

## 関連

- [ナレッジ索引](../index.md)
