# claude-a11y-agent 設計思想の段階的取り込み計画

## 目的

Gemini-A11y Agent v1.0 の実行環境（Google Colab + Google Sheets + Google Drive）は維持したまま、参考リポジトリ `koteikara/claude-a11y-agent` の設計思想を段階的に取り込む。

本計画では、Cloud Run / Web管理画面 / Secret Manager などの実行基盤は導入せず、まずは以下を優先する。

- 処理責務の整理
- old / ai / gold の成果物管理思想
- 回帰検証の強化
- lxml ベースの検証スクリプト整備
- README / docs の整理

---

## 参考リポジトリから取り込む考え方

### 1. Sheets をジョブ台帳として扱う

現行のスプレッドシート列構成は維持する。  
ただし内部概念として、処理状態を次のように整理する。

| 現行運用 | 参考リポジトリ思想 | 意味 |
|---|---|---|
| 未処理 | queued | 処理待ち |
| 処理中 | running | 実行中 |
| 成功 | done | 自動処理完了 |
| 要確認 | needs_review | 人による確認が必要 |
| 失敗 | error | 処理失敗 |

v1.0 時点では、既存列を壊さず、内部ログ・README・将来設計上の整理に留める。

---

### 2. Drive を old / ai / gold の成果物置き場として扱う

参考リポジトリでは、AI生成物を人が確認し、最終版へ承認する運用思想がある。  
現行環境でもこの考え方を取り込む。

| 区分 | 内容 |
|---|---|
| old | 元HTML、取得直後または移行前HTML |
| ai | Gemini-A11y Agent が自動補正したHTML |
| gold | 人が確認・承認した最終HTML |

初期段階では Web管理画面は導入せず、Driveフォルダ構成と命名規則で管理する。

---

## 段階的な改変計画

### Phase 1：現行処理の責務整理

- Colab起動、Sheets列、Drive保存先は維持
- `extractor.py`
- `chunker.py`
- `cleaners.py`
- `runner.py`
- `llm_text.py`

上記の責務を README / docs に明文化する。

特に以下を v1.0 の固定仕様として整理する。

- `#contents_0` 抽出
- DOM順 innerHTML 再構成
- table前導入文の独立保持
- h4 と table の紐付け
- table単体LLM差し戻し
- LLM戻り値検証
- row / col / none の table header 方向判定
- YouTube iframe title 補完

---

### Phase 2：old / ai / gold フォルダ設計

現行の出力先を大きく壊さず、以下のようなフォルダ設計を検討する。

```text
HTML入力/
  old/
    <自治体名>/<ファイル名>.html

HTML出力/
  ai/
    <自治体名>/<ファイル名>.html

HTML出力/
  gold/
    <自治体名>/<ファイル名>.html
```

初期導入では、まず `ai` 出力のみ現行出力先に対応させ、`old` / `gold` は将来拡張として扱う。

---

### Phase 3：lxml ベースの回帰検証

外部ネットワーク前提の `pip install` は禁止する。
検証スクリプトは `bs4` を使わず `lxml` で実装する。

回帰検証の最初の対象は、佐賀市 休日在宅当番医ページとする。

検証項目：

* table前導入文が残っていること
* `更新：YYYY年MM月DD日` が除外されていること
* h3 / h4 見出しが維持されていること
* 当番医テーブルに `thead` があること
* 先頭行が `th scope="col"` になっていること
* 2行目以降の1列目が `th scope="row"` になっていること
* table caption が存在すること
* Menu / PageTop / footer など共通部品が混入していないこと

---

### Phase 4：README / docs の分離

README は社内利用者向けに簡潔化し、詳細は docs に分離する。

想定する構成：

```text
README.md
docs/
  developer.md
  regression-tests.md
  known-issues.md
  migration-plan-from-claude-a11y-agent.md
```

README に残す内容：

* ツール概要
* v1.0 の主な機能
* 実行方法の概要
* 既知事項
* ドキュメント一覧

docs に分離する内容：

* 詳細な処理フロー
* 回帰検証手順
* 開発者向け注意事項
* 参考リポジトリ思想の取り込み計画

---

## 今回は取り込まないもの

以下は現時点では取り込まない。

* Cloud Run Service
* Cloud Run Jobs
* Secret Manager
* Web管理画面
* Basic認証
* Cloud Scheduler
* Apps Scriptメニュー
* 本格的な承認UI
* サービスアカウント前提の本番運用

理由：

* 現行の実行環境を変えないため
* v1.0 は社内向けリリースとして、まず処理品質と回帰検証を安定させるため
* 実行基盤の変更は、処理ロジックが安定してから別フェーズで検討するため

---

## 最初に実施するタスク

1. 本ドキュメントを追加する
2. README から本ドキュメントへのリンクを追加する
3. 現行リポジトリ内の処理責務を確認し、別途 `docs/developer.md` に整理する
4. 佐賀市 14256 を対象にした lxml 回帰検証スクリプト案を作成する
5. ただし、このPRではコード変更は行わない

---

## 判断基準

この計画で優先するのは、実行基盤の刷新ではなく、以下である。

* 欠落しないこと
* 壊さないこと
* 検証できること
* 人が確認できる成果物構造に近づけること
* 将来 Cloud Run / Web UI に移行できる責務分離を進めること
