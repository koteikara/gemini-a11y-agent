# 画像付き alt 評価

IMG-R-05、IMG-R-09、IMG-W-01 の候補カードでは画像プレビュー、現在のalt、ルールベース判定、推奨alt、手入力欄を表示する。

対応画像ソース:

- data URI
- absolute HTTP/HTTPS URL
- relative URL + ベースURL
- サンプルHTML内の自己完結data URI SVG

ルールベース判定は、空alt、`画像`、`写真`、ファイル名ベース、リンク画像なのに目的が伝わらないaltを `needs_fix` とする。API評価では取得可能な画像を Gemini `generateContent` の inlineData として送り、画像取得に失敗した場合はテキストのみの候補生成へフォールバックする。
