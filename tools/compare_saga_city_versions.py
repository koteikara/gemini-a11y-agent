#!/usr/bin/env python3
"""Compare Saga City legacy AI, v1.0 AI, and gold HTML fixtures.

This script intentionally uses only the Python standard library and performs
string-based checks. DOM-level regression checks remain the responsibility of
existing regression tools such as regression_check_14256.py.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
SAGA_ROOT = ROOT / "tests" / "fixtures" / "html" / "saga-city"
DEFAULT_PREVIOUS = SAGA_ROOT / "ai-v0"
DEFAULT_CURRENT = SAGA_ROOT / "ai-v1.0"
FALLBACK_CURRENT = SAGA_ROOT / "ai"
DEFAULT_GOLD = SAGA_ROOT / "gold"

CASES = [
    {
        "name": "Saga City 14256",
        "previous": "sg02395_0820.html",
        "current": "sg02395_0820.html",
        "gold": "sg02395.html",
    }
]

TEXT_CHECKS = {
    "intro_text": "休日（日曜日または祝日）在宅当番医について",
    "doctor_info_text": "日曜・祝日在宅当番医情報",
    "consultation_hours_text": "診療時間",
    "update_line": "更新：",
}

COUNT_PATTERNS = {
    "h3_count": "<h3",
    "h4_count": "<h4",
    "table_count": "<table",
    "thead_count": "<thead",
    "caption_count": "<caption",
    "scope_col_count": 'scope="col"',
    "scope_row_count": 'scope="row"',
    "th_count": "<th",
    "rgb_fullwidth": "rgb（",
    "caption_id_count": 'id="caption',
}

COMMON_PARTS = {
    "menu_present": "Menu",
    "pagetop_present": "PageTop",
    "footer_present": "<footer",
}


@dataclass(frozen=True)
class HtmlMetrics:
    exists: bool
    path: Path
    values: dict[str, int | bool]
    duplicate_caption_ids: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare Saga City ai-v0, ai-v1.0, and gold HTML fixtures."
    )
    parser.add_argument("--previous", type=Path, default=DEFAULT_PREVIOUS)
    parser.add_argument("--current", type=Path, default=None)
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLD)
    return parser.parse_args()


def resolve_current_dir(raw_current: Path | None) -> Path:
    if raw_current is not None:
        return raw_current
    if DEFAULT_CURRENT.exists():
        return DEFAULT_CURRENT
    return FALLBACK_CURRENT


def read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def duplicate_caption_id_count(html: str) -> int:
    ids = re.findall(r'id=["\'](caption[^"\']*)["\']', html, flags=re.IGNORECASE)
    counts = Counter(ids)
    return sum(count - 1 for count in counts.values() if count > 1)


def collect_metrics(path: Path) -> HtmlMetrics:
    html = read_text(path)
    if html is None:
        return HtmlMetrics(False, path, {}, 0)

    lower_html = html.lower()
    values: dict[str, int | bool] = {}
    for key, needle in TEXT_CHECKS.items():
        values[key] = needle in html
    for key, needle in COUNT_PATTERNS.items():
        values[key] = lower_html.count(needle.lower())
    for key, needle in COMMON_PARTS.items():
        values[key] = needle.lower() in lower_html
    values["caption_id_duplicates"] = duplicate_caption_id_count(html)
    return HtmlMetrics(True, path, values, int(values["caption_id_duplicates"]))


def closeness(value: int, target: int) -> int:
    return abs(value - target)


def bool_label(value: bool | int) -> str:
    return "OK" if bool(value) else "NG"


def presence_label(value: bool | int) -> str:
    return "YES" if bool(value) else "NO"


def result_text_metric(prev: HtmlMetrics, cur: HtmlMetrics, gold: HtmlMetrics, key: str) -> str:
    cur_v = bool(cur.values.get(key, False))
    gold_v = bool(gold.values.get(key, False))
    if not prev.exists:
        return "matches_gold" if cur_v == gold_v else "differs_from_gold"
    prev_v = bool(prev.values.get(key, False))
    if cur_v == gold_v and prev_v != gold_v:
        return "improved"
    if cur_v != gold_v and prev_v == gold_v:
        return "regressed"
    return "stable" if cur_v == prev_v else "changed"


def result_count_closer(prev: HtmlMetrics, cur: HtmlMetrics, gold: HtmlMetrics, key: str) -> str:
    cur_v = int(cur.values.get(key, 0))
    gold_v = int(gold.values.get(key, 0))
    if not prev.exists:
        return "matches_gold" if cur_v == gold_v else "differs_from_gold"
    prev_v = int(prev.values.get(key, 0))
    cur_dist = closeness(cur_v, gold_v)
    prev_dist = closeness(prev_v, gold_v)
    if cur_dist < prev_dist:
        return "improved"
    if cur_dist > prev_dist:
        return "regressed"
    return "stable"


def result_structure_added(prev: HtmlMetrics, cur: HtmlMetrics, gold: HtmlMetrics, key: str) -> str:
    cur_v = int(cur.values.get(key, 0))
    gold_v = int(gold.values.get(key, 0))
    if not prev.exists:
        return "matches_gold" if cur_v == gold_v else "differs_from_gold"
    prev_v = int(prev.values.get(key, 0))
    if prev_v < gold_v and cur_v > prev_v:
        return "improved" if cur_v <= gold_v else "warning"
    if prev_v == cur_v:
        return "stable"
    if cur_v < prev_v and gold_v >= prev_v:
        return "regressed"
    return result_count_closer(prev, cur, gold, key)


def result_absence(prev: HtmlMetrics, cur: HtmlMetrics, gold: HtmlMetrics, key: str) -> str:
    cur_v = bool(cur.values.get(key, False))
    if not prev.exists:
        return "warning" if cur_v else "matches_gold"
    prev_v = bool(prev.values.get(key, False))
    if prev_v and not cur_v:
        return "improved"
    if not prev_v and cur_v:
        return "regressed"
    return "stable" if not cur_v else "warning"


def result_not_increased(prev: HtmlMetrics, cur: HtmlMetrics, gold: HtmlMetrics, key: str) -> str:
    cur_v = int(cur.values.get(key, 0))
    gold_v = int(gold.values.get(key, 0))
    if not prev.exists:
        return "warning" if cur_v > gold_v else "matches_gold"
    prev_v = int(prev.values.get(key, 0))
    if cur_v < prev_v:
        return "improved"
    if cur_v > prev_v:
        return "warning"
    return "stable"


def value_for(metrics: HtmlMetrics, key: str, labeler: Callable[[bool | int], str] | None = None) -> str:
    if not metrics.exists:
        return "MISSING"
    value = metrics.values.get(key, 0)
    if labeler is not None:
        return labeler(value)
    return str(value)


def print_row(name: str, previous: str, current: str, gold: str, result: str) -> None:
    print(f"{name:<31} {previous:>9}   {current:>7}   {gold:>5}   {result}")


def main() -> int:
    args = parse_args()
    current_dir = resolve_current_dir(args.current)

    summary = Counter()
    had_regression = False
    had_missing_previous = False

    for case in CASES:
        prev = collect_metrics(args.previous / case["previous"])
        cur = collect_metrics(current_dir / case["current"])
        gold = collect_metrics(args.gold / case["gold"])

        print(f"== {case['name']} version comparison ==")
        print(f"previous: {prev.path}")
        print(f"current : {cur.path}")
        print(f"gold    : {gold.path}")
        if not prev.exists:
            had_missing_previous = True
            print(f"[WARNING] previous fixture not found: {prev.path}")
        if not cur.exists:
            print(f"[ERROR] current fixture not found: {cur.path}")
            return 1
        if not gold.exists:
            print(f"[ERROR] gold fixture not found: {gold.path}")
            return 1
        print()
        print(f"{'Metric':<31} {'previous':>9}   {'current':>7}   {'gold':>5}   result")

        rows: list[tuple[str, str, str, str, str]] = []
        for key in ("intro_text", "doctor_info_text", "consultation_hours_text", "update_line"):
            rows.append((key, value_for(prev, key, bool_label), value_for(cur, key, bool_label), value_for(gold, key, bool_label), result_text_metric(prev, cur, gold, key)))
        for key in ("h3_count", "h4_count", "table_count"):
            rows.append((key, value_for(prev, key), value_for(cur, key), value_for(gold, key), result_count_closer(prev, cur, gold, key)))
        for key in ("thead_count", "caption_count", "scope_col_count", "scope_row_count", "th_count"):
            rows.append((key, value_for(prev, key), value_for(cur, key), value_for(gold, key), result_structure_added(prev, cur, gold, key)))
        for key in ("menu_present", "pagetop_present", "footer_present"):
            rows.append((key, value_for(prev, key, presence_label), value_for(cur, key, presence_label), value_for(gold, key, presence_label), result_absence(prev, cur, gold, key)))
        for key in ("rgb_fullwidth", "caption_id_count", "caption_id_duplicates"):
            rows.append((key, value_for(prev, key), value_for(cur, key), value_for(gold, key), result_not_increased(prev, cur, gold, key)))

        for row in rows:
            print_row(*row)
            summary[row[4]] += 1
            if row[4] == "regressed":
                had_regression = True

        if cur.duplicate_caption_ids:
            print(f"[WARNING] current caption id duplicates: {cur.duplicate_caption_ids}")
        print()

    print("== Summary ==")
    for key in ("improved", "stable", "changed", "matches_gold", "differs_from_gold", "regressed", "warning"):
        print(f"{key}: {summary[key]}")
    if had_missing_previous:
        print("status: WARNING (previous fixture missing; current vs gold only)")
        return 0
    if had_regression:
        print("status: FAIL")
        return 1
    print("status: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
