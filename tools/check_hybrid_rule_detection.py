#!/usr/bin/env python3
"""Smoke-check report-only hybrid a11y candidate detection."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from a11y_agent.hybrid_rules import detect_hybrid_candidates  # noqa: E402

EXPECTED_RULE_IDS = [
    "HTML-R-15",
    "HTML-R-16",
    "LINK-R-02",
    "LINK-R-04",
    "LINK-R-08",
    "LINK-R-09",
    "IMG-R-05",
    "IMG-R-09",
]

SAMPLE_HTML = """
<table>
  <tr><td rowspan="2">区分</td><td>内容</td></tr>
  <tr><td>詳細</td></tr>
</table>
<p>申請方法は<a href="/apply.html">こちら</a>をご確認ください。</p>
<p>問い合わせ: <a href="mailto:test@example.jp">test@example.jp</a></p>
<a href="#section1">本文へ移動</a>
<h2 id="section1">本文</h2>
<a href="/other.html#section2">別ページの該当箇所</a>
<a href="/detail.html"><img src="/thumb.jpg" alt="施設外観"></a>
<a href="/large.jpg"><img src="/thumb.jpg" alt="施設外観"></a>
"""


def main() -> int:
    before = SAMPLE_HTML
    candidates = detect_hybrid_candidates(SAMPLE_HTML, base_url="https://example.jp/current.html")
    detected = sorted({str(c.get("rule_id")) for c in candidates})
    missing = [rid for rid in EXPECTED_RULE_IDS if rid not in detected]
    auto_fix_enabled = [c for c in candidates if c.get("auto_fix") is not False]

    if SAMPLE_HTML != before or missing or auto_fix_enabled:
        print("status: FAIL")
        if SAMPLE_HTML != before:
            print("error: HTML input was modified")
        if missing:
            print("missing:")
            for rid in missing:
                print(f"- {rid}")
        if auto_fix_enabled:
            print(f"error: candidates with auto_fix enabled: {len(auto_fix_enabled)}")
        return 1

    print("status: PASS")
    print("detected:")
    for rid in EXPECTED_RULE_IDS:
        print(f"- {rid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
