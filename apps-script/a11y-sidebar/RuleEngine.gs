/**
 * Server-side helpers kept intentionally small. The MVP rule execution runs in
 * Sidebar.html so pasted HTML is not sent outside the spreadsheet project.
 */
function getA11ySidebarMetadata() {
  return {
    source: 'a11y_agent/rules/a11y_hybrid_detect_fix.jsonl',
    ruleCount: A11Y_SIDEBAR_RULES.length,
    modes: ['LLMなし', '手動LLM連携', 'API自動連携（任意・未設定）']
  };
}

function normalizeA11ySidebarRulesForClient() {
  return A11Y_SIDEBAR_RULES.map(function(rule, index) {
    var copy = Object.assign({}, rule);
    copy.order = index + 1;
    copy.status = '未実行';
    copy.enabled = rule.defaultEnabled;
    return copy;
  });
}
