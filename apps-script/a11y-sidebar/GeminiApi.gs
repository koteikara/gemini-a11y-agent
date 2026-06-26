var A11Y_API_SUPPORTED_RULES = {'HTML-R-15':true,'LINK-R-02':true,'LINK-R-04':true,'IMG-R-05':true,'IMG-R-09':true,'IMG-W-02':true,'IMG-W-01':true};

function generateCandidateWithApi(payload) {
  payload = payload || {};
  var status = getA11yApiSettingsStatus();
  var provider = status.provider || 'gemini';
  var model = status.model || 'gemini-2.5-flash';
  var pricing = resolveA11yPricing(provider, model, status.pricingMode);
  var logBase = {provider: provider, model: model, mode: payload.mode || 'api-candidate', ruleId: payload.ruleId, candidateId: payload.candidateId, pricing: pricing, usdJpyRate: status.usdJpyRate, imageMode: 'text_only', imageSourceResolved: 'no', imageMimeType: '', altAssessment: '', suggestedAlt: ''};
  try {
    if (provider !== 'gemini') throw new Error('未対応providerです: ' + provider);
    if (!status.hasApiKey) throw new Error('APIキーが未設定です。');
    if (!A11Y_API_SUPPORTED_RULES[payload.ruleId]) throw new Error('API候補生成の対象外ルールです: ' + payload.ruleId);
    var apiKey = PropertiesService.getUserProperties().getProperty(A11Y_API_PROP_KEYS.geminiKey);
    var imageInfo = resolveGeminiImagePart_(payload);
    var endpoint = 'https://generativelanguage.googleapis.com/v1beta/models/' + encodeURIComponent(model) + ':generateContent?key=' + encodeURIComponent(apiKey);
    logBase.imageMode = imageInfo.imageMode; logBase.imageSourceResolved = imageInfo.resolved ? 'yes' : 'no'; logBase.imageMimeType = imageInfo.mimeType || '';
    var res = UrlFetchApp.fetch(endpoint, {method: 'post', contentType: 'application/json', muteHttpExceptions: true, payload: JSON.stringify(buildGeminiRequest_(payload, imageInfo))});
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
    appendA11yUsageLog(Object.assign({}, logBase, {usage: usage, cost: estimateA11yCost(usage, pricing, status.usdJpyRate), status: 'success', altAssessment: validation.value.altAssessment || '', suggestedAlt: validation.value.suggestedAlt || validation.value.alt || ''}));
    return {ok:true,value:validation.value,usage:usage};
  } catch (e) {
    appendA11yUsageLog(Object.assign({}, logBase, {usage: {}, cost: {}, status: 'error', error: e.message}));
    return {ok:false,error:e.message};
  }
}

function buildGeminiRequest_(payload, imageInfo) {
  var prompt = [
    'You are helping fix small Japanese HTML accessibility candidates.',
    'Return JSON only. Do not include html, fullHtml, document, markdown, or explanations outside JSON.',
    'Keep the answer short and suitable for the requested field.',
    JSON.stringify({ruleId: payload.ruleId, message: payload.message, payload: payload.payload || {}, imageMode: imageInfo && imageInfo.imageMode, outputContract: {ruleId: payload.ruleId, replacementText: 'optional', alt: 'optional', caption: 'optional', title: 'optional', altAssessment: 'appropriate|needs_fix|inappropriate|unknown for image alt rules', suggestedAlt: 'optional for image alt rules', reason: 'required'}}, null, 2)
  ].join('\n');
  var parts = [{text: prompt}];
  if (imageInfo && imageInfo.part) parts.push(imageInfo.part);
  return {contents: [{role: 'user', parts: parts}], generationConfig: {responseMimeType: 'application/json'}};
}

function parseGeminiUsage_(response) {
  var usage = response.usageMetadata || {};
  usage.responseId = response.responseId || '';
  usage.modelVersion = response.modelVersion || '';
  return usage;
}

function resolveGeminiImagePart_(payload) {
  var result = {imageMode: 'text_only', resolved: false, mimeType: '', part: null};
  var ruleId = payload.ruleId || '';
  if (!{'IMG-R-05':true,'IMG-R-09':true,'IMG-W-01':true}[ruleId]) return result;
  var src = ((payload.payload || {}).src || '').trim();
  if (!src) { result.imageMode = 'image_unresolved'; return result; }
  try {
    var mime = '';
    var bytes = null;
    if (/^data:/i.test(src)) {
      var m = src.match(/^data:([^;,]+)(;base64)?,(.*)$/i);
      if (!m) throw new Error('data URIを解析できません。');
      mime = m[1] || 'application/octet-stream';
      bytes = m[2] ? Utilities.base64Decode(m[3]) : Utilities.newBlob(decodeURIComponent(m[3]), mime).getBytes();
      result.imageMode = 'image_inline';
    } else {
      var url = src;
      if (!/^https?:\/\//i.test(url) && payload.baseUrl) url = new URL_(src, payload.baseUrl);
      if (!/^https?:\/\//i.test(url)) throw new Error('画像URLを解決できません。');
      var fetched = UrlFetchApp.fetch(url, {muteHttpExceptions: true});
      if (fetched.getResponseCode() < 200 || fetched.getResponseCode() >= 300) throw new Error('画像取得に失敗しました: ' + fetched.getResponseCode());
      var blob = fetched.getBlob();
      mime = blob.getContentType() || guessImageMime_(url);
      bytes = blob.getBytes();
      result.imageMode = 'image_url';
    }
    result.resolved = true;
    result.mimeType = mime;
    result.part = {inlineData: {mimeType: mime, data: Utilities.base64Encode(bytes)}};
  } catch (e) {
    result.imageMode = 'image_unresolved';
    result.error = e.message;
  }
  return result;
}
function URL_(path, base) { return new URL(path, base).toString(); }
function guessImageMime_(url) { var m = String(url).match(/\.([a-z0-9]+)(?:\?|$)/i); return m && m[1] === 'jpg' ? 'image/jpeg' : (m ? 'image/' + m[1].toLowerCase() : 'application/octet-stream'); }
