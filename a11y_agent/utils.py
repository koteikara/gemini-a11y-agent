# ==============================================================================
# utils.py — 汎用ユーティリティ（ドメインロジックなし）
# ==============================================================================

import datetime
from config import JST


def now_jst() -> str:
    """JST現在時刻を 'YYYY-MM-DD HH:MM:SS' で返す"""
    return datetime.datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")


def safe_strip(x) -> str:
    """None安全な strip"""
    return (x or "").strip()


def guess_mime_from_url(url: str) -> str:
    """URL末尾から画像MIMEを推定（デフォルト: image/jpeg）"""
    u = url.lower()
    if u.endswith(".png"):
        return "image/png"
    if u.endswith(".webp"):
        return "image/webp"
    if u.endswith(".gif"):
        return "image/gif"
    return "image/jpeg"
