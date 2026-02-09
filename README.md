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
