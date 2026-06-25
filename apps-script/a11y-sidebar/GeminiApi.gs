var A11Y_API_SUPPORTED_RULES = {'HTML-R-15':true,'LINK-R-02':true,'LINK-R-04':true,'IMG-R-05':true,'IMG-W-02':true,'IMG-W-01':true};

function generateCandidateWithApi(payload) {
  payload = payload || {};
  var status = getA11yApiSettingsStatus();
  var provider = status.provider || 'gemini';
  var model = status.model || 'gemini-2.5-flash';
  var pricing = resolveA11yPricing(provider, model, status.pricingMode);
  var logBase = {provider: provider, model: model, mode: payload.mode || 'api-candidate', ruleId: payload.ruleId, candidateId: payload.candidateId, pricing: pricing, usdJpyRate: status.usdJpyRate};
  try {
    if (provider !== 'gemini') throw new Error('未対応providerです: ' + provider);
    if (!status.hasApiKey) throw new Error('APIキーが未設定です。');
    if (!A11Y_API_SUPPORTED_RULES[payload.ruleId]) throw new Error('API候補生成の対象外ルールです: ' + payload.ruleId);
    var apiKey = PropertiesService.getUserProperties().getProperty(A11Y_API_PROP_KEYS.geminiKey);
    var endpoint = 'https://generativelanguage.googleapis.com/v1beta/models/' + encodeURIComponent(model) + ':generateContent?key=' + encodeURIComponent(apiKey);
    var res = UrlFetchApp.fetch(endpoint, {method: 'post', contentType: 'application/json', muteHttpExceptions: true, payload: JSON.stringify(buildGeminiRequest_(payload))});
    var code = res.getResponseCode();
    var body = res.getContentText();
    if (code < 200 || code >= 300) throw new Error('Gemini API error ' + code + ': ' + body.slice(0, 500));
    var parsed = JSON.parse(body);
    var usage = parseGeminiUsage_(parsed);
    var text = (((parsed.candidates || [])[0] || {}).content || {}).parts || [];
    text = text.map(function(part) { return part.text || ''; }).join('\n').trim().replace(/^```json\s*/,'').replace(/```$/,'').trim();
    var validation = A11yManualLlm.validateResponse(payload.ruleId, text);
    if (!validation.ok) {
      appendA11yUsageLog(Object.assign({}, logBase, {usage: usage, cost: estimateA11yCost(usage, pricing, status.usdJpyRate), status: 'validation_error', error: validation.error}));
      return {ok:false,error:validation.error,usage:usage};
    }
    appendA11yUsageLog(Object.assign({}, logBase, {usage: usage, cost: estimateA11yCost(usage, pricing, status.usdJpyRate), status: 'success'}));
    return {ok:true,value:validation.value,usage:usage};
  } catch (e) {
    appendA11yUsageLog(Object.assign({}, logBase, {usage: {}, cost: {}, status: 'error', error: e.message}));
    return {ok:false,error:e.message};
  }
}

function buildGeminiRequest_(payload) {
  var prompt = [
    'You are helping fix small Japanese HTML accessibility candidates.',
    'Return JSON only. Do not include html, fullHtml, document, markdown, or explanations outside JSON.',
    'Keep the answer short and suitable for the requested field.',
    JSON.stringify({ruleId: payload.ruleId, message: payload.message, payload: payload.payload || {}, outputContract: {ruleId: payload.ruleId, replacementText: 'optional', alt: 'optional', caption: 'optional', title: 'optional', reason: 'required'}}, null, 2)
  ].join('\n');
  return {contents: [{role: 'user', parts: [{text: prompt}]}], generationConfig: {responseMimeType: 'application/json'}};
}

function parseGeminiUsage_(response) {
  var usage = response.usageMetadata || {};
  usage.responseId = response.responseId || '';
  usage.modelVersion = response.modelVersion || '';
  return usage;
}
