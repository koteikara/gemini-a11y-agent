from a11y_agent.table_response_validator import (
    detect_unsafe_table_output,
    parse_single_table_response,
)


def test_rejects_pseudo_row_cell_llm_output():
    original = "<table><tr><td>工事名称</td></tr></table>"
    unsafe = "<table><row><cell>工事名称</cell></row></table>"

    table_html, detail = parse_single_table_response(unsafe)

    assert table_html is None
    assert detail["unsafe_reason"] == "pseudo_row_cell_tags_found"
    assert parse_single_table_response(original)[0] is not None


def test_rejects_broken_escaped_closing_fragment():
    unsafe = "<table>&lt;/</row></table>"

    table_html, detail = parse_single_table_response(unsafe)

    assert table_html is None
    assert detail["unsafe_reason"] == "broken_escaped_closing_fragment_found"
    assert detect_unsafe_table_output("<table>&lt;/</td></table>") == "broken_escaped_closing_fragment_found"


def test_accepts_valid_tr_td_table():
    safe = """
    <table>
      <caption>入札結果一覧</caption>
      <thead><tr><th scope="col">工事名称</th></tr></thead>
      <tbody><tr><td>道路改良工事</td></tr></tbody>
    </table>
    """

    table_html, detail = parse_single_table_response(safe)

    assert table_html is not None
    assert detail["unsafe_reason"] == ""
    assert "<tr>" in table_html
    assert "<td>道路改良工事</td>" in table_html


def test_rejects_tr_td_th_outside_table():
    unsafe = "<table><tr><td>工事名称</td></tr></table><tr><td>外側</td></tr>"

    table_html, detail = parse_single_table_response(unsafe)

    assert table_html is None
    assert detail["unsafe_reason"] == "table_row_or_cell_outside_table"
    assert "tr" in detail["stray_table_cell_tags"]
