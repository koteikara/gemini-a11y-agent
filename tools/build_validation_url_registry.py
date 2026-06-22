#!/usr/bin/env python3
"""Build a v1.0 URL registry CSV from validation page Excel/CSV lists.

This local-only helper intentionally uses only the Python standard library so
selected municipality URL lists can be converted without adding dependencies.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

EXPECTED_HEADERS = ["No.", "URL", "ページ名", "ランク"]
REGISTRY_HEADERS = [
    "自治体名",
    "URL",
    "保存ファイル名",
    "XPath",
    "ステータス",
    "開始日時",
    "完了日時",
    "消費トークン",
    "想定コスト(円)",
    "処理バージョン",
    "画像解析（Vision）",
    "VisionTokens",
    "VisionCalls",
]
DEFAULT_SLUGS = {
    "安城市": "anjo",
    "浦添市": "urasoe",
    "弘前市": "hirosaki",
    "福山市": "fukuyama",
    "豊橋市": "toyohashi",
}
NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pkgrel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


@dataclass(frozen=True)
class SourceRow:
    municipality: str
    no: int
    url: str


class ConversionError(Exception):
    """Raised for fatal input or output validation errors."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert municipality validation page .xlsx/.csv files to the v1.0 URLレジストリ CSV format.",
    )
    parser.add_argument("--input-dir", required=True, type=Path, help="Directory containing municipality .xlsx/.csv files.")
    parser.add_argument("--output", required=True, type=Path, help="Destination URL registry CSV path. Written as UTF-8 with BOM.")
    parser.add_argument("--default-xpath", default="", help="XPath used when a municipality is not present in --xpath-map.")
    parser.add_argument("--xpath-map", type=Path, help="JSON file mapping municipality names to XPath values.")
    parser.add_argument("--vision", default="OFF", choices=["OFF", "ON"], help="Value for the URLレジストリ Vision column. Default: OFF.")
    parser.add_argument("--allow-unknown-municipality", action="store_true", help="Use municipality_###.html for unknown municipality names instead of failing.")
    return parser.parse_args()


def cell_text(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    value = cell.find("main:v", NS)
    if cell_type == "s" and value is not None and value.text is not None:
        return shared_strings[int(value.text)]
    if cell_type == "inlineStr":
        return "".join(text.text or "" for text in cell.findall(".//main:t", NS)).strip()
    return (value.text if value is not None and value.text is not None else "").strip()


def column_index(cell_ref: str) -> int:
    letters = "".join(ch for ch in cell_ref if ch.isalpha())
    index = 0
    for ch in letters:
        index = index * 26 + (ord(ch.upper()) - ord("A") + 1)
    return index - 1


def read_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    strings: list[str] = []
    for item in root.findall("main:si", NS):
        strings.append("".join(text.text or "" for text in item.findall(".//main:t", NS)).strip())
    return strings


def sheet_path_for_name(zf: zipfile.ZipFile, sheet_name: str) -> str:
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rel_targets = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels.findall("pkgrel:Relationship", NS)}
    for sheet in workbook.findall(".//main:sheet", NS):
        if sheet.attrib.get("name") == sheet_name:
            rel_id = sheet.attrib.get(f"{{{NS['rel']}}}id")
            target = rel_targets.get(rel_id or "")
            if not target:
                break
            return "xl/" + target.lstrip("/") if not target.startswith("xl/") else target
    raise ConversionError(f"対象ページ sheet not found")


def read_xlsx_rows(path: Path) -> list[dict[str, str]]:
    with zipfile.ZipFile(path) as zf:
        sheet_path = sheet_path_for_name(zf, "対象ページ")
        shared_strings = read_shared_strings(zf)
        root = ET.fromstring(zf.read(sheet_path))
        rows: list[list[str]] = []
        for row in root.findall(".//main:sheetData/main:row", NS):
            values: list[str] = []
            for cell in row.findall("main:c", NS):
                idx = column_index(cell.attrib.get("r", "A1"))
                while len(values) <= idx:
                    values.append("")
                values[idx] = cell_text(cell, shared_strings)
            rows.append(values)
    return rows_to_dicts(path, rows)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def rows_to_dicts(path: Path, rows: list[list[str]]) -> list[dict[str, str]]:
    for row_index, row in enumerate(rows):
        normalized = [value.strip() for value in row]
        if all(header in normalized for header in EXPECTED_HEADERS):
            return [
                {header: row[normalized.index(header)].strip() if normalized.index(header) < len(row) else "" for header in EXPECTED_HEADERS}
                for row in rows[row_index + 1 :]
                if any(cell.strip() for cell in row)
            ]
    raise ConversionError(f"{path.name}: required headers not found: {', '.join(EXPECTED_HEADERS)}")


def read_source(path: Path) -> list[dict[str, str]]:
    if path.suffix.lower() == ".xlsx":
        return read_xlsx_rows(path)
    if path.suffix.lower() == ".csv":
        return read_csv_rows(path)
    raise ConversionError(f"unsupported input file: {path.name}")


def parse_no(value: str, path: Path) -> int:
    try:
        return int(float(value))
    except ValueError as exc:
        raise ConversionError(f"{path.name}: invalid No. value: {value!r}") from exc


def collect_sources(input_dir: Path) -> tuple[list[SourceRow], list[str]]:
    if not input_dir.is_dir():
        raise ConversionError(f"input directory not found: {input_dir}")
    paths = sorted([p for p in input_dir.iterdir() if p.suffix.lower() in {".xlsx", ".csv"}])
    if not paths:
        raise ConversionError(f"no .xlsx or .csv files found in {input_dir}")
    source_rows: list[SourceRow] = []
    warnings: list[str] = []
    seen_urls: dict[str, str] = {}
    for path in paths:
        municipality = path.stem
        dict_rows = read_source(path)
        municipality_count = 0
        for row in dict_rows:
            for header in EXPECTED_HEADERS:
                if header not in row:
                    raise ConversionError(f"{path.name}: required header missing: {header}")
            url = row["URL"].strip()
            if not url:
                warnings.append(f"{municipality}: skipped row with empty URL")
                continue
            if url in seen_urls:
                warnings.append(f"duplicate URL: {url} ({seen_urls[url]}, {municipality})")
            else:
                seen_urls[url] = municipality
            source_rows.append(SourceRow(municipality, parse_no(row["No."].strip(), path), url))
            municipality_count += 1
        if municipality_count != 50:
            warnings.append(f"{municipality}: expected 50 rows, got {municipality_count}")
    if len(source_rows) != 250:
        warnings.append(f"total: expected 250 rows, got {len(source_rows)}")
    return source_rows, warnings


def load_xpath_map(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in data.items()):
        raise ConversionError("--xpath-map must be a JSON object mapping strings to strings")
    return data


def build_registry_rows(source_rows: Iterable[SourceRow], xpath_map: dict[str, str], default_xpath: str, vision: str, allow_unknown: bool) -> list[list[str]]:
    output_rows: list[list[str]] = []
    filenames: set[str] = set()
    for row in source_rows:
        slug = DEFAULT_SLUGS.get(row.municipality)
        if slug is None:
            if not allow_unknown:
                raise ConversionError(f"unknown municipality slug: {row.municipality}")
            slug = "municipality"
        filename = f"{slug}_{row.no:03d}.html"
        if filename in filenames:
            raise ConversionError(f"duplicate 保存ファイル名: {filename}")
        filenames.add(filename)
        output_rows.append([
            row.municipality,
            row.url,
            filename,
            xpath_map.get(row.municipality, default_xpath),
            "未完了",
            "",
            "",
            "",
            "",
            "",
            vision,
            "",
            "",
        ])
    return output_rows


def write_csv(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(REGISTRY_HEADERS)
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    try:
        xpath_map = load_xpath_map(args.xpath_map)
        source_rows, warnings = collect_sources(args.input_dir)
        registry_rows = build_registry_rows(source_rows, xpath_map, args.default_xpath, args.vision, args.allow_unknown_municipality)
        write_csv(args.output, registry_rows)
    except (ConversionError, OSError, zipfile.BadZipFile, ET.ParseError, json.JSONDecodeError) as exc:
        print("status: FAIL", file=sys.stderr)
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"status: {'PASS_WITH_WARNINGS' if warnings else 'PASS'}")
    if warnings:
        print("warnings:")
        for warning in warnings:
            print(f"- {warning}")
    print(f"municipalities: {len({row.municipality for row in source_rows})}")
    print(f"rows: {len(registry_rows)}")
    print(f"output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
