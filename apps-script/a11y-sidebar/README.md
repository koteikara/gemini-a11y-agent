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


## サイドバー起動方式とRULES注入

- `Sidebar.html` は Apps Script テンプレートscriptletを使い、起動時に `RULES` をクライアント側JavaScriptへ初期注入します。
- 現在のMVPはテンプレート注入方式です。`Sidebar.html` に `const RULES = <?!= JSON.stringify(normalizeA11ySidebarRulesForClient()) ?>;` を残し、`google.script.run` による非同期ルール取得には切り替えていません。
- そのため `showA11ySidebar()` は `HtmlService.createHtmlOutputFromFile('Sidebar')` ではなく、`HtmlService.createTemplateFromFile('Sidebar').evaluate()` を使います。
- この起動方式でない場合、サイドバー上で `const RULES = <?!= ... ?>` がそのまま残り、JavaScript構文エラーになる可能性があります。
- `ManualLlm.gs` と `Sidebar.html` には似た手動LLM用のプロンプト生成・JSON検証ロジックがあります。MVPではAPI通信や `google.script.run` 往復を増やさないため、実際のサイドバー操作は `Sidebar.html` 側のクライアントロジックを正とします。`ManualLlm.gs` は将来サーバー側呼び出しへ切り替える場合の予備実装として同梱しています。

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


## Google Sheets実機での手動起動確認

1. Google Sheetsを開く。
2. 拡張機能 > Apps Script を開く。
3. `Code.gs` / `Rules.gs` / `RuleEngine.gs` / `ManualLlm.gs` / `Sidebar.html` を同名ファイルとして配置する。
4. スプレッドシートを再読み込みする。
5. メニュー「アクセシビリティ補正」>「HTML補正サイドバーを開く」を選ぶ。
6. サイドバーが開くことを確認する。
7. 「HTML補正」「使い方」タブが表示されることを確認する。
8. `samples/sample-input.html` を入力HTMLに貼り付ける。
9. 「HTML解析」を押す。
10. iframe / img / table / a / form の件数が表示されることを確認する。
11. 16ルールが処理一覧に表示されることを確認する。
12. 「上から順に実行」を押し、候補が表示されることを確認する。
13. 候補を1つ適用し、出力HTMLが変わることを確認する。
14. 出力HTMLに `data-a11y-candidate-id` が残らないことを確認する。
15. 出力HTMLをコピーできることを確認する。

この環境ではGoogle SheetsコンテナバインドApps Scriptの実機起動までは自動確認できないため、上記手順でブラウザ上の起動と操作を確認してください。

## 既存Colab版との共存

このサイドバーはGoogle Sheets上の補助UIです。既存Colab/Python本体、`runner.py`、`cleaners.py`、`hybrid_rules.py`、`io_sheets.py`、既存fixture/gold/ai-v1.0出力は変更せず、従来の一括処理と共存します。

## API設定タブ

API設定タブでは、Gemini API連携に必要なユーザー個人の設定を保存します。

- providerはMVPではGeminiです。
- modelの初期値は `gemini-2.5-flash` です。
- APIキーは `PropertiesService.getUserProperties()` の `A11Y_GEMINI_API_KEY` にユーザー単位で保存します。
- APIキーはスプレッドシート本文、出力HTML、`A11Y_API_USAGE_LOG` には保存しません。
- 画面再表示時もAPIキー文字列は表示しません。
- 「APIキーを削除」でUserPropertiesからAPIキーを削除できます。
- API連携では候補情報や周辺テキストが外部APIへ送信されます。個人情報、非公開情報、機密情報を含むHTMLでは使用しないでください。

## HTML解析後の操作手順

1. コンテンツ部分のHTMLを入力HTMLへ貼り付けます。
2. 「1. HTMLを解析する」を押します。
3. 解析結果サマリーと進行ガイドで、次の操作が「2. チェック済み処理を上から実行する」であることを確認します。
4. 不要なルールはチェックを外すかスキップします。
5. 「2. チェック済み処理を上から実行する」を押します。
6. 候補カードで、検出理由、対象情報、推奨入力欄を確認します。
7. LLMなしで手入力するか、手動LLM連携でJSON回答を貼り戻すか、APIキー設定済みの場合は「APIで候補生成」を使います。
8. 候補内容を確認してから「HTMLへ適用」を押します。API応答だけでは自動適用しません。
9. 出力HTMLを確認し、「6. 出力HTMLをコピーする」を押します。

## API候補生成

API候補生成の対象は `HTML-R-15`、`LINK-R-02`、`LINK-R-04`、`IMG-R-05`、`IMG-W-02`、`IMG-W-01` です。送信する情報は候補ごとの `ruleId`、検出メッセージ、`href`、リンク文言、`src`、周辺テキストなどの最小限のpayloadです。HTML全文は送信しません。

Gemini APIの応答はJSONとして検証します。`ruleId` が一致し、`html` / `fullHtml` / `document` を含まず、`replacementText` / `alt` / `caption` / `title` のいずれかを含む場合だけ候補入力欄へ反映します。

## 使用履歴シート

API連携を実行すると、`A11Y_API_USAGE_LOG` シートが存在しない場合は自動作成され、以下の列で追記されます。

| 列 | 内容 |
| --- | --- |
| timestamp | 記録日時 |
| userEmail | 取得可能な実行者メール。不明時は `unknown` |
| provider | `gemini` など |
| model | 使用モデル |
| mode | `api-candidate` / `connection-test` など |
| ruleId | 対象ルール |
| candidateId | 候補ID |
| promptTokenCount | 入力token数 |
| candidatesTokenCount | 出力candidate token数 |
| thoughtsTokenCount | thinking token数が返る場合のtoken数 |
| totalTokenCount | 合計token数 |
| inputUnitUsdPer1M | 100万入力tokenあたり単価 |
| outputUnitUsdPer1M | 100万出力tokenあたり単価 |
| estimatedUsd | 概算USD |
| estimatedJpy | 概算JPY |
| currencyRateUsdJpy | USD/JPY換算レート |
| status | `success` / `error` / `validation_error` など |
| error | エラー詳細 |
| responseId | API応答ID |
| modelVersion | API応答のモデルバージョン |
| note | 料金メモ |

## token数と概算金額

Gemini API応答の `usageMetadata` から `promptTokenCount`、`candidatesTokenCount`、`thoughtsTokenCount`、`totalTokenCount` を取得します。概算金額は `Pricing.gs` のモデル別単価とAPI設定タブのUSD/JPYレートから算出します。

```text
estimatedUsd =
  promptTokenCount / 1,000,000 * inputUnitUsdPer1M
  + (candidatesTokenCount + thoughtsTokenCount) / 1,000,000 * outputUnitUsdPer1M

estimatedJpy = estimatedUsd * currencyRateUsdJpy
```

料金モードが `unknown` の場合、token数のみ記録し、金額は空欄にします。概算金額は参考値であり、実際の請求額、無料枠、割引、価格改定、レート制限とは異なる場合があります。
