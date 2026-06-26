import csv
from pathlib import Path

from tools.audit_output_html_quality import audit_file, main


def write_html(tmp_path: Path, body: str, name: str = "sample.html") -> Path:
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return path


def rule_ids(issues):
    return {issue.rule_id for issue in issues}


def severities(issues, rule_id):
    return {issue.severity for issue in issues if issue.rule_id == rule_id}


def test_pseudo_table_tags_are_critical(tmp_path):
    path = write_html(tmp_path, "<html><body><row><cell>broken</cell></row></body></html>")
    issues, _, _ = audit_file(path, tmp_path)
    assert "OUT-TABLE-001" in rule_ids(issues)
    assert "Critical" in severities(issues, "OUT-TABLE-001")


def test_cms_control_strings_are_high(tmp_path):
    path = write_html(tmp_path, "<html><body>EndClear ParentBack</body></html>")
    issues, _, _ = audit_file(path, tmp_path)
    assert "OUT-CMS-001" in rule_ids(issues)
    assert "High" in severities(issues, "OUT-CMS-001")


def test_non_body_elements_are_high(tmp_path):
    path = write_html(tmp_path, "<html><body>本文へスキップ このサイトではJavaScriptを使用しています</body></html>")
    issues, _, _ = audit_file(path, tmp_path)
    assert "OUT-EXTRACT-001" in rule_ids(issues)
    assert "High" in severities(issues, "OUT-EXTRACT-001")


def test_mojibake_is_high(tmp_path):
    path = write_html(tmp_path, "<html><body>���</body></html>")
    issues, _, _ = audit_file(path, tmp_path)
    assert "OUT-ENC-001" in rule_ids(issues)
    assert "High" in severities(issues, "OUT-ENC-001")


def test_ambiguous_link_text_is_medium(tmp_path):
    path = write_html(tmp_path, '<html><body><a href="/x">こちら</a></body></html>')
    issues, _, _ = audit_file(path, tmp_path)
    assert "OUT-LINK-001" in rule_ids(issues)
    assert "Medium" in severities(issues, "OUT-LINK-001")


def test_long_icon_alt_is_medium(tmp_path):
    path = write_html(tmp_path, '<html><body><img src="/img/pdf_icon.png" alt="PDFファイルを新しいウィンドウで開くためのアイコンです"></body></html>')
    issues, _, _ = audit_file(path, tmp_path)
    assert "OUT-ALT-001" in rule_ids(issues)
    assert "Medium" in severities(issues, "OUT-ALT-001")


def test_valid_table_has_no_critical(tmp_path):
    path = write_html(
        tmp_path,
        '<table><caption>休日当番医一覧</caption><thead><tr><th scope="col">日付</th><th scope="col">医療機関</th></tr></thead><tbody><tr><th scope="row">1日</th><td>A医院</td></tr></tbody></table>',
    )
    issues, metric, _ = audit_file(path, tmp_path)
    assert metric.table_count == 1
    assert not [issue for issue in issues if issue.severity == "Critical"]


def test_markdown_and_csv_reports_are_generated(tmp_path):
    input_dir = tmp_path / "html"
    input_dir.mkdir()
    write_html(input_dir, '<html><body><a href="/x">こちら</a></body></html>')
    md = tmp_path / "report.md"
    csv_path = tmp_path / "report.csv"

    assert main(["--input-dir", str(input_dir), "--output-md", str(md), "--output-csv", str(csv_path), "--no-fail"]) == 0
    assert "## Summary" in md.read_text(encoding="utf-8")
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))
    assert rows[0]["rule_id"] == "OUT-LINK-001"
