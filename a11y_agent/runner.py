# ==============================================================================
# runner.py — メインループ（エントリーポイント）
# ==============================================================================

import time
import requests
from collections import defaultdict

import gspread
from google.colab import userdata
from google import genai
from bs4 import BeautifulSoup

from config import (
    TOOL_VERSION,
    MODEL_ID,
    MASTER_SHEET_ID,
    MAX_CHUNK_CHARS,
    CONVERT_LAYOUT_TABLES_TO_DIV,
    IFRAME_TITLE_FETCH_CAP_PER_PAGE,
    VISION_ON_TARGET_ALL_IMGS,
    VISION_CAP_PER_PAGE,
    TRIM_AFTER_MENU_PAGETOP,
    DROP_COMMON_SELECTORS,
    ENABLE_BLOCK_LEVEL_END_TRIM,
    MIN_LLM_OUTPUT_CHARS,
    COST_PER_1M_TOKENS_JPY,
    SLEEP_BETWEEN_BLOCKS,
    SLEEP_BETWEEN_VISION_CALLS,
)
from utils import now_jst, guess_mime_from_url
from extractor import robust_extract_xpath_first
from chunker import structural_chunk
from cleaners import (
    pre_clean,
    absolutize_paths,
    convert_layout_tables_to_div_preserve_dom,
    chunk_has_data_table_like,
)
from trim_common import (
    drop_common_blocks_by_selectors,
    trim_after_menu_pagetop,
    extract_text_for_block,
    is_end_trim_trigger,
    is_noise_block,
)
from llm_text import call_llm, prompt_tables, prompt_text_normalize, needs_text_normalize
from vision_alt import (
    collect_images_for_vision,
    generate_alt_with_vision,
    apply_alt_results,
)
from io_sheets import (
    authenticate,
    open_sheet_strict,
    read_pending_rows,
    write_result,
    save_to_drive,
)


# ==============================================================================
# ログ関数
# ==============================================================================

def print_block_log(block_no, total_tokens, step_tokens, step_calls, extra_msg=""):
    """ブロック処理のログ出力"""
    parts = []
    for k in ["tables", "text_normalize"]:
        if step_calls.get(k, 0) > 0:
            parts.append(f"{k}=tokens:{step_tokens[k]},calls:{step_calls[k]}")
    msg = " / ".join(parts) if parts else "no_calls"
    if extra_msg:
        msg = f"{msg} / {extra_msg}"
    print(f"    🧾 block={block_no} total_tokens={total_tokens} | {msg}")


def print_startup_info():
    """起動時の設定情報ログ"""
    print(f"🚀 {TOOL_VERSION} 起動")
    print(
        "ℹ️ シート: A=自治体 B=URL C=ファイル名 D=XPath E=ステータス"
        " F=開始 G=完了 H=総tokens I=円 J=Ver K=Vision L=VisionTokens M=VisionCalls"
    )
    print(f"ℹ️ chunk: MAX_CHUNK_CHARS={MAX_CHUNK_CHARS}")
    print(
        f"ℹ️ layout table->div: {'ON' if CONVERT_LAYOUT_TABLES_TO_DIV else 'OFF'}"
    )
    print(f"ℹ️ iframe title fetch cap: {IFRAME_TITLE_FETCH_CAP_PER_PAGE}")
    print(f"ℹ️ vision: K=ON -> ALL_IMGS cap={VISION_CAP_PER_PAGE}")
    print(
        f"ℹ️ end-trim(Menu/PageTop): {'ON' if TRIM_AFTER_MENU_PAGETOP else 'OFF'}"
        f" / drop-common-selectors: {'ON' if DROP_COMMON_SELECTORS else 'OFF'}"
    )
    print(
        f"ℹ️ block-level end trim: {'ON' if ENABLE_BLOCK_LEVEL_END_TRIM else 'OFF'}"
    )


def print_page_summary(
    filename,
    out_path,
    total_tokens,
    jpy_cost,
    page_trim_applied,
    page_trim_reason,
    page_dropped_blocks,
    page_step_tokens,
    page_step_calls,
):
    """ページ処理完了時のサマリーログ"""
    print("\n📊 Step tokens summary (this page, Pass1)")
    for k, v in sorted(page_step_tokens.items(), key=lambda x: x[1], reverse=True):
        if v:
            print(f"  - {k}: {v}")
    print("\n📞 Step call count summary (this page, Pass1)")
    for k, v in sorted(page_step_calls.items(), key=lambda x: x[1], reverse=True):
        if v:
            print(f"  - {k}: {v} calls")
    print("\n📄 Page Processing Summary:")
    print(f"  - Trim Applied: {page_trim_applied}")
    print(f"  - Trim Reason: {page_trim_reason or 'N/A'}")
    print(f"  - Dropped Blocks: {page_dropped_blocks}")
    print(f"\n✅ 成功: {filename}")
    print(f"   - 保存: {out_path}")
    print(f"   - トークン(total): {total_tokens} / コスト: ¥{jpy_cost}")


# ==============================================================================
# 1ページ処理
# ==============================================================================

def process_page(row: dict, client, vision_cache: dict) -> dict:
    """
    1ページ分の処理パイプライン。

    Args:
        row: read_pending_rowsが返す辞書
        client: genai.Client (Gemini APIクライアント)
        vision_cache: Vision結果キャッシュ {src -> alt_text}

    Returns:
        結果辞書
    """
    url = row["url"]
    xpath = row["xpath"]
    municipality = row["municipality"]
    filename = row["filename"]
    vision_flag = row["vision_flag"]

    page_dropped_blocks = 0
    page_trim_applied = False
    page_trim_reason = None

    start = now_jst()

    # ------------------------------------------------------------------
    # Step 2: 抽出
    # ------------------------------------------------------------------
    extracted_html, (method, method_detail), full_html = robust_extract_xpath_first(
        url, xpath
    )

    # ------------------------------------------------------------------
    # Step 3: チャンク分割
    # ------------------------------------------------------------------
    chunks = structural_chunk(extracted_html, MAX_CHUNK_CHARS)

    print(f"  ✅ 抽出方式: {method} / {method_detail}")
    print(f"  📦 分割: {len(chunks)} ブロック")
    print(f"  🎨 Vision alt: {'ON' if vision_flag else 'OFF'} (K列)")

    page_step_tokens = defaultdict(int)
    page_step_calls = defaultdict(int)
    final_blocks = []

    # ------------------------------------------------------------------
    # Step 4-9: ブロック単位処理
    # ------------------------------------------------------------------
    for b, raw_ch in enumerate(chunks, start=1):
        if page_trim_applied:
            page_dropped_blocks += 1
            continue

        raw_len = len(raw_ch)
        raw_text = extract_text_for_block(raw_ch)

        # Step 4a: ブロック段階の終端カット
        if ENABLE_BLOCK_LEVEL_END_TRIM and is_end_trim_trigger(raw_text):
            page_trim_applied = True
            page_trim_reason = f"end_trim_trigger(block={b})"
            dropped = len(chunks) - b + 1
            page_dropped_blocks += dropped
            print(
                f"  ✂️ end-trim triggered at block {b}:"
                f" reason={page_trim_reason} dropped_blocks={dropped}"
            )
            break

        # Step 4b: ノイズブロック判定
        if is_noise_block(raw_text):
            page_dropped_blocks += 1
            print(
                f"  🗑️ noise block skipped: block={b}"
                f" raw_len={raw_len} text='{raw_text[:60]}'"
            )
            continue

        block_tokens = 0
        step_tokens = defaultdict(int)
        step_calls = defaultdict(int)

        # Step 5: pre_clean（layout table→div含む）
        ch, meta1 = pre_clean(raw_ch, base_url=url, do_layout_table_convert=True)
        pre_len = len(ch)

        # Step 6a: データtable LLM修正
        table_fix = False
        try:
            if "<table" in ch and chunk_has_data_table_like(ch):
                out, tok = call_llm(client, prompt_tables(ch))
                step_tokens["tables"] += tok
                step_calls["tables"] += 1
                block_tokens += tok
                if out and len(out) >= MIN_LLM_OUTPUT_CHARS:
                    ch = out
                    table_fix = True
        except Exception as ex:
            print(f"    ⚠️ LLM(tables) exception block={b}: {str(ex)[:140]}")

        # Step 6b: 表記正規化
        text_norm = False
        try:
            if needs_text_normalize(ch):
                out, tok = call_llm(client, prompt_text_normalize(ch))
                step_tokens["text_normalize"] += tok
                step_calls["text_normalize"] += 1
                block_tokens += tok
                if out and len(out) >= MIN_LLM_OUTPUT_CHARS:
                    ch = out
                    text_norm = True
        except Exception as ex:
            print(
                f"    ⚠️ LLM(text_normalize) exception block={b}: {str(ex)[:140]}"
            )

        # Step 7: LLM後 再クリーニング
        ch, meta2 = pre_clean(ch, base_url=url, do_layout_table_convert=False)
        post_len = len(ch)

        # Step 8: 空ブロック破棄
        if not ch or len(ch.strip()) < 20:
            page_dropped_blocks += 1
            if raw_len < 50:
                print(f"  ⚠️ empty-ish -> skipped (raw_len<50): block={b}")
            else:
                print(
                    f"  ⚠️ empty-ish -> skipped (no raw fallback):"
                    f" block={b} raw_len={raw_len}"
                )
            continue

        # Step 9: 積み上げ
        final_blocks.append(ch)

        extra = (
            f"raw_len={raw_len},pre_len={pre_len},post_len={post_len},"
            f"tables_before={meta1.get('tables_before', 0)},"
            f"layout_conv={meta1.get('layout_converted', 0)},"
            f"table_fix={'1' if table_fix else '0'},"
            f"text_norm={'1' if text_norm else '0'}"
        )
        print(f"  ◽️ ブロック {b}/{len(chunks)} 変換中...")
        print_block_log(b, block_tokens, step_tokens, step_calls, extra_msg=extra)

        for k, v in step_tokens.items():
            page_step_tokens[k] += v
        for k, v in step_calls.items():
            page_step_calls[k] += v

        time.sleep(SLEEP_BETWEEN_BLOCKS)

    # ------------------------------------------------------------------
    # Step 10: 結合（marker無し）
    # ------------------------------------------------------------------
    final_html = "".join(final_blocks)

    # ------------------------------------------------------------------
    # Step 11: post-merge layout table→div（保険）
    # ------------------------------------------------------------------
    if CONVERT_LAYOUT_TABLES_TO_DIV and "<table" in final_html:
        before = len(BeautifulSoup(final_html, "html.parser").find_all("table"))
        final_html, tb, ta, conv = convert_layout_tables_to_div_preserve_dom(
            final_html
        )
        after = len(BeautifulSoup(final_html, "html.parser").find_all("table"))
        print(
            f"  🧩 Layout table->div post-merge:"
            f" tables_before={before}, tables_after={after}, converted={conv}"
        )

    # ------------------------------------------------------------------
    # Step 12: 絶対パス化
    # ------------------------------------------------------------------
    final_html = absolutize_paths(final_html, url)

    # ------------------------------------------------------------------
    # Step 13: 最終クリーニング
    # ------------------------------------------------------------------
    final_html, _ = pre_clean(final_html, base_url=url, do_layout_table_convert=False)

    # ------------------------------------------------------------------
    # Step 14: 共通部品セレクタ削除（安全弁）
    # ------------------------------------------------------------------
    if DROP_COMMON_SELECTORS:
        final_html = drop_common_blocks_by_selectors(final_html)

    # ------------------------------------------------------------------
    # Step 15: Menu/PageTop 境界カット
    # ------------------------------------------------------------------
    if TRIM_AFTER_MENU_PAGETOP and not page_trim_applied:
        final_html, trimmed = trim_after_menu_pagetop(final_html)
        if trimmed:
            page_trim_applied = True
            page_trim_reason = "menu_pagetop_trim"

    # ------------------------------------------------------------------
    # Step 16: Vision（K列がONのとき）
    # ------------------------------------------------------------------
    vision_tokens = 0
    vision_calls = 0
    vision_cache_hits = 0

    if vision_flag:
        soup_chk = BeautifulSoup(final_html, "html.parser")
        img_count_extracted = len(soup_chk.find_all("img"))

        candidates = (
            collect_images_for_vision(final_html, url)
            if VISION_ON_TARGET_ALL_IMGS
            else []
        )
        targets = candidates[:VISION_CAP_PER_PAGE]
        failures = []
        alt_map = {}

        print(
            f"  🎨 Vision check:"
            f" extracted_img_count={img_count_extracted},"
            f" candidates={len(candidates)}, targets={len(targets)}"
        )
        for t in targets[:5]:
            print(
                f"     - target img#{t['img_index']}"
                f" reason={t.get('reason', '')}"
                f" old_alt={t.get('old_alt', '')[:60]}"
            )

        for t in targets:
            src = t["src"]
            ctx = t["context"]
            try:
                if src in vision_cache:
                    alt_text = vision_cache[src]
                    tok = 0
                    vision_cache_hits += 1
                else:
                    ir = requests.get(
                        src, timeout=20, headers={"User-Agent": "Mozilla/5.0"}
                    )
                    ir.raise_for_status()
                    mime = guess_mime_from_url(src)
                    alt_text, tok = generate_alt_with_vision(
                        client, ir.content, mime, ctx
                    )
                    vision_cache[src] = alt_text
                    vision_calls += 1

                vision_tokens += tok
                alt_map[t["img_index"]] = {"alt": alt_text}
            except Exception as ex:
                failures.append(f"{src} ({str(ex)[:80]})")

            time.sleep(SLEEP_BETWEEN_VISION_CALLS)

        if alt_map:
            final_html = apply_alt_results(final_html, alt_map)

        # Vision後の最終クリーニング + 安全弁
        final_html, _ = pre_clean(
            final_html, base_url=url, do_layout_table_convert=False
        )
        if DROP_COMMON_SELECTORS:
            final_html = drop_common_blocks_by_selectors(final_html)

        # 既にtrim済みなら再trimしない
        if TRIM_AFTER_MENU_PAGETOP and not page_trim_applied:
            final_html, trimmed2 = trim_after_menu_pagetop(final_html)
            if trimmed2:
                page_trim_applied = True
                page_trim_reason = page_trim_reason or "menu_pagetop_trim_post_vision"

        print(
            f"  🎨 Vision alt summary:"
            f" api_calls={vision_calls}, tokens={vision_tokens},"
            f" cache_hits={vision_cache_hits}"
        )
        if failures:
            print(f"  🎨 Vision failures: {len(failures)}")
            for fmsg in failures[:5]:
                print(f"     - {fmsg}")
    else:
        print("  🎨 Vision alt summary: OFF")

    # ------------------------------------------------------------------
    # Step 17: Drive保存
    # ------------------------------------------------------------------
    out_path = save_to_drive(final_html, municipality, filename)

    # ------------------------------------------------------------------
    # 結果集計
    # ------------------------------------------------------------------
    pass1_tokens = sum(page_step_tokens.values())
    total_tokens = pass1_tokens + vision_tokens
    jpy_cost = round((total_tokens / 1_000_000) * COST_PER_1M_TOKENS_JPY, 2)
    end = now_jst()

    # ログ
    print_page_summary(
        filename,
        out_path,
        total_tokens,
        jpy_cost,
        page_trim_applied,
        page_trim_reason,
        page_dropped_blocks,
        page_step_tokens,
        page_step_calls,
    )

    return {
        "start": start,
        "end": end,
        "total_tokens": total_tokens,
        "jpy_cost": jpy_cost,
        "vision_tokens": vision_tokens,
        "vision_calls": vision_calls,
        "page_trim_applied": page_trim_applied,
        "page_trim_reason": page_trim_reason,
        "page_dropped_blocks": page_dropped_blocks,
        "page_step_tokens": dict(page_step_tokens),
        "page_step_calls": dict(page_step_calls),
        "out_path": out_path,
    }


# ==============================================================================
# main
# ==============================================================================

def main():
    """エントリーポイント"""

    # Step 1: 認証
    creds, authed_email = authenticate()
    print(f"✅ 認証アカウント: {authed_email}")

    gc = gspread.authorize(creds)
    sh = open_sheet_strict(gc, MASTER_SHEET_ID, authed_email)
    ws = sh.get_worksheet(0)

    client = genai.Client(api_key=userdata.get("GEMINI_API_KEY"))

    print_startup_info()

    # Step 1b: 未完了行取得
    pending = read_pending_rows(ws)
    print(f"📋 未完了ページ: {len(pending)} 件")

    vision_cache = {}

    for row in pending:
        print(f"\n🔄 処理開始: {row['municipality']} ({row['url']})")

        try:
            result = process_page(row, client, vision_cache)

            # Step 18: シートへ結果書き戻し
            write_result(
                ws,
                sheet_row=row["sheet_row"],
                start=result["start"],
                end=result["end"],
                total_tokens=result["total_tokens"],
                jpy_cost=result["jpy_cost"],
                version=TOOL_VERSION,
                vision_tokens=result["vision_tokens"],
                vision_calls=result["vision_calls"],
            )
        except Exception as ex:
            print(f"  ❌ ページ処理エラー: {row['url']}: {str(ex)[:200]}")

        time.sleep(0.5)


if __name__ == "__main__":
    main()
