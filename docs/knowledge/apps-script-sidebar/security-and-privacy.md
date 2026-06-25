---
type: Security Privacy
title: セキュリティとプライバシー
description: HTMLを外部APIへ自動送信せず、script実行を避け、ユーザー操作を明示する。
tags: [a11y, sidebar, operations]
timestamp: 2026-06-25T00:00:00+09:00
---

# セキュリティとプライバシー

HTMLを外部APIへ自動送信せず、script実行を避け、ユーザー操作を明示する。

## 方針

- 既存Colab/Pythonフローは変更しない。
- MVPでは無料のLLMなし処理を標準にする。
- 手動LLM連携はプロンプト作成とJSON貼り戻しのみで、外部LLM APIへ自動送信しない。
- APIキーを必須にしない。
- Gemini固定にしない。
- 高リスク変更は自動確定せず要確認候補にする。

## 一時属性の扱い

候補を安定して再特定するため、解析後の内部DOMには `data-a11y-candidate-id` を付与する。これはサイドバー内の管理属性であり、出力HTML生成時に必ず削除する。貼り戻し用HTMLへ一時属性を残さない。

## 自動補正の範囲

MVPで自動補正するのは iframe の `frameborder` 削除など低リスクなものに限る。`allowfullscreen` は保持する。table caption文言、リンク文言、img alt、署名ブロック削除、複雑表の再構成、レイアウトtableのdiv化は自動確定しない。

## 関連

- [ナレッジ索引](../index.md)


## APIキーと外部送信

Gemini APIキーはUserPropertiesに保存し、シート本文や使用履歴には記録しません。API連携では候補HTMLや周辺テキストが外部APIへ送信されるため、個人情報、非公開情報、機密情報を含むHTMLでは使用しないでください。
