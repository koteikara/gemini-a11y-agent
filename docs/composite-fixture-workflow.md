# 合成fixture運用手順

## 1. 目的

`saga-city-test` は実在ページそのものではなく、回帰検証用の合成HTMLです。

このfixtureは、old/gold差分から代表的な修正観点を集約しています。旧版AI出力とv1.0出力を比較し、精度改善・退行・warningを確認するために使用します。

## 2. 入力HTML

```text
tests/fixtures/html/saga-city-test/old/sg02395-composite.html
```

## 3. 期待HTML

```text
tests/fixtures/html/saga-city-test/gold/sg02395-composite.html
```

## 4. 旧版AI出力の配置先

```text
tests/fixtures/html/saga-city-test/ai-v0/sg02395-composite.html
```

## 5. v1.0 AI出力の配置先

```text
tests/fixtures/html/saga-city-test/ai-v1.0/sg02395-composite.html
```

## 6. 生成手順

1. 旧版Gemini-A11y Agentで `old/sg02395-composite.html` を処理し、結果を `ai-v0/sg02395-composite.html` に保存します。
2. v1.0 Gemini-A11y Agentで `old/sg02395-composite.html` を処理し、結果を `ai-v1.0/sg02395-composite.html` に保存します。
3. 実行環境は既存のColab / Sheets / Driveを使います。
4. ただし、検証用HTMLは外部サイトURLではなくローカルHTMLとして扱うため、通常ページ取得処理とは別に、手動または一時的な入力方法で処理します。

## 7. 配置後の確認コマンド

```bash
python tools/check_saga_city_test_fixture.py

python tools/compare_saga_city_versions.py \
  --fixture-root tests/fixtures/html/saga-city-test \
  --case sg02395-composite
```

## 8. 判定

- `regressed` があれば要確認です。
- `warning` は既知副作用か、新規副作用かを確認します。
- `improved` が導入文・h3/h4・table構造で出ているか確認します。
- `status: PASS` または warningのみなら社内v1.0確認材料とします。
