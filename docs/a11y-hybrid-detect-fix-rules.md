# a11y hybrid detect/fix ルール

`a11y_agent/rules/a11y_hybrid_detect_fix.jsonl` は、将来の v1.1 以降で検出・修正候補を段階的に広げるためのアクセシビリティルール定義です。各行は JSONL 形式で、ルールID、検出ID、検出方式、検出条件、候補ペイロード、LLMタスク、修正プロンプト、出力契約を持ちます。

## v1.0 本体との関係

初回組み込みでは v1.0 の既存処理・既存出力を壊さないことを優先します。JSONL は本体に同梱しますが、自動修正には接続しません。`a11y_agent/hybrid_rules.py` は JSONL の読み込み、ID一覧取得、HTMLからの候補検出だけを担当します。

## feature flag と report-only 動作

- `FEATURE_HYBRID_RULES_REPORT=0` が通常運用の既定値です。
- `FEATURE_HYBRID_RULES_REPORT=1` の場合のみ、runner が最終HTMLに対して report-only 検出を実行します。
- report-only 検出は HTML を変更しません。
- 候補の `auto_fix` は常に `False` です。
- Drive保存HTML、Google Sheets列構成、fixture / gold / ai-v1.0 出力は変更しません。
- JSONL の場所を変える検証時だけ `HYBRID_RULES_JSONL_PATH` を指定できます。未指定時は標準配置を読みます。

## 初回で report-only 検出する主なルール

| ルール | 検出ID | 初回の扱い |
| --- | --- | --- |
| HTML-R-15 | DET-R15-CAPTION | caption が無い、または空の table を候補化 |
| HTML-R-16 | DET-R16-MERGE | rowspan / colspan を含む table を候補化 |
| LINK-R-02 | DET-L02-VAGUE | 「こちら」「詳細」「more」「click here」など曖昧リンク文言を候補化 |
| LINK-R-04 | DET-L04-MAIL | 直書きメールアドレス、または mailto ラベルがメールアドレスそのもののリンクを候補化 |
| LINK-R-08 | DET-L08-XANCHOR | 別ページ + fragment のリンクを候補化 |
| LINK-R-09 | DET-L09-INPAGE | ページ内 fragment リンクと対応 id の有無を候補化 |
| IMG-R-05 | DET-I05-LINKIMG | `<a>` 内の `<img>` を候補化 |
| IMG-R-09 | DET-I09-ZOOM | 画像ファイルへリンクするサムネイル画像リンクを候補化 |

## JSONL に含むルール概要

| ルール | 概要 |
| --- | --- |
| HTML-R-08 | 本文表記正規化候補 |
| HTML-R-15 | table caption 不足候補 |
| HTML-R-16 | rowspan / colspan を含む複雑表候補 |
| HTML-W-02 | layout table 候補 |
| IMG-W-01 | Vision alt 生成候補 |
| IMG-W-02 | iframe / YouTube title 補完候補 |
| LINK-R-02 | 曖昧リンク文言候補 |
| LINK-R-04 | メールアドレス露出候補 |
| LINK-R-08 | 別ページ fragment リンク候補 |
| LINK-R-09 | ページ内 fragment リンク候補 |
| IMG-R-05 | 画像リンク候補 |
| IMG-R-09 | 拡大画像リンク候補 |
| SKIP-04 | 署名・定型末尾候補 |
| FORM-R-01 | label 不足フォーム候補 |
| ARIA-R-01 | ARIA 整合性確認候補 |
| HEAD-R-01 | 見出しレベル確認候補 |

## 既存処理との対応表

| ルール | v1.0 既存処理との対応 |
| --- | --- |
| HTML-R-08 | `prompt_text_normalize` / `needs_text_normalize` に近い |
| HTML-R-15 | table 補正プロンプトおよび caption 補正に近い |
| HTML-W-02 | `convert_layout_tables_to_div_preserve_dom` による layout table -> div 変換に近い |
| IMG-W-01 | Vision alt 処理に近い |
| IMG-W-02 | YouTube iframe title 補完に近い |

## 検証

```bash
python tools/check_hybrid_rules.py
python tools/check_hybrid_rule_detection.py
python -m pytest tests/test_hybrid_rules_report_only.py
```

`check_hybrid_rules.py` は、JSONL の読み込み、必須キー、ID重複、`出力契約` の JSON parse、ルール件数 16 件を確認します。`check_hybrid_rule_detection.py` と `tests/test_hybrid_rules_report_only.py` は、代表的なHTMLから report-only 候補を抽出できること、全候補の `auto_fix` が `False` のままであること、入力HTML文字列を変更しないことを確認します。これらの検出テストは候補抽出のみを対象とし、HTML出力、fixture、gold、ai-v1.0 出力は変更しません。自動修正はまだ有効化していません。

## 今後の段階的有効化方針

1. report-only の候補検出ログを実ページで観察する。
2. 誤検出が多いルールは検出条件を調整する。
3. fixture / gold / ai-v1.0 を変更しない範囲で検出基盤を拡充する。
4. 個別ルールごとに安全な自動修正を別PRで検討する。
5. 自動修正を有効化する場合も、feature flag と回帰検証を必須にする。
