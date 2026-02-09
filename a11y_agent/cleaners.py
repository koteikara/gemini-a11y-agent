# ==============================================================================
# cleaners.py — HTML前処理・属性削除・レイアウトtable変換・絶対パス化
# ==============================================================================

import re
import requests
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from config import (
    FORBIDDEN_TAGS,
    DROP_ATTRS_BY_TAG,
    IFRAME_ALLOWED_ATTRS,
    FILE_EXTS,
    IFRAME_TITLE_FETCH_CAP_PER_PAGE,
    IFRAME_TITLE_FETCH_TIMEOUT,
    CONVERT_LAYOUT_TABLES_TO_DIV,
)

# ==============================================================================
# モジュール内部定数
# ==============================================================================

# --- style内 px 指定の正規表現 ---
PX_PROP_PAT = re.compile(
    r"(?i)\b("
    r"width|height|min-width|min-height|max-width|max-height"
    r")\s*:\s*\d+(?:\.\d+)?px\s*;?"
)

# --- PDF等の「種別/容量」表記削除用 ---
BR_OPEN = r"[【\[\(（〔<＜]"
BR_CLOSE = r"[】\]\)）〕>＞]"

FILE_WORD = r"(PDF|ＰＤＦ|Word|Excel|PowerPoint|ファイル)"
UNIT_WORD = r"(B|KB|MB|GB|TB|バイト|bytes|キロバイト|メガバイト|ギガバイト|テラバイト)"
NUM_WORD = r"\d+(?:\.\d+)?"

FILEINFO_PATTERNS = [
    re.compile(
        rf"{BR_OPEN}\s*{FILE_WORD}\s*(?:ファイル)?\s*[:：]\s*.*?{NUM_WORD}\s*{UNIT_WORD}\s*.*?{BR_CLOSE}",
        re.IGNORECASE,
    ),
    re.compile(
        rf"{BR_OPEN}\s*(PDF|ＰＤＦ)\s*(?:ファイル)?\s*[:：].*?{BR_CLOSE}",
        re.IGNORECASE,
    ),
]

# --- iframe title補完用 ---
URLISH_TITLE_PAT = re.compile(r"^(https?://|/).+", re.IGNORECASE)

# --- UI的テキストパターン（table判定用） ---
UIISH_TEXT_PAT = re.compile(
    r"(にメールを送る|メールを送る|クリック|詳細|申し込み|申込み|予約|送信|問合せ|問い合わせ)"
)

# --- div に残すべきでない table由来属性 ---
DIV_FORBIDDEN_ATTRS_FROM_TABLE = {
    "scope", "headers", "axis", "abbr", "rowspan", "colspan"
}


# ==============================================================================
# 内部ヘルパー
# ==============================================================================

def _is_file_like_link(a_tag) -> bool:
    """aタグがファイルリンクか判定"""
    try:
        href = (a_tag.get("href") or "").lower()
        if any(href.endswith(ext) for ext in FILE_EXTS):
            return True
        typ = (a_tag.get("type") or "").lower()
        if "pdf" in typ:
            return True
        return False
    except Exception:
        return False


def _is_layout_table(table_tag: Tag) -> bool:
    """tableがレイアウト用か判定"""
    try:
        if table_tag.find("caption") is not None:
            return False
        if table_tag.find("thead") is not None:
            return False

        ths = table_tag.find_all("th")
        scoped_th = [
            th for th in ths
            if (th.get("scope") or "").lower() in ("col", "row")
        ]
        if len(scoped_th) >= 2:
            return False

        if table_tag.find("iframe") is not None:
            return True
        if table_tag.find("img") is not None:
            return True
        if any(_is_file_like_link(a) for a in table_tag.find_all("a")):
            return True

        rows = table_tag.find_all("tr")
        row_count = len(rows)

        ui_nodes = len(
            table_tag.find_all(
                ["a", "img", "br", "iframe", "button", "input", "select"]
            )
        )
        uiish = ui_nodes >= max(2, row_count)

        text_all = table_tag.get_text(" ", strip=True)
        ui_words = bool(UIISH_TEXT_PAT.search(text_all))

        if 1 <= row_count <= 12 and (uiish or ui_words) and len(ths) <= 1:
            return True

        return False
    except Exception:
        return False


def _rename_to_div_and_strip_attrs(t: Tag) -> None:
    """tagをdivにリネームし、table由来の不正属性を除去"""
    try:
        t.name = "div"
    except Exception:
        return
    try:
        for a in list(t.attrs.keys()):
            if a in DIV_FORBIDDEN_ATTRS_FROM_TABLE:
                del t[a]
    except Exception:
        pass


def fetch_title_from_url(src_url: str) -> str:
    """URLからページ<title>を取得（iframe title補完用）"""
    try:
        resp = requests.get(
            src_url,
            timeout=IFRAME_TITLE_FETCH_TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")
        t = soup.find("title")
        title = (t.get_text(" ", strip=True) if t else "").strip()
        title = re.sub(r"\s{2,}", " ", title).strip()
        return title
    except Exception:
        return ""


# ==============================================================================
# 公開関数
# ==============================================================================

def drop_forbidden_tags(html_content: str) -> str:
    """FORBIDDEN_TAGS(graphic等)をunwrap"""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        for t in soup.find_all(list(FORBIDDEN_TAGS)):
            t.unwrap()
        return str(soup)
    except Exception:
        return html_content


def remove_deprecated_and_nonstandard_attrs(html_content: str) -> str:
    """DROP_ATTRS_BY_TAGに基づく非推奨属性削除 + iframeホワイトリスト"""
    try:
        soup = BeautifulSoup(html_content, "html.parser")

        for tag_name, attrs in DROP_ATTRS_BY_TAG.items():
            for t in soup.find_all(tag_name):
                for a in list(attrs):
                    if t.has_attr(a):
                        del t[a]

        # iframe：ホワイトリスト以外を削除（frameborderも確実に落とす）
        for fr in soup.find_all("iframe"):
            for attr in list(fr.attrs.keys()):
                if attr not in IFRAME_ALLOWED_ATTRS:
                    del fr[attr]
            if fr.has_attr("frameborder"):
                del fr["frameborder"]

        return str(soup)
    except Exception:
        return html_content


def strip_px_sizes_from_style_attr(html_content: str) -> str:
    """style属性内の width/height px指定を除去"""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        for t in soup.find_all(True):
            if not t.has_attr("style"):
                continue

            style = str(t.get("style") or "")
            new_style = PX_PROP_PAT.sub("", style)

            new_style = re.sub(r"\s{2,}", " ", new_style)
            new_style = re.sub(r";\s*;", ";", new_style)
            new_style = new_style.strip().strip(";").strip()

            if not new_style:
                del t["style"]
            else:
                t["style"] = new_style
        return str(soup)
    except Exception:
        return html_content


def remove_fileinfo_anywhere_text(html_content: str) -> str:
    """PDF種別/容量表記を括弧種類問わず削除"""
    try:
        soup = BeautifulSoup(html_content, "html.parser")

        # 1) ファイルリンクのリンクテキスト内を優先で削除
        for a in soup.find_all("a"):
            if not _is_file_like_link(a):
                continue
            for node in list(a.descendants):
                if isinstance(node, NavigableString):
                    txt = str(node)
                    new_txt = txt
                    for pat in FILEINFO_PATTERNS:
                        new_txt = pat.sub("", new_txt)
                    new_txt = re.sub(r"\s{2,}", " ", new_txt).strip()
                    if new_txt != txt:
                        node.replace_with(new_txt)

        # 2) ページ全体（ヒットしそうな語がある箇所だけ）
        for node in soup.find_all(string=True):
            if not isinstance(node, NavigableString):
                continue
            txt = str(node)
            if ("PDF" not in txt) and ("ＰＤＦ" not in txt) and ("ファイル" not in txt):
                continue
            new_txt = txt
            for pat in FILEINFO_PATTERNS:
                new_txt = pat.sub("", new_txt)
            if new_txt != txt:
                node.replace_with(new_txt)

        return str(soup)
    except Exception:
        return html_content


def enrich_iframe_titles(html_content: str, base_url: str = "") -> str:
    """iframe titleをsrc先<title>で補完"""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        iframes = soup.find_all("iframe")
        if not iframes:
            return str(soup)

        cache = {}
        fetched = 0

        for fr in iframes:
            raw_src = (fr.get("src") or "").strip()
            if not raw_src:
                continue

            src = urljoin(base_url, raw_src) if base_url else raw_src
            cur_title = (fr.get("title") or "").strip()

            need = False
            if not cur_title:
                need = True
            elif URLISH_TITLE_PAT.match(cur_title):
                need = True
            elif cur_title.lower() == raw_src.lower():
                need = True
            elif cur_title.lower() == src.lower():
                need = True

            if not need:
                continue

            if fetched >= IFRAME_TITLE_FETCH_CAP_PER_PAGE and src not in cache:
                continue

            if src in cache:
                new_title = cache[src]
            else:
                new_title = fetch_title_from_url(src)
                cache[src] = new_title
                fetched += 1

            if new_title:
                fr["title"] = new_title

        return str(soup)
    except Exception:
        return html_content


def convert_layout_tables_to_div_preserve_dom(html_content: str):
    """
    レイアウトと判定したtableをdivにリネーム（DOM保持）。

    Returns:
        (html, tables_before, tables_after, converted_count)
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        tables = soup.find_all("table")
        tables_before = len(tables)
        if not tables:
            return str(soup), tables_before, tables_before, 0

        converted = 0
        for tbl in list(soup.find_all("table")):
            if not _is_layout_table(tbl):
                continue

            for sub in tbl.find_all(
                ["tbody", "thead", "tfoot", "tr", "td", "th"], recursive=True
            ):
                if isinstance(sub, Tag):
                    _rename_to_div_and_strip_attrs(sub)

            _rename_to_div_and_strip_attrs(tbl)

            existing_class = tbl.get("class") or []
            if isinstance(existing_class, str):
                existing_class = [existing_class]
            if "layout-table" not in existing_class:
                existing_class = list(existing_class) + ["layout-table"]
            tbl["class"] = existing_class

            converted += 1

        tables_after = len(soup.find_all("table"))
        return str(soup), tables_before, tables_after, converted
    except Exception:
        return html_content, 0, 0, 0


def chunk_has_data_table_like(html_chunk: str) -> bool:
    """チャンク内にデータ寄りtableがあればTrue（LLM修正対象判定）"""
    try:
        soup = BeautifulSoup(html_chunk, "html.parser")
        tables = soup.find_all("table")
        if not tables:
            return False

        for t in tables:
            has_caption = t.find("caption") is not None
            has_thead = t.find("thead") is not None

            ths = t.find_all("th")
            th_with_scope = [
                th for th in ths
                if (th.get("scope") or "").lower() in ("col", "row")
            ]

            rows = t.find_all("tr")
            row_count = len(rows)

            link_img_br = len(t.find_all(["a", "img", "br", "iframe"]))
            uiish = link_img_br >= max(3, row_count)

            text_all = t.get_text(" ", strip=True)
            ui_words = bool(UIISH_TEXT_PAT.search(text_all))

            if has_caption:
                return True
            if has_thead and len(th_with_scope) >= 1:
                return True
            if len(ths) >= 2 and row_count >= 3 and not uiish:
                return True

            if (
                (not has_caption)
                and (not has_thead)
                and (len(ths) <= 1)
                and (1 <= row_count <= 10)
                and (uiish or ui_words)
            ):
                continue

        return False
    except Exception:
        return False


def absolutize_paths(html_content: str, base_url: str) -> str:
    """img src / a href / iframe src を絶対URLに変換"""
    soup = BeautifulSoup(html_content, "html.parser")
    for tag in soup.find_all(["img", "a", "iframe"]):
        if tag.name == "img":
            attr = "src"
        elif tag.name == "a":
            attr = "href"
        else:
            attr = "src"
        if tag.get(attr):
            tag[attr] = urljoin(base_url, tag[attr])
    return str(soup)


def pre_clean(
    html: str,
    base_url: str,
    do_layout_table_convert: bool = True,
) -> tuple:
    """
    前処理の統合パイプライン。

    内部で呼ぶ順序:
        1. drop_forbidden_tags
        2. remove_deprecated_and_nonstandard_attrs
        3. strip_px_sizes_from_style_attr
        4. remove_fileinfo_anywhere_text
        5. enrich_iframe_titles
        6. convert_layout_tables_to_div（フラグ依存）

    Returns:
        (cleaned_html, meta_dict)
    """
    meta = {
        "tables_before": 0,
        "tables_after": 0,
        "layout_converted": 0,
    }

    h = html
    h = drop_forbidden_tags(h)
    h = remove_deprecated_and_nonstandard_attrs(h)
    h = strip_px_sizes_from_style_attr(h)
    h = remove_fileinfo_anywhere_text(h)
    h = enrich_iframe_titles(h, base_url=base_url)

    if do_layout_table_convert and CONVERT_LAYOUT_TABLES_TO_DIV:
        try:
            meta["tables_before"] = len(
                BeautifulSoup(h, "html.parser").find_all("table")
            )
        except Exception:
            meta["tables_before"] = 0

        if meta["tables_before"] > 0:
            h2, tb, ta, conv = convert_layout_tables_to_div_preserve_dom(h)
            h = h2
            meta["tables_after"] = ta
            meta["layout_converted"] = conv

    return h, meta
