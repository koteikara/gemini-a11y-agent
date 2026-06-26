from collections import Counter
from html.parser import HTMLParser
import re
from typing import Dict, Optional, Tuple


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

UNSAFE_TABLE_OUTPUT_PATTERNS = (
    (
        re.compile(
            r"&lt;\s*/\s*</\s*(row|cell|tr|td|th|table)(?=[\s>/])",
            re.IGNORECASE,
        ),
        "broken_escaped_closing_fragment_found",
    ),
    (
        re.compile(r"<\s*/?\s*(row|cell)(?=[\s>/])", re.IGNORECASE),
        "pseudo_row_cell_tags_found",
    ),
)


def detect_unsafe_table_output(resp_html: str) -> Optional[str]:
    """Return a short rejection reason when LLM table HTML is unsafe."""
    text = resp_html or ""
    for pattern, reason in UNSAFE_TABLE_OUTPUT_PATTERNS:
        if pattern.search(text):
            return reason
    return None


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def _attrs_to_html(attrs) -> str:
    rendered = []
    for key, value in attrs:
        if value is None:
            rendered.append(key)
        else:
            escaped = str(value).replace("&", "&amp;").replace('"', "&quot;")
            rendered.append(f'{key}="{escaped}"')
    return (" " + " ".join(rendered)) if rendered else ""


class _TableSafetyParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.tables_found = 0
        self.table_depth = 0
        self.disallowed_outside_tags = []
        self.stray_table_cell_tags = []
        self.outside_text_parts = []
        self.table_parts = []
        self.table_row_count = 0
        self.first_row_cell_count = 0
        self._current_row_cell_count = 0
        self._seen_first_row = False

    def _in_table(self) -> bool:
        return self.table_depth > 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "table":
            self.tables_found += 1
            self.table_depth += 1
        elif not self._in_table():
            if tag in {"tr", "td", "th"}:
                self.stray_table_cell_tags.append(tag)
            elif tag not in _ALLOWED_NON_VISIBLE_OUTSIDE_TABLE:
                self.disallowed_outside_tags.append(tag)

        if self._in_table():
            self.table_parts.append(f"<{tag}{_attrs_to_html(attrs)}>")
            if tag == "tr":
                self.table_row_count += 1
                self._current_row_cell_count = 0
            elif tag in {"td", "th"} and self.table_row_count == 1:
                self._current_row_cell_count += 1

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self._in_table():
            self.table_parts.append(f"</{tag}>")
            if tag == "tr" and not self._seen_first_row:
                self.first_row_cell_count = self._current_row_cell_count
                self._seen_first_row = True
        elif tag in {"tr", "td", "th"}:
            self.stray_table_cell_tags.append(tag)

        if tag == "table" and self.table_depth > 0:
            self.table_depth -= 1

    def handle_startendtag(self, tag, attrs):
        tag = tag.lower()
        if self._in_table():
            self.table_parts.append(f"<{tag}{_attrs_to_html(attrs)} />")
        elif tag not in _ALLOWED_NON_VISIBLE_OUTSIDE_TABLE:
            self.disallowed_outside_tags.append(tag)

    def handle_data(self, data):
        if self._in_table():
            self.table_parts.append(data)
        else:
            self.outside_text_parts.append(data)

    def handle_entityref(self, name):
        self.handle_data(f"&{name};")

    def handle_charref(self, name):
        self.handle_data(f"&#{name};")


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
        "unsafe_reason": "",
        "stray_table_cell_tags": [],
    }

    unsafe_reason = detect_unsafe_table_output(resp_html or "")
    if unsafe_reason:
        detail["unsafe_reason"] = unsafe_reason
        return None, detail

    try:
        parser = _TableSafetyParser()
        parser.feed(resp_html or "")
        parser.close()
        detail["parse_ok"] = True
        detail["tables_found"] = parser.tables_found
        detail["has_non_table_elements"] = bool(parser.disallowed_outside_tags)
        detail["non_table_tags_sample"] = [
            tag for tag, _ in Counter(parser.disallowed_outside_tags).most_common(5)
        ]
        detail["non_table_text_len"] = len(_normalize_space("".join(parser.outside_text_parts)))
        detail["table_shape_ok"] = parser.table_row_count >= 1 and parser.first_row_cell_count >= 1
        detail["stray_table_cell_tags"] = sorted(set(parser.stray_table_cell_tags))

        if parser.tables_found != 1:
            return None, detail
        if detail["stray_table_cell_tags"]:
            detail["unsafe_reason"] = "table_row_or_cell_outside_table"
            return None, detail
        if detail["has_non_table_elements"] or detail["non_table_text_len"] > 0:
            return None, detail
        if not detail["table_shape_ok"]:
            return None, detail

        return "".join(parser.table_parts), detail
    except Exception:
        return None, detail


def format_table_response_detail(detail: Dict[str, object]) -> str:
    """ログ用に検証内訳を短く整形。"""
    return (
        "parse_ok={} tables_found={} has_non_table_elements={} "
        "non_table_tags_sample={} non_table_text_len={} table_shape_ok={} "
        "unsafe_reason={} stray_table_cell_tags={} raw_head={!r}"
    ).format(
        "Y" if detail.get("parse_ok") else "N",
        detail.get("tables_found", 0),
        "Y" if detail.get("has_non_table_elements") else "N",
        detail.get("non_table_tags_sample", []),
        detail.get("non_table_text_len", 0),
        "Y" if detail.get("table_shape_ok") else "N",
        detail.get("unsafe_reason", ""),
        detail.get("stray_table_cell_tags", []),
        detail.get("raw_head", ""),
    )
