# ==============================================================================
# config.py — 全定数・設定値（一元管理）
# ==============================================================================

import datetime
import re

# === ツール情報 ===
TOOL_VERSION = "Ver 35.0-minpatch+AltFixPatch (patched v22 end-trim + cleanup-fixes)"
BUILD_ID = "v22.1"
MODEL_ID = "gemini-2.0-flash"

# === シート・Drive ===
MASTER_SHEET_ID = "1jA-tsRQxlbZa1_2vzIG5K55rpMR13uv6svjUtuVFcY0"
OUTPUT_PARENT_PATH = (
    "/content/drive/Shareddrives/【SV・ND】共有プロジェクト（自治体）"
    "/00_データ交換用/データ移行_アクセシビリティAI対応プロジェクト"
    "/Gemini-A11y Agent/HTML出力"
)

# === 時刻・コスト ===
JST = datetime.timezone(datetime.timedelta(hours=9))
COST_PER_1M_TOKENS_JPY = 50

# === 分割 ===
MAX_CHUNK_CHARS = 8000

# === Vision ===
VISION_ON_TARGET_ALL_IMGS = True
VISION_CAP_PER_PAGE = 50

# === Feature Flags（修正範囲） ===
FEATURE_IFRAME_TITLE_ENRICH = True
FEATURE_IFRAME_YT_OEMBED = True
FEATURE_IFRAME_TITLE_GENERIC_FIX = True
FEATURE_IFRAME_TITLE_LOG = True

# === iframe ===
IFRAME_TITLE_FETCH_CAP_PER_PAGE = 10
IFRAME_TITLE_FETCH_TIMEOUT = 12  # seconds

# === レイアウトtable ===
CONVERT_LAYOUT_TABLES_TO_DIV = True

# === LLMフォールバック ===
MIN_LLM_OUTPUT_CHARS = 50

# === 待機 ===
SLEEP_BETWEEN_BLOCKS = 0.15
SLEEP_BETWEEN_VISION_CALLS = 0.2

# === 実行フラグ ===
TRIM_AFTER_MENU_PAGETOP = True
DROP_COMMON_SELECTORS = True
ENABLE_BLOCK_LEVEL_END_TRIM = True

# === 未知タグの暫定除去 ===
FORBIDDEN_TAGS = {"graphic", "graphics", "figurecaption"}

# === 非推奨/非標準属性のまとめ削除（タグ別） ===
DROP_ATTRS_BY_TAG = {
    "table": {
        "border", "cellpadding", "cellspacing",
        "width", "height", "align", "bgcolor", "valign",
        "rules", "frame", "summary",
    },
    "tr": {"align", "valign", "bgcolor", "height", "width"},
    "th": {"align", "valign", "bgcolor", "width", "height", "nowrap"},
    "td": {"align", "valign", "bgcolor", "width", "height", "nowrap"},
    "img": {"border", "hspace", "vspace", "align", "width", "height"},
    "a": {"size", "type"},
}

# === iframeホワイトリスト ===
IFRAME_ALLOWED_ATTRS = {
    "src", "title", "name",
    "width", "height",
    "loading", "referrerpolicy",
    "allow", "allowfullscreen",
    "sandbox",
    "scrolling",
    "style", "class", "id",
    "aria-label", "aria-labelledby", "aria-describedby",
}

# === ファイルリンク判定用拡張子 ===
FILE_EXTS = (
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".ppt", ".pptx", ".zip", ".csv",
)
