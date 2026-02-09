# ==============================================================================
# chunker.py — 構造ベースチャンク分割
# ==============================================================================

from bs4 import BeautifulSoup
from bs4.element import Tag


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

        return [c for c in final if c.strip()] or [str(body)]
    except Exception:
        if len(html) <= limit:
            return [html]
        return [html[i : i + limit] for i in range(0, len(html), limit)]
