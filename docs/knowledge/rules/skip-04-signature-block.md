---
type: A11y Rule
title: SKIP-04 署名ブロック
description: 署名ブロックに関するアクセシビリティ対応ルール。
resource: a11y_agent/rules/a11y_hybrid_detect_fix.jsonl
rule_id: SKIP-04
tags: [a11y, sidebar, rule]
timestamp: 2026-06-25T00:00:00+09:00
---

# SKIP-04 署名ブロック

## 目的

HTML断片内の「署名ブロック」に関するアクセシビリティ上の懸念を見つけ、人間が安全に判断できる候補へ整理する。

## サイドバー版での扱い

- MVPで検出し、要確認候補として表示する。人間が適用・スキップ・手修正を選ぶ。
- 標準では外部LLM APIへ自動送信しない。
- 必要に応じて手動LLM連携のプロンプト対象にできる。

## 関連

- [ルール索引](index.md)
- [実行モード](../apps-script-sidebar/execution-modes.md)
