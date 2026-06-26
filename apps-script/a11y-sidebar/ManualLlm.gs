var A11yManualLlm = (function () {
  function buildPrompt(payload) {
    var ruleId = payload && payload.ruleId ? payload.ruleId : 'UNKNOWN';
    return [
      '以下のHTMLアクセシビリティ候補を改善してください。',
      'ツールへ戻すため、回答はJSONのみで返してください。',
      'HTML全体は返さず、候補に必要な短い文言だけを返してください。',
      '対象ルール: ' + ruleId,
      '入力:',
      JSON.stringify(payload || {}, null, 2),
      '出力形式:',
      JSON.stringify({
        ruleId: ruleId,
        replacementText: 'リンク文言などの改善案。不要な場合は省略可',
        alt: '画像alt案。不要な場合は省略可',
        caption: 'table caption案。不要な場合は省略可',
        title: 'iframe title案。不要な場合は省略可',
        altAssessment: '画像alt判定。appropriate / needs_fix / inappropriate / unknown。不要な場合は省略可',
        suggestedAlt: '画像付きalt評価の推奨alt。不要な場合は省略可',
        reason: '理由'
      }, null, 2)
    ].join('\n');
  }

  function validateResponse(ruleId, responseText) {
    try {
      var parsed = JSON.parse(responseText);
      if (parsed.ruleId !== ruleId) return {ok:false,error:'ruleIdが一致しません。'};
      if (parsed.html || parsed.fullHtml || parsed.document) {
        return {ok:false,error:'HTML全体を書き換える回答は受け付けません。'};
      }
      if (!parsed.replacementText && !parsed.alt && !parsed.caption && !parsed.title && !parsed.suggestedAlt) {
        return {ok:false,error:'replacementText / alt / caption / title / suggestedAlt のいずれかが必要です。'};
      }
      return {ok:true,value:parsed};
    } catch (e) {
      return {ok:false,error:'JSONとして解析できません: ' + e.message};
    }
  }

  return {buildPrompt: buildPrompt, validateResponse: validateResponse};
})();
