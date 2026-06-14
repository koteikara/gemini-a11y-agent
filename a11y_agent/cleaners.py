# ==============================================================================
# cleaners.py — HTML前処理・属性削除・レイアウトtable変換・絶対パス化
# ==============================================================================

import re
import logging
import requests
from urllib.parse import quote, urljoin
from lxml import html as lxml_html

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from .config import (
    FORBIDDEN_TAGS,
    DROP_ATTRS_BY_TAG,
    IFRAME_ALLOWED_ATTRS,
    FILE_EXTS,
    IFRAME_TITLE_FETCH_CAP_PER_PAGE,
    IFRAME_TITLE_FETCH_TIMEOUT,
    CONVERT_LAYOUT_TABLES_TO_DIV,
    BUILD_ID,
    FEATURE_IFRAME_TITLE_ENRICH,
    FEATURE_IFRAME_YT_OEMBED,
    FEATURE_IFRAME_TITLE_GENERIC_FIX,
    FEATURE_IFRAME_TITLE_LOG,
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
YOUTUBE_EMBED_PAT = re.compile(r"^https?://(?:www\.)?(?:youtube\.com|youtube-nocookie\.com)/embed/([A-Za-z0-9_-]{6,})", re.IGNORECASE)
GENERIC_IFRAME_TITLES = {"youtube video player", "youtube", "video player", "player"}
GENERIC_VIDEO_TITLES = {"video", "動画", "movie"}
YOUTUBE_SUFFIX = "（YouTube）"
MAX_IFRAME_TITLE_SEED_LEN = 100

# --- UI的テキストパターン（table判定用） ---
UIISH_TEXT_PAT = re.compile(
    r"(にメールを送る|メールを送る|クリック|詳細|申し込み|申込み|予約|送信|問合せ|問い合わせ)"
)

HEADER_TEXT_MIN_LEN = 1
HEADER_TEXT_MAX_LEN = 30
HEADER_TEXT_MAX_NUMERICISH_RATIO = 0.6
HEADER_TEXT_MIN_NONEMPTY_CELLS = 2
HEADER_UI_TAGS = ["a", "button", "input", "select", "textarea"]

ROW_HEADER_HINT_PAT = re.compile(
    r"(診療科|診療|科目|区分|分類|日付|曜日|時間|施設|会場|担当|当番|窓口|項目)",
    re.IGNORECASE,
)
ROW_HEADER_PHONE_PAT = re.compile(r"^(?:\+?\d[\d\-()\s]{7,}|\d{2,4}-\d{2,4}-\d{3,4})$")
ROW_HEADER_MAX_LEN = 10
ROW_HEADER_REPEAT_RATIO = 0.25

TABLE_HEADER_DICT_WORDS = [
    "診療科", "医療機関名", "電話", "TEL", "所在地", "住所", "時間", "受付",
    "区分", "内容", "対象", "備考", "特定健診", "診療", "休診", "曜日",
]
TABLE_HEADER_WORD_PAT = re.compile("|".join(re.escape(w) for w in TABLE_HEADER_DICT_WORDS), re.IGNORECASE)
TABLE_PHONE_PAT = re.compile(r"0\d{1,4}-\d{1,4}-\d{3,4}")
TABLE_URL_PAT = re.compile(r"https?://", re.IGNORECASE)

TABLE_ORIENT_COL_MIN = 2.5
TABLE_ORIENT_ROW_MIN = 2.5
TABLE_ORIENT_DELTA_MIN = 1.0
TABLE_ORIENT_MAX_BLANK_RATIO = 0.5

# --- div に残すべきでない table由来属性 ---
DIV_FORBIDDEN_ATTRS_FROM_TABLE = {
    "scope", "headers", "axis", "abbr", "rowspan", "colspan"
}

# --- 本文混入の内部識別ラベル削除 ---
FORBIDDEN_INTERNAL_TEXT_PATTERNS = [
    "BASIC_PARTS_SET",
    "INDEX PAGE ITEM",
]

def _build_internal_token_pattern(token: str):
    body = re.escape(token).replace(r"\ ", r"\s+")
    return re.compile(rf"(?<![A-Za-z0-9_]){body}(?![A-Za-z0-9_])", re.IGNORECASE)


FORBIDDEN_INTERNAL_TEXT_TOKEN_PATTERNS = [
    _build_internal_token_pattern(token)
    for token in FORBIDDEN_INTERNAL_TEXT_PATTERNS
]

INTERNAL_MARKER_ROLLBACK_MIN_REMOVED_CHARS = 20
INTERNAL_MARKER_ROLLBACK_MIN_REDUCTION_RATIO = 0.6

# --- Protect explanation text before data tables ---
PROTECT_TABLE_INTRO_KEYWORDS = [
    "休日", "夜間", "受診", "診療時間", "当番医", "在宅当番医",
    "受付", "保険証", "小児", "歯科", "特定健診", "お問い合わせ",
    "ご利用ください",
]
PROTECT_TABLE_INTRO_MIN_TEXT_LEN = 30
PROTECT_TABLE_INTRO_HINT_PAT = re.compile(r"(?:※|注記|注意|ください|しましょう|受付|診療時間)")

UPDATE_ONLY_TEXT_PAT = re.compile(
    r"^更新\s*[:：]\s*\d{4}年\s*\d{1,2}月\s*\d{1,2}日$"
)

logger = logging.getLogger(__name__)


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


def _drop_internal_markers(text: str) -> str:
    """本文テキストから内部識別ラベルを除去して空白を正規化。"""
    original_text = str(text or "")
    new_text = original_text
    for pat in FORBIDDEN_INTERNAL_TEXT_TOKEN_PATTERNS:
        new_text = pat.sub(" ", new_text)
    new_text = re.sub(r"\s+", " ", new_text).strip()

    removed_chars = len(original_text) - len(new_text)
    reduction_ratio = (removed_chars / len(original_text)) if original_text else 0.0
    if (
        removed_chars >= INTERNAL_MARKER_ROLLBACK_MIN_REMOVED_CHARS
        and reduction_ratio >= INTERNAL_MARKER_ROLLBACK_MIN_REDUCTION_RATIO
    ):
        return original_text
    return new_text


def _is_marker_like_text_node(text: str) -> bool:
    """内部マーカ混入ノードらしさを判定（日本語文の巻き込み防止）。"""
    t = str(text or "")
    t_strip = t.strip()
    if not t_strip:
        return False
    if not any(pat.search(t) for pat in FORBIDDEN_INTERNAL_TEXT_TOKEN_PATTERNS):
        return False

    # 長文本文は対象外（短いマーカー文ノードのみに限定）
    if len(t_strip) > 200:
        return False

    ascii_chars = len(re.findall(r"[\x00-\x7F]", t_strip))
    ascii_ratio = (ascii_chars / len(t_strip)) if t_strip else 0.0
    if ascii_ratio < 0.6:
        return False

    jp_punct_count = sum(t_strip.count(ch) for ch in ("。", "、"))
    kana_count = len(re.findall(r"[\u3040-\u30FF]", t_strip))
    if jp_punct_count >= 1 or kana_count >= 3:
        return False

    jp_char_count = len(re.findall(r"[\u3040-\u30FF\u3400-\u9FFF]", t))
    ascii_word_count = len(re.findall(r"[A-Za-z0-9_]+", t))

    # 日本語文の本文らしい塊は対象外にする（短い混入行は許容）。
    if jp_char_count >= 20 and ascii_word_count <= 10 and len(t) >= 50:
        return False

    return True


def _shorten_for_log(text: str, max_len: int = 80) -> str:
    t = str(text or "").replace("\n", "\\n")
    if len(t) <= max_len:
        return t
    return t[:max_len] + "..."


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


def _cell_text(cell: Tag) -> str:
    return re.sub(r"\s+", " ", cell.get_text(" ", strip=True)).strip()


def _is_numericish_text(text: str) -> bool:
    t = re.sub(r"\s+", "", str(text or ""))
    if not t:
        return False
    return bool(re.fullmatch(r"[0-9０-９.,/\-+()％%:：]+", t))


def _row_total_colspan(row: Tag) -> int:
    total = 0
    for c in row.find_all(["td", "th"], recursive=False):
        try:
            total += max(1, int(c.get("colspan", 1)))
        except Exception:
            total += 1
    return total


def _normalize_lxml_cell_text(text: str) -> str:
    return re.sub(r"[\s\u00A0]+", "", str(text or "")).strip()


def _digit_ratio(text: str) -> float:
    t = str(text or "")
    if not t:
        return 0.0
    digit_count = sum(ch.isdigit() for ch in t)
    return digit_count / len(t)


def _header_like_score(text: str):
    t_norm = _normalize_lxml_cell_text(text)
    if not t_norm:
        return 0.0, False, True

    score = 0.0
    dict_hit = bool(TABLE_HEADER_WORD_PAT.search(t_norm))
    digit_ratio = _digit_ratio(t_norm)

    if len(t_norm) <= 10:
        score += 1.0
    if digit_ratio < 0.2:
        score += 1.0
    if dict_hit:
        score += 2.0
    if TABLE_PHONE_PAT.search(t_norm):
        score -= 1.0
    if TABLE_URL_PAT.search(t_norm):
        score -= 1.0

    return max(0.0, score), dict_hit, False


def _avg_digit_ratio(values):
    if not values:
        return 0.0
    return sum(_digit_ratio(v) for v in values) / len(values)


def _avg_text_len(values):
    if not values:
        return 0.0
    return sum(len(v) for v in values) / len(values)


def _score_data_likeness(values):
    if not values:
        return 0.0
    score = 0.0
    if _avg_digit_ratio(values) >= 0.2:
        score += 0.5
    if _avg_text_len(values) > 10:
        score += 0.5
    if any(TABLE_PHONE_PAT.search(v) for v in values):
        score += 0.5
    if any(("住所" in v) or ("所在地" in v) for v in values):
        score += 0.5
    return score


def _table_first_axis_orientation_lxml(table_el):
    rows = table_el.xpath("./tr | ./tbody/tr")
    if len(rows) < 2:
        return "none", "row_count_lt_2", {}

    grid = []
    for row in rows:
        cells = row.xpath("./th | ./td")
        if not cells:
            continue
        grid.append(cells)
    if len(grid) < 2:
        return "none", "effective_row_count_lt_2", {}

    min_cols = min(len(r) for r in grid)
    if min_cols < 2:
        return "none", "col_count_lt_2", {}

    if any(c.tag.lower() != "td" for c in grid[0][:min_cols]):
        return "none", "first_row_has_th", {}
    if any(r[0].tag.lower() != "td" for r in grid):
        return "none", "first_col_has_th", {}

    all_texts = []
    blank_count = 0
    for row_cells in grid:
        for cell in row_cells[:min_cols]:
            txt = "".join(cell.itertext())
            all_texts.append(txt)
            if not _normalize_lxml_cell_text(txt):
                blank_count += 1
    blank_ratio = blank_count / len(all_texts) if all_texts else 0.0
    if blank_ratio > TABLE_ORIENT_MAX_BLANK_RATIO:
        return "none", "blank_ratio_high", {
            "rows": len(grid),
            "cols": min_cols,
            "blank_ratio": blank_ratio,
        }

    row1_texts = ["".join(c.itertext()) for c in grid[0][:min_cols]]
    col1_texts = ["".join(r[0].itertext()) for r in grid]
    row1_scores = [_header_like_score(t) for t in row1_texts]
    col1_scores = [_header_like_score(t) for t in col1_texts]

    col_score = sum(s for s, _, _ in row1_scores) / max(1, len(row1_scores))
    row_score = sum(s for s, _, _ in col1_scores) / max(1, len(col1_scores))

    row2_texts = ["".join(c.itertext()) for c in grid[1][:min_cols]]
    col2_texts = ["".join(r[1].itertext()) for r in grid]
    col_score += _score_data_likeness(row2_texts)
    row_score += _score_data_likeness(col2_texts)

    delta = col_score - row_score
    if col_score >= TABLE_ORIENT_COL_MIN and delta >= TABLE_ORIENT_DELTA_MIN:
        orient = "col"
    elif row_score >= TABLE_ORIENT_ROW_MIN and delta <= -TABLE_ORIENT_DELTA_MIN:
        orient = "row"
    else:
        orient = "none"

    info = {
        "rows": len(grid),
        "cols": min_cols,
        "col_score": round(col_score, 3),
        "row_score": round(row_score, 3),
        "delta": round(delta, 3),
        "dict_hits_row1": sum(1 for _, hit, _ in row1_scores if hit),
        "dict_hits_col1": sum(1 for _, hit, _ in col1_scores if hit),
    }
    return orient, "classified", info


def _promote_lxml_cell_to_th(cell, scope_value: str):
    if cell.tag.lower() == "th":
        cell.set("scope", scope_value)
        return
    new_cell = lxml_html.Element("th")
    for attr, value in cell.attrib.items():
        new_cell.set(attr, value)
    new_cell.set("scope", scope_value)
    new_cell.text = cell.text
    for child in list(cell):
        cell.remove(child)
        new_cell.append(child)
    new_cell.tail = cell.tail
    cell.getparent().replace(cell, new_cell)


def _fix_table_header_orientation_lxml(html_content: str, log: bool = True):
    wrapped_html = f"<div>{html_content}</div>"
    root = lxml_html.fromstring(wrapped_html)
    converted_col = 0
    converted_row = 0

    for table in root.xpath(".//table"):
        rows = table.xpath("./tr | ./tbody/tr")
        if table.xpath("./thead"):
            if log:
                print("[table-header-orient] orient=skip reason=thead_exists")
            continue
        if len(rows) < 2:
            if log:
                print("[table-header-orient] orient=skip reason=row_count_lt_2")
            continue
        if _is_layout_table(BeautifulSoup(lxml_html.tostring(table, encoding="unicode"), "html.parser").find("table")):
            if log:
                print("[table-header-orient] orient=skip reason=layout_suspected")
            continue

        orient, reason, info = _table_first_axis_orientation_lxml(table)
        if orient == "col":
            row1 = rows[0]
            for cell in row1.xpath("./td | ./th"):
                _promote_lxml_cell_to_th(cell, "col")
                converted_col += 1
        elif orient == "row":
            for row in rows:
                cells = row.xpath("./td | ./th")
                if not cells:
                    continue
                _promote_lxml_cell_to_th(cells[0], "row")
                converted_row += 1

        if log:
            if info:
                print(
                    "[table-header-orient] "
                    f"orient={orient} rows={info.get('rows', 0)} cols={info.get('cols', 0)} "
                    f"col={info.get('col_score', 0)} row={info.get('row_score', 0)} "
                    f"delta={info.get('delta', 0)} "
                    f"dict_row1={info.get('dict_hits_row1', 0)} dict_col1={info.get('dict_hits_col1', 0)}"
                )
            else:
                print(f"[table-header-orient] orient={orient} reason={reason}")

    fixed_html = "".join(
        lxml_html.tostring(child, encoding="unicode")
        for child in root
    )
    return fixed_html, {"orient_col_fixed_count": converted_col, "orient_row_fixed_count": converted_row}


def _get_first_data_row(table_tag: Tag):
    for row in table_tag.find_all("tr"):
        if row.find_parent("thead") is not None:
            continue
        return row
    return None


def _is_simple_header_candidate(table_tag: Tag):
    first_row = _get_first_data_row(table_tag)
    if first_row is None:
        return False, "no_first_data_row", []

    if first_row.find("th") is not None:
        return False, "already_has_th", []

    rows = table_tag.find_all("tr")
    if len(rows) < 2:
        return False, "row_count_lt_2", []

    if first_row.find_all(["td", "th"], recursive=False) == []:
        return False, "first_row_no_cells", []

    data_rows = [r for r in rows if r.find_parent("thead") is None]
    if len(data_rows) < 2:
        return False, "data_rows_lt_2", []

    first_count = _row_total_colspan(first_row)
    rep_row = None
    for r in data_rows[1:]:
        if r.find_all(["td", "th"], recursive=False):
            rep_row = r
            break
    if rep_row is None:
        return False, "no_representative_row", []

    rep_count = _row_total_colspan(rep_row)
    if abs(first_count - rep_count) > 1:
        return False, "col_count_mismatch", []

    first_cells = first_row.find_all("td", recursive=False)
    nonempty_texts = [_cell_text(c) for c in first_cells if _cell_text(c)]
    if len(nonempty_texts) < HEADER_TEXT_MIN_NONEMPTY_CELLS:
        return False, "too_few_nonempty", []

    lengths_ok = all(
        HEADER_TEXT_MIN_LEN <= len(t) <= HEADER_TEXT_MAX_LEN
        for t in nonempty_texts
    )
    if not lengths_ok:
        return False, "text_len_out_of_range", []

    numericish_count = sum(1 for t in nonempty_texts if _is_numericish_text(t))
    if (numericish_count / max(1, len(nonempty_texts))) > HEADER_TEXT_MAX_NUMERICISH_RATIO:
        return False, "numericish_ratio_high", []

    ui_only_count = 0
    for c in first_cells:
        text = _cell_text(c)
        if not text:
            continue
        if c.find(HEADER_UI_TAGS) is None:
            continue
        ui_text = re.sub(r"\s+", "", c.get_text(" ", strip=True))
        own_text = re.sub(r"\s+", "", text)
        if own_text and own_text == ui_text:
            ui_only_count += 1
    if ui_only_count == len(nonempty_texts):
        return False, "all_ui_only_cells", []

    preview = nonempty_texts[:8]
    return True, "fixable", preview


def _looks_like_row_header_text(text: str) -> bool:
    t = re.sub(r"\s+", " ", str(text or "")).strip()
    if not t:
        return False
    if len(t) > ROW_HEADER_MAX_LEN:
        return False
    if _is_numericish_text(t):
        return False
    if ROW_HEADER_PHONE_PAT.match(t):
        return False
    return True


def _get_prev_heading_text(node: Tag) -> str:
    for prev in node.find_all_previous(["h2", "h3", "h4"]):
        txt = re.sub(r"\s+", " ", prev.get_text(" ", strip=True)).strip()
        if txt:
            return txt
    return ""


def _is_target_data_table(table: Tag) -> bool:
    if table.find("caption") is None:
        return False
    if table.find("thead") is None:
        return False
    if _is_layout_table(table):
        return False

    header_row = table.find("thead").find("tr") if table.find("thead") else None
    if header_row is None:
        return False
    cols = _row_total_colspan(header_row)
    return cols >= 2


def fix_data_table_headers(html_content: str, log: bool = True):
    """data table の thead/tbody/caption 見出し構造を in-place 補正。"""
    try:
        oriented_html, orient_meta = _fix_table_header_orientation_lxml(html_content, log=log)
        soup = BeautifulSoup(oriented_html, "html.parser")
        table_count = 0
        header_fixed_count = 0
        row_header_fixed_count = 0

        for table in soup.find_all("table"):
            if not _is_target_data_table(table):
                if table.find("caption") is None and not _is_layout_table(table):
                    heading = _get_prev_heading_text(table)
                    if heading:
                        cap = soup.new_tag("caption")
                        cap.string = f"{heading}一覧"
                        table.insert(0, cap)
                continue

            table_count += 1
            thead = table.find("thead")

            for th in thead.find_all("th"):
                if (th.get("scope") or "").lower() != "col":
                    th["scope"] = "col"
                    header_fixed_count += 1

            tbody = table.find("tbody")
            if tbody is None:
                continue

            thead_first_text = ""
            head_first_cell = thead.find(["th", "td"])
            if head_first_cell is not None:
                thead_first_text = _cell_text(head_first_cell)

            first_col_cells = []
            for row_index, row in enumerate(tbody.find_all("tr", recursive=False)):
                cells = row.find_all(["th", "td"], recursive=False)
                if not cells:
                    continue
                if row_index == 0 and cells[0].name == "th" and (cells[0].get("scope") or "").lower() == "col":
                    continue
                first_col_cells.append(cells[0])

            first_col_texts = [
                _cell_text(c)
                for c in first_col_cells
                if _looks_like_row_header_text(_cell_text(c))
            ]
            repeat_ratio = 0.0
            if first_col_texts:
                repeat_ratio = 1 - (len(set(first_col_texts)) / len(first_col_texts))

            can_promote = bool(ROW_HEADER_HINT_PAT.search(thead_first_text)) or repeat_ratio >= ROW_HEADER_REPEAT_RATIO

            if not can_promote:
                continue

            for cell in first_col_cells:
                txt = _cell_text(cell)
                if not _looks_like_row_header_text(txt):
                    continue

                if cell.name == "th" and (cell.get("scope") or "").lower() == "row":
                    continue

                cell.name = "th"
                if (cell.get("scope") or "").lower() != "row":
                    cell["scope"] = "row"
                row_header_fixed_count += 1

        if log:
            print(
                f"  [table-fix] tables={table_count} "
                f"header_fixed={header_fixed_count} "
                f"row_header_fixed={row_header_fixed_count}"
            )

        return str(soup), {
            "table_count": table_count,
            "header_fixed_count": header_fixed_count,
            "row_header_fixed_count": row_header_fixed_count,
            "orient_col_fixed_count": orient_meta.get("orient_col_fixed_count", 0),
            "orient_row_fixed_count": orient_meta.get("orient_row_fixed_count", 0),
        }
    except Exception:
        return html_content, {
            "table_count": 0,
            "header_fixed_count": 0,
            "row_header_fixed_count": 0,
            "orient_col_fixed_count": 0,
            "orient_row_fixed_count": 0,
        }


def fix_data_table_header_row(html_content: str, log: bool = True):
    """互換用ラッパー。"""
    return fix_data_table_headers(html_content, log=log)


def fetch_title_from_url(src_url: str, timeout_sec: int = IFRAME_TITLE_FETCH_TIMEOUT) -> str:
    """URLからページ<title>を取得（iframe title補完用）"""
    try:
        resp = requests.get(
            src_url,
            timeout=timeout_sec,
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


def fetch_youtube_oembed_title(embed_url: str, timeout_sec: int = IFRAME_TITLE_FETCH_TIMEOUT):
    """YouTube埋め込みURLのoEmbedから動画タイトルを取得。"""
    canonical_embed_url = embed_url.split("?", 1)[0].split("#", 1)[0]
    m = YOUTUBE_EMBED_PAT.match(canonical_embed_url)
    if not m:
        return "", "invalid_youtube_embed"

    video_id = m.group(1)
    watch_url = "https://www.youtube.com/watch?v=" + video_id
    try:
        resp = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": watch_url, "format": "json"},
            timeout=timeout_sec,
            headers={"User-Agent": "Mozilla/5.0"},
        )
    except Exception as ex:
        return "", f"exception={ex.__class__.__name__}"

    if resp.status_code != 200:
        return "", f"status={resp.status_code}"

    try:
        data = resp.json()
    except Exception as ex:
        return "", f"exception={ex.__class__.__name__}"

    title = re.sub(r"\s{2,}", " ", str(data.get("title") or "").strip()).strip()
    if not title:
        return "", "exception=empty_title"
    return title, ""


def _clean_title_seed(text: str) -> str:
    t = re.sub(r"\s+", " ", str(text or "")).strip()
    t = re.sub(r"[【】\[\]<>＜＞]", " ", t)
    t = re.sub(r"\s*[|｜\-–—]\s*", " ", t)
    t = re.sub(r"\s*\(?\s*YouTube\s*\)?\s*", " ", t, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", t).strip(" 　-–—|｜")


def _format_youtube_iframe_title(base_title: str) -> str:
    cleaned = _clean_title_seed(base_title)
    cleaned = cleaned[:MAX_IFRAME_TITLE_SEED_LEN]
    if not cleaned:
        cleaned = "動画"
    return f"{cleaned}{YOUTUBE_SUFFIX}"


def _extract_context_text(iframe_tag: Tag) -> str:
    targets = ["h1", "h2", "h3", "h4", "h5", "h6", "p"]
    node = iframe_tag
    while isinstance(node, Tag) and node.parent is not None:
        for sib in node.find_previous_siblings():
            if not isinstance(sib, Tag):
                continue
            cands = []
            if sib.name in targets:
                cands.append(sib)
            cands.extend(sib.find_all(targets))
            for cand in reversed(cands):
                txt = _clean_title_seed(cand.get_text(" ", strip=True))
                if txt:
                    return txt
        node = node.parent
    return ""


def _is_bad_youtube_title(cur_title: str) -> bool:
    t_norm = re.sub(r"\s+", " ", cur_title).strip().lower()
    if not t_norm:
        return True
    if t_norm in GENERIC_IFRAME_TITLES:
        return True
    if t_norm in GENERIC_VIDEO_TITLES:
        return True
    return False


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


def remove_forbidden_internal_text_anywhere(html_content: str) -> str:
    """本文に混入した内部識別ラベルをテキストノードから除去。"""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        changed_nodes = 0
        max_removed_chars = 0
        max_reduction_ratio = 0.0
        sample_before = ""
        sample_after = ""

        for node in soup.find_all(string=True):
            if not isinstance(node, NavigableString):
                continue

            txt = str(node)
            if not _is_marker_like_text_node(txt):
                continue
            new_txt = _drop_internal_markers(txt)
            if new_txt != txt:
                changed_nodes += 1
                removed_chars = len(txt) - len(new_txt)
                reduction_ratio = (removed_chars / len(txt)) if txt else 0.0
                if removed_chars > max_removed_chars:
                    max_removed_chars = removed_chars
                if reduction_ratio > max_reduction_ratio:
                    max_reduction_ratio = reduction_ratio
                if not sample_before:
                    sample_before = _shorten_for_log(txt)
                    sample_after = _shorten_for_log(new_txt)
                node.replace_with(new_txt)

        logger.debug(
            "removed_internal_markers: changed_nodes=%d max_removed_chars=%d max_reduction_ratio=%.3f",
            changed_nodes,
            max_removed_chars,
            max_reduction_ratio,
        )
        if sample_before:
            logger.debug(
                "removed_internal_markers_sample: before='%s' after='%s'",
                sample_before,
                sample_after,
            )

        return str(soup)
    except Exception:
        return html_content


def enrich_iframe_titles(
    html_content: str,
    base_url: str = "",
    fetch_cap_per_page: int = IFRAME_TITLE_FETCH_CAP_PER_PAGE,
    fetch_timeout_sec: int = IFRAME_TITLE_FETCH_TIMEOUT,
    log: bool = False,
) -> str:
    """iframe titleをYouTube中心に補完・整形（再実行安全）。"""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        iframes = soup.find_all("iframe")
        if not iframes:
            return str(soup)

        cache = {}  # src -> (base_title, method)
        yt_cache = {}  # src -> (base_title, method, reason)
        fetched = 0
        updated_count = 0
        skipped_count = 0
        cap_reached_count = 0
        update_logs = []
        skip_logs = []

        for fr in iframes:
            raw_src = (fr.get("src") or "").strip()
            if not raw_src:
                skipped_count += 1
                continue

            src = urljoin(base_url, raw_src) if base_url else raw_src
            cur_title_raw = fr.get("title") or ""
            cur_title = cur_title_raw.strip()
            t_norm = re.sub(r"\s+", " ", cur_title).strip().lower()

            is_youtube = bool(YOUTUBE_EMBED_PAT.match(src.split("?", 1)[0]))

            need = False
            if is_youtube:
                if _is_bad_youtube_title(cur_title):
                    need = True
                elif YOUTUBE_SUFFIX not in cur_title:
                    need = True
            else:
                if not t_norm:
                    need = True
                elif URLISH_TITLE_PAT.match(cur_title):
                    need = True
                elif t_norm == raw_src.lower():
                    need = True
                elif t_norm == src.lower():
                    need = True
                elif FEATURE_IFRAME_TITLE_GENERIC_FIX and t_norm in GENERIC_IFRAME_TITLES:
                    need = True

            if not need:
                skipped_count += 1
                continue

            if is_youtube:
                method = "cache"
                reason = ""
                base_title = ""

                if src in yt_cache:
                    base_title, method, reason = yt_cache[src]
                else:
                    if fetched >= fetch_cap_per_page:
                        cap_reached_count += 1
                        method = "oembed_failed"
                        reason = "status=fetch_cap_reached"
                    elif not FEATURE_IFRAME_YT_OEMBED:
                        method = "oembed_failed"
                        reason = "status=feature_disabled"
                    else:
                        base_title, fail_reason = fetch_youtube_oembed_title(src, timeout_sec=fetch_timeout_sec)
                        fetched += 1
                        if base_title:
                            method = "youtube_oembed"
                        else:
                            method = "oembed_failed"
                            reason = fail_reason or "exception=unknown"
                    yt_cache[src] = (base_title, method, reason)

                if method == "youtube_oembed":
                    new_title = _format_youtube_iframe_title(base_title)
                else:
                    new_title = ""
            else:
                method = "cache"
                if src in cache:
                    base_title, method = cache[src]
                else:
                    base_title = ""
                    if is_youtube and FEATURE_IFRAME_YT_OEMBED:
                        base_title = fetch_youtube_oembed_title(src, timeout_sec=fetch_timeout_sec)
                        method = "youtube_oembed" if base_title else ""
                    if not base_title:
                        if is_youtube:
                            base_title = _extract_context_text(fr)
                            method = "context_text" if base_title else "fallback"
                            if not base_title:
                                base_title = "動画"
                        else:
                            method = "html_title"
                            base_title = fetch_title_from_url(src, timeout_sec=fetch_timeout_sec)
                    if base_title:
                        cache[src] = (base_title, method)
                    fetched += 1

                if is_youtube:
                    new_title = _format_youtube_iframe_title(base_title)
                else:
                    new_title = base_title

            if new_title and new_title != cur_title_raw:
                fr["title"] = new_title
                updated_count += 1
                if len(update_logs) < 5:
                    update_logs.append(
                        {
                            "src": src,
                            "old_title": cur_title_raw,
                            "t_norm": t_norm,
                            "new_title": new_title,
                            "method": method,
                        }
                    )
            else:
                skipped_count += 1
                if is_youtube and method == "oembed_failed" and len(skip_logs) < 5:
                    skip_logs.append(
                        {
                            "src": src,
                            "old_title": cur_title_raw,
                            "method": method,
                            "reason": reason,
                        }
                    )

        if log:
            print(
                "  [iframe-title] "
                f"BUILD_ID={BUILD_ID} "
                f"cap={fetch_cap_per_page} "
                f"timeout={fetch_timeout_sec} "
                f"base_url={base_url or '-'}"
            )
            print(
                "  [iframe-title] enabled: "
                f"yt_oembed={'ON' if FEATURE_IFRAME_YT_OEMBED else 'OFF'} "
                f"generic_fix={'ON' if FEATURE_IFRAME_TITLE_GENERIC_FIX else 'OFF'}"
            )
            print(
                "  ℹ️ iframe title enrich: "
                f"iframe_count={len(iframes)} "
                f"updated_count={updated_count} "
                f"skipped_count={skipped_count} "
                f"fetch_count={fetched} "
                f"cap_reached_count={cap_reached_count}"
            )
            for idx, item in enumerate(update_logs, start=1):
                src_short = item["src"]
                if len(src_short) > 120:
                    src_short = src_short[:117] + "..."
                print(
                    f"    ↳ update#{idx} src={src_short} "
                    f"old_title={item['old_title']!r} "
                    f"t_norm={item['t_norm']!r} "
                    f"new_title={item['new_title']!r} "
                    f"method={item['method']}"
                )
            for idx, item in enumerate(skip_logs, start=1):
                src_short = item["src"]
                if len(src_short) > 120:
                    src_short = src_short[:117] + "..."
                print(
                    f"    ↳ skip#{idx} src={src_short} "
                    f"old_title={item['old_title']!r} "
                    f"method={item['method']} "
                    f"reason={item['reason']}"
                )

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


def has_data_table_ahead(blocks, lookahead: int = 3) -> bool:
    """次ブロック群にレイアウトtable以外のtableが存在するか判定。"""
    try:
        def _is_data_table_candidate(table: Tag) -> bool:
            if _is_layout_table(table):
                return False
            if table.find("caption") is not None:
                return True
            if table.find("thead") is not None:
                return True
            for th in table.find_all("th"):
                if (th.get("scope") or "").lower() == "col":
                    return True
            return False

        if isinstance(blocks, (BeautifulSoup, Tag)):
            tables = blocks.find_all("table")
            for table in tables:
                if _is_data_table_candidate(table):
                    return True
            return False

        target_blocks = list(blocks or [])[:lookahead]
        for block in target_blocks:
            soup = BeautifulSoup(str(block or ""), "html.parser")
            for table in soup.find_all("table"):
                if _is_data_table_candidate(table):
                    return True
        return False
    except Exception:
        return False


def is_protect_table_intro(current_blocks, upcoming_blocks, lookahead: int = 3):
    """
    テーブル前説明文保護判定：
    - 現在ブロック内に説明文キーワードがある
    - 次のNブロック内にデータテーブルがある

    Returns:
        (protect: bool, intro_detected: bool, table_ahead: bool, keyword_hit: str)
    """
    intro_detected = False
    table_ahead = False
    keyword_hit = ""

    def _detect_intro_text(text: str):
        norm = re.sub(r"\s+", " ", str(text or "")).strip()
        if len(norm) < PROTECT_TABLE_INTRO_MIN_TEXT_LEN:
            return False, ""

        hit = ""
        for kw in PROTECT_TABLE_INTRO_KEYWORDS:
            if kw in norm:
                hit = kw
                break

        if hit:
            return True, hit
        if PROTECT_TABLE_INTRO_HINT_PAT.search(norm):
            return True, "hint"
        return False, ""

    try:
        for block in list(current_blocks or []):
            text = BeautifulSoup(str(block or ""), "html.parser").get_text(" ", strip=True)
            is_intro, hit = _detect_intro_text(text)
            if is_intro:
                intro_detected = True
                keyword_hit = hit
                break
    except Exception:
        intro_detected = False

    table_ahead = has_data_table_ahead(upcoming_blocks, lookahead=lookahead)
    return intro_detected and table_ahead, intro_detected, table_ahead, keyword_hit


def remove_update_only_nodes(html_content: str) -> str:
    """Remove elements whose entire visible text is only a page update date."""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        candidate_tags = [
            "p", "div", "span", "li", "dt", "dd", "section", "article", "header", "footer"
        ]
        for tag in list(soup.find_all(candidate_tags)):
            visible_text = tag.get_text(" ", strip=True)
            normalized = re.sub(r"\s+", "", visible_text)
            if UPDATE_ONLY_TEXT_PAT.fullmatch(normalized):
                tag.decompose()
        return str(soup)
    except Exception:
        return html_content

def protect_table_intro_blocks(html_content: str) -> str:
    """DOMを壊さず、テーブル導入文保護のための前処理フック。"""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        return str(soup)
    except Exception:
        return html_content


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
        5. remove_forbidden_internal_text_anywhere
        6. protect_table_intro_blocks
        7. fix_data_table_headers
        8. enrich_iframe_titles
        9. convert_layout_tables_to_div（フラグ依存）

    Returns:
        (cleaned_html, meta_dict)
    """
    meta = {
        "tables_before": 0,
        "tables_after": 0,
        "layout_converted": 0,
        "table_count": 0,
        "header_fixed_count": 0,
        "row_header_fixed_count": 0,
        "orient_col_fixed_count": 0,
        "orient_row_fixed_count": 0,
    }

    h = html
    h = drop_forbidden_tags(h)
    h = remove_deprecated_and_nonstandard_attrs(h)
    h = strip_px_sizes_from_style_attr(h)
    h = remove_fileinfo_anywhere_text(h)
    h = remove_update_only_nodes(h)

    logger.debug("pre_clean_before_remove_internal_head=%s", h[:400].replace("\n", "\\n"))
    h = remove_forbidden_internal_text_anywhere(h)
    logger.debug("pre_clean_after_remove_internal_head=%s", h[:400].replace("\n", "\\n"))
    h = protect_table_intro_blocks(h)

    h, table_meta = fix_data_table_headers(h, log=True)
    meta.update(table_meta)

    if FEATURE_IFRAME_TITLE_ENRICH:
        h = enrich_iframe_titles(
            h,
            base_url=base_url,
            log=FEATURE_IFRAME_TITLE_LOG,
        )

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
