import unittest
from lxml import html as lxml_html

from a11y_agent.cleaners import fix_data_table_headers


class TableHeaderOrientationTest(unittest.TestCase):
    def _first_table(self, html_text):
        root = lxml_html.fromstring(f"<div>{html_text}</div>")
        return root.xpath(".//table")[0]

    def test_orient_col_adds_th_scope_col_without_text_change(self):
        src = """
        <table>
          <tr><td>診療科</td><td>医療機関名</td><td>電話</td><td>所在地</td><td>特定健診</td></tr>
          <tr><td>内科</td><td>中央病院&nbsp;本院</td><td>0952-00-0000</td><td>佐賀市\n本庄町</td><td>○</td></tr>
          <tr><td>外科</td><td>北病院</td><td>0952-11-1111</td><td>佐賀市駅前</td><td>×</td></tr>
        </table>
        """
        out, meta = fix_data_table_headers(src, log=False)
        table = self._first_table(out)

        head_cells = table.xpath("./tr[1]/*")
        self.assertTrue(all(c.tag.lower() == "th" for c in head_cells))
        self.assertTrue(all((c.get("scope") or "") == "col" for c in head_cells))
        # Text content must remain unchanged (including nbsp/newline semantics)
        second_row_second = table.xpath("./tr[2]/*[2]")[0]
        self.assertIn("中央病院", "".join(second_row_second.itertext()))
        self.assertGreaterEqual(meta.get("orient_col_fixed_count", 0), 5)

    def test_orient_row_adds_th_scope_row(self):
        src = """
        <table>
          <tr><td>曜日</td><td>月</td><td>火</td></tr>
          <tr><td>受付</td><td>9:00-12:00</td><td>9:00-12:00</td></tr>
          <tr><td>診療</td><td>13:00-17:00</td><td>13:00-17:00</td></tr>
        </table>
        """
        out, meta = fix_data_table_headers(src, log=False)
        table = self._first_table(out)
        first_col = table.xpath("./tr/*[1]")
        self.assertTrue(all(c.tag.lower() == "th" for c in first_col))
        self.assertTrue(all((c.get("scope") or "") == "row" for c in first_col))
        self.assertGreaterEqual(meta.get("orient_row_fixed_count", 0), 3)

    def test_orient_none_keeps_table_unchanged_for_blank_heavy(self):
        src = """
        <table>
          <tr><td>&nbsp;</td><td>&nbsp;</td></tr>
          <tr><td>&nbsp;</td><td>2025/01/01</td></tr>
        </table>
        """
        out, meta = fix_data_table_headers(src, log=False)
        table = self._first_table(out)
        self.assertEqual(len(table.xpath(".//th")), 0)
        self.assertEqual(meta.get("orient_col_fixed_count", 0), 0)
        self.assertEqual(meta.get("orient_row_fixed_count", 0), 0)


if __name__ == "__main__":
    unittest.main()
