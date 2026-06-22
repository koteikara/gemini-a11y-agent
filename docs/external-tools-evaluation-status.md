# 外部支援ツール評価ステータス一覧

## 目的

このドキュメントは、PR #41〜#44 で追加した外部支援ツール評価ドキュメント群を横断的に整理し、現在の評価ステータス、採用可否、次アクション、禁止事項を一覧で確認するためのものです。

対象は kage / Headroom / Firecrawl の3ツールです。今回の整理は、いずれかの外部ツールを Gemini-A11y Agent v1.0 本体へ組み込むためのものではありません。個別評価メモの内容を一覧化し、今後の判断をしやすくするためのドキュメント追加に限定します。

## 評価対象ツール一覧

- kage
- Headroom
- Firecrawl

## 現在の評価ステータス表

| ツール | 位置づけ | 現在の状態 | 実行可否 | 本体組み込み | 次アクション |
| --- | ---- | ----- | ---- | ------ | ------ |
| kage | fixture作成前の証跡保存・オフライン確認用 | 最小評価メモ作成済み | Codex環境ではインストール・実保存不可。`go install` が 403、Chrome / Chromium 未検出 | しない | ローカルPCまたはColab外の環境で1ページだけ保存評価 |
| Headroom | ログ・差分・Codex引き継ぎ圧縮補助 | 最小評価メモ作成済み | Codex環境では `headroom` コマンド未検出 | しない | 利用可能な環境で、検証ログやcompare結果の圧縮可否を確認 |
| Firecrawl | 取得fallback・JS依存ページ調査候補 | 最小評価メモ作成済み | 実API評価は未実施。外部API利用条件、コスト、APIキー管理、自治体URL送信可否の確認が必要 | しない | 利用条件・コスト・robots.txt・情報管理方針確認後、必要なら1ページだけ実API評価 |

## ツール別の判断

### kage

kage は、fixture作成前の証跡保存・オフライン確認用として扱います。Codex環境では `go install` が 403 となり、Chrome / Chromium も未検出のため、インストールや実ページ保存はできませんでした。

本体組み込みは行いません。次に評価する場合は、ローカルPCまたはColab外の環境で、1ページだけ保存評価を行います。

### Headroom

Headroom は、ログ・差分・Codex引き継ぎの圧縮補助として扱います。Codex環境では `headroom` コマンドが未検出のため、実行評価はできませんでした。

本体組み込みは行いません。次に評価する場合は、利用可能な環境で、検証ログや `compare` 結果を圧縮しても必要な判断材料が残るか確認します。

### Firecrawl

Firecrawl は、取得fallback・JS依存ページ調査候補として扱います。実API評価は未実施です。外部APIの利用条件、コスト、APIキー管理、自治体URLや取得結果を外部APIへ送信してよいかの確認が必要です。

本体組み込みは行いません。次に評価する場合は、利用条件・コスト・robots.txt・情報管理方針を確認したうえで、必要な場合に限り1ページだけ実API評価を行います。

## 次アクション一覧

| ツール | 次アクション |
| --- | --- |
| kage | ローカルPCまたはColab外の環境で1ページだけ保存評価し、保存HTMLに `contents_0`、導入文、h3、h4、table が残るか確認する |
| Headroom | 利用可能な環境で、検証ログや `compare` 結果の圧縮可否、エラー原因や判定結果が欠落しないか確認する |
| Firecrawl | 利用条件・コスト・robots.txt・情報管理方針を確認し、必要なら1ページだけ実API評価して、本文構造やtableが保持されるか確認する |

## 共通の禁止事項

以下は禁止します。

- 外部ツールを v1.0 本体処理へ直接組み込まない
- 変換対象HTML本文を外部ツールの出力で自動置換しない
- gold fixture を外部ツールで自動生成しない
- ai-v1.0 fixture を外部ツールで自動生成しない
- Firecrawl Markdown / clean HTML をHTML補正入力として使わない
- kage出力HTMLを標準入力HTMLとして使わない
- HeadroomでHTML本文やfixture本文を圧縮・要約・改変しない
- APIキー、GitHub token、個人情報、非公開情報をログやfixtureに含めない
- 既存のv1.0処理フローを変更しない

## 本体処理へ組み込まない方針

kage / Headroom / Firecrawl は、現時点ではいずれも Gemini-A11y Agent v1.0 本体処理へ組み込みません。

v1.0本体のHTML補正処理は、合成fixtureで `ai-v1.0` と `gold` が一致している前提を維持します。外部ツールは、証跡保存、調査、ログ圧縮などの補助用途に限定し、標準入力HTML、fixture、gold、ai-v1.0 出力の自動生成・自動置換には使いません。

## 関連ドキュメントリンク

- 外部支援ツール評価: [`docs/external-tools-evaluation.md`](external-tools-evaluation.md)
- kage 最小評価メモ: [`docs/kage-evaluation-14256.md`](kage-evaluation-14256.md)
- Headroom 最小評価メモ: [`docs/headroom-evaluation.md`](headroom-evaluation.md)
- Firecrawl 最小評価メモ: [`docs/firecrawl-evaluation.md`](firecrawl-evaluation.md)
