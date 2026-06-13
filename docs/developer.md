# 開発者向け詳細

## 現行の実行環境

Gemini-A11y Agent v1.0 は、社内向けの既存運用を前提として、以下の実行環境を維持します。

- Google Colab
- Google Sheets
- Google Drive

v1.0 では Cloud Run、Web 管理画面、Secret Manager などの新しい実行基盤は導入しません。Google Sheets を処理対象の台帳として扱い、Google Drive を HTML 成果物の保存先として扱います。

## 主要モジュールの責務

### `extractor.py`

- URL から HTML を取得します。
- 指定 XPath を優先して本文 HTML を抽出します。
- `//*[@id="contents_0"]` のような本文コンテナ配下を DOM 順で再構成します。
- XPath 抽出が十分でない場合のフォールバック抽出を担当します。

### `chunker.py`

- 抽出済み HTML を構造ベースで chunk に分割します。
- data table の前にある導入文を保持します。
- 最初の data table より前の連続テキストを、グローバル導入ブロックとして独立させます。
- table 直前の `h4` は日付見出しとして table 側へ紐付けます。
- `更新：YYYY年MM月DD日` 形式の更新行を出力対象から除外します。

### `cleaners.py`

- HTML の前処理、不要属性削除、リンク絶対パス化を担当します。
- data table / layout table の判定と補正を担当します。
- caption / thead / th / scope など、table アクセシビリティ補正のルールベース処理を担当します。
- thead が無い table について、row / col / none の見出し方向をヒューリスティックに判定します。
- YouTube iframe の title 補完に必要な処理を担当します。

### `runner.py`

- メインループのエントリーポイントです。
- Google Sheets から未完了行を読み込みます。
- URL 取得、XPath 抽出、chunk 分割、cleaner、LLM 呼び出し、Drive 保存、Sheets 更新を順に制御します。
- table 単体 LLM 差し戻しと、LLM 戻り値検証後のフォールバックを統括します。
- end-trim と共通部品除去の適用タイミングを制御します。

### `llm_text.py`

- Gemini API 呼び出しを担当します。
- data table のアクセシビリティ修正用プロンプトを生成します。
- 表記正規化用プロンプトを生成します。
- LLM 出力から Markdown フェンスを除去し、利用可能な HTML 文字列として返します。

## 処理フロー

1. Sheets から未完了行取得
2. URL / HTML 取得
3. XPath 抽出
4. chunk 分割
5. `pre_clean`
6. table 補正
7. table 単体 LLM 差し戻し
8. iframe title 補完
9. end-trim / 共通部品除去
10. Drive 保存 / Sheets 更新

## 開発上の制約

- bs4 禁止
  - 新規の検証スクリプトや追加実装では bs4 依存を増やさず、lxml を優先してください。
  - 既存コードに残る bs4 利用の扱いは、別タスクで段階的に整理します。
- 外部ネットワーク前提の `pip install` 禁止
  - Colab 実行時に外部ネットワークから追加パッケージを取得する前提にしないでください。
- lxml 優先
  - HTML 解析、XPath 抽出、回帰検証は lxml ベースで実装してください。
- セル文言は変更しない
  - table 補正では caption / thead / th / scope など構造・アクセシビリティ属性を対象とし、既存セルの文言は変更しません。
