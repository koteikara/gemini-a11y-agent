# 合成fixture運用手順

## 1. 目的

`saga-city-test` は実在ページそのものではなく、回帰検証用の合成HTMLです。

このfixtureは、old/gold差分から代表的な修正観点を集約しています。今後は `ai-v0` を生成せず、v1.0出力がgoldに一致するかを確認するために使用します。

旧版からの改善内容は、過去に確認済みの旧版課題と、`ai-v1.0` / `gold` の比較結果をもとに整理します。

## 2. 入力HTML

```text
tests/fixtures/html/saga-city-test/old/sg02395-composite.html
```

## 3. 期待HTML

```text
tests/fixtures/html/saga-city-test/gold/sg02395-composite.html
```

## 4. v1.0 AI出力の配置先

```text
tests/fixtures/html/saga-city-test/ai-v1.0/sg02395-composite.html
```

## 5. 生成方針

1. `ai-v0/sg02395-composite.html` は今後生成しません。
2. v1.0 Gemini-A11y Agentで `old/sg02395-composite.html` を処理し、結果を `ai-v1.0/sg02395-composite.html` に保存します。
3. 実行環境は既存のColab / Sheets / Driveを使います。
4. ただし、検証用HTMLは外部サイトURLではなくローカルHTMLとして扱うため、通常ページ取得処理とは別に、手動または一時的な入力方法で処理します。

## 6. 配置後の確認コマンド

```bash
python tools/check_saga_city_test_fixture.py

python tools/compare_saga_city_versions.py \
  --fixture-root tests/fixtures/html/saga-city-test \
  --case sg02395-composite
```

## 7. 判定

- `ai-v1.0` と `gold` の比較を基本にします。
- `regressed` があれば要確認です。
- `warning` は既知副作用か、新規副作用かを確認します。
- `status: PASS` または warningのみなら社内v1.0確認材料とします。
- `previous fixture missing` warning は、`ai-v0` を生成しない方針のため想定どおりであり、失敗扱いしません。

## 現在の配置状況

- `old/sg02395-composite.html`: 配置済み
- `gold/sg02395-composite.html`: 配置済み
- `ai-v1.0/sg02395-composite.html`: 配置済み
- `ai-v0/sg02395-composite.html`: 今後生成しない

v1.0出力は current vs gold 比較で gold と一致確認済みです。
今後の確認は `old` → `ai-v1.0` → `gold` を基本にします。

## 旧版比較について

当初は `ai-v0` を生成して三者比較する想定でしたが、今後 `ai-v0` は生成しません。

旧版で確認していた課題と、v1.0で改善された内容は以下に整理します。

- [`docs/v1-improvements-from-legacy.md`](v1-improvements-from-legacy.md)

## v1.0出力の生成

合成fixtureの old HTML を現行 v1.0 処理に流す場合は、以下を実行します。

```bash
python tools/run_saga_city_test_fixture_v1.py
```

既存の `ai-v1.0/sg02395-composite.html` を上書きする場合は、明示的に `--overwrite` を付けます。

```bash
python tools/run_saga_city_test_fixture_v1.py --overwrite
```

出力を書き込まず確認する場合は、`--dry-run` を使います。

```bash
python tools/run_saga_city_test_fixture_v1.py --dry-run
```

このスクリプトは通常のSheets/Drive運用を置き換えるものではなく、合成fixtureをv1.0処理へ通すための補助入口です。
