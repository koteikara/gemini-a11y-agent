# Gemini-A11y Agent v1.0 リリースノート

## 位置づけ

v1.0 は社内向け検証版です。  
Colab + Google Sheets + Google Drive の既存運用を維持したまま、自治体HTML本文のアクセシビリティ補正精度を安定させることを目的とします。

## 主な改善

- `#contents_0` 配下本文のDOM順抽出
- table前導入文の保持
- h3 / h4 見出しの保持
- table単体LLM差し戻し
- LLM戻り値検証
- row / col / none によるtable見出し方向判定
- caption / thead / th / scope 補正
- YouTube iframe title 補完
- 更新行のみノードの除外
- Menu / PageTop 誤検知抑制
- old / ai / gold fixture 管理
- saga-city-test 合成fixtureによる回帰検証

## 検証結果

`saga-city-test` 合成fixtureにおいて、`ai-v1.0` と `gold` の比較結果は以下です。

```text
matches_gold: 18
differs_from_gold: 0
regressed: 0
warning: 0
```

`ai-v0` は生成しない方針のため、`previous fixture missing` warning は想定どおりです。

## 代表的に改善確認できた項目

* table前導入文が欠落しない
* h3 / h4 が欠落しない
* 当番医テーブルに caption / thead / th / scope が付与される
* 更新行のみのノードが除外される
* Menu / PageTop が誤検知されない
* `rgb（` や caption id 重複などの既知副作用が発生していない

## 実行環境

* Google Colab
* Google Sheets
* Google Drive
* Gemini API
* 既存の運用環境を維持

## 今回は導入しないもの

* Cloud Run
* Web管理画面
* Secret Manager
* Cloud Scheduler
* 本格的な承認UI

## 主な確認コマンド

```bash
python tools/check_saga_city_test_fixture.py

python tools/compare_saga_city_versions.py \
  --fixture-root tests/fixtures/html/saga-city-test \
  --case sg02395-composite

python tools/regression_check_14256.py tests/fixtures/html/saga-city/ai
python tools/regression_check_14256.py tests/fixtures/html/saga-city/gold
```

## 関連ドキュメント

* `docs/v1-improvements-from-legacy.md`
* `docs/operations-v1.0.md`
* `docs/migration-plan-from-claude-a11y-agent.md`
* `docs/composite-fixture-workflow.md`
* `docs/regression-tests.md`
* `docs/known-issues.md`
* `docs/external-tools-evaluation.md`
