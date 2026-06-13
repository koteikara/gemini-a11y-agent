#!/usr/bin/env python3
"""Validate the Saga City synthetic regression fixture.

Uses only the Python standard library.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "html" / "saga-city-test"
OLD_HTML = FIXTURE_ROOT / "old" / "sg02395-composite.html"
GOLD_HTML = FIXTURE_ROOT / "gold" / "sg02395-composite.html"
MANIFEST = FIXTURE_ROOT / "manifest.json"
INTRO_TEXTS = [
    "休日（日曜日または祝日）在宅当番医について",
    "日曜・祝日在宅当番医情報",
    "診療時間",
]
GOLD_PATTERNS = ["<thead", 'scope="col"', 'scope="row"', "<caption"]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    for path in (OLD_HTML, GOLD_HTML, MANIFEST):
        if not path.exists():
            errors.append(f"missing required file: {path}")

    if errors:
        for error in errors:
            print(f"[ERROR] {error}")
        return 1

    old_html = read(OLD_HTML)
    gold_html = read(GOLD_HTML)
    manifest = json.loads(read(MANIFEST))

    combined_html = old_html + "\n" + gold_html
    for case in manifest.get("cases", []):
        case_id = case.get("id")
        if not case_id:
            errors.append("manifest case is missing id")
            continue
        if f"case: {case_id}" not in combined_html:
            required_texts = case.get("required_texts", [])
            expected_patterns = case.get("expected_gold_patterns", [])
            markers = required_texts + expected_patterns + case.get("old_contains", [])
            if not any(marker in combined_html for marker in markers):
                warnings.append(f"manifest case has no matching comment or content marker: {case_id}")

    if "更新：" not in old_html:
        errors.append("old composite does not contain 更新：")
    if "更新：" in gold_html:
        errors.append("gold composite contains 更新：")

    lower_gold = gold_html.lower()
    for pattern in GOLD_PATTERNS:
        if pattern.lower() not in lower_gold:
            errors.append(f"gold composite missing required pattern: {pattern}")

    for text in INTRO_TEXTS:
        if text not in old_html:
            errors.append(f"old composite missing intro text: {text}")
        if text not in gold_html:
            errors.append(f"gold composite missing intro text: {text}")

    for warning_name in manifest.get("known_warnings", []):
        if warning_name == "rgb_fullwidth" and "rgb（" in combined_html:
            warnings.append("known warning marker present: rgb_fullwidth")
        if warning_name in {"caption_id_duplicates", "caption_id_prefix"} and 'id="caption' in combined_html:
            warnings.append(f"known warning marker present: {warning_name}")

    for warning in warnings:
        print(f"[WARNING] {warning}")
    for error in errors:
        print(f"[ERROR] {error}")

    if errors:
        print("status: FAIL")
        return 1
    print("status: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
