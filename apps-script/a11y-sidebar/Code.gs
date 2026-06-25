/**
 * Google Sheets container-bound entry points for the accessibility sidebar.
 * Copy this file with Sidebar.html, Rules.gs, RuleEngine.gs, ManualLlm.gs,
 * ApiSettings.gs, GeminiApi.gs, UsageLog.gs, and Pricing.gs into a
 * spreadsheet-bound Apps Script project.
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('アクセシビリティ補正')
    .addItem('HTML補正サイドバーを開く', 'showA11ySidebar')
    .addToUi();
}

function showA11ySidebar() {
  var html = HtmlService.createTemplateFromFile('Sidebar')
    .evaluate()
    .setTitle('HTMLアクセシビリティ補正')
    .setWidth(480);
  SpreadsheetApp.getUi().showSidebar(html);
}

function getA11ySidebarRules() {
  return A11Y_SIDEBAR_RULES;
}

function buildManualLlmPrompt(payload) {
  return A11yManualLlm.buildPrompt(payload);
}

function validateManualLlmResponse(ruleId, responseText) {
  return A11yManualLlm.validateResponse(ruleId, responseText);
}
