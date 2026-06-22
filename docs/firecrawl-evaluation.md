# Firecrawl 最小評価メモ

## 1. 評価目的

Firecrawl は、Gemini-A11y Agent v1.0 の標準取得処理へ組み込むためではなく、通常の `requests` / XPath / trafilatura で取得しにくいページに対する調査用・取得fallback候補として評価します。

このメモでは、Firecrawl を実APIで試す前に、評価対象、確認観点、判定基準、外部API利用時の注意点を整理します。現時点では自治体ページURLや取得結果を Firecrawl API へ送信しません。

## 2. Firecrawlの想定用途

Firecrawl は、既存の取得手段で本文・構造・リンクを確認しにくい場合の補助として扱います。

想定用途は以下です。

- JS依存ページの調査
- `requests` 取得に失敗するページの確認
- URL一覧取得
- サイト内ページ探索
- PDF / DOCX リンク抽出
- スクリーンショット証跡取得
- XPath抽出失敗時の調査用取得

## 3. 使わない対象

Firecrawl は以下には使いません。

- v1.0本体の標準取得処理
- 変換対象HTMLの自動置換
- gold fixtureの自動生成
- ai-v1.0 fixtureの自動生成
- Firecrawl MarkdownをHTML補正入力として使うこと
- Firecrawl clean HTMLをHTML補正入力として使うこと
- 既存のv1.0処理フローの変更

Firecrawl の Markdown や clean HTML は調査には有用な可能性がありますが、Gemini-A11y Agent のアクセシビリティ補正では、元HTMLのDOM構造、本文領域、table、見出し、iframe、画像、属性をできるだけ保持することが重要です。Markdown化・クリーン化された出力を補正入力にすると、検証済みのfixture前提が崩れる可能性があります。

## 4. 評価対象にするサンプル

まずは実APIを呼ばず、文書上の評価メモとして整理します。

初期候補は、既存の佐賀市ページまたは、将来 `requests` / XPath / trafilatura で取得に失敗したページとします。

候補URL：

```text
https://www.city.saga.lg.jp/main/14256.html
```

ただし、実際に Firecrawl API へ自治体ページURLや取得結果を送信するかどうかは、以下を確認してから判断します。

- Firecrawl の利用条件
- API利用コスト
- APIキー管理方法
- 自治体ページURLや取得結果を外部APIへ渡すことの可否
- robots.txt や対象サイトの利用条件
- プロジェクトの情報管理方針

## 5. 評価観点

Firecrawl を試す場合、または試せない場合でも、以下の観点を確認・記録します。

- `#contents_0` 相当の本文領域を保持できるか
- table構造が崩れないか
- h3 / h4 / 導入文が欠落しないか
- iframeや画像情報が保持されるか
- Markdown化でアクセシビリティ補正に必要な情報が失われないか
- clean HTML化で元DOM構造や属性が失われないか
- PDF / DOCX リンク抽出が調査補助として有用か
- スクリーンショット証跡がレビューや原因調査に役立つか
- API利用コストが許容範囲か
- 自治体ページURLや取得結果を外部APIへ渡して問題ないか
- robots.txt や各サイトの利用条件に反しないか
- Colab運用にAPIキー管理を追加しても問題ないか
- APIキー、GitHub token、個人情報、非公開情報がログやfixtureに混入しないか

## 6. 判定基準

Firecrawl は、以下を満たす場合に限り、調査用・fallback候補として継続評価します。

- 本文領域、見出し、table、iframe、画像情報の欠落や破壊が評価上許容できる範囲である
- Markdownやclean HTMLを補正入力にせず、調査結果としてのみ扱える
- gold fixture や ai-v1.0 fixture を自動生成・変更しない運用にできる
- 外部APIへ対象URLや取得結果を送信することが、利用条件・情報管理方針・コスト面で許容される
- robots.txt や対象サイトの利用条件に反しない
- APIキーを安全に管理でき、リポジトリ・ログ・fixtureに保存しない運用にできる

以下に該当する場合は、v1.0運用では採用しません。

- Markdown化やclean HTML化により、アクセシビリティ補正に必要なDOM構造や情報が失われる
- Firecrawl出力を補正入力やfixture生成元として使う必要が出る
- APIコスト、利用条件、情報管理、APIキー管理のいずれかに懸念が残る
- 自治体ページURLや取得結果の外部送信可否を確認できない

## 7. 外部API・コスト・利用条件の扱い

Firecrawl は外部API中心のツールであるため、実行前に以下を確認します。

- 無料枠・有料プラン・従量課金・レート制限
- APIキーの発行、保管、失効、ローテーション方法
- Colabで利用する場合の secrets 管理方法
- APIキーをリポジトリ、PR本文、ログ、fixture、Notebook出力に保存しない手順
- 自治体ページURLや取得結果を外部APIへ送信することの可否
- 対象サイトの robots.txt、利用条件、スクレイピングに関する制限
- 取得結果に個人情報・非公開情報・認証情報が含まれないこと
- 証跡として保存する場合の保存場所、保存期間、公開可否

実API評価を行う場合も、最初は最小件数・最小範囲で実施し、コストとログ出力を確認します。

## 8. Gemini-A11y Agent本体へ組み込まないこと

Firecrawl は、現時点では Gemini-A11y Agent v1.0 本体へ組み込みません。

特に以下を禁止します。

- 標準取得処理を Firecrawl に置き換えること
- Firecrawl出力で変換対象HTMLを自動置換すること
- Firecrawl出力から gold fixture を自動生成すること
- Firecrawl出力から ai-v1.0 fixture を自動生成すること
- Firecrawl MarkdownをHTML補正入力として使うこと
- Firecrawl clean HTMLをHTML補正入力として使うこと

Firecrawl の評価結果は、取得失敗時の原因調査、サイト内探索、リンク抽出、スクリーンショット証跡などの補助情報としてのみ扱います。

## 9. 次のアクション

1. Firecrawl の利用条件、料金、APIキー管理方法を確認する。
2. 自治体ページURLや取得結果を外部APIへ送信してよいか、プロジェクトの情報管理方針に照らして確認する。
3. 対象サイトの robots.txt と利用条件を確認する。
4. 実API評価を行う場合は、まず `https://www.city.saga.lg.jp/main/14256.html` または将来 `requests` / XPath / trafilatura で取得に失敗したページを1件だけ対象にする。
5. HTML、Markdown、スクリーンショット、リンク抽出結果を比較し、本文領域・table・見出し・iframe・画像情報が保持されるかを記録する。
6. 評価結果を本体処理へ直結させず、必要に応じてこのメモまたは別の評価メモへ追記する。
