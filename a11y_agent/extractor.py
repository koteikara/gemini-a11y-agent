# ==============================================================================
# extractor.py — URL取得・本文抽出（XPath優先）
# ==============================================================================

import requests
from lxml import html as lxml_html
import trafilatura
import logging


logger = logging.getLogger(__name__)


VISIBLE_BLOCK_TAGS = {
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "div", "section", "article", "main",
    "ul", "ol", "li", "dl", "dt", "dd",
    "blockquote", "pre", "table",
}
SKIP_TAGS = {"script", "style", "noscript", "template"}


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


def _rebuild_inner_html_dom_order(root) -> str:
    """root配下をDOM順に再連結したinnerHTMLを返す。"""
    parts = []
    if root.text:
        parts.append(root.text)
    for child in list(root):
        if not isinstance(getattr(child, "tag", None), str):
            continue
        if (child.tag or "").lower() in SKIP_TAGS:
            continue
        parts.append(lxml_html.tostring(child, encoding="unicode", method="html"))
    return "".join(parts)


def _is_table_only_root(root) -> bool:
    """可視ブロック要素がtable以外に存在しなければtable-only。"""
    for node in root.iterdescendants():
        tag = (getattr(node, "tag", "") or "").lower()
        if not tag or tag in SKIP_TAGS:
            continue
        if tag not in VISIBLE_BLOCK_TAGS:
            continue
        if tag != "table":
            text = (node.text_content() or "").strip()
            if text or tag.startswith("h"):
                return False
    return True


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
                    dom_order_inner = _rebuild_inner_html_dom_order(root)
                    if dom_order_inner:
                        table_only = _is_table_only_root(root)
                        starts_with_table = dom_order_inner.lstrip().lower().startswith("<table")
                        if starts_with_table and not table_only:
                            xp = dom_order_inner
                        else:
                            xp = dom_order_inner
                        logger.debug(
                            "xpath_root_table_only=%s starts_with_table=%s",
                            table_only,
                            starts_with_table,
                        )
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
