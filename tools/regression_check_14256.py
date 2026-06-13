#!/usr/bin/env python3
"""Regression checks for Saga City 14256 generated HTML.

This script validates the v1.0 baseline page described in
``docs/regression-tests.md`` using lxml-based DOM inspection only.
It performs no network access and does not install dependencies.

Example fixture inputs for the Saga City 14256 equivalent page:
    python tools/regression_check_14256.py tests/fixtures/html/saga-city/ai/sg02395_0820.html
    python tools/regression_check_14256.py tests/fixtures/html/saga-city/gold/sg02395.html
    python tools/regression_check_14256.py tests/fixtures/html/saga-city/ai
    python tools/regression_check_14256.py tests/fixtures/html/saga-city/gold

The old fixture is pre-correction HTML and is not a required validation
target for this script. Passing old/ is allowed, but emits a warning.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


INTRO_TEXT = "休日（日曜日または祝日）在宅当番医について"
REQUIRED_TEXTS = (
    INTRO_TEXT,
    "日曜・祝日在宅当番医情報",
    "診療時間",
)
COMMON_COMPONENT_TEXTS = ("Menu", "PageTop")
RGB_WARNING_TEXT = "rgb（"
EXPECTED_CAPTION_TEXT = "令和8年2月11日（水曜日）一覧"
FALLBACK_CAPTION_TEXT = "2月11日"
REQUIRED_HEADER_TEXTS = ("診療科", "医療機関名", "電話", "所在地", "特定健診")


@dataclass(frozen=True)
class CheckResult:
    level: str
    name: str
    detail: str = ""


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def document_text(root: Any) -> str:
    return normalize_space(" ".join(root.xpath("//text()")))


def text_before_element(root: Any, element: Any) -> str:
    chunks: list[str] = []
    for node in root.iter():
        if node is element:
            break
        if node.text:
            chunks.append(node.text)
        if node.tail:
            chunks.append(node.tail)
    return normalize_space(" ".join(chunks))


def has_text_starting_with(root: Any, prefix: str) -> bool:
    for text in root.xpath("//text()"):
        if normalize_space(text).startswith(prefix):
            return True
    return False


def table_caption_text(table: Any) -> str:
    return normalize_space(" ".join(table.xpath(".//caption//text()")))


def table_header_text(table: Any) -> str:
    return normalize_space(" ".join(table.xpath(".//thead//text() | .//th//text()")))


def table_has_required_headers(table: Any) -> bool:
    header_text = table_header_text(table)
    return all(required in header_text for required in REQUIRED_HEADER_TEXTS)


def table_has_target_caption(table: Any) -> bool:
    caption_text = table_caption_text(table)
    return EXPECTED_CAPTION_TEXT in caption_text or FALLBACK_CAPTION_TEXT in caption_text


def find_duty_table(root: Any) -> Any | None:
    all_tables = root.xpath("//table")

    for table in all_tables:
        if EXPECTED_CAPTION_TEXT in table_caption_text(table):
            return table

    for table in all_tables:
        if FALLBACK_CAPTION_TEXT in table_caption_text(table) and table_has_required_headers(table):
            return table

    for table in all_tables:
        if table_has_required_headers(table):
            return table

    tables = root.xpath("//table[.//caption or .//thead or .//th]")
    if tables:
        return tables[0]
    return all_tables[0] if all_tables else None


def table_has_row_scope_from_second_tbody_row(table: Any) -> bool:
    rows = table.xpath(".//tbody/tr[position() >= 2]")
    if not rows:
        return False
    for row in rows:
        first_cell = row.xpath("./*[self::th or self::td][1]")
        if not first_cell:
            return False
        cell = first_cell[0]
        if cell.tag.lower() != "th" or cell.get("scope") != "row":
            return False
    return True


def duplicate_caption_ids(root: Any) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for caption in root.xpath("//caption[@id]"):
        caption_id = caption.get("id")
        if not caption_id:
            continue
        if caption_id in seen:
            duplicates.add(caption_id)
        seen.add(caption_id)
    return sorted(duplicates)


def run_checks(root: Any, raw_html: str) -> list[CheckResult]:
    results: list[CheckResult] = []
    full_text = document_text(root)
    table = find_duty_table(root)

    def required(condition: bool, name: str, ok_detail: str = "", fail_detail: str = "") -> None:
        results.append(CheckResult("PASS" if condition else "FAIL", name, ok_detail if condition else fail_detail))

    for required_text in REQUIRED_TEXTS:
        required(required_text in full_text, f"必須テキストが存在する: {required_text}")

    if table is None:
        required(False, "table前導入文が当番医テーブルより前に存在する", fail_detail="検査対象の table が見つかりません")
    else:
        before_table = text_before_element(root, table)
        required(
            INTRO_TEXT in before_table,
            "table前導入文が当番医テーブルより前に存在する",
            fail_detail=f"導入文が対象 table より前にありません: {INTRO_TEXT}",
        )

    required(not has_text_starting_with(root, "更新："), "`更新：` で始まる行が存在しない")
    required(bool(root.xpath("//h3")), "h3 が存在する")
    required(bool(root.xpath("//h4")), "h4 が存在する")

    if table is None:
        for name in (
            "当番医テーブルに thead が存在する",
            '当番医テーブルの先頭行に th scope="col" が存在する',
            'tbody 2行目以降の1列目に th scope="row" が存在する',
            "caption が存在する",
        ):
            required(False, name, fail_detail="検査対象の table が見つかりません")
    else:
        required(bool(table.xpath(".//thead")), "当番医テーブルに thead が存在する")
        required(
            bool(table.xpath(".//tr[1]/*[self::th][@scope='col']"))
            or bool(table.xpath(".//thead//tr[1]/*[self::th][@scope='col']")),
            '当番医テーブルの先頭行に th scope="col" が存在する',
        )
        required(
            table_has_row_scope_from_second_tbody_row(table),
            'tbody 2行目以降の1列目に th scope="row" が存在する',
            fail_detail='tbody/tr[position() >= 2] の先頭セルが th scope="row" ではありません',
        )
        required(bool(table.xpath(".//caption")), "caption が存在する")
        required(
            table_has_target_caption(table),
            "当番医テーブルの caption に対象日が含まれる",
            ok_detail=f"caption: {table_caption_text(table)}",
            fail_detail=f"caption に {EXPECTED_CAPTION_TEXT} または {FALLBACK_CAPTION_TEXT} が含まれません: {table_caption_text(table)}",
        )
        missing_headers = [required_header for required_header in REQUIRED_HEADER_TEXTS if required_header not in table_header_text(table)]
        required(
            not missing_headers,
            "当番医テーブルの header text に必須項目がすべて含まれる",
            ok_detail="必須 header: " + ", ".join(REQUIRED_HEADER_TEXTS),
            fail_detail="不足 header: " + ", ".join(missing_headers),
        )

    common_text_matches = [text for text in COMMON_COMPONENT_TEXTS if text in full_text]
    footer_elements = root.xpath("//footer")
    required(
        not common_text_matches and not footer_elements,
        "Menu / PageTop / footer 相当の共通部品が混入していない",
        fail_detail=", ".join(common_text_matches + (["footer element"] if footer_elements else [])),
    )

    if RGB_WARNING_TEXT in raw_html:
        results.append(CheckResult("WARNING", "CSS の rgb（ が存在する", "v1.0 既知事項のため warning"))

    duplicate_ids = duplicate_caption_ids(root)
    if duplicate_ids:
        results.append(
            CheckResult(
                "WARNING",
                "caption id の重複が存在する",
                "重複 id: " + ", ".join(duplicate_ids),
            )
        )

    return results


def print_results(results: Iterable[CheckResult]) -> None:
    for result in results:
        suffix = f" - {result.detail}" if result.detail else ""
        print(f"[{result.level}] {result.name}{suffix}")


def is_old_fixture_path(path: Path) -> bool:
    return "old" in path.parts


def discover_html_files(input_path: Path) -> list[Path]:
    if input_path.is_dir():
        return sorted(input_path.rglob("*.html"), key=lambda path: path.as_posix())
    return [input_path]


def lxml_import_failure_message(exc: ModuleNotFoundError) -> str:
    return (
        f"[FAIL] lxml を import できません: {exc}\n"
        "この検証スクリプトは lxml 前提です。外部ネットワーク前提の pip install は行わず、"
        "lxml が利用可能な実行環境で実行してください。"
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run lxml regression checks for Saga City 14256 HTML.")
    parser.add_argument(
        "html_path",
        type=Path,
        help=(
            "Path to the generated/local 14256 HTML file or a directory containing HTML files "
            "(e.g. tests/fixtures/html/saga-city/ai/sg02395_0820.html, "
            "tests/fixtures/html/saga-city/gold/sg02395.html, or tests/fixtures/html/saga-city/ai)"
        ),
    )
    return parser.parse_args(argv)


def check_file(html_path: Path, html: Any, parser_error: type[Exception]) -> list[CheckResult]:
    results: list[CheckResult] = []
    if is_old_fixture_path(html_path):
        results.append(CheckResult("WARNING", "old/ fixture が指定されています", "old/ は補正前 HTML のため通常の必須検証対象外です"))

    try:
        raw_html = html_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [*results, CheckResult("FAIL", "HTMLファイルを読み込めません", str(exc))]

    try:
        root = html.fromstring(raw_html)
    except (parser_error, ValueError) as exc:
        return [*results, CheckResult("FAIL", "HTMLをパースできません", str(exc))]

    return [*results, *run_checks(root, raw_html)]


def print_summary(file_count: int, passed: int, failed: int, warnings: int) -> None:
    print("\n== Summary ==")
    print(f"files: {file_count}")
    print(f"passed: {passed}")
    print(f"failed: {failed}")
    print(f"warnings: {warnings}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    input_path = args.html_path

    try:
        from lxml import html
        from lxml.etree import ParserError
    except ModuleNotFoundError as exc:
        print(lxml_import_failure_message(exc), file=sys.stderr)
        return 1

    html_paths = discover_html_files(input_path)
    is_directory_run = input_path.is_dir()
    if not html_paths:
        print(f"[FAIL] 対象 HTML が見つかりません: {input_path}", file=sys.stderr)
        if is_directory_run:
            print_summary(0, 0, 0, 0)
        return 1

    failed_files = 0
    passed_files = 0
    warning_count = 0

    for index, html_path in enumerate(html_paths):
        if is_directory_run:
            if index > 0:
                print()
            print(f"== {html_path} ==")

        results = check_file(html_path, html, ParserError)
        print_results(results)

        has_failure = any(result.level == "FAIL" for result in results)
        if has_failure:
            failed_files += 1
        else:
            passed_files += 1
        warning_count += sum(1 for result in results if result.level == "WARNING")

    if is_directory_run:
        print_summary(len(html_paths), passed_files, failed_files, warning_count)

    return 1 if failed_files else 0


if __name__ == "__main__":
    raise SystemExit(main())
