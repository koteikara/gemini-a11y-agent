from collections import Counter
import re
from typing import Dict, Optional, Tuple

from lxml import html as lxml_html


_ALLOWED_NON_VISIBLE_OUTSIDE_TABLE = {
    "html",
    "head",
    "body",
    "meta",
    "title",
    "link",
    "style",
    "script",
    "noscript",
}


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def _is_descendant_of(node, ancestor) -> bool:
    p = node
    while p is not None:
        if p is ancestor:
            return True
        p = p.getparent()
    return False


def _validate_table_shape(table_el) -> bool:
    rows = table_el.xpath(".//tr")
    if len(rows) < 1:
        return False
    first_cells = rows[0].xpath("./th|./td")
    return len(first_cells) >= 2


def parse_single_table_response(resp_html: str) -> Tuple[Optional[str], Dict[str, object]]:
    """LLMのtable返却を安全に検証し、採用可能ならtable outerHTMLを返す。"""
    detail: Dict[str, object] = {
        "parse_ok": False,
        "tables_found": 0,
        "has_non_table_elements": False,
        "non_table_tags_sample": [],
        "non_table_text_len": 0,
        "raw_head": (resp_html or "")[:200],
        "table_shape_ok": False,
    }

    try:
        wrapped = f"<div data-llm-table-root='1'>{resp_html or ''}</div>"
        root = lxml_html.fromstring(wrapped)
        detail["parse_ok"] = True
        tables = root.xpath(".//table")
        detail["tables_found"] = len(tables)
        if len(tables) != 1:
            return None, detail

        table_el = tables[0]

        # table外の可視タグ混入を検知（html/body等のラッパーやscript/styleは許可）。
        outside_tags = []
        for el in root.xpath(".//*"):
            if not isinstance(el.tag, str):
                continue
            tag = el.tag.lower()
            if tag == "div" and el.get("data-llm-table-root") == "1":
                continue
            if _is_descendant_of(el, table_el):
                continue
            if tag in _ALLOWED_NON_VISIBLE_OUTSIDE_TABLE:
                continue
            outside_tags.append(tag)

        detail["has_non_table_elements"] = bool(outside_tags)
        detail["non_table_tags_sample"] = [
            tag for tag, _ in Counter(outside_tags).most_common(5)
        ]

        text_nodes = root.xpath(
            "//text()["
            "not(ancestor::table) and "
            "not(ancestor::script) and "
            "not(ancestor::style) and "
            "not(ancestor::noscript) and "
            "not(ancestor::head) and "
            "not(ancestor::title)]"
        )
        outside_text = _normalize_space("".join(text_nodes))
        detail["non_table_text_len"] = len(outside_text)

        detail["table_shape_ok"] = _validate_table_shape(table_el)

        if detail["has_non_table_elements"] or detail["non_table_text_len"] > 0:
            return None, detail
        if not detail["table_shape_ok"]:
            return None, detail

        return lxml_html.tostring(table_el, encoding="unicode"), detail
    except Exception:
        return None, detail


def format_table_response_detail(detail: Dict[str, object]) -> str:
    """ログ用に検証内訳を短く整形。"""
    return (
        "parse_ok={} tables_found={} has_non_table_elements={} "
        "non_table_tags_sample={} non_table_text_len={} table_shape_ok={} raw_head={!r}"
    ).format(
        "Y" if detail.get("parse_ok") else "N",
        detail.get("tables_found", 0),
        "Y" if detail.get("has_non_table_elements") else "N",
        detail.get("non_table_tags_sample", []),
        detail.get("non_table_text_len", 0),
        "Y" if detail.get("table_shape_ok") else "N",
        detail.get("raw_head", ""),
    )
