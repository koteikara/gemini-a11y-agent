# ==============================================================================
# llm_text.py — LLM呼び出し（table修正・表記正規化）
# ==============================================================================

import re
from bs4 import BeautifulSoup

from .config import MODEL_ID


def call_llm(client, prompt: str, temperature: float = 0.1):
    """
    Gemini APIにプロンプトを送信。

    Args:
        client: genai.Client
        prompt: プロンプト文字列
        temperature: 生成温度

    Returns:
        (response_text, total_tokens)
        response_textは```htmlフェンス除去済み
    """
    res = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config={"temperature": temperature},
    )
    text = (res.text or "").replace("```html", "").replace("```", "").strip()
    usage = getattr(res, "usage_metadata", None)
    tokens = (
        usage.total_token_count
        if usage and hasattr(usage, "total_token_count")
        else 0
    )
    return text, tokens


def prompt_tables(html: str) -> str:
    """データtableのアクセシビリティ修正プロンプトを生成"""
    return f"""
あなたは自治体サイトのHTMLアクセシビリティ修正担当です。
次の厳格ルールで修正してください。
- 入力HTMLから要素を削除してはいけない
- table要素以外（h/p/div等）は1文字たりとも変更してはいけない
- 修正対象は table要素のアクセシビリティ関連のみ（caption/thead/th/scope など）
- セル文言（テキスト）を変えない
- タグ名・属性名を創作しない（既存HTMLの範囲で修正）
- <row>、</row>、<cell>、</cell> はHTML標準タグではないため絶対に使用しない
- 行は <tr>、セルは <td> または <th> を使用する
- 壊れた閉じタグやエスケープされたHTML断片を出力しない
- 判断に迷う場合は、元のtable構造を大きく変更しない
- 入力HTML全体を、同じ順序・同じ要素構成で返す（tableだけ返すのは禁止）
修正後のHTMLのみを出力（Markdown不可）。

{html}
"""


def prompt_text_normalize(html: str) -> str:
    """表記正規化プロンプトを生成"""
    return f"""
あなたは自治体サイトのHTMLアクセシビリティ修正担当です。
表記正規化のみを行ってください。
- 日付/曜日/時間
- 通貨/単位記号の日本語化
- 不要スペース・装飾記号の整理
- タグ名・属性名を創作しない（既存HTMLの範囲で修正）
意味は変えない
修正後のHTMLのみを出力（Markdown不可）。

{html}
"""


def needs_text_normalize(html: str) -> bool:
    """表記正規化が必要か判定（パターンマッチ）"""
    t = BeautifulSoup(html, "html.parser").get_text(" ", strip=False)
    patterns = [
        r"\b\d{1,2}:\d{2}\b",
        r"\b\d{1,4}/\d{1,2}/\d{1,2}\b",
        r"（[日月火水木金土]）",
        r"[¥$]",
        r"[㎡㎝㎜㎞]",
        r"[０-９Ａ-Ｚａ-ｚ]",
        r"(日　時|年　月|月　日|受　付|場　所)",
        r"（R\d{1,2}\.\d{1,2}\.\d{1,2}）",
        r"(PDF|ＰＤＦ)\s*(ファイル)?\s*[:：]",
    ]
    return any(re.search(p, t) for p in patterns)
