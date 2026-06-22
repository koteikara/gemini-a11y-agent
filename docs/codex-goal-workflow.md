# Codex `/goal`・`/plan` 運用ルール

## 目的

Gemini-A11y Agent の長めの修正作業で、Codex が途中から元の制約を忘れたり、v1.0方針から逸脱したりすることを防ぐため、Codex CLI の `/goal` と `/plan` を使った作業運用ルールをまとめます。

## `/goal` の位置づけ

`/goal` は、作業全体の目的と守るべき制約を最初に固定するためのものです。Gemini-A11y Agent では、HTML本文、table構造、fixture方針、外部支援ツールの扱いを誤って変更しないために使います。

標準goal文:

```text
Gemini-A11y Agent v1.0 の既存方針を維持し、HTML本文・table構造・fixture方針を壊さずに、指定された開発またはドキュメント修正だけを行う。外部ツールは本体処理へ組み込まず、評価・証跡・開発補助に限定する。
```

## `/plan` と併用する理由

`/plan` は、実装や編集に入る前に、変更対象、触ってよいファイル、触ってはいけないファイル、確認コマンドを明確にするために使います。

特に以下の事故を避けるために、長めの作業では `/goal` と `/plan` を併用します。

- 本体コードを変更しない依頼でPythonコードを編集してしまう。
- fixture、`gold`、`ai-v1.0` を不要に更新してしまう。
- 外部支援ツールをv1.0本体処理へ組み込んでしまう。
- Colab / Sheets / Drive などCodex環境外の確認を完了扱いにしてしまう。

## 推奨手順

Codex CLI では、長めの作業開始時に以下の順で進めます。

```text
/goal <今回の目的と制約>
/plan <変更対象、触ってよいファイル、触ってはいけないファイル、確認コマンドを整理>
```

## 作業種別ごとのgoal例

### ドキュメント修正

```text
/goal Gemini-A11y Agent v1.0 の方針を変えず、指定された評価・運用ドキュメントだけを更新する。Python実装、fixture、gold、ai-v1.0 出力は変更しない。
```

### PRレビュー対応

```text
/goal PRレビューコメントに対応する。指摘された箇所だけを修正し、既存のv1.0検証前提、fixture方針、本文不改変方針を維持する。
```

### 実装修正

```text
/goal 指定された不具合だけを最小差分で修正する。自治体HTML本文、tableセル文言、gold fixtureを不必要に変更せず、既存テストと比較結果を維持する。
```

### 外部ツール評価

```text
/goal 外部ツールは Gemini-A11y Agent 本体処理へ組み込まず、評価・証跡保存・開発補助としてのみ整理する。標準入力HTML、gold fixture、ai-v1.0 fixture の自動生成には使わない。
```

### 運用開始チェックリスト整備

```text
/goal v1.0運用開始前に確認すべき項目をドキュメントとして整理する。本体コード、fixture、gold、ai-v1.0 出力は変更しない。
```

## Codex CLI と Codex Web / ChatGPT Codexタスクの違い

Codex CLI では `/goal` と `/plan` をコマンドとして使える場合があります。一方、Codex Web / ChatGPT Codexタスクでは `/goal` コマンドそのものが使えない場合があります。

その場合は、プロンプト冒頭に次のような `Goal:` セクションを書き、同じ制約として扱います。

```text
Goal:
Gemini-A11y Agent v1.0 の既存方針を維持し、本体コード・fixture・gold・ai-v1.0 出力を変更せず、指定されたドキュメント整備だけを行う。
```

## 禁止事項

- `/goal` を設定していても、gold fixture を外部ツールや推測で自動生成しない。
- HTML本文やtableセル文言を要約・圧縮・意訳しない。
- v1.0本体処理へ外部ツールを直接組み込まない。
- APIキー、GitHub token、個人情報、非公開情報をgoalやプロンプトに含めない。
- `/goal` の目的と異なる追加修正を勝手に行わない。
- `/plan` なしで大きな複数ファイル修正に入らない。

## 関連ドキュメントリンク

- [Codex運用フロー](codex-workflow.md)
- [v1.0運用開始前チェックリスト](v1.0-operation-readiness-checklist.md)
- [v1.0運用手順](operations-v1.0.md)
- [外部支援ツール評価](external-tools-evaluation.md)
- [外部支援ツール評価ステータス一覧](external-tools-evaluation-status.md)
