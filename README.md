# Gemini-A11y Agent v1.0

自治体サイトHTMLを対象に、本文抽出・アクセシビリティ補正を自動化するツールです。  
社内でのデータ移行・品質補正プロセスに組み込むことを目的としています。

---

## 対象・前提

- 対象本文：`//*[@id="contents_0"]` 配下
- 目的：
  - table 前の注意文・案内文（導入文）を欠落させない
  - 在宅当番医などの一覧表（data table）をアクセシブルに変換
  - YouTube iframe の title を適切に補完

---

## 主な機能（v1.0）

### 1) iframe（YouTube）title 補完
- YouTube oEmbed から title を取得
- 最大100文字、整形なしで `"<取得タイトル>（YouTube）"` を付与
- 40文字トリムや “…” 付与は行いません

### 2) table（data table）アクセシビリティ補正
- caption / thead / th / scope を整備（セル文言は変更しない）
- thead がある場合：`th scope="col"` を付与
- tbody 先頭列の row header（`th scope="row"`）昇格（ヒューリスティック）
- thead が無い表に対しては、row/col/none を判定して見出し方向を補正（lxmlのルールベース）
  - col：先頭行を `th scope="col"`
  - row：先頭列を `th scope="row"`
  - none：安全側で未変換

### 3) table 前導入文（説明文）欠落対策
- 最初の data table より前の連続テキストは「グローバル導入ブロック」として独立保持
- 日付見出し（h4）は table 側に紐付け（直前 h4 のみ同一ブロック化）
- `更新：YYYY年MM月DD日` 行は出力から除外（運用要件）

### 4) LLM table 修正の安全化（差し戻し方式）
- LLMには table 単体（outerHTML）のみ渡し、DOMノードとして差し戻し
- LLM戻り値は検証し、条件不一致時は元tableを保持して継続（フォールバック）
  - これにより、非table要素の消失事故を構造的に防止

---

## やらないこと（v1.0のNG）
- READMEに書く内容を引き継ぎ書へ重複させない
- iframe title の再トリム・再整形は行わない
- end-trim を全面OFFにはしない
- table の `<colgroup><col/>` は修正対象としない

---

## 既知事項（Known Issues）
- CSS内の `rgb()` が `rgb（...）` のように全角括弧になる場合があります（スタイルが無効化される可能性あり）
- caption の `id` が重複し得る命名になる場合があります（HTML妥当性の観点で次期対応候補）
- table header の row/col/none 判定はヒューリスティックです（安全側で none を選択する場合があります）

---

## 検証済み例（社内確認）
- 佐賀市 休日在宅当番医（https://www.city.saga.lg.jp/main/14256.html）
  - table前導入文の欠落が解消
  - 日付h4見出しが維持
  - 当番医テーブルの先頭行が `th scope="col"` へ補正

---

## 開発メモ（重要）
- chunker 検証用スクリプトは bs4 を使わず lxml で実装すること
- 外部ネットワーク前提の `pip install` は禁止

---

## ドキュメント

- claude-a11y-agent 設計思想の段階的取り込み計画: [`docs/migration-plan-from-claude-a11y-agent.md`](docs/migration-plan-from-claude-a11y-agent.md)
- 開発者向け詳細: [`docs/developer.md`](docs/developer.md)
- 回帰検証手順: [`docs/regression-tests.md`](docs/regression-tests.md)
- 佐賀市 fixture HTML: [`tests/fixtures/html/saga-city/`](tests/fixtures/html/saga-city/)
- 検証用合成fixture: `tests/fixtures/html/saga-city-test/`
- 合成fixture運用手順: [`docs/composite-fixture-workflow.md`](docs/composite-fixture-workflow.md)
- v1.0改善内容: [`docs/v1-improvements-from-legacy.md`](docs/v1-improvements-from-legacy.md)
- v1.0リリースノート: [`docs/release-notes-v1.0.md`](docs/release-notes-v1.0.md)
- v1.0運用手順: [`docs/operations-v1.0.md`](docs/operations-v1.0.md)
- Codex運用フロー: [`docs/codex-workflow.md`](docs/codex-workflow.md)
- 外部支援ツール評価: [`docs/external-tools-evaluation.md`](docs/external-tools-evaluation.md)
- 合成fixtureチェック: `python tools/check_saga_city_test_fixture.py`
- 合成fixture v1.0出力生成: `python tools/run_saga_city_test_fixture_v1.py`
- 合成fixtureバージョン比較: `python tools/compare_saga_city_versions.py`
- Saga City fixture inventory: `tools/check_saga_city_fixture_inventory.py`
- 既知事項と次期対応候補: [`docs/known-issues.md`](docs/known-issues.md)
