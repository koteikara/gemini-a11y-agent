---
type: A11y Rule
title: HTML-R-16 結合セルtable
description: 結合セルtableに関するアクセシビリティ対応ルール。
resource: a11y_agent/rules/a11y_hybrid_detect_fix.jsonl
rule_id: HTML-R-16
tags: [a11y, sidebar, rule]
timestamp: 2026-06-25T00:00:00+09:00
---

# HTML-R-16 結合セルtable

## 目的

HTML断片内の「結合セルtable」に関するアクセシビリティ上の懸念を見つけ、人間が安全に判断できる候補へ整理する。

## サイドバー版での扱い

- 自動変更せず、検出または要確認候補として扱う。
- 標準では外部LLM APIへ自動送信しない。
- 必要に応じて手動LLM連携のプロンプト対象にできる。

## 関連

- [ルール索引](index.md)
- [実行モード](../apps-script-sidebar/execution-modes.md)
