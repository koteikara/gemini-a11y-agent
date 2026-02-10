# ==============================================================================
# chunker.py — 構造ベースチャンク分割
# ==============================================================================

from bs4 import BeautifulSoup
import logging
import re
from bs4.element import NavigableString, Tag

from .cleaners import chunk_has_data_table_like, PROTECT_TABLE_INTRO_KEYWORDS

logger = logging.getLogger(__name__)


UPDATE_LINE_PAT = re.compile(r"^更新：\d{4}年\d{2}月\s*\d{1,2}日$")


TEXT_LIKE_TAGS = {
    "p",
    "ul",
    "ol",
    "li",
    "div",
    "section",
    "article",
    "span",
    "dl",
    "dt",
    "dd",
    "blockquote",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
}


def _is_data_table_block(node) -> bool:
    """ノードがデータテーブルを含むか（既存判定を流用）。"""
    try:
        if not isinstance(node, Tag):
            return False
        if node.name == "table":
            return chunk_has_data_table_like(str(node))
        if node.find("table") is None:
            return False
        return chunk_has_data_table_like(str(node))
    except Exception:
        return False


def _is_intro_text_block(node) -> bool:
    """テーブル導入文候補になりうるテキスト系ブロックか判定。"""
    try:
        if isinstance(node, NavigableString):
            return bool(str(node).strip())
        if not isinstance(node, Tag):
            return False
        if node.name in {"script", "style", "noscript", "table"}:
            return False
        if node.find("table") is not None:
            return False
        if node.name in TEXT_LIKE_TAGS:
            return bool(node.get_text(" ", strip=True))
        return bool(node.get_text(" ", strip=True))
    except Exception:
        return False


def _is_heading_node(node) -> bool:
    return isinstance(node, Tag) and node.name in {"h2", "h3", "h4"}


def _has_intro_keyword(node) -> bool:
    try:
        text = " ".join((node.get_text(" ", strip=True) if isinstance(node, Tag) else str(node)).split())
        return any(kw in text for kw in PROTECT_TABLE_INTRO_KEYWORDS)
    except Exception:
        return False


def _is_note_line(node) -> bool:
    try:
        text = (node.get_text(" ", strip=True) if isinstance(node, Tag) else str(node)).strip()
        return text.startswith("※")
    except Exception:
        return False


def _is_update_line_only(node) -> bool:
    try:
        text = (node.get_text(" ", strip=True) if isinstance(node, Tag) else str(node)).strip()
        return bool(UPDATE_LINE_PAT.match(text))
    except Exception:
        return False


def _intro_priority(node) -> int:
    if _is_heading_node(node):
        return 0
    if _has_intro_keyword(node):
        return 1
    if _is_note_line(node):
        return 2
    return 3


def _merge_table_intro_children(children: list) -> list:
    """データテーブル直前の連続する導入文ブロックを同一要素としてマージ。"""
    merged = []
    i = 0
    while i < len(children):
        child = children[i]
        if _is_data_table_block(child):
            j = i - 1
            intro_start = i
            while j >= 0 and _is_intro_text_block(children[j]):
                intro_start = j
                j -= 1

            if intro_start < i and merged and len(merged) >= (i - intro_start):
                intro_parts = merged[-(i - intro_start):]
                merged = merged[: -(i - intro_start)]
                filtered_intro_parts = [x for x in intro_parts if not _is_update_line_only(x)]
                merged.append("".join(str(x) for x in filtered_intro_parts) + str(child))
            else:
                merged.append(child)
            i += 1
            continue

        merged.append(child)
        i += 1
    return merged


def _split_children_to_chunks(node: Tag, limit: int) -> list:
    """再帰的に子要素をlimit以内に分割"""
    chunks = []
    buf = ""

    def flush():
        nonlocal buf
        if buf.strip():
            chunks.append(buf)
        buf = ""

    for child in list(node.children):
        try:
            child_html = str(child)
        except Exception:
            continue

        if not child_html.strip():
            continue

        if len(child_html) > limit:
            flush()
            if isinstance(child, Tag) and len(list(child.children)) > 0:
                sub_chunks = _split_children_to_chunks(child, limit)
                if sub_chunks:
                    chunks.extend(sub_chunks)
                else:
                    for i in range(0, len(child_html), limit):
                        chunks.append(child_html[i : i + limit])
            else:
                for i in range(0, len(child_html), limit):
                    chunks.append(child_html[i : i + limit])
            continue

        if len(buf) + len(child_html) > limit and buf:
            flush()
            buf = child_html
        else:
            buf += child_html

    flush()
    return chunks


def structural_chunk(html: str, limit: int) -> list:
    """
    body直下の子要素を基準に再帰分割。

    Args:
        html:  抽出済みHTML
        limit: 1チャンクの最大文字数（MAX_CHUNK_CHARS）

    Returns:
        チャンクHTMLのリスト（空文字は除外済み）
    """
    try:
        soup = BeautifulSoup(html, "html.parser")
        body = soup.find("body") or soup

        direct_children = [c for c in body.contents if str(c).strip()]
        direct_children = _merge_table_intro_children(direct_children)
        if not direct_children:
            return [str(body)]

        if len(direct_children) == 1:
            only = direct_children[0]
            only_html = str(only)
            if len(only_html) <= limit:
                return [only_html]
            if isinstance(only, Tag):
                return _split_children_to_chunks(only, limit)
            return [only_html[i : i + limit] for i in range(0, len(only_html), limit)]

        chunks = []
        buf = ""
        for c in direct_children:
            h = str(c)
            if len(h) > limit and isinstance(c, Tag):
                if buf.strip():
                    chunks.append(buf)
                    buf = ""
                chunks.extend(_split_children_to_chunks(c, limit))
                continue
            if len(h) > limit and not isinstance(c, Tag):
                if buf.strip():
                    chunks.append(buf)
                    buf = ""
                chunks.extend([h[i : i + limit] for i in range(0, len(h), limit)])
                continue

            if len(buf) + len(h) > limit and buf:
                chunks.append(buf)
                buf = h
            else:
                buf += h
        if buf.strip():
            chunks.append(buf)

        final = []
        for ch in chunks:
            if len(ch) <= limit:
                final.append(ch)
            else:
                tmp = BeautifulSoup(ch, "html.parser")
                root = tmp.find(True) or tmp
                if isinstance(root, Tag):
                    final.extend(_split_children_to_chunks(root, limit))
                else:
                    final.extend(
                        [ch[i : i + limit] for i in range(0, len(ch), limit)]
                    )

        final_chunks = [c for c in final if c.strip()] or [str(body)]
        if final_chunks:
            logger.debug("chunk_1_head=%s", final_chunks[0][:400].replace("\n", "\\n"))
            starts_with_table = [
                c.lstrip().lower().startswith("<table")
                for c in final_chunks
            ]
            logger.debug("chunk_starts_with_table=%s", starts_with_table)
        return final_chunks
    except Exception:
        if len(html) <= limit:
            fallback = [html]
        else:
            fallback = [html[i : i + limit] for i in range(0, len(html), limit)]
        if fallback:
            logger.debug("chunk_1_head=%s", fallback[0][:400].replace("\n", "\\n"))
            logger.debug(
                "chunk_starts_with_table=%s",
                [c.lstrip().lower().startswith("<table") for c in fallback],
            )
        return fallback
