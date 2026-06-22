# URLレジストリ変換手順

## 1. 目的

5自治体×各50ページの選抜ExcelまたはCSVを、Gemini-A11y Agent v1.0 の既存 `URLレジストリ` シートに貼り付けられる A〜M列のCSVへ変換します。

この手順はローカル作業用です。実URL一覧、Google Sheets ID、Drive ID、APIキー、個人情報はリポジトリに入れません。

## 2. 入力Excel形式

入力ファイルは `local/validation-pages/` など、コミット対象外のローカルディレクトリに置きます。

```text
local/validation-pages/
  安城市.xlsx
  浦添市.xlsx
  弘前市.xlsx
  福山市.xlsx
  豊橋市.xlsx
```

各Excelには、少なくとも次のシートがある想定です。

- `<自治体名>_概要`
- `対象ページ`

`対象ページ` シートには、次のヘッダー行が必要です。

| 列 | 項目 |
| --- | --- |
| A | No. |
| B | URL |
| C | ページ名 |
| D | ランク |

ツールは新規依存を追加しないため、標準ライブラリの `zipfile` と `xml.etree.ElementTree` で `.xlsx` を読み取ります。CSV入力にも対応しており、CSVの場合もヘッダーは `No.,URL,ページ名,ランク` とします。

## 3. 出力URLレジストリ形式

出力CSVはUTF-8 BOM付きで、ExcelやGoogle Sheetsで日本語が崩れにくい形式です。列順は既存 `URLレジストリ` の A〜M列に合わせます。

| 列 | 項目 | 出力内容 |
| --- | --- | --- |
| A | 自治体名 | 入力ファイル名 |
| B | URL | 入力Excel/CSVのURL |
| C | 保存ファイル名 | 自動生成 |
| D | XPath | `--xpath-map` または `--default-xpath` の指定値 |
| E | ステータス | `未完了` |
| F | 開始日時 | 空欄 |
| G | 完了日時 | 空欄 |
| H | 消費トークン | 空欄 |
| I | 想定コスト(円) | 空欄 |
| J | 処理バージョン | 空欄 |
| K | 画像解析（Vision） | `--vision` の指定値。既定は `OFF` |
| L | VisionTokens | 空欄 |
| M | VisionCalls | 空欄 |

## 4. 実行例

```bash
python tools/build_validation_url_registry.py \
  --input-dir ./local/validation-pages \
  --output ./local/url_registry_250.csv \
  --default-xpath '//*[@id="contents_0"]' \
  --vision OFF
```

終了時には件数と出力先を表示します。

```text
status: PASS
municipalities: 5
rows: 250
output: local/url_registry_250.csv
```

警告がある場合もCSV生成は継続し、`PASS_WITH_WARNINGS` を表示します。重大エラーでは終了コード1になります。

## 5. XPath指定方法

D列のXPathは次の優先順で決まります。

1. `--xpath-map` で指定した自治体別XPath
2. `--default-xpath`
3. 未指定の場合は空欄

`--xpath-map` はJSONファイルです。

```json
{
  "安城市": "//*[@id=\"contents_0\"]",
  "浦添市": "//*[@id=\"content\"]",
  "弘前市": "//*[@id=\"main\"]",
  "福山市": "//*[@id=\"contents\"]",
  "豊橋市": "//*[@id=\"contents_0\"]"
}
```

実ページ確認後にXPathを調整できるよう、ツール側では自治体ごとのXPathを固定しません。

## 6. 保存ファイル名ルール

C列の保存ファイル名は、次の形式で生成します。

```text
<municipality_slug>_<no:03d>.html
```

既定のslug対応は次のとおりです。

| 自治体名 | slug |
| --- | --- |
| 安城市 | anjo |
| 浦添市 | urasoe |
| 弘前市 | hirosaki |
| 福山市 | fukuyama |
| 豊橋市 | toyohashi |

例:

```text
anjo_001.html
urasoe_001.html
hirosaki_001.html
fukuyama_001.html
toyohashi_001.html
```

未知の自治体名は既定ではエラーにします。検証目的で安全な代替名を使う場合のみ、`--allow-unknown-municipality` を指定すると `municipality_001.html` のような名前を生成します。

## 7. Google Sheetsへの投入手順

1. 佐賀市実績はコピー側で保管する。
2. 250ページ検証用スプレッドシートの `URLレジストリ` 2行目以降をクリアする。
3. 変換後CSVを開く。
4. A〜M列を `URLレジストリ` に貼り付ける。
5. E列がすべて `未完了` であることを確認する。
6. K列がまずは `OFF` であることを確認する。
7. D列XPathを自治体ごとに確認する。
8. 最初は5自治体×1ページだけで試験する。

## 8. 注意事項

- `対象ページ` シートがないExcelはエラーになります。
- `No.` / `URL` / `ページ名` / `ランク` ヘッダーがない入力はエラーになります。
- URLが空の行はスキップし、警告します。
- 各自治体50件でない場合は警告します。
- 全体が250件でない場合は警告します。
- URL重複がある場合は警告します。
- 保存ファイル名が重複する場合はエラーになります。
- 本体コード、fixture、gold、ai-v1.0 出力は変更しません。

## 9. 実URL一覧をリポジトリに入れない方針

`local/` 配下は `.gitignore` で除外します。次のファイルはコミットしません。

- `local/validation-pages/*.xlsx`
- `local/validation-pages/*.csv`
- `local/url_registry_250.csv`
- 実URL一覧CSV
- Google Sheets ID
- DriveフォルダID
- APIキーや個人情報

## 10. 関連ドキュメント

- [README](../README.md)
- [v1.0運用手順](operations-v1.0.md)
- [v1.0 250ページ検証計画](v1.0-250-page-validation-plan.md)（存在する場合）
