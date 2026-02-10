import unittest

from a11y_agent.table_response_validator import (
    format_table_response_detail,
    parse_single_table_response,
)


class TableResponseValidatorTest(unittest.TestCase):
    def test_accepts_html_body_wrapped_single_table(self):
        src = """
        <html><body>
          <table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>
        </body></html>
        """
        table_html, detail = parse_single_table_response(src)
        self.assertIsNotNone(table_html)
        self.assertEqual(detail["tables_found"], 1)
        self.assertFalse(detail["has_non_table_elements"])
        self.assertEqual(detail["non_table_text_len"], 0)
        self.assertTrue(detail["table_shape_ok"])

    def test_rejects_visible_non_table_elements(self):
        src = """
        <html><body>
          <p>注記</p>
          <table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>
        </body></html>
        """
        table_html, detail = parse_single_table_response(src)
        self.assertIsNone(table_html)
        self.assertTrue(detail["has_non_table_elements"])
        self.assertIn("p", detail["non_table_tags_sample"])

    def test_rejects_multiple_tables(self):
        src = """
        <table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>
        <table><tr><th>C</th><th>D</th></tr><tr><td>3</td><td>4</td></tr></table>
        """
        table_html, detail = parse_single_table_response(src)
        self.assertIsNone(table_html)
        self.assertEqual(detail["tables_found"], 2)

    def test_rejects_table_shape_breakage(self):
        src = "<table><tr><td>単一セル</td></tr></table>"
        table_html, detail = parse_single_table_response(src)
        self.assertIsNone(table_html)
        self.assertFalse(detail["table_shape_ok"])

    def test_detail_formatter_includes_requested_fields(self):
        _, detail = parse_single_table_response("<div>oops</div>")
        msg = format_table_response_detail(detail)
        self.assertIn("parse_ok=Y", msg)
        self.assertIn("tables_found=0", msg)
        self.assertIn("non_table_tags_sample", msg)
        self.assertIn("raw_head=", msg)


if __name__ == "__main__":
    unittest.main()
