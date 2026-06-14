# v1.0で改善された内容

## 目的

このドキュメントは、Gemini-A11y Agent v1.0 が旧版からどのように改善されたかを整理するものです。

旧版AI出力 `ai-v0` は今後生成せず、過去に確認済みの課題と、現在の `ai-v1.0` / `gold` 比較結果をもとに改善内容を記録します。

## 検証対象

```text
tests/fixtures/html/saga-city-test/
  old/sg02395-composite.html
  ai-v1.0/sg02395-composite.html
  gold/sg02395-composite.html
```

## 検証結果

Colab実運用環境で `old/sg02395-composite.html` を v1.0 処理に通し、`ai-v1.0/sg02395-composite.html` を生成しました。

比較結果：

```text
matches_gold: 18
differs_from_gold: 0
regressed: 0
warning: 0
```

`ai-v0` は生成しないため、`previous fixture missing` の warning は想定どおりです。

## 旧版で確認していた主な課題

旧版では、以下の課題が確認されていました。

### 1. table前導入文が欠落する

旧版では、table前の h3 / p / 注意文などが table チャンクに吸収され、table処理時にLLMが非table要素を落とすことがありました。

影響：

- 「休日（日曜日または祝日）在宅当番医について」が欠落する
- 診療時間の説明が欠落する
- 小児受診や事前問い合わせの注意文が欠落する
- tableだけが残り、利用者に必要な前提説明が消える

v1.0での改善：

- table前導入文を独立保持
- h4のみtable側へ紐付け
- table単体をLLMに渡して差し戻す方式へ変更
- 非table要素がLLM応答で消える経路を抑止

検証結果：

- `intro_text`: gold と一致
- `doctor_info_text`: gold と一致
- `consultation_hours_text`: gold と一致

### 2. h3 / h4 見出しが欠落する

旧版では、日付見出しやセクション見出しがtable処理に巻き込まれて欠落する可能性がありました。

v1.0での改善：

- h3はグローバル導入文側に保持
- h4は直後のtableと関連する見出しとして保持
- chunker側で導入文とtableの結合ルールを見直し

検証結果：

- `h3_count`: gold と一致
- `h4_count`: gold と一致

### 3. table見出し構造が不十分

旧版では、先頭行がtdのまま残る、またはscopeが不足するケースがありました。

v1.0での改善：

- row / col / none の判定を追加
- 先頭行が列見出しの場合、`th scope="col"` を付与
- tbody側の1列目を行見出しとして `th scope="row"` に補正
- LLM戻り値検証により、不正なtable応答は採用しない

検証結果：

- `table_count`: gold と一致
- `thead_count`: gold と一致
- `caption_count`: gold と一致
- `scope_col_count`: gold と一致
- `scope_row_count`: gold と一致
- `th_count`: gold と一致

### 4. 更新行が不要に残る

旧版では、`更新：YYYY年M月D日` のようなページ更新日がAI出力に残ることがありました。

v1.0での改善：

- `remove_update_only_nodes()` を追加
- ノード全体が更新行のみの場合に削除
- 本文中の「更新」という語は削除しない

検証結果：

- `update_line`: gold と一致

### 5. Menu / PageTop の誤検知

旧版比較では、HTMLコメントや説明文中の Menu / PageTop を拾い、共通部品混入として誤検知することがありました。

v1.0での改善：

- HTMLParserベースの判定へ変更
- コメント、script、style、head、metaを除外
- id / class / href / aria-label / 可視テキストを対象に判定

検証結果：

- `menu_present`: gold と一致
- `pagetop_present`: gold と一致
- `footer_present`: gold と一致

### 6. 既知副作用の抑制

v1.0では、以下の既知副作用も検証対象に含めています。

- `rgb（` の発生
- caption id の増加
- caption id 重複

検証結果：

- `rgb_fullwidth`: gold と一致
- `caption_id_count`: gold と一致
- `caption_id_duplicates`: gold と一致

## v1.0の到達点

`saga-city-test` 合成fixtureでは、v1.0出力がgoldと18項目すべて一致しました。

このため、少なくとも以下の代表課題については、v1.0で改善済みと判断します。

- table前導入文の保持
- h3 / h4 見出しの保持
- table構造補正
- 更新行削除
- Menu / PageTop 誤検知抑制
- 既知副作用の抑制

## 今後の検証方針

今後は `ai-v0` を生成せず、以下を基本とします。

```text
old → ai-v1.0 → gold
```

確認コマンド：

```bash
python tools/check_saga_city_test_fixture.py

python tools/compare_saga_city_versions.py \
  --fixture-root tests/fixtures/html/saga-city-test \
  --case sg02395-composite
```

`previous fixture missing` は、`ai-v0` を生成しない方針のため想定どおりです。

## 注意

この結果は、`saga-city-test` 合成fixtureに含めた代表ケースに対する検証結果です。
すべての自治体ページで完全に同じ結果を保証するものではありません。

今後、別パターンの課題が見つかった場合は、`*-test` fixtureを追加し、同じ形式で検証します。
