# Gemini-A11y Agent（modular / v22）

自治体サイトの HTML を入力として、  
**本文コンテンツのみ**を抽出し、アクセシビリティ観点で安全に自動修正するエージェントです。

巨大な単一スクリプト構成を廃止し、  
**Google Colab で安定実行できることを前提にモジュール分割**した構成になっています。

---

## 目的・思想（重要）

- 対象は **自治体公式サイト**
- 出力は **ページ全体ではなく「本文コンテンツのみ」**
- WCAG / JIS X 8341-3 観点での **機械的・再現可能な修正のみ**を行う
- LLM（Gemini）は **補助的に使用**し、創作・推測をさせない
- DOM を破壊する危険な処理（親ごと削除等）は禁止
- 「途中で切れる」「フッター等が混入する」事故を最優先で防ぐ

---

## 主な機能

- table の安全な分離・修正  
  - レイアウト表 → div 変換  
  - データ表のみ LLM 修正（caption / thead / scope）

- PDF 等の容量・種別表記の削除  
  - 括弧種別に依存しない正規表現処理

- 非推奨属性の削除  
  - table / th / td / img / a など
  - style 内の px 固定サイズ除去

- iframe title の補完  
  - src 先ページの `<title>` を取得  
  - 相対パス対応・アクセス回数制限あり

- img alt の自動生成（Vision）  
  - 原則すべての img を対象  
  - 推測禁止・括弧禁止・200文字未満

- Menu / PageTop / footer 以降の終端カット  
  - **テキスト判定＋セレクタ削除の二重安全弁**

- Google スプレッドシートへの結果書き戻し  
  - ステータス / トークン / コスト / バージョン管理

---

## ディレクトリ構成

```text
gemini-a11y-agent/
├─ README.md
├─ .gitignore
└─ a11y_agent/
   ├─ __init__.py
   ├─ config.py        # 設定値・定数（version / chunk size / flags）
   ├─ utils.py         # 共通ユーティリティ（時刻 / MIME 判定など）
   ├─ extractor.py     # XPath優先の本文抽出
   ├─ chunker.py       # 再帰チャンク分割
   ├─ cleaners.py      # 前後処理（属性削除・px削除・iframe補完など）
   ├─ trim_common.py   # 共通部品削除・Menu/PageTop終端カット
   ├─ llm_text.py      # LLM（table / text normalize）
   ├─ vision_alt.py    # Vision による alt 生成
   ├─ io_sheets.py     # Google Sheets I/O・認証
   └─ runner.py        # main（処理全体のオーケストレーション）

````md
## 実行環境

### 前提

- Google Colab（動作前提）
- Python 3.10 以上
- Gemini API Key  
  - Colab の `userdata`（`GEMINI_API_KEY`）に設定済みであること
- 対象の Google スプレッドシートが  
  **実行アカウントに「閲覧以上」で共有**されていること

---

### 依存パッケージ（Colab）

Colab 上で以下を実行する。

```python
!pip install -U \
  google-genai \
  google-auth \
  gspread \
  beautifulsoup4 \
  lxml \
  trafilatura \
  requests
````

#### 注意事項

* Colab 標準パッケージとの **依存関係警告は許容**（実行を止めない）
* バージョン固定は行わない（Colab 更新耐性を優先）
* `google-colab` が要求する `google-auth` / `requests` と
  `pip install -U` の結果が食い違うことがある

  * **警告が出ても import / 実行できていれば問題なし**
* `auth.authenticate_user()` は **Colab 環境専用**

  * `python runner.py` のような非 Notebook 実行では失敗する
* `trafilatura` 未導入時は `ModuleNotFoundError` が発生する
* 依存関係が壊れた場合は
  **「ランタイム再起動 → pip 再実行」** が最短復旧手順

---

## 実行手順（Colab）

### 1. リポジトリ配置

Colab 上で以下の構成になるよう配置する。

```text
/content/
└─ a11y_agent/
   ├─ runner.py
   ├─ config.py
   ├─ extractor.py
   ├─ chunker.py
   ├─ cleaners.py
   ├─ trim_common.py
   ├─ llm_text.py
   ├─ vision_alt.py
   ├─ io_sheets.py
   └─ utils.py
```

* GitHub から `git clone` してもよい
* ZIP 展開でも可
* `a11y_agent` ディレクトリが import 可能であることが前提

---

### 2. 実行

```python
import sys
sys.path.append("/content/a11y_agent")

from runner import main
main()
```

---

### 3. 実行結果

* 修正済み HTML
  → Google Drive 指定フォルダへ保存
* Google スプレッドシート
  → 該当行が「完了」に更新される
  → トークン数・コスト・バージョン等が記録される

---

## Google スプレッドシート仕様（要点）

| 列 | 内容              |
| - | --------------- |
| A | 自治体名            |
| B | 対象 URL          |
| C | 出力ファイル名         |
| D | XPath           |
| E | ステータス           |
| F | 開始時刻            |
| G | 完了時刻            |
| H | 総トークン数          |
| I | 円換算コスト          |
| J | ツールバージョン        |
| K | Vision ON / OFF |
| L | Vision Tokens   |
| M | Vision Calls    |

---

## v22（modular）での重要な変更点

* 巨大 1 ファイル構成を完全廃止
* 機能単位でモジュール分割（Colab 安定動作前提）
* XPath 抽出 → 再帰チャンク分割 → 安全結合の流れを固定
* レイアウト table → div 変換は **DOM 保持方式**
* Menu / PageTop / footer 以降の終端カットを標準仕様化
* 共通部品セレクタ削除を **安全弁として追加**
* CHUNK 結合時に marker を混入させる方式を廃止
* raw HTML へのフォールバック復活を禁止
  （不要領域・フッター再混入防止）

---

## 既知の制約・注意点

* JavaScript により動的生成されるコンテンツは対象外
* iframe の src 先が取得不可・重い場合、title 補完はスキップされる
* Vision（画像 alt 生成）は API 制限により **ページ単位で上限あり**
* ローカル実行は可能だが
  認証・Drive 周りの追加設定が必要なため非推奨

---

## Codex 利用時のルール（必須）

* 修正は **必ずファイル単位**
* 差分出力は禁止、**全文コードのみ**
* DOM 構造を破壊する処理は禁止
  （親要素ごと削除、decompose 前提処理など）
* LLM による創作・推測は禁止
* 以下が発生した場合は最優先で修正する

  * 本文の途中欠落
  * footer / Menu / PageTop の混入

---

## README の位置づけ

* 本リポジトリの **設計・仕様・運用の正本**
* Codex / 他担当者 / 将来引き継ぎ用の一次資料
* 判断に迷った場合は **README を最優先**とする

```
```
