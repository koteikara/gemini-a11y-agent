# 概算金額の計算

API使用金額は概算です。実際の請求額、無料枠、割引、レート制限、価格改定とは一致しない場合があります。

## 料金モード

- `unknown`: token数のみ記録し、金額は空欄にします。
- `free`: 無料枠として0円計算します。
- `paid`: `Pricing.gs` のモデル別単価に基づいて概算します。

## 計算式

```text
estimatedUsd =
  promptTokenCount / 1,000,000 * inputUnitUsdPer1M
  + (candidatesTokenCount + thoughtsTokenCount) / 1,000,000 * outputUnitUsdPer1M

estimatedJpy = estimatedUsd * currencyRateUsdJpy
```

USD/JPYレートはAPI設定タブで手入力します。初期値は150です。外部為替APIは使いません。
