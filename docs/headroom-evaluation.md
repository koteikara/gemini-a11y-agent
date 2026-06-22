# Headroom 評価メモ

## 1. 評価目的

Headroom を、Gemini-A11y Agent の本体処理ではなく、開発・検証・引き継ぎ時に発生する長いテキストを圧縮・要約する補助ツールとして評価します。

この評価では、圧縮後のテキストが人間またはCodexの一次確認を助けるかを確認します。圧縮後テキストを検証結果の唯一の根拠にはせず、必要に応じて元ログ・元diff・元コマンド出力へ戻って確認します。

## 2. Headroomの想定用途

Headroom の用途は、以下のような長い開発・検証補助テキストの圧縮に限定します。

- Colab実行ログの圧縮
- regression / compare 結果の圧縮
- Codexへの長い引き継ぎ内容の圧縮
- PR履歴や作業サマリの圧縮
- old / ai / gold 差分を人間やAIが読む前の要約補助

## 3. 使わない対象

以下は Headroom の入力対象にしません。

- 変換対象HTML本文
- table単体LLM入力
- gold fixture
- ai-v1.0 fixture
- アクセシビリティ補正本体の前処理

Headroom の圧縮・要約により、HTML構造、セル文言、属性、周辺文脈が失われる可能性があります。そのため、Gemini-A11y Agent v1.0 の検証前提である `old` / `ai-v1.0` / `gold` の関係や、本文欠落・タグ構造破壊・文言改変を避ける方針には介入させません。

## 4. 評価対象にするサンプル

実ファイルや機密ログは追加せず、リポジトリ内で再現可能な既存コマンドの出力を想定サンプルとして扱います。

候補コマンド:

```bash
python tools/check_saga_city_test_fixture.py

python tools/compare_saga_city_versions.py \
  --fixture-root tests/fixtures/html/saga-city-test \
  --case sg02395-composite
```

2026-06-22 時点のCodex環境では `headroom` コマンドが見つからなかったため、実圧縮は未実施です。Headroom を利用できる環境で再評価する場合は、上記コマンドの出力を一時ファイルに保存し、その一時ファイルを圧縮対象にしてください。ただし、HTML本文、fixture本文、APIキー、GitHub token、個人情報を含むログは入力しないでください。

## 5. 評価観点

Headroom を試す場合、または試せない場合でも、以下の観点で結果を記録します。

- 圧縮後も `PASS` / `WARNING` / `ERROR` が判別できるか
- `matches_gold` / `differs_from_gold` / `regressed` / `warning` が欠落しないか
- `previous fixture missing` のような想定内警告を誤って失敗扱いしないか
- Codexへの指示に必要な前提・禁止事項が残るか
- HTML本文やfixtureの内容を圧縮対象にしていないか
- APIキー、GitHub token、個人情報を含むログを対象にしていないか
- 圧縮後テキストだけで判断せず、必要時に元出力を参照できる運用になっているか

## 6. 判定基準

Headroom は、以下を満たす場合に補助利用候補として扱います。

- 圧縮後も検証結果の状態語や重要な警告が保持される
- 想定内警告と失敗を区別できる
- Codexへの引き継ぎに必要な目的、前提、禁止事項が残る
- 元ログ・元diff・元コマンド出力を一次根拠として保持できる
- HTML本文、fixture、gold、ai-v1.0 を圧縮・要約・改変しない運用にできる
- 秘匿情報を含む入力を除外できる

以下のいずれかに該当する場合は、Gemini-A11y Agent の運用には採用しません。

- `ERROR` や `regressed` などの重要状態が欠落する
- `previous fixture missing` などの想定内警告を失敗として誤認させる
- 禁止事項や前提条件が圧縮で欠落する
- HTML本文やfixture本文を入力する必要がある
- 秘匿情報を安全に除外できない

## 7. セキュリティ・秘匿情報の扱い

Headroom に渡す前に、対象テキストに以下が含まれていないことを確認します。

- APIキー
- GitHub token
- 個人情報
- 非公開URLや認証付きURL
- 未公開の顧客情報・案件情報
- HTML本文やfixture本文のうち、圧縮対象外と定めたもの

秘匿情報を含む可能性があるログは、Headroom に渡しません。マスキング済みであっても、元ログを確認できない状態で圧縮結果だけを判断材料にしないでください。

## 8. Gemini-A11y Agent本体へ組み込まないこと

Headroom は、Gemini-A11y Agent 本体処理へ組み込みません。

特に、以下は行いません。

- 変換対象HTML本文をHeadroomに渡す
- table単体LLM入力をHeadroomに渡す
- gold fixtureをHeadroomで生成・要約・改変する
- ai-v1.0 fixtureをHeadroomで生成・要約・改変する
- アクセシビリティ補正本体の前処理として使う
- 圧縮後テキストを検証結果の唯一の根拠にする
- 既存のv1.0処理フローを変更する

## 9. 次のアクション

1. Headroom を利用できるローカル環境または検証環境を用意する。
2. `python tools/check_saga_city_test_fixture.py` の出力を一時ファイルに保存し、圧縮後も `PASS` / `WARNING` / `ERROR` が判別できるか確認する。
3. `python tools/compare_saga_city_versions.py --fixture-root tests/fixtures/html/saga-city-test --case sg02395-composite` の出力を一時ファイルに保存し、`matches_gold` / `differs_from_gold` / `regressed` / `warning` が保持されるか確認する。
4. Codex引き継ぎ文のサンプルを、HTML本文・fixture本文・秘匿情報を含まない範囲で用意し、目的、前提、禁止事項が圧縮後も残るか確認する。
5. 圧縮結果と元出力を比較し、補助利用可否をこのメモまたは後続PRで更新する。
