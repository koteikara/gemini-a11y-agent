# kage評価：佐賀市ページ 14256

## 1. 実行環境

- 実施日: 2026-06-22
- 実行場所: Codex検証環境（Linux / `/workspace/gemini-a11y-agent`）
- 対象ページ: `https://www.city.saga.lg.jp/main/14256.html`
- kageの位置づけ: fixture作成前の証跡保存・オフライン確認用
- Go: `go version go1.25.1 linux/amd64`
- Chrome / Chromium: この環境では `google-chrome`、`chromium`、`chromium-browser` が見つからなかった
- ネットワーク制約: `go install` 実行時に `proxy.golang.org` および `github.com` への接続が 403 で失敗した

このため、今回のCodex環境では kage のインストールおよび実ページ保存までは完了できなかった。以下は、実行可否確認の結果と、Colab外またはローカルPCで再実施する際の最小評価手順を記録する。

## 2. 実行コマンド

実行可否確認として、以下を実行した。

```bash
command -v kage || true

go version || true

google-chrome --version || chromium --version || chromium-browser --version || true
```

結果:

- `kage` は未インストール
- Go は利用可能
- Chrome / Chromium は未検出

kageのインストール確認として、以下を試した。

```bash
GOBIN=/tmp/kage-bin go install github.com/tamnd/kage/cmd/kage@latest
```

結果:

```text
go: github.com/tamnd/kage/cmd/kage@latest: module github.com/tamnd/kage/cmd/kage: Get "https://proxy.golang.org/github.com/tamnd/kage/cmd/kage/@v/list": Forbidden
```

Go module proxyを使わない直接取得も試した。

```bash
GOBIN=/tmp/kage-bin GOPROXY=direct go install github.com/tamnd/kage/cmd/kage@latest
```

結果:

```text
go: github.com/tamnd/kage/cmd/kage@latest: module github.com/tamnd/kage/cmd/kage: git ls-remote -q https://github.com/tamnd/kage in /root/go/pkg/mod/cache/vcs/1b448e08f3ac3532bb4c9d7f48821be28326f8342f5625783e1af394117bcfa4: exit status 128:
	fatal: unable to access 'https://github.com/tamnd/kage/': CONNECT tunnel failed, response 403
```

ローカルPCまたはColab外の検証環境で再実施する場合の想定コマンドは以下。

```bash
go install github.com/tamnd/kage/cmd/kage@latest

kage clone \
  --max-depth 0 \
  --max-pages 1 \
  -o /path/to/kage-output/saga-city-14256 \
  https://www.city.saga.lg.jp/main/14256.html

du -sh /path/to/kage-output/saga-city-14256

find /path/to/kage-output/saga-city-14256 -maxdepth 3 -type f | sort

rg -n "contents_0|<h3|<h4|<table|iframe|<img" /path/to/kage-output/saga-city-14256
```

## 3. 保存結果の概要

今回のCodex環境では、kage本体の取得とChrome / Chromiumの実行環境を満たせなかったため、対象ページの保存物は生成していない。

したがって、このリポジトリには kage 出力HTML、CSS、画像、フォント、ログ、スクリーンショットなどの保存物を追加しない。

## 4. 確認観点ごとの結果

| 確認観点 | 今回の結果 | メモ |
|---|---|---|
| 保存HTML内に `contents_0` が残るか | 未確認 | kage実行不可のため、保存HTMLを生成できなかった。再実施時は `rg -n "contents_0"` で確認する。 |
| 導入文が残るか | 未確認 | 再実施時は保存HTMLをブラウザ表示し、元ページ冒頭の本文が残るか目視確認する。 |
| h3 / h4 が残るか | 未確認 | 再実施時は `rg -n "<h3|<h4"` とブラウザ表示で確認する。 |
| table構造が残るか | 未確認 | 再実施時は `rg -n "<table|<thead|<tbody|<tr|<th|<td"` で構造を確認する。 |
| iframeや画像周辺の情報がどのように保存されるか | 未確認 | 再実施時は `rg -n "iframe|<img|src="` で、iframe要素、代替テキスト、ローカル化された画像パスを確認する。 |
| 保存HTMLが fixture 作成前の参考資料として使えそうか | 条件付きで未判断 | 保存物が生成できれば、fixture自動生成ではなく、元ページ更新前の目視確認・証跡確認に限定して使える可能性がある。 |
| 保存物の容量がどの程度になるか | 未確認 | 再実施時は `du -sh` の結果を記録する。 |
| GitHubに保存すべきか、Google Drive等の外部保管にすべきか | Drive等の外部保管を推奨 | 実保存物は画像・CSS・フォントを含み容量が増えやすく、外部サイト由来の複製物でもあるため、GitHubには原則コミットしない。 |

## 5. 保存物の容量

保存物は今回生成していないため、容量は未計測。

再実施時は以下を記録する。

```bash
du -sh /path/to/kage-output/saga-city-14256
```

また、HTML単体と関連アセットの内訳を確認する場合は以下を使う。

```bash
find /path/to/kage-output/saga-city-14256 -type f -printf '%s %p\n' | sort -nr | head -50
```

## 6. GitHub保存 / Drive保存の推奨判断

現時点の推奨は、kage保存物そのものはGoogle Drive等の外部ストレージに保管し、GitHubには評価メモだけを残す運用とする。

理由:

- kage保存物はCSS、画像、フォント、メディア等を含み、ページによって容量が大きくなる可能性がある
- 外部サイト由来の複製物をリポジトリに継続保存すると、著作権・ライセンス・更新差分の扱いが複雑になる
- Gemini-A11y Agentのテスト再現性に必要なのは、管理済みfixtureと比較結果であり、kage出力一式ではない
- 今回の目的は、fixture作成前の証跡保存・オフライン確認用としての適性確認であり、kage出力をソース管理することではない

GitHubに保存してよいもの:

- 評価結果ドキュメント
- 実行コマンド
- 容量・確認結果のサマリ
- 保存先の管理方針

GitHubに保存しないもの:

- kage出力HTML
- ローカル化された画像、CSS、フォント、メディア
- 不要な実行ログ
- APIキー、GitHub token、個人情報を含む可能性があるファイル

## 7. 今後の扱い

- kageは、ColabではなくローカルPCまたはColab外の検証環境で評価する
- 評価対象はまず `https://www.city.saga.lg.jp/main/14256.html` の1ページに限定する
- kage出力は、fixture作成前の証跡保存、元ページ更新前の目視確認、レビュー用参考資料としてのみ扱う
- kage出力から `gold` fixture や `ai-v1.0` fixture を自動生成しない
- kage出力をGemini-A11y Agentの標準入力HTMLとして使わない
- 保存物の容量と構造確認が完了したら、本ドキュメントに実測値を追記する

## 8. 本体組み込みは行わない

今回の評価では、kageをGemini-A11y Agent本体へ組み込まない。

また、以下も行わない。

- kage出力HTMLを Gemini-A11y Agent の標準入力HTMLとして使うこと
- kage出力HTMLから `gold` fixture を自動生成すること
- kage出力HTMLから `ai-v1.0` fixture を自動生成すること
- HTML補正本体に kage を組み込むこと
- v1.0の既存処理フローを変更すること

今回の変更はドキュメント追加と、外部ツール評価方針ドキュメントから本評価メモへのリンク追加に限定する。
