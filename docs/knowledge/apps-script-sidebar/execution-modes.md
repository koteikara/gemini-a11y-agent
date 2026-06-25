---
type: Execution Modes
title: 実行モード
description: 標準はLLMなし。手動LLM連携はプロンプトコピー方式。API自動連携は任意拡張。
tags: [a11y, sidebar, operations]
timestamp: 2026-06-25T00:00:00+09:00
---

# 実行モード

標準はLLMなし。手動LLM連携はプロンプトコピー方式。API自動連携は任意拡張。

## 方針

- 既存Colab/Pythonフローは変更しない。
- MVPでは無料のLLMなし処理を標準にする。
- 高リスク変更は自動確定せず要確認候補にする。

## 関連

- [ナレッジ索引](../index.md)


## API連携モード

LLMなし、手動LLM連携に加え、API設定タブでGemini APIキーを保存した場合のみ候補カードからAPI候補生成を実行できます。APIキー未設定時は手入力と手動LLM連携を引き続き利用します。
