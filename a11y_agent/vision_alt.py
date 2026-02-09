# ==============================================================================
# vision_alt.py — Vision alt生成
# ==============================================================================

import re
import requests
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .config import MODEL_ID


def sanitize_alt(alt: str) -> str:
    """alt文字列の正規化（括弧除去・句点整形等）"""
    s = (alt or "").strip().strip('"').strip("'")
    s = re.sub(r"\s+", " ", s)

    # 括弧は禁止
    s = s.replace("（", "").replace("）", "").replace("(", "").replace(")", "")

    # 終端の「写真/図/表/グラフ」単独は落とす
    s = re.sub(r"(写真|イラスト|図|表|グラフ)\s*$',", "", s).strip()

    # 「。の写真。」整形
    s = s.replace("。の写真。", "の写真。")

    if s and not s.endswith("。"):
        s += "。"
    s = re.sub(r"。。+", "。", s).strip()
    s = s.lstrip("。").strip()
    if s and not s.endswith("。"):
        s += "。"
    s = re.sub(r"。。+", "。", s).strip()
    return s


def collect_images_for_vision(html: str, base_url: str) -> list:
    """
    Vision対象画像を収集。

    Returns:
        [{"img_index": int, "src": str, "context": str,
          "old_alt": str, "reason": str}, ...]
    """
    soup = BeautifulSoup(html, "html.parser")
    targets = []
    for idx, img in enumerate(soup.find_all("img"), start=1):
        src = img.get("src")
        if not src:
            continue
        abs_src = urljoin(base_url, src)
        alt = (img.get("alt") or "").strip()
        ctx = img.parent.get_text(" ", strip=True)[:250] if img.parent else ""
        targets.append(
            {
                "img_index": idx,
                "src": abs_src,
                "context": ctx,
                "old_alt": alt,
                "reason": "vision_on_all",
            }
        )
    return targets


def generate_alt_with_vision(
    client,
    image_bytes: bytes,
    mime: str,
    context_text: str,
):
    """
    Gemini Visionでalt生成。

    Args:
        client: genai.Client
        image_bytes: 画像バイナリ
        mime: MIMEタイプ
        context_text: 周辺文脈テキスト

    Returns:
        (alt_text, total_tokens)
    """
    prompt = f"""
あなたは自治体サイトのアクセシビリティ担当です。
次の画像の代替テキスト（alt）を日本語で作成してください。

条件：
- 200文字未満
- 画像内にテキストがある場合、その文字を必ず含める
- 推測で断定しない
- 括弧（）は使わない
- 可能なら「〜の写真。…」の形式にする
- 出力は alt 文字列のみ（余計な説明禁止）

周辺文脈：
{context_text}
""".strip()

    res = client.models.generate_content(
        model=MODEL_ID,
        contents=[
            {
                "role": "user",
                "parts": [
                    {"inline_data": {"mime_type": mime, "data": image_bytes}},
                    {"text": prompt},
                ],
            }
        ],
        config={"temperature": 0.1},
    )
    alt = sanitize_alt((res.text or "").strip())
    usage = getattr(res, "usage_metadata", None)
    tokens = (
        usage.total_token_count
        if usage and hasattr(usage, "total_token_count")
        else 0
    )
    return alt, tokens


def apply_alt_results(html: str, alt_map: dict) -> str:
    """
    alt_map = {img_index: {"alt": str}} をHTMLに適用。
    """
    soup = BeautifulSoup(html, "html.parser")
    imgs = soup.find_all("img")
    for idx, img in enumerate(imgs, start=1):
        if idx in alt_map:
            img["alt"] = alt_map[idx]["alt"]
    return str(soup)
