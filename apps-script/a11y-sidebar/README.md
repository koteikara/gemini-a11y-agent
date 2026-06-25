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

## タブ構成

サイドバーは将来の機能追加に備え、タブ定義を配列で管理する構成です。MVP時点では次の2タブを表示します。

- **HTML補正**: 入力HTML、HTML解析、要素数サマリー、LLM利用モード、処理一覧、上から順に実行、個別実行、スキップ、要確認候補、出力HTML、コピー、リセットをまとめています。
- **使い方**: 操作説明、LLM連携説明、検証手順、FAQなどを今後追記するための仮置きタブです。

タブボタンは `button` 要素で、`role="tablist"`、`role="tab"`、`role="tabpanel"`、`aria-selected`、`hidden` を使い、サイドバー幅でも縦に読み進めやすい構成にしています。

## 候補適用の操作手順

1. `samples/sample-input.html` などのHTML断片を入力HTMLへ貼り付けます。
2. 「HTML解析」を押すと iframe / img / table / a / form の件数が表示され、低リスク自動補正として iframe の `frameborder` を削除します。`allowfullscreen` は保持します。
3. 「上から順に実行」または各ルールの「個別実行」を押します。
4. 候補ごとの入力欄に、`title`、`caption`、`replacementText`、`alt` などを入力します。
5. 「HTMLへ適用」を押すと、対象要素を `data-a11y-candidate-id` で再特定してDOMへ反映します。
6. 適用しない候補は「スキップ」を押します。末尾署名・問い合わせ候補は「残す / 削除する」を選択し、削除を選んだ場合だけ対象要素を削除します。
7. 出力HTMLを確認し、「コピーする」で貼り戻し用HTMLをコピーします。

出力HTML生成時には、候補管理用の `data-a11y-candidate-id` を削除します。一時属性は貼り戻し用HTMLに残しません。

## 手動LLM連携の操作手順

1. LLM利用モードは標準で「LLMなし」です。APIキーは不要で、HTMLを外部APIへ自動送信しません。
2. 必要な候補で「LLM用プロンプトを作成」を押します。
3. 表示されたプロンプトをコピーし、ユーザー自身が任意の ChatGPT / Gemini / Claude などのWeb UIへ貼り付けます。
4. LLMのJSON回答をサイドバーの貼り戻し欄へ貼り、「回答JSONを検証」を押します。
5. `ruleId` 一致、HTML全体を書き換えていないこと、`replacementText` / `alt` / `caption` / `title` のいずれかがあることを確認できた場合だけ候補入力欄へ反映します。
6. 最後にユーザーが内容を確認し、「HTMLへ適用」を押します。

MVPではAPI自動連携は未実装です。Gemini固定ではなく、将来の任意プロバイダー連携のための表示に留めています。

## 既存Colab版との共存

このサイドバーはGoogle Sheets上の補助UIです。既存Colab/Python本体、`runner.py`、`cleaners.py`、`hybrid_rules.py`、`io_sheets.py`、既存fixture/gold/ai-v1.0出力は変更せず、従来の一括処理と共存します。
