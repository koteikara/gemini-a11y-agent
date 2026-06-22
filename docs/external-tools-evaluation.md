# 外部支援ツール評価：Headroom / Firecrawl / kage

## 目的

このドキュメントは、Gemini-A11y Agent の今後の運用・検証・証跡保存・トークン削減に役立つ可能性がある外部ツールを評価するものです。

対象は以下です。

- Headroom
- Firecrawl
- kage

v1.0本体のHTML補正処理は、すでに `saga-city-test` 合成fixtureで `ai-v1.0` と `gold` が一致しているため、現時点では外部ツールを本体処理へ直接組み込みません。

## 現時点の基本方針

| ツール | 位置づけ | 優先度 | 本体組み込み |
|---|---|---:|---|
| Headroom | ログ・差分・Codex引き継ぎの圧縮補助 | 中 | しない |
| Firecrawl | 取得fallback・JS依存ページ調査 | 中〜低 | しない |
| kage | fixture作成前の証跡保存・オフライン確認 | 高 | しない |

---

## Headroom

### 概要

Headroom は、AIエージェントやLLMアプリケーションに渡すコンテキストを圧縮するためのツールです。

主な対象は以下です。

- tool outputs
- logs
- RAG chunks
- files
- conversation history
- Codex / Claude / Cursor などのエージェント作業履歴

### Gemini-A11y Agentで期待できるメリット

Headroomは、HTML補正そのものではなく、開発・検証・引き継ぎ作業のトークン削減に使える可能性があります。

想定用途：

- Colab実行ログの圧縮
- regression / compare 結果の圧縮
- Codexへの長い引き継ぎ内容の圧縮
- PR履歴や作業サマリの圧縮
- old / ai / gold 差分を人間やAIが読む前の要約補助

### 使わない対象

以下には使わない方針です。

- 変換対象HTML本文
- table単体LLM入力
- gold fixture
- ai-v1.0 fixture
- アクセシビリティ補正本体の前処理

理由：

Gemini-A11y Agentでは、本文欠落・タグ構造破壊・セル文言改変を避けることが最重要です。  
圧縮や要約により、HTML構造や文言が変わると、v1.0で安定させた検証前提が崩れます。

### 評価観点

Headroomを試す場合は、以下を確認します。

- Colabログを圧縮しても、エラー原因を特定できるか
- compare結果を圧縮しても、matches_gold / regressed / warning が読み取れるか
- Codexへの指示文作成時に、必要な経緯が欠落しないか
- 圧縮前後で判断が変わらないか
- APIキーや秘匿情報がログに含まれる場合の取り扱いに問題がないか

### 判断

Headroomは、本体処理ではなく、開発・検証・引き継ぎ補助として評価します。  
v1.0本体には組み込みません。

---

## Firecrawl

### 概要

Firecrawl は、Webページを検索・スクレイピング・クロールし、Markdown、HTML、JSON、スクリーンショットなどに変換できるWebデータ取得APIです。

主な機能：

- Search
- Scrape
- Crawl
- Map
- Batch scrape
- JS-heavy page 対応
- Screenshot
- PDF / DOCX 等の解析
- Click / scroll / input などの操作

### Gemini-A11y Agentで期待できるメリット

Firecrawlは、通常の `requests` / XPath / trafilatura で取得しにくいページの補助取得として使える可能性があります。

想定用途：

- JS依存ページの調査
- requests取得に失敗するページの確認
- URL一覧取得
- サイト内ページ探索
- PDF / DOCX リンク抽出
- スクリーンショット証跡取得
- XPath抽出失敗時の調査用取得

### 使わない対象

以下には現時点では使いません。

- v1.0本体の標準取得処理
- 変換対象HTMLの自動置換
- gold fixtureの自動生成
- Firecrawl MarkdownをHTML補正入力として使うこと

理由：

FirecrawlのLLM-ready Markdownやclean HTMLは便利ですが、自治体HTMLのアクセシビリティ補正では、元DOM構造の保持が重要です。  
Markdown化・クリーン化により、table構造、見出し、iframe、属性、XPath対象範囲が変わる可能性があります。

### 評価観点

Firecrawlを試す場合は、以下を確認します。

- `#contents_0` 相当の本文領域を保持できるか
- table構造が崩れないか
- h3 / h4 / 導入文が欠落しないか
- iframeや画像情報が保持されるか
- Markdown化でアクセシビリティ補正に必要な情報が失われないか
- API利用コストが許容範囲か
- 自治体ページURLや取得結果を外部APIへ渡して問題ないか
- robots.txtや各サイトの利用条件に反しないか
- Colab運用にAPIキー管理を追加しても問題ないか

### 判断

Firecrawlは、取得fallback候補として保留評価します。  
本体処理にはまだ組み込みません。

---

## kage

### 概要

kage は、Webサイトをheadless Chromeでレンダリングし、最終DOMを保存したうえでJavaScriptを除去し、CSS・画像・フォントをローカル化するオフライン複製ツールです。

主な用途：

- 実ページのオフライン保存
- JS実行後DOMの保存
- スクリプトを除去した静的ミラー作成
- ローカルHTTPサーバーでの確認
- ZIMや単一実行ファイルへのパック

### Gemini-A11y Agentで期待できるメリット

kageは、fixture作成前の証跡保存や、元ページの状態を凍結する用途に向いています。

想定用途：

- 対象ページの処理前証跡保存
- 自治体ページが更新される前の状態保存
- `old` fixture作成時の参考資料
- JS実行後にしか本文が出ないページの調査
- 目視確認用のオフラインミラー作成
- 社内レビュー用の証跡共有

### 使わない対象

以下には現時点では使いません。

- Gemini-A11y Agentの標準入力HTML
- gold fixtureの自動生成
- ai-v1.0 fixtureの自動生成
- kage出力HTMLをそのまま補正対象にすること

理由：

kage出力は、証跡・閲覧用としては有用ですが、以下の変化があり得ます。

- JavaScriptが削除される
- CSS / 画像 / フォントパスがローカルに書き換えられる
- 元HTMLではなく、レンダリング後DOMになる
- XPath構造が元ページと完全には一致しない可能性がある
- 保存容量が大きくなる可能性がある

### 評価観点

kageを試す場合は、以下を確認します。

- `#contents_0` が保存HTML内に残るか
- 導入文・h3・h4・tableが保持されるか
- iframeや画像周辺の情報がどう保存されるか
- 保存HTMLがfixture作成の参考になるか
- ローカル保存容量が許容範囲か
- ColabではなくローカルPCで運用する方がよいか
- Go / Chrome / Chromium 依存が運用上問題ないか
- 保存した証跡をGitHubに入れるか、Driveに置くか

### 判断

kageは、3ツールの中では最も優先して評価する価値があります。  
ただし、補正本体には組み込まず、fixture作成前の証跡保存・オフライン確認用として扱います。

---

## 比較表

| 観点 | Headroom | Firecrawl | kage |
|---|---|---|---|
| 主目的 | コンテキスト圧縮 | Web取得API | オフライン複製 |
| 期待用途 | ログ・差分・引き継ぎ圧縮 | 取得fallback | 証跡保存・fixture補助 |
| 外部API | 構成次第 | 必要 | 不要 |
| ローカル実行 | 可能 | API中心 | 可能 |
| JS描画対応 | 対象外 | 対応 | headless Chromeで対応 |
| HTML構造保持 | 圧縮対象次第でリスク | 要検証 | レンダリング後DOMとして保存 |
| 本体処理への直接導入 | しない | しない | しない |
| 評価優先度 | 中 | 中〜低 | 高 |

---

## 今後の評価順

推奨する評価順は以下です。

1. kage
2. Headroom
3. Firecrawl

理由：

- kageは、検証対象を増やす際の証跡保存に直接役立つ
- Headroomは、長いログやCodex引き継ぎの効率化に役立つ
- Firecrawlは有用だが、外部API・コスト・自治体ページの取り扱い確認が必要

---

## 評価時の禁止事項

以下は禁止します。

- 変換対象HTML本文を外部ツールの出力で自動置換する
- gold fixtureを外部ツールで自動生成する
- ai-v1.0 fixtureを外部ツールで自動生成する
- HTML補正本体に外部ツールを直接組み込む
- 検証済みのv1.0処理フローを変更する
- APIキーやGitHub tokenをログやfixtureに含める

---

## 次のアクション候補

### kage評価

1ページだけを対象に、ローカルPCまたはColab外の環境で試す。

候補：

```text
https://www.city.saga.lg.jp/main/14256.html
```

確認：

* 保存HTMLに `contents_0` が残るか
* 導入文・h3・h4・tableが残るか
* 保存物の容量
* Drive保存・GitHub保存のどちらがよいか

### Headroom評価

Colabログや比較結果を対象に試す。

確認：

* 圧縮後もエラー原因が分かるか
* Codex指示作成に必要な文脈が残るか
* 秘匿情報を含むログを扱わない運用にできるか

### Firecrawl評価

通常取得に失敗するページが見つかったときに限定して試す。

確認：

* HTML形式で本文構造が保持されるか
* Markdown化でtableや見出しが欠落しないか
* 外部APIに対象URLを渡すことが許容されるか
