/** Centralized approximate pricing. Update manually when provider prices change. */
var A11Y_MODEL_PRICING = {
  gemini: {
    'gemini-2.5-flash': {inputUsdPer1M: 0.30, outputUsdPer1M: 2.50, note: 'Manual estimate; confirm current Google pricing before paid use.'},
    'gemini-2.5-flash-lite': {inputUsdPer1M: 0.10, outputUsdPer1M: 0.40, note: 'Manual estimate; confirm current Google pricing before paid use.'}
  }
};

function resolveA11yPricing(provider, model, pricingMode) {
  if (pricingMode === 'free') return {inputUsdPer1M: 0, outputUsdPer1M: 0, note: 'free mode'};
  if (pricingMode === 'unknown') return {inputUsdPer1M: '', outputUsdPer1M: '', note: 'unknown pricing'};
  var p = A11Y_MODEL_PRICING[provider] && A11Y_MODEL_PRICING[provider][model];
  return p || {inputUsdPer1M: '', outputUsdPer1M: '', note: 'pricing not configured'};
}

function estimateA11yCost(usage, pricing, usdJpyRate) {
  var input = Number(pricing.inputUsdPer1M);
  var output = Number(pricing.outputUsdPer1M);
  if (pricing.inputUsdPer1M === '' || pricing.outputUsdPer1M === '' || isNaN(input) || isNaN(output)) {
    return {estimatedUsd: '', estimatedJpy: ''};
  }
  var prompt = Number(usage.promptTokenCount || 0);
  var candidates = Number(usage.candidatesTokenCount || 0);
  var thoughts = Number(usage.thoughtsTokenCount || 0);
  var usd = prompt / 1000000 * input + (candidates + thoughts) / 1000000 * output;
  return {estimatedUsd: usd, estimatedJpy: usd * Number(usdJpyRate || 0)};
}
