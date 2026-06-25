---
type: Sidebar UI Flow
title: UIフロー
description: タブ、貼り付け、解析、候補適用、手動LLM、コピーの順に操作する。
tags: [a11y, sidebar, operations]
timestamp: 2026-06-25T00:00:00+09:00
---

# UIフロー

貼り付け、解析、スキップ、上から順に実行、候補確認、コピーの順に操作する。

## タブ構成

- **HTML補正**: 入力HTML、HTML解析、要素数サマリー、LLM利用モード、処理一覧、実行ボタン、スキップ、候補一覧、出力HTML、コピー、リセットを配置する。
- **使い方**: 操作説明、LLM連携説明、検証手順、FAQを後から増やすための仮置きタブ。

タブは配列定義で管理し、`activeTab` を状態として持つ。タブボタンとタブパネルを分離し、追加時にHTML全体を大きく書き換えない。`role="tablist"`、`role="tab"`、`role="tabpanel"`、`aria-selected`、`hidden` を使う。


## 起動時のRULES注入

サイドバーはApps Scriptテンプレート注入方式でルール一覧を初期化する。`Sidebar.html` の `const RULES = <?!= JSON.stringify(normalizeA11ySidebarRulesForClient()) ?>;` を評価するため、起動側の `showA11ySidebar()` は `HtmlService.createTemplateFromFile('Sidebar').evaluate()` を使う。`createHtmlOutputFromFile('Sidebar')` のままだとscriptletがHTMLに残り、クライアント側JavaScriptの構文エラーになる可能性がある。

手動LLM連携はMVPでは `Sidebar.html` 側のクライアントロジックを正とし、外部LLM APIへの自動送信や追加の `google.script.run` 往復は行わない。`ManualLlm.gs` は将来サーバー側ロジックへ切り替える場合の予備として保持する。

## 候補適用UI

1. HTML解析時に iframe の `frameborder` を低リスク自動補正で削除する。
2. 候補作成時に対象要素へ `data-a11y-candidate-id` を付与する。
3. 候補は `candidateId`、`ruleId`、`selectorKey`、`payload` を持つ。
4. 適用時は `data-a11y-candidate-id` で対象要素を再特定する。
5. 出力HTMLを生成する前に `data-a11y-candidate-id` を削除する。

## 対応する操作

- `IMG-W-02`: `title` を入力してiframeへ追加・更新する。
- `HTML-R-15`: `caption` を入力し、table先頭にcaptionを追加する。
- `LINK-R-02` / `LINK-R-04`: 表示テキストだけを置換し、`href` は変更しない。
- `IMG-R-05` / `IMG-R-09`: `alt` を追加・更新する。
- `SKIP-04`: 「残す / 削除する」を選び、削除を選んだ場合だけremoveする。

## 関連

- [ナレッジ索引](../index.md)


## 解析後の進行ガイド

HTML解析後は「HTMLを貼る」「HTML解析」「処理を実行」「候補を確認」「HTMLへ適用」「出力をコピー」の進行ガイドを画面上部に表示します。次に押すべきボタンは「チェック済み処理を上から実行する」です。
