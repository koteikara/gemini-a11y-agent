var A11Y_USAGE_LOG_SHEET_NAME = 'A11Y_API_USAGE_LOG';
var A11Y_USAGE_LOG_HEADERS = ['timestamp','userEmail','provider','model','mode','ruleId','candidateId','promptTokenCount','candidatesTokenCount','thoughtsTokenCount','totalTokenCount','inputUnitUsdPer1M','outputUnitUsdPer1M','estimatedUsd','estimatedJpy','currencyRateUsdJpy','status','error','responseId','modelVersion','note','imageMode','imageSourceResolved','imageMimeType','altAssessment','suggestedAlt'];

function getA11yUsageLogSheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(A11Y_USAGE_LOG_SHEET_NAME) || ss.insertSheet(A11Y_USAGE_LOG_SHEET_NAME);
  if (sheet.getLastRow() === 0) sheet.appendRow(A11Y_USAGE_LOG_HEADERS);
  return sheet;
}

function appendA11yUsageLog(entry) {
  entry = entry || {};
  var usage = entry.usage || {};
  var pricing = entry.pricing || {};
  var cost = entry.cost || {};
  var email = 'unknown';
  try { email = Session.getActiveUser().getEmail() || 'unknown'; } catch (e) {}
  getA11yUsageLogSheet_().appendRow([
    new Date(), email, entry.provider || '', entry.model || '', entry.mode || '', entry.ruleId || '', entry.candidateId || '',
    usage.promptTokenCount || '', usage.candidatesTokenCount || '', usage.thoughtsTokenCount || '', usage.totalTokenCount || '',
    pricing.inputUsdPer1M, pricing.outputUsdPer1M, cost.estimatedUsd, cost.estimatedJpy, entry.usdJpyRate || '',
    entry.status || '', entry.error || '', usage.responseId || '', usage.modelVersion || '', pricing.note || entry.note || '', entry.imageMode || '', entry.imageSourceResolved || '', entry.imageMimeType || '', entry.altAssessment || '', entry.suggestedAlt || ''
  ]);
}

function getA11yUsageSummary() {
  var sheet = getA11yUsageLogSheet_();
  var values = sheet.getDataRange().getValues();
  var rows = values.slice(1);
  var today = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd');
  var summary = {sheetName: A11Y_USAGE_LOG_SHEET_NAME, recent: [], todayCalls: 0, todayTotalTokens: 0, todayEstimatedUsd: 0, todayEstimatedJpy: 0};
  rows.forEach(function(row) {
    var rowDay = row[0] instanceof Date ? Utilities.formatDate(row[0], Session.getScriptTimeZone(), 'yyyy-MM-dd') : '';
    if (rowDay === today) {
      summary.todayCalls += 1;
      summary.todayTotalTokens += Number(row[10] || 0);
      summary.todayEstimatedUsd += Number(row[13] || 0);
      summary.todayEstimatedJpy += Number(row[14] || 0);
    }
  });
  summary.recent = rows.slice(-10).reverse().map(function(row) { return {timestamp: row[0], provider: row[2], model: row[3], ruleId: row[5], candidateId: row[6], totalTokenCount: row[10], estimatedUsd: row[13], estimatedJpy: row[14], status: row[16], error: row[17], imageMode: row[21], altAssessment: row[24], suggestedAlt: row[25]}; });
  return summary;
}
