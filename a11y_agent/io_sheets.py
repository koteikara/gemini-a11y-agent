# ==============================================================================
# io_sheets.py — スプレッドシート読み書き・Drive保存・認証
# ==============================================================================

import os

import gspread
from gspread.exceptions import SpreadsheetNotFound, APIError
from google.colab import auth, drive
from google.auth import default

from config import OUTPUT_PARENT_PATH, TOOL_VERSION
from utils import safe_strip


# ==============================================================================
# 認証
# ==============================================================================

def authenticate():
    """
    Colab認証 + Drive mount + creds取得。

    Returns:
        (creds, authed_email: str)
    """
    auth.authenticate_user()
    creds, _ = default()
    drive.mount("/content/drive")

    authed_email = getattr(creds, "service_account_email", None)
    if not authed_email:
        try:
            authed_email = creds._service_account_email
        except Exception:
            authed_email = "unknown"

    return creds, authed_email


# ==============================================================================
# シートオープン
# ==============================================================================

def open_sheet_strict(gc, sheet_id: str, authed_email: str):
    """
    シートを開く。404時は原因候補を含むRuntimeError。
    """
    try:
        return gc.open_by_key(sheet_id)
    except SpreadsheetNotFound as e:
        raise RuntimeError(
            "SpreadsheetNotFound(404): gspread からシートが見えません。\n"
            f"- MASTER_SHEET_ID: {sheet_id}\n"
            f"- 認証アカウント: {authed_email}\n\n"
            "原因候補：\n"
            "1) MASTER_SHEET_ID が誤り（スプレッドシートURLの /d/<...>/ を再確認）\n"
            "2) 上記の認証アカウントにシートが共有されていない（閲覧権限以上で共有）\n"
        ) from e
    except APIError as e:
        raise RuntimeError(f"gspread APIError: {e}") from e


# ==============================================================================
# 行の読み込み
# ==============================================================================

def read_pending_rows(ws) -> list:
    """
    未完了行を辞書リストで返す。

    列マッピング:
        A=自治体名, B=URL, C=ファイル名, D=XPath, E=ステータス,
        F=開始, G=完了, H=総tokens, I=コスト, J=バージョン,
        K=Vision ON/OFF, L=VisionTokens, M=VisionCalls

    Returns:
        [{"row_index": int,         # 0-based（rows配列内のindex）
          "sheet_row": int,          # シート上の行番号（ヘッダ+1 なので idx0+2）
          "municipality": str,
          "url": str,
          "filename": str,
          "xpath": str,
          "status": str,
          "vision_flag": bool}, ...]
    """
    all_values = ws.get_all_values()
    rows = all_values[1:]  # ヘッダ行を除く

    pending = []
    for idx0, row in enumerate(rows):
        r = row + [""] * (13 - len(row))  # M列まで確保

        municipality = safe_strip(r[0])
        url = safe_strip(r[1])
        filename = safe_strip(r[2])
        xpath = safe_strip(r[3])
        status = safe_strip(r[4])
        vision_flag = safe_strip(r[10]).upper() == "ON"

        if not url:
            continue
        if status.startswith("完了"):
            continue

        pending.append(
            {
                "row_index": idx0,
                "sheet_row": idx0 + 2,  # ヘッダ行=1 なので +2
                "municipality": municipality,
                "url": url,
                "filename": filename or f"output_{idx0 + 2}.html",
                "xpath": xpath,
                "status": status,
                "vision_flag": vision_flag,
            }
        )

    return pending


# ==============================================================================
# 結果書き戻し
# ==============================================================================

def write_result(
    ws,
    sheet_row: int,
    start: str,
    end: str,
    total_tokens: int,
    jpy_cost: float,
    version: str,
    vision_tokens: int,
    vision_calls: int,
) -> None:
    """
    結果をシートに書き戻し（E〜J列 + L〜M列）。
    """
    ws.update(
        range_name=f"E{sheet_row}:J{sheet_row}",
        values=[
            [
                "完了",
                start,
                end,
                total_tokens,
                f"¥{jpy_cost}",
                version,
            ]
        ],
    )
    ws.update(
        range_name=f"L{sheet_row}:M{sheet_row}",
        values=[[vision_tokens, vision_calls]],
    )


# ==============================================================================
# Drive保存
# ==============================================================================

def save_to_drive(html_content: str, municipality: str, filename: str) -> str:
    """
    HTMLをDriveに保存。

    Returns:
        出力パス文字列
    """
    target_dir = f"{OUTPUT_PARENT_PATH}/{municipality}"
    os.makedirs(target_dir, exist_ok=True)
    out_path = f"{target_dir}/{filename}"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    return out_path
