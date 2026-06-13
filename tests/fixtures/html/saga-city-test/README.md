# saga-city-test fixture

このfixtureは実在ページそのものではなく、検証用に合成したHTMLです。

`saga-city/old/sg02395.html` と `saga-city/gold/sg02395.html` の差分から、アクセシビリティ補正の代表修正ケースを抽出し、1つのcomposite HTMLとして管理します。

## ディレクトリ

- `old/`: AI入力用の補正前composite HTMLです。
- `gold/`: 期待出力となる正解composite HTMLです。
- `ai-v0/`: 旧版AI出力の配置先です。
- `ai-v1.0/`: v1.0出力の配置先です。

## 方針

今後、実在ページfixtureとは分離した検証用HTMLは、`*-test` 配下に追加します。
