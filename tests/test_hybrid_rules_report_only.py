import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from a11y_agent.hybrid_rules import detect_hybrid_candidates


class HybridRulesReportOnlyTest(unittest.TestCase):
    def _detect(self, html_text, *, base_url="https://example.jp/current.html"):
        before = html_text
        candidates = detect_hybrid_candidates(html_text, base_url=base_url)
        self.assertEqual(html_text, before)
        self.assertTrue(all(c.get("auto_fix") is False for c in candidates))
        return candidates

    def _find_rule(self, candidates, rule_id):
        matches = [c for c in candidates if c.get("rule_id") == rule_id]
        self.assertTrue(matches, f"missing candidate for {rule_id}: {candidates!r}")
        return matches[0]

    def test_html_r15_caption_missing(self):
        candidates = self._detect("""
        <table>
          <tr><td>項目</td><td>内容</td></tr>
        </table>
        """)
        candidate = self._find_rule(candidates, "HTML-R-15")
        self.assertEqual(candidate.get("detect_id"), "DET-R15-CAPTION")
        self.assertIs(candidate.get("auto_fix"), False)

    def test_html_r16_rowspan_colspan(self):
        candidates = self._detect("""
        <table>
          <tr><td rowspan="2">区分</td><td>内容</td></tr>
          <tr><td>詳細</td></tr>
        </table>
        """)
        candidate = self._find_rule(candidates, "HTML-R-16")
        self.assertIs(candidate.get("auto_fix"), False)

    def test_link_r02_vague_link_text(self):
        candidates = self._detect('<p>申請方法は<a href="/apply.html">こちら</a>をご確認ください。</p>')
        candidate = self._find_rule(candidates, "LINK-R-02")
        self.assertEqual(candidate.get("href"), "/apply.html")
        self.assertEqual(candidate.get("anchor_text"), "こちら")
        self.assertIs(candidate.get("auto_fix"), False)

    def test_link_r04_mailto(self):
        candidates = self._detect('<p>問い合わせ: <a href="mailto:test@example.jp">test@example.jp</a></p>')
        candidate = self._find_rule(candidates, "LINK-R-04")
        self.assertEqual(candidate.get("email"), "test@example.jp")
        self.assertIs(candidate.get("auto_fix"), False)

    def test_link_r09_in_page_anchor(self):
        candidates = self._detect('<a href="#section1">本文へ移動</a><h2 id="section1">本文</h2>')
        candidate = self._find_rule(candidates, "LINK-R-09")
        self.assertIs(candidate.get("target_exists"), True)
        self.assertIs(candidate.get("auto_fix"), False)

    def test_link_r08_cross_page_fragment(self):
        candidates = self._detect('<a href="/other.html#section2">別ページの該当箇所</a>')
        candidate = self._find_rule(candidates, "LINK-R-08")
        self.assertEqual(candidate.get("fragment"), "section2")
        self.assertIs(candidate.get("auto_fix"), False)

    def test_img_r05_linked_image(self):
        candidates = self._detect('<a href="/detail.html"><img src="/thumb.jpg" alt="施設外観"></a>')
        candidate = self._find_rule(candidates, "IMG-R-05")
        self.assertEqual(candidate.get("img_src"), "/thumb.jpg")
        self.assertEqual(candidate.get("href"), "/detail.html")
        self.assertEqual(candidate.get("alt"), "施設外観")
        self.assertIs(candidate.get("auto_fix"), False)

    def test_img_r09_zoom_image_link(self):
        candidates = self._detect('<a href="/large.jpg"><img src="/thumb.jpg" alt="施設外観"></a>')
        candidate = self._find_rule(candidates, "IMG-R-09")
        self.assertEqual(candidate.get("full_image_href"), "/large.jpg")
        self.assertEqual(candidate.get("thumbnail_src"), "/thumb.jpg")
        self.assertIs(candidate.get("auto_fix"), False)

    def test_detection_exceptions_do_not_stop_processing(self):
        bad_rules = [{"id": "HTML-R-15"}, {"id": "HTML-R-15"}]
        with self.assertLogs("a11y_agent.hybrid_rules", level="WARNING"):
            candidates = detect_hybrid_candidates("<table></table>", rules=bad_rules)
        self.assertEqual(candidates, [])


if __name__ == "__main__":
    unittest.main()
