# Codex運用フロー

## 1. 目的

このドキュメントは、Gemini-A11y Agent の開発・検証・ドキュメント整備を Codex に安全かつ再現性高く依頼するための運用ルールをまとめるものです。

対象は、通常のコード修正、fixture追加、ドキュメント更新、PRレビュー、外部支援ツール評価の依頼形式です。アプリ本体の新機能追加そのものを目的とするものではありません。

## 2. Codexに任せてよい作業

Codexには、既存仕様・既存運用に沿った範囲で、以下の作業を任せてよいです。

- README / docs / release notes / operations guide の更新
- 既存仕様に沿った小規模なPython修正
- 既存テスト・fixture比較の実行
- PR本文の作成
- PR差分の要約
- 既存ドキュメント間のリンク整理
- 評価メモ・設計メモの作成
- 回帰リスクの洗い出し
- `git diff --check` や既存検証コマンドの実行

## 3. Codexに任せない作業

以下は、明示的な確認や指示なしに Codex に任せてはいけません。

- 確認なしに `gold` fixture を更新すること
- 確認なしに `ai-v1.0` 出力を更新すること
- 変換対象HTML本文を外部ツール出力で置き換えること
- APIキー、GitHub token、個人情報、非公開情報をリポジトリに追加すること
- Google Drive / Google Sheets / Colab の実環境に依存する判断を、Codex環境だけで完了扱いにすること
- kage / Headroom / Firecrawl を v1.0 本体処理へ直接組み込むこと
- Firecrawl APIキーや外部API設定を勝手に追加すること
- 依存関係を追加すること。ただし、明示的な指示がある場合は別

## 4. 作業モード

Codexへの依頼時は、作業目的に応じて以下のモードを指定すると、成果物と確認範囲を揃えやすくなります。

| モード | 用途 | 成果物 |
| --- | --- | --- |
| brainstorm | 新機能・評価方針・設計方針の整理 | 方針メモ、論点整理 |
| design | 実装前の仕様化 | docs配下の設計書 |
| implementation | Pythonコード修正 | ソースコード、テスト結果 |
| fixture | fixture追加・比較 | fixture、比較結果 |
| review | PR確認・回帰リスク確認 | レビューコメント、確認結果 |
| docs | README・運用手順・評価メモ更新 | Markdownドキュメント |

## 5. PR作成時の必須確認

PR本文には、最低限以下を含めます。

- Motivation
- Description
- Testing
- 変更したファイル
- 本体コード変更の有無
- fixture変更の有無
- `gold` / `ai-v1.0` 変更の有無
- 既知の制約
- 次アクション

可能な場合は、以下の標準確認コマンドを実行します。

```bash
git diff --check

python tools/check_saga_city_test_fixture.py

python tools/compare_saga_city_versions.py \
  --fixture-root tests/fixtures/html/saga-city-test \
  --case sg02395-composite
```

`compare_saga_city_versions.py` で `previous fixture missing` 警告が出る場合は、`ai-v0` を生成しない方針による想定内警告かどうかを PR本文に明記します。

## 6. fixture / gold / ai-v1.0 の扱い

fixtureを扱う作業では、以下を守ります。

- `gold` は期待値であり、安易に更新しない
- `ai-v1.0` は現在の処理結果であり、更新する場合は理由を明記する
- `old` / `ai-v1.0` / `gold` の関係を崩さない
- 変更時は、どのケースで何が変わったかをPR本文に書く
- 外部ツール出力から `gold` や `ai-v1.0` を自動生成しない
- table、iframe、画像alt、導入文、h3 / h4 などの保持を確認する

## 7. 外部支援ツール評価時のルール

PR #41〜#45 で整理した外部支援ツール評価の方針に従い、kage / Headroom / Firecrawl は現時点では本体処理へ組み込みません。

- kage: fixture作成前の証跡保存・オフライン確認用
- Headroom: ログ・差分・Codex引き継ぎ圧縮補助
- Firecrawl: 取得fallback・JS依存ページ調査候補
- 外部ツールの現在状態は [`docs/external-tools-evaluation-status.md`](external-tools-evaluation-status.md) を確認する
- 詳細な評価方針は [`docs/external-tools-evaluation.md`](external-tools-evaluation.md) を確認する

外部支援ツール評価では、以下を禁止します。

- 外部ツールを v1.0 本体処理へ直接組み込まない
- 変換対象HTML本文を外部ツールの出力で自動置換しない
- `gold` fixture を外部ツールで自動生成しない
- `ai-v1.0` fixture を外部ツールで自動生成しない
- Firecrawl Markdown / clean HTML をHTML補正入力として使わない
- kage出力HTMLを標準入力HTMLとして使わない
- HeadroomでHTML本文やfixture本文を圧縮・要約・改変しない
- APIキー、GitHub token、個人情報、非公開情報をログやfixtureに含めない

## 8. Codex環境外で確認が必要な作業

以下は Codex 環境だけでは完了判断しないでください。確認できない場合は、PR本文に「未確認」「環境制約」「次に確認すべき場所」を明記します。

- Google Colabでの実行確認
- Google Sheets連携確認
- Google Drive保存確認
- Gemini APIキーを使う実行確認
- Chrome / Chromium を必要とする kage 評価
- 外部APIキーを必要とする Firecrawl 評価
- ログインが必要なWeb画面確認
- 実ブラウザでの出力HTML目視確認

## 9. Codex依頼テンプレート

今後 Codex に作業を依頼する場合は、以下のテンプレートを利用できます。

````md
# Codex依頼テンプレート

## 目的

何を達成したいかを1〜3文で書く。

## 対象ファイル

- `path/to/file`

## 実施内容

- 変更内容1
- 変更内容2
- 変更内容3

## 禁止事項

- やってはいけないこと1
- やってはいけないこと2

## 完了条件

- 条件1
- 条件2
- 条件3

## 確認コマンド

```bash
git diff --check

python tools/check_saga_city_test_fixture.py

python tools/compare_saga_city_versions.py \
  --fixture-root tests/fixtures/html/saga-city-test \
  --case sg02395-composite
```

## PR本文に含めること

- Motivation
- Description
- Testing
- 変更対象
- 変更していないもの
- 既知の制約
````

## 10. 関連ドキュメントリンク

- [README](../README.md)
- [v1.0運用手順](operations-v1.0.md)
- [外部支援ツール評価](external-tools-evaluation.md)
- [外部支援ツール評価ステータス](external-tools-evaluation-status.md)
- [kage評価メモ](kage-evaluation-14256.md)
- [Headroom評価メモ](headroom-evaluation.md)
- [Firecrawl評価メモ](firecrawl-evaluation.md)
- [合成fixture運用手順](composite-fixture-workflow.md)
- [回帰検証手順](regression-tests.md)
