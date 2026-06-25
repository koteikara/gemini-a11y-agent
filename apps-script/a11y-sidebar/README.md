# Google Sheets HTMLアクセシビリティ補正サイドバー

この実装は既存のColab/Python一括処理を置き換えません。`a11y_agent/runner.py`、`cleaners.py`、`hybrid_rules.py`、`io_sheets.py`、既存fixture/gold/Drive保存処理は変更せず、Google SheetsのコンテナバインドApps Scriptへコピーして使う軽量補助ツールとして追加しています。

## ファイル

- `Code.gs`: カスタムメニューとサイドバー起動。
- `Rules.gs`: `a11y_agent/rules/a11y_hybrid_detect_fix.jsonl` 由来の16ルール定義とUIメタ情報。
- `RuleEngine.gs`: サーバー側メタデータ補助。
- `ManualLlm.gs`: 手動LLM連携プロンプト生成とJSON検証。
- `Sidebar.html`: HTML貼り付け、解析、実行、スキップ、候補表示、出力コピーUI。

## 導入手順

1. Google Sheetsを開く。
2. 拡張機能 > Apps Script を開く。
3. このディレクトリの `Code.gs`、`Rules.gs`、`RuleEngine.gs`、`ManualLlm.gs`、`Sidebar.html` を同名ファイルとしてコピーする。
4. スプレッドシートを再読み込みする。
5. メニュー「アクセシビリティ補正」>「HTML補正サイドバーを開く」を選ぶ。
6. `samples/sample-input.html` のようなコンテンツ部分HTMLを貼り付け、解析・実行する。

## LLM利用モード

- 標準は「LLMなし」。HTMLは外部APIへ自動送信しません。
- 「手動LLM連携」はプロンプト生成と回答JSON貼り戻しを想定します。任意のLLM Web UIをユーザー自身が使います。
- 「API自動連携」は将来拡張用の表示のみで、MVPでは実API呼び出しも共通APIキーも必須にしません。Gemini固定ではありません。

## MVPルール

実装済み: `IMG-W-02`, `HTML-R-15`, `LINK-R-02`, `LINK-R-04`, `LINK-R-08`, `LINK-R-09`, `IMG-R-05`, `IMG-R-09`, `SKIP-04`。
検出のみ/手動候補: `HTML-R-08`, `HTML-R-16`, `HTML-W-02`, `HTML-R-21`, `LINK-R-06`, `IMG-W-01`。
未実装: `LINK-R-03` はネットワーク通信が必要なためMVPでは実行しません。

## 制約

候補は安全側に倒し、多くを「要確認」として表示します。高リスクな表再構成、画像alt自動生成、署名削除、リンク文言の自動置換は自動確定しません。
