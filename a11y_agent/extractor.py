# ==============================================================================
# extractor.py — URL取得・本文抽出（XPath優先）
# ==============================================================================

import requests
from lxml import html as lxml_html
import trafilatura
import logging


logger = logging.getLogger(__name__)


def _inner_html(el) -> str:
    """lxml要素のinnerHTMLを返す（先頭/末尾テキストを保持）。"""
    try:
        parts = []
        if el.text:
            parts.append(el.text)
        for child in el:
            parts.append(
                lxml_html.tostring(child, encoding="unicode", method="html")
            )
        return "".join(parts)
    except Exception:
        return ""


def extract_by_xpath(full_html: str, xpath: str):
    """
    lxmlでXPath抽出。成功時はHTML文字列、失敗時はNone。
    """
    try:
        if not xpath:
            return None
        tree = lxml_html.fromstring(full_html)
        els = tree.xpath(xpath)
        if els:
            first = els[0]
            if hasattr(first, "tag"):
                inner = _inner_html(first)
                return inner or lxml_html.tostring(
                    first,
                    encoding="unicode",
                    method="html",
                )
            return str(first)
    except Exception:
        return None
    return None


def robust_extract_xpath_first(url: str, xpath: str):
    """
    XPath優先の堅牢抽出。

    Returns:
        (extracted_html, (method, method_detail), full_html)
        method: "xpath" | "trafilatura" | "full"
    """
    resp = requests.get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0"})
    resp.encoding = resp.apparent_encoding
    full_html = resp.text

    xp = extract_by_xpath(full_html, xpath)

    if xp:
        logger.debug("extracted_html_head=%s", xp[:400].replace("\n", "\\n"))

    # XPathが本文コンテナを指している場合はroot配下本文全体（innerHTML）を厳密に採用
    try:
        if xpath:
            tree = lxml_html.fromstring(full_html)
            roots = tree.xpath(xpath)
            if roots:
                root = roots[0]
                if hasattr(root, "xpath"):
                    root_inner = _inner_html(root)
                    if root_inner:
                        root_children_tags = [
                            (getattr(c, "tag", "") or "").lower()
                            for c in list(root)
                            if isinstance(getattr(c, "tag", None), str)
                        ]
                        logger.debug(
                            "xpath_root_children_head=%s",
                            root_children_tags[:20],
                        )
                        root_children = [
                            c
                            for c in list(root)
                            if isinstance(getattr(c, "tag", None), str)
                        ]
                        has_non_table_root_child = any(
                            (c.tag or "").lower() != "table" for c in root_children
                        )
                        starts_with_table = root_inner.lstrip().lower().startswith("<table")
                        if starts_with_table and has_non_table_root_child:
                            # root直下のDOM順連結で、先頭テキスト/要素の欠落を防ぐ
                            ordered_parts = []
                            if root.text:
                                ordered_parts.append(root.text)
                            for c in list(root):
                                ordered_parts.append(
                                    lxml_html.tostring(c, encoding="unicode", method="html")
                                )
                            xp = "".join(ordered_parts)
                        else:
                            xp = root_inner
                        logger.debug("extracted_html_head=%s", xp[:400].replace("\n", "\\n"))
    except Exception:
        pass

    if xp and len(xp) > 200:
        return xp, ("xpath", xpath), full_html

    try:
        extracted = trafilatura.extract(
            full_html,
            include_links=True,
            include_images=True,
            include_tables=True,
            output_format="html",
        )
        if extracted and len(extracted) > 200:
            return extracted, ("trafilatura", "trafilatura"), full_html
    except Exception:
        pass

    return full_html, ("full", "full_html"), full_html
