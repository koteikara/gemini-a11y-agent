# ==============================================================================
# trim_common.py
# - 共通部品削除
# - Menu / PageTop を境界にした終端カット
# - ブロック段階の終端カット / ノイズブロック判定
# ※ ロジックは Gemini-A11y Agent v21 から切り出し
# ==============================================================================

import re
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from .cleaners import is_protect_table_intro

# ------------------------------------------------------------------------------
# 明確な共通部品セレクタ（安全弁）
# ------------------------------------------------------------------------------
COMMON_DROP_SELECTORS = [
    "#footer",
    ".drawer_menu",
    ".spm",
    ".pagetop",
    ".menu-trigger",
    "#bg",
    "#bg_in",
    ".banner_2",
]

def drop_common_blocks_by_selectors(html: str) -> str:
    """
    footer / pagetop / sp menu など明確な共通部品を selector で削除
    """
    try:
        soup = BeautifulSoup(html, "html.parser")
        for sel in COMMON_DROP_SELECTORS:
            for t in soup.select(sel):
                try:
                    t.decompose()
                except Exception:
                    try:
                        t.unwrap()
                    except Exception:
                        pass
        return str(soup)
    except Exception:
        return html


# ------------------------------------------------------------------------------
# Menu / PageTop 終端カット
# ------------------------------------------------------------------------------
TRIM_MARKER_PATTERNS = [
    re.compile(r"^\s*PageTop\s*$", re.IGNORECASE),
    re.compile(r"^\s*(?:##\s*)?Menu\s*$", re.IGNORECASE),
    re.compile(r"^\s*メニュー\s*$"),
    re.compile(r"^\s*ページトップ\s*$"),
    re.compile(r"^\s*footer\s*$", re.IGNORECASE),
    re.compile(r"^\s*スマホメニュー\s*$"),
    re.compile(r"^\s*スマホ固定メニュー\s*$"),
]

def _match_trim_marker(text: str) -> bool:
    s = (text or "").strip()
    if not s:
        return False
    for pat in TRIM_MARKER_PATTERNS:
        if pat.search(s):
            return True
    return False


def trim_after_menu_pagetop(html: str):
    """
    body直下の子要素のうち、
    Menu / PageTop 等のマーカーを含む最初のブロックを見つけ、
    そのブロック以降を丸ごと削除する。

    Returns:
        (html, trimmed: bool)
    """
    try:
        soup = BeautifulSoup(html, "html.parser")
        body = soup.find("body") or soup

        top_children = [c for c in body.contents if isinstance(c, Tag)]
        if not top_children:
            return str(soup), False

        cut_index = None

        for node in body.descendants:
            if not isinstance(node, NavigableString):
                continue
            if not _match_trim_marker(str(node)):
                continue

            cur = node.parent
            while cur is not None and cur is not body and cur.parent is not body:
                cur = cur.parent

            if cur is None or cur is body:
                continue

            for i, t in enumerate(top_children):
                if t is cur:
                    cut_index = i
                    break

            if cut_index is not None:
                break

        if cut_index is None:
            return str(soup), False

        for t in top_children[cut_index:]:
            try:
                t.decompose()
            except Exception:
                try:
                    t.unwrap()
                except Exception:
                    pass

        return str(soup), True

    except Exception:
        return html, False


# ------------------------------------------------------------------------------
# ブロック段階の終端カット / ノイズブロック判定（安全）
# ------------------------------------------------------------------------------
END_TRIM_TEXT_PATTERNS = [
    # 佐賀市 promotion987 の混入開始点
    re.compile(r"INDEX\s*PAGE\s*ITEM", re.IGNORECASE),
    re.compile(r"BASIC_PARTS_SET", re.IGNORECASE),
]

NOISE_BLOCK_TEXT_PATTERNS = [
    re.compile(r"footer\s*スマホメニュー", re.IGNORECASE),
    re.compile(r"^bg_in$", re.IGNORECASE),
    re.compile(r"^bg$", re.IGNORECASE),
]

def extract_text_for_block(html_snippet: str) -> str:
    """
    ブロックHTMLを安全にテキスト化（終端カット/ノイズ判定用）
    """
    try:
        return BeautifulSoup(html_snippet, "html.parser").get_text(" ", strip=True)
    except Exception:
        return (html_snippet or "").strip()

def is_end_trim_trigger(block_text: str) -> bool:
    """
    ブロック内に「以降は不要領域」混入の開始点が出たら True
    """
    if not block_text:
        return False
    for pat in END_TRIM_TEXT_PATTERNS:
        if pat.search(block_text):
            return True
    return False

def is_noise_block(block_text: str) -> bool:
    """
    それ単体で意味を持たない共通ノイズブロックなら True
    """
    if not block_text:
        return True
    s = block_text.strip()
    for pat in NOISE_BLOCK_TEXT_PATTERNS:
        if pat.search(s):
            return True
    return False


def should_apply_end_trim(block_text: str, current_blocks, upcoming_blocks, has_accepted_content: bool):
    """end-trim実行可否を返す。テーブル導入文の保護条件を優先。"""
    if not is_end_trim_trigger(block_text):
        return False, False, False

    protect, intro_detected, table_ahead = is_protect_table_intro(
        current_blocks=current_blocks,
        upcoming_blocks=upcoming_blocks,
    )
    if protect:
        return False, intro_detected, table_ahead
    if not has_accepted_content:
        return False, intro_detected, table_ahead
    return True, intro_detected, table_ahead
