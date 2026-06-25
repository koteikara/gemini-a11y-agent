---
type: Manual LLM Workflow
title: 手動LLM連携
description: ユーザーが任意LLM Web UIへプロンプトを貼り、JSON回答を検証してから適用判断する。
tags: [a11y, sidebar, operations]
timestamp: 2026-06-25T00:00:00+09:00
---

# 手動LLM連携

ユーザーが任意LLM Web UIへプロンプトを貼り、JSON回答を検証してから適用判断する。

## 方針

- 既存Colab/Pythonフローは変更しない。
- MVPでは無料のLLMなし処理を標準にする。
- サイドバーから外部LLM APIへ自動送信しない。
- APIキーを必須にせず、Gemini固定にもせず、ChatGPT / Gemini / Claude など任意のWeb UIへユーザー自身が貼り付ける。
- 高リスク変更は自動確定せず要確認候補にする。

## UIの流れ

1. HTML補正タブでHTMLを解析し、候補を検出する。
2. 候補ごとの「LLM用プロンプトを作成」を押す。
3. サイドバーに表示されたプロンプトをコピーする。
4. 任意のLLM Web UIへ貼り付ける。
5. LLM回答JSONをサイドバーへ貼り戻す。
6. 「回答JSONを検証」を押す。
7. `ruleId` が一致し、HTML全体を書き換えるキーを含まず、`replacementText` / `alt` / `caption` / `title` のいずれかを含む場合だけ、候補入力欄へ反映する。
8. ユーザーが内容を確認してから「HTMLへ適用」を押す。

## 対象になりやすい候補

- `IMG-W-02`: YouTube iframe title案。
- `HTML-R-15`: table caption案。
- `LINK-R-02`: 曖昧リンク文言の置換案。
- `LINK-R-04`: mailtoリンクの表示文言案。
- `IMG-R-05` / `IMG-R-09`: リンク画像や拡大リンク画像のalt案。

## 関連

- [ナレッジ索引](../index.md)


## API連携との違い

手動LLM連携はユーザーがプロンプトをコピーし、任意のLLM画面へ貼り付ける方式です。APIキーは不要で、サイドバーから外部APIへ自動送信しません。API連携では候補カード単位でユーザー確認後に送信します。
