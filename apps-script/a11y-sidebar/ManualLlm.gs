var A11yManualLlm = (function () {
  function buildPrompt(payload) {
    var ruleId = payload && payload.ruleId ? payload.ruleId : 'UNKNOWN';
    return [
      '以下のHTMLアクセシビリティ候補を改善してください。',
      'ツールへ戻すため、回答はJSONのみで返してください。',
      '対象ルール: ' + ruleId,
      '入力:',
      JSON.stringify(payload || {}, null, 2),
      '出力形式:',
      JSON.stringify({ruleId: ruleId, replacementText: '改善後の短い文言', reason: '理由'}, null, 2)
    ].join('\n');
  }

  function validateResponse(ruleId, responseText) {
    try {
      var parsed = JSON.parse(responseText);
      if (parsed.ruleId !== ruleId) return {ok:false,error:'ruleIdが一致しません。'};
      if (!parsed.replacementText || String(parsed.replacementText).trim() === '') {
        return {ok:false,error:'replacementTextが空です。'};
      }
      if (parsed.html || parsed.fullHtml || parsed.document) {
        return {ok:false,error:'HTML全体を書き換える回答は受け付けません。'};
      }
      return {ok:true,value:parsed};
    } catch (e) {
      return {ok:false,error:'JSONとして解析できません: ' + e.message};
    }
  }

  return {buildPrompt: buildPrompt, validateResponse: validateResponse};
})();
