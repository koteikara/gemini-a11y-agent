# agmsg 評価メモ

## 目的

agmsg は、Claude Code / Codex / Gemini CLI / GitHub Copilot CLI / OpenCode などのCLI AIエージェント間で、ローカルSQLiteを介してメッセージをやり取りする開発支援ツールです。

Gemini-A11y Agent では、HTML補正本体や Colab 標準実行環境には組み込まず、ローカル開発環境での開発・レビュー・検証連携を補助する候補として評価します。

## 想定する開発チーム構成

- `implementer`: 指定された実装またはドキュメント修正を行う。
- `reviewer`: 差分、禁止事項、v1.0方針との整合を確認する。
- `verifier`: fixture確認、比較コマンド、PR本文に記載する確認結果を整理する。

## 最小評価手順

1. ローカル開発環境の1リポジトリだけで試す。
2. 秘匿情報を含まない短いメッセージだけで `manual` または `turn` 運用を試す。
3. `implementer` / `reviewer` / `verifier` の役割を分け、指示が混線しないか確認する。
4. `/goal` と組み合わせて、各役割が同じ制約を維持できるか確認する。
5. agmsg経由の指示だけで fixture、`gold`、`ai-v1.0` を生成・更新しないことを確認する。

## 確認項目

- [ ] Codex / Claude Code / Gemini CLI 間で作業連携しやすいか。
- [ ] 実装担当・レビュー担当・検証担当の分担が明確になるか。
- [ ] PRレビュー前の差分確認に役立つか。
- [ ] fixture方針・禁止事項に反していないかのチェックに役立つか。
- [ ] 長いCodex引き継ぎの分割に役立つか。
- [ ] 外部ツール評価作業のレビュー補助に使えるか。
- [ ] Codex monitor mode を使わなくても、manual / turn 運用で十分か。

## 禁止事項

- agmsg を v1.0 本体のHTML補正処理へ組み込まない。
- agmsg を Colab 標準運用へ組み込まない。
- 変換対象HTML本文、table単体LLM入力、fixture本文をagmsgのメッセージで改変しない。
- agmsg 経由の指示だけで `gold` fixture や `ai-v1.0` fixture を自動生成しない。
- APIキー、GitHub token、個人情報、非公開情報をメッセージに含めない。
- Codex monitor mode はベータ扱いとし、いきなり標準運用にしない。

## 採用判断

- v1.0本体には組み込まない。
- Colab標準運用には組み込まない。
- ローカル開発環境での補助連携としてのみ評価する。
- メッセージには秘匿情報を含めない。
- まずは手動確認または turn 運用を優先する。
