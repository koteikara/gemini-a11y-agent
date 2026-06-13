# 回帰検証手順

## 目的

回帰確認は、v1.0 で修正した本文抽出・table 補正・共通部品除去が、既知の重要ページで継続して機能していることを確認するために行います。

特に、data table 前の導入文欠落、日付見出しの消失、table header 補正の退行、Menu / PageTop / footer などの混入を早期に検出することを目的とします。

## 最初の基準ページ

最初の基準ページは以下です。

- 佐賀市 休日在宅当番医
- https://www.city.saga.lg.jp/main/14256.html

このページは、table 前導入文、日付見出し、当番医 table、共通部品除去の確認に適しています。

## 確認項目

出力 HTML に対して、少なくとも以下を確認します。

- table 前導入文が残る
- `更新：YYYY年MM月DD日` が出ない
- `h3` / `h4` が維持される
- 当番医テーブルは単純に最初の table を使わず、caption/header から特定する
- 当番医テーブルの caption に `令和8年2月11日（水曜日）一覧` または `2月11日` が含まれる
- 当番医テーブルの header text に `診療科` / `医療機関名` / `電話` / `所在地` / `特定健診` がすべて含まれる
- 当番医テーブルに `thead` がある
- 先頭行が `th scope="col"` になっている
- 2行目以降の1列目が `th scope="row"` になっている
- `caption` が存在する
- Menu / PageTop / footer が混入しない

## 検証スクリプト方針

- 検証スクリプトは lxml で実装します。
- bs4 は使用しません。
- 外部ネットワーク前提の `pip install` は行いません。
- 検証対象は、処理後に Drive へ保存された HTML、またはローカルに取得した同等の出力 HTML とします。
- 判定は文字列比較だけに依存せず、可能な限り DOM 構造と XPath で確認します。
- 佐賀市 14256 の検証対象 table は「最初の table」として固定せず、caption/header から当番医テーブルを特定します。優先順位は、完全な対象日 caption、対象日を含む caption と必須 header の組み合わせ、必須 header のみ、最後に従来の table 候補の順です。

## lxml での確認観点

実装時は、以下のような観点で XPath / DOM 検査を行います。

- 導入文候補テキストが table より前に存在すること
- `更新：` で始まる更新行が存在しないこと
- `//h3` と `//h4` が空でないこと
- 対象 table は caption/header から当番医テーブルとして特定できること
- 対象 table の caption に `令和8年2月11日（水曜日）一覧` または `2月11日` が含まれること
- 対象 table の header text に `診療科` / `医療機関名` / `電話` / `所在地` / `特定健診` がすべて含まれること
- 対象 table に `.//thead` が存在すること
- 対象 table のヘッダー行に `.//th[@scope="col"]` が存在すること
- 対象 table の tbody 2行目以降の1列目に `th[@scope="row"]` が存在すること
- 対象 table に `.//caption` が存在すること
- `Menu`、`PageTop`、`footer` 相当の共通部品テキストが出力に含まれないこと

## 運用メモ

回帰確認項目は、今後の自治体ページ追加に応じて増やします。最初は佐賀市 休日在宅当番医を基準にし、同様の table 構造を持つページを追加して、table header row / col / none 判定の安全性を継続確認します。

## Fixture の場所

佐賀市 HTML fixture は `tests/fixtures/html/saga-city/` 配下に配置しています。

- `old/`: 補正前 HTML。回帰差分の参照用であり、必須検証の対象外です。
- `ai/`: AI 補正後 HTML。佐賀市 14256 相当の fixture は `tests/fixtures/html/saga-city/ai/sg02395_0820.html` です。
- `gold/`: 期待 HTML。佐賀市 14256 相当の fixture は `tests/fixtures/html/saga-city/gold/sg02395.html` です。

## 実行例

佐賀市 14256 の処理後 HTML をローカルファイルとして用意し、以下を実行します。
外部ネットワークアクセスや `pip install` は不要です。

```bash
python tools/regression_check_14256.py ./14256.html
python tools/regression_check_14256.py tests/fixtures/html/saga-city/ai/sg02395_0820.html
python tools/regression_check_14256.py tests/fixtures/html/saga-city/gold/sg02395.html
```

`old/` は補正前 HTML のため、必須検証の対象外です。

## fixtureディレクトリ一括検証

```bash
python tools/regression_check_14256.py tests/fixtures/html/saga-city/ai
python tools/regression_check_14256.py tests/fixtures/html/saga-city/gold
```

このチェッカーは佐賀市14256相当ページ専用です。
ディレクトリを指定した場合、以下のみを検証対象とし、それ以外のHTMLは SKIP します。

- `tests/fixtures/html/saga-city/ai/sg02395_0820.html`
- `tests/fixtures/html/saga-city/gold/sg02395.html`

`old/` は補正前HTMLのため、通常の必須検証対象にはしません。

Codex等の実行環境に `lxml` が無い場合、実HTML検証は実行できません。
外部ネットワーク前提の `pip install` は行わず、`lxml` が利用可能な環境で実行してください。

必須検証に失敗した場合は exit code 1 を返します。
`rgb（` や `caption id` 重複は v1.0 既知事項のため warning として扱い、warning のみの場合は exit code 0 を返します。
