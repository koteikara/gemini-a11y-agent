#!/usr/bin/env python3
"""Run the Saga City synthetic fixture through the current v1.0 HTML flow."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from textwrap import shorten

DEFAULT_INPUT = Path("tests/fixtures/html/saga-city-test/old/sg02395-composite.html")
DEFAULT_OUTPUT = Path("tests/fixtures/html/saga-city-test/ai-v1.0/sg02395-composite.html")
DEFAULT_BASE_URL = "https://www.city.saga.lg.jp/"
GEMINI_REQUIRED_MESSAGE = (
    "Gemini API を使う処理が必要です。通常のColab実行環境またはAPIキー設定済み環境で実行してください。"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate ai-v1.0 output for the Saga City synthetic composite fixture."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help=f"input HTML (default: {DEFAULT_INPUT})")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help=f"output HTML (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--dry-run", action="store_true", help="print a preview and validation summary without writing output")
    parser.add_argument("--overwrite", action="store_true", help="allow replacing an existing output file")
    return parser.parse_args()


def build_client():
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(GEMINI_REQUIRED_MESSAGE)
    try:
        from google import genai
    except Exception as exc:  # pragma: no cover - depends on local runtime
        raise RuntimeError(f"{GEMINI_REQUIRED_MESSAGE} (google-genai import failed: {exc})") from exc
    return genai.Client(api_key=api_key)


def run_check(command: list[str]) -> tuple[int, str]:
    proc = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return proc.returncode, proc.stdout.strip()


def print_validation_summary(output_path: Path) -> None:
    checks = [
        [sys.executable, "tools/check_saga_city_test_fixture.py"],
        [
            sys.executable,
            "tools/compare_saga_city_versions.py",
            "--fixture-root",
            "tests/fixtures/html/saga-city-test",
            "--case",
            output_path.stem,
        ],
    ]
    for command in checks:
        code, out = run_check(command)
        status = "OK" if code == 0 else "WARN"
        print(f"[{status}] {' '.join(command)}")
        if out:
            print(out)


def main() -> int:
    args = parse_args()
    if not args.input.exists():
        print(f"入力ファイルが見つかりません: {args.input}", file=sys.stderr)
        return 2
    if args.output.exists() and not args.overwrite and not args.dry_run:
        print(f"出力ファイルが既に存在します。上書きする場合は --overwrite を指定してください: {args.output}", file=sys.stderr)
        return 2

    try:
        client = build_client()
        from a11y_agent.runner import process_extracted_html
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"{GEMINI_REQUIRED_MESSAGE} ({exc})", file=sys.stderr)
        return 1

    source_html = args.input.read_text(encoding="utf-8")
    result = process_extracted_html(source_html, client, base_url=DEFAULT_BASE_URL, sleep_between_blocks=False)
    output_html = result["html"]

    print("\n=== v1.0 fixture processing summary ===")
    print(f"input: {args.input}")
    print(f"output: {args.output}")
    print(f"chunks: {result.get('chunk_count', 0)}")
    print(f"tokens: {result.get('total_tokens', 0)}")
    print(f"step_calls: {result.get('page_step_calls', {})}")
    print(f"trim_applied: {result.get('page_trim_applied')} reason={result.get('page_trim_reason') or '-'}")

    if args.dry_run:
        print("\n=== dry-run preview ===")
        print(shorten(output_html.replace("\n", " "), width=600, placeholder=" ..."))
        print("\n(dry-run: 出力ファイルは書き込んでいません)")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output_html, encoding="utf-8")
    print(f"書き込み完了: {args.output}")
    print_validation_summary(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
