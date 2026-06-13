#!/usr/bin/env python3
"""Check Saga City old/ai/gold fixture inventory.

This script intentionally uses only the Python standard library. It does not
parse HTML and does not access the network; it only verifies fixture placement,
counts, and representative file presence.
"""

from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path("tests/fixtures/html/saga-city")
FIXTURE_DIRS = ("old", "ai", "gold")
EXPECTED_HTML_COUNT = 51
AI_TARGET = BASE_DIR / "ai" / "sg02395_0820.html"
GOLD_TARGET = BASE_DIR / "gold" / "sg02395.html"
OLD_TARGET_PATTERN = "sg02395"
PREVIEW_COUNT = 3


def status_line(ok: bool, message: str) -> None:
    label = "PASS" if ok else "FAIL"
    print(f"[{label}] {message}")


def info_line(message: str) -> None:
    print(f"[INFO] {message}")


def warn_line(message: str) -> None:
    print(f"[WARN] {message}")


def html_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*.html"), key=lambda path: path.name)


def format_paths(paths: list[Path]) -> str:
    if not paths:
        return "(none)"
    return ", ".join(path.as_posix() for path in paths)


def print_file_preview(label: str, files: list[Path]) -> None:
    names = [path.name for path in files]
    head = names[:PREVIEW_COUNT]
    tail = names[-PREVIEW_COUNT:] if len(names) > PREVIEW_COUNT else []
    info_line(f"{label} first files: {', '.join(head) if head else '(none)'}")
    info_line(f"{label} last files: {', '.join(tail) if tail else '(none)'}")


def main() -> int:
    print("== Saga City fixture inventory ==")

    failures: list[str] = []
    inventories: dict[str, list[Path]] = {}

    for label in FIXTURE_DIRS:
        directory = BASE_DIR / label
        files = html_files(directory)
        inventories[label] = files
        print(f"{label}: {len(files)} html files")

    print()

    for label in FIXTURE_DIRS:
        directory = BASE_DIR / label
        exists = directory.is_dir()
        status_line(exists, f"{label} directory exists")
        if not exists:
            failures.append(f"missing directory: {directory.as_posix()}")
            continue

        files = inventories[label]
        has_html = bool(files)
        status_line(has_html, f"{label} directory has *.html files")
        if not has_html:
            failures.append(f"no html files: {directory.as_posix()}")

        count_ok = len(files) == EXPECTED_HTML_COUNT
        status_line(count_ok, f"{label} html count is {EXPECTED_HTML_COUNT}")
        if not count_ok:
            failures.append(
                f"unexpected html count in {directory.as_posix()}: "
                f"expected {EXPECTED_HTML_COUNT}, got {len(files)}"
            )

    print()

    ai_exists = AI_TARGET.is_file()
    status_line(ai_exists, f"ai target exists: {AI_TARGET.as_posix()}")
    if not ai_exists:
        failures.append(f"missing ai target: {AI_TARGET.as_posix()}")

    gold_exists = GOLD_TARGET.is_file()
    status_line(gold_exists, f"gold target exists: {GOLD_TARGET.as_posix()}")
    if not gold_exists:
        failures.append(f"missing gold target: {GOLD_TARGET.as_posix()}")

    old_candidates = [
        path for path in inventories.get("old", []) if OLD_TARGET_PATTERN in path.name
    ]
    if old_candidates:
        info_line(f"old target candidates: {format_paths(old_candidates)}")
    else:
        warn_line(
            f"old target candidates: no filenames include {OLD_TARGET_PATTERN!r}; "
            "warning only"
        )

    print()
    for label in FIXTURE_DIRS:
        print_file_preview(label, inventories[label])

    print()
    print("== Summary ==")
    if failures:
        print("status: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("status: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
