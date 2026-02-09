# ==============================================================================
# extractor.py — URL取得・本文抽出（XPath優先）
# ==============================================================================

import requests
from lxml import html as lxml_html
import trafilatura


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
            return lxml_html.tostring(els[0], encoding="unicode", method="html")
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
