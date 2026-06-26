# 出力HTML品質監査

## 1. 目的

`tools/audit_output_html_quality.py` は、Gemini-A11y Agent v1.0 の試験出力HTMLを手書き報告ではなく機械的に監査するためのツールです。任意のHTML出力ディレクトリを読み取り、問題箇所を検出・分類し、重大度、ファイル名、行番号または周辺HTML断片、修正方針候補を Markdown / CSV に出力します。

## 2. 使い方

```bash
python tools/audit_output_html_quality.py \
  --input-dir local/validation-smoke-outputs \
  --output-md local/validation-smoke-report.md \
  --output-csv local/validation-smoke-report.csv
```

重大問題がある場合、終了コードは `1` です。レポートだけ生成したい場合は `--no-fail` を指定します。

```bash
python tools/audit_output_html_quality.py \
  --input-dir local/validation-smoke-outputs \
  --output-md local/validation-smoke-report.md \
  --output-csv local/validation-smoke-report.csv \
  --no-fail
```

標準出力には `status`、ファイル数、重大度別件数、レポートパスが表示されます。

## 3. 入力ディレクトリ

実HTMLはリポジトリにコミットしません。ローカル検証では次のような `.gitignore` 対象の `local/` 配下に置きます。

```text
local/validation-smoke-outputs/
  anjo_001.html
  urasoe_001.html
  hirosaki_001.html
  fukuyama_001.html
  toyohashi_001.html
```

## 4. 出力レポート

Markdown レポートには以下を含みます。

1. Summary
2. File Results
3. Critical Issues
4. High Issues
5. Medium Issues
6. Table Metrics
7. Repeated Noise
8. Suggested Next Actions

CSV は次の列を出力します。

```text
file,severity,rule_id,line,message,snippet,suggestion
```

## 5. 検査ルール一覧

| rule_id | 内容 | 重大度 |
| --- | --- | --- |
| OUT-TABLE-001 | 非標準tableタグ `<row>` / `<cell>` | Critical |
| OUT-TABLE-002 | table外の `tr` / `td` / `th` 疑い | Critical |
| OUT-TABLE-003 | captionなしtable | High |
| OUT-TABLE-004 | th / scope不足 | Medium |
| OUT-TABLE-005 | エスケープされた壊れた閉じタグらしき断片 | Critical |
| OUT-TABLE-006 | captionが汎用的すぎるtable | High |
| OUT-TABLE-007 | table内の行数・列数が極端に不安定な箇所 | High |
| OUT-EXTRACT-001 | 本文外要素混入 | High |
| OUT-CMS-001 | CMS制御文字列混入 | High |
| OUT-CMS-002 | 戻りリンク大量混入 | High |
| OUT-ENC-001 | 文字化け | High |
| OUT-ALT-001 | 装飾アイコンalt過剰 | Medium |
| OUT-LINK-001 | 曖昧リンク文言 | Medium |
| OUT-SIZE-001 | 出力HTMLが大きすぎる | Medium |

## 6. 重大度の意味

- Critical: HTML構造破壊など、出力品質の根本問題です。残っている場合は本検証に進みません。
- High: 本文外要素、CMS部品、文字化けなど、品質・可読性に大きく影響する問題です。
- Medium: alt品質、曖昧リンク、サイズ増加要因など、後続修正で改善すべき問題です。
- Low: 参考情報または軽微な注意です。

## 7. 5ページ試験での使い方

5自治体×1ページの出力HTMLを `local/validation-smoke-outputs/` に置き、`--no-fail` 付きで監査します。生成された `local/validation-smoke-report.md` と `.csv` はコミットせず、PR本文や運用ログには件数概要と主な `rule_id` のみを記載します。

## 8. 250ページ本検証前の判定基準

5ページ再試験で Critical が1件でも残る場合、250ページ本検証へ進まない。

High が残る場合も、本文抽出範囲やCMS共通部品除去の影響を確認してから本検証可否を判断します。

## 9. 注意事項

- 実HTML、実URL一覧、Google Sheets ID、Drive ID、APIキー、個人情報はコミットしません。
- このPRの監査ツールは検出・レポート化のみを行い、出力HTMLの修正や hybrid a11y 自動修正の有効化は行いません。
- `runner.py`、`cleaners.py`、`llm_text.py`、fixture、gold、ai-v1.0 出力は変更対象外です。
