/** API settings stored per user. API keys are never written to sheets. */
var A11Y_API_PROP_KEYS = {
  provider: 'A11Y_API_PROVIDER',
  geminiKey: 'A11Y_GEMINI_API_KEY',
  geminiModel: 'A11Y_GEMINI_MODEL',
  pricingMode: 'A11Y_PRICING_MODE',
  usdJpyRate: 'A11Y_USD_JPY_RATE'
};

function saveA11yApiSettings(settings) {
  settings = settings || {};
  var props = PropertiesService.getUserProperties();
  props.setProperty(A11Y_API_PROP_KEYS.provider, settings.provider || 'gemini');
  props.setProperty(A11Y_API_PROP_KEYS.geminiModel, settings.model || 'gemini-2.5-flash');
  props.setProperty(A11Y_API_PROP_KEYS.pricingMode, settings.pricingMode || 'unknown');
  props.setProperty(A11Y_API_PROP_KEYS.usdJpyRate, String(settings.usdJpyRate || '150'));
  if (settings.apiKey) props.setProperty(A11Y_API_PROP_KEYS.geminiKey, settings.apiKey);
  return getA11yApiSettingsStatus();
}

function getA11yApiSettingsStatus() {
  var props = PropertiesService.getUserProperties();
  var provider = props.getProperty(A11Y_API_PROP_KEYS.provider) || 'gemini';
  return {
    provider: provider,
    model: props.getProperty(A11Y_API_PROP_KEYS.geminiModel) || 'gemini-2.5-flash',
    pricingMode: props.getProperty(A11Y_API_PROP_KEYS.pricingMode) || 'unknown',
    usdJpyRate: Number(props.getProperty(A11Y_API_PROP_KEYS.usdJpyRate) || 150),
    hasApiKey: !!props.getProperty(A11Y_API_PROP_KEYS.geminiKey)
  };
}

function deleteA11yApiKey() {
  PropertiesService.getUserProperties().deleteProperty(A11Y_API_PROP_KEYS.geminiKey);
  return getA11yApiSettingsStatus();
}

function testA11yApiConnection() {
  return generateCandidateWithApi({
    ruleId: 'LINK-R-02',
    candidateId: 'connection-test',
    message: '接続テスト',
    payload: {href: 'https://example.com', linkText: 'こちら', contextText: '申請方法はこちらをご覧ください。'},
    mode: 'connection-test'
  });
}
