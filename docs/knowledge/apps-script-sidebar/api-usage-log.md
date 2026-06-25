# API使用履歴ログ

API連携を使った場合、`A11Y_API_USAGE_LOG` シートを自動作成し、成功、APIエラー、JSON検証エラー、レート制限などの結果を追記します。

## 列

1. timestamp
2. userEmail
3. provider
4. model
5. mode
6. ruleId
7. candidateId
8. promptTokenCount
9. candidatesTokenCount
10. thoughtsTokenCount
11. totalTokenCount
12. inputUnitUsdPer1M
13. outputUnitUsdPer1M
14. estimatedUsd
15. estimatedJpy
16. currencyRateUsdJpy
17. status
18. error
19. responseId
20. modelVersion
21. note

## userEmail

`Session.getActiveUser().getEmail()` で取得できる場合だけ記録し、取得できない場合は `unknown` とします。

## UI表示

使用履歴タブでは直近10件、今日のAPI呼び出し回数、今日の合計token数、今日の概算USD/JPYを表示します。詳細確認はシートを直接開いて行います。
