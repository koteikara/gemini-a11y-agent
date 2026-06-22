# Gemini-A11y Agent v1.0 運用手順

## 目的

このドキュメントは、Gemini-A11y Agent v1.0 を既存の Google Colab / Google Sheets / Google Drive 環境で実行するための運用手順をまとめたものです。

v1.0では、実行環境は変更しません。  
従来どおり、Google Sheets に処理対象を記載し、Google Colab から実行し、HTML出力を Google Drive に保存します。

## 事前確認

- v1.0運用開始前の確認: [`docs/v1.0-operation-readiness-checklist.md`](v1.0-operation-readiness-checklist.md)
- 試験運用結果の記録: [`v1.0-trial-operation-log-template.md`](v1.0-trial-operation-log-template.md)

## 実行環境

- Google Colab
- Google Sheets
- Google Drive
- Gemini API
- Python
- `google-genai`
- `beautifulsoup4`
- `lxml`
- `requests`
- `trafilatura`
- `gspread`

## 事前準備

### 1. Gemini APIキー

Colabのシークレット、または既存の運用方法で Gemini APIキーを設定します。

推奨する環境変数名：

```text
GEMINI_API_KEY
```

または

```text
GOOGLE_API_KEY
```

v1.0の既定モデルは以下です。

```text
gemini-2.5-flash
```

必要に応じて、以下の環境変数でモデルを上書きできます。

```text
GEMINI_MODEL_ID
```

例：

```python
import os
os.environ["GEMINI_MODEL_ID"] = "gemini-2.5-flash"
```

## Google Sheets の準備

処理対象一覧シートを用意します。

### 列構成

v1.0では以下の列を前提にします。

| 列 | 項目 | 内容 |
| - | - | - |
| A | 自治体 | 自治体名 |
| B | URL | 処理対象ページURL |
| C | ファイル名 | 出力HTMLファイル名 |
| D | XPath | 抽出対象XPath |
| E | ステータス | 未完了 / 成功 / エラー等 |
| F | 開始 | 処理開始日時 |
| G | 完了 | 処理完了日時 |
| H | 総tokens | 使用tokens |
| I | 円 | 概算コスト |
| J | Ver | 実行バージョン |
| K | Vision | Vision alt のON/OFF |
| L | VisionTokens | Vision使用tokens |
| M | VisionCalls | Vision呼び出し数 |

### 入力例

```text
A: 佐賀市
B: https://www.city.saga.lg.jp/main/14256.html
C: 14256.html
D: //*[@id="contents_0"]
E: 未完了
K: OFF
```

### 注意

* D列のXPathは、本文領域を指定します
* 原則として `//*[@id="contents_0"]` のように本文全体を含むXPathを指定します
* E列が未完了の行を処理対象にします
* K列がONの場合はVision alt処理の対象になります
* 今回のv1.0検証では、Vision alt は必須ではありません

## Google Drive の準備

HTML出力先として、既存の共有ドライブ配下を使用します。

現在の想定出力先：

```text
Google Drive /
  共有ドライブ /
    【SV・ND】共有プロジェクト（自治体）/
      00_データ交換用/
        データ移行_アクセシビリティAI対応プロジェクト/
          Gemini-A11y Agent/
            HTML出力/
              <自治体名>/
                <ファイル名>.html
```

例：

```text
HTML出力/佐賀市/14256.html
```

### 注意

* 出力先フォルダが存在しない場合は、スクリプト側で作成される想定です
* 同名ファイルがある場合は、既存運用に従って上書きまたは保存してください
* 出力HTMLは、シートC列のファイル名に基づきます

## Colabでの実行手順

### 1. Google Drive をマウント

```python
from google.colab import drive
drive.mount('/content/drive')
```

### 2. リポジトリを取得

初回：

```python
!git clone https://github.com/koteikara/gemini-a11y-agent.git
%cd gemini-a11y-agent
```

既にclone済みの場合：

```python
%cd /content/gemini-a11y-agent
!git pull origin main
```

### 3. 必要ライブラリをインストール

```python
!pip install -q -U google-genai beautifulsoup4 lxml requests trafilatura gspread
```

### 4. Gemini APIキーを設定

Colabシークレットを使う場合：

```python
import os
from google.colab import userdata

gemini_key = userdata.get("GEMINI_API_KEY")
os.environ["GEMINI_API_KEY"] = gemini_key
os.environ["GOOGLE_API_KEY"] = gemini_key

print("Gemini API key loaded:", bool(gemini_key))
```

### 5. 実行前確認

```python
!python -m py_compile a11y_agent/config.py
!python -m py_compile a11y_agent/runner.py
```

### 6. 通常処理を実行

既存のColabノートブック、または既存の実行セルから実行します。

実行時のログで以下を確認します。

```text
🚀 Ver ...
✅ 抽出方式: xpath
📦 分割: N ブロック
[table-header-orient]
[table-fix]
Step tokens summary
Page Processing Summary
✅ 成功
```

## 実行後の確認

### シート側

以下を確認します。

* E列が `成功` になっている
* F列に開始日時が入っている
* G列に完了日時が入っている
* H列に総tokensが入っている
* I列に概算コストが入っている
* J列にバージョンが入っている
* K〜M列にVision情報が記録されている

### Drive側

以下を確認します。

```text
HTML出力/<自治体名>/<ファイル名>.html
```

例：

```text
HTML出力/佐賀市/14256.html
```

## 出力HTMLの確認観点

最低限、以下を確認します。

* 本文冒頭が欠落していない
* table前導入文が残っている
* h3 / h4 が残っている
* tableに caption がある
* tableに thead がある
* 列見出しに `th scope="col"` がある
* 行見出しに `th scope="row"` がある
* `更新：YYYY年M月D日` のような単独更新行が除外されている
* Menu / PageTop / footer が混入していない
* iframe に適切な title が付いている
* 不要な内部ラベルが混入していない

## 佐賀市14256の回帰確認

ローカルまたはColabで以下を実行します。

```bash
python tools/regression_check_14256.py tests/fixtures/html/saga-city/ai
python tools/regression_check_14256.py tests/fixtures/html/saga-city/gold
```

## 合成fixtureによる確認

v1.0の代表ケース確認は以下で実行します。

```bash
python tools/check_saga_city_test_fixture.py

python tools/compare_saga_city_versions.py \
  --fixture-root tests/fixtures/html/saga-city-test \
  --case sg02395-composite
```

期待結果：

```text
matches_gold: 18
differs_from_gold: 0
regressed: 0
warning: 0
```

`previous fixture missing` warning は、`ai-v0` を生成しない方針のため想定どおりです。

## 外部支援ツールについて

Headroom / Firecrawl / kage / agmsg は、現時点では通常のv1.0運用フローには組み込みません。

- Headroom: ログ・差分・引き継ぎの圧縮補助として評価
- Firecrawl: 取得fallback候補として評価
- kage: fixture作成前の証跡保存・オフライン確認用として評価
- agmsg: 複数CLIエージェント間の開発・レビュー・検証連携補助として評価

詳細は以下を参照してください。

- [`docs/external-tools-evaluation.md`](external-tools-evaluation.md)
- Codex運用フロー: [`docs/codex-workflow.md`](codex-workflow.md)

## よくあるエラー

### No module named 'a11y_agent'

Colabの実行場所がリポジトリ直下ではない可能性があります。

```python
%cd /content/gemini-a11y-agent
!PYTHONPATH=. python tools/run_saga_city_test_fixture_v1.py --dry-run
```

### Gemini APIキーが取得できない

Colabシークレット名を確認してください。

```python
from google.colab import userdata
userdata.get("GEMINI_API_KEY")
```

### model not found

古いモデルIDを使っている可能性があります。
v1.0の既定は以下です。

```text
gemini-2.5-flash
```

### GitHubにpushできない

通常運用ではColabからGitHubへpushする必要はありません。
fixtureを更新する場合のみ、GitHub token を使います。

## 運用上の注意

* 通常の自治体HTML処理では、GitHubへpushする必要はありません
* 出力HTMLはGoogle Driveに保存されます
* GitHubへ追加するのは、検証fixtureやdocsを更新する場合だけです
* APIキーやGitHub tokenをノートブックやログに表示しないでください
* トークンが画面に表示された場合は、GitHub側で削除・再発行してください

## 関連ドキュメント

- a11y hybrid detect/fix ルール: [`docs/a11y-hybrid-detect-fix-rules.md`](a11y-hybrid-detect-fix-rules.md)
  - 通常運用では `FEATURE_HYBRID_RULES_REPORT=0` のままにし、report-only 検出を明示的に有効化しません。
