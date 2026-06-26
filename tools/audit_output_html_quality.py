#!/usr/bin/env python3
"""Audit generated HTML output quality and emit Markdown/CSV reports."""
from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

SEVERITY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}

@dataclass(frozen=True)
class Issue:
    file: str
    severity: str
    rule_id: str
    line: int | None
    message: str
    snippet: str
    suggestion: str

@dataclass
class TableMetric:
    file: str
    table_count: int = 0
    caption_missing: int = 0
    thead_missing: int = 0
    th_missing: int = 0
    scope_missing: int = 0
    unstable_tables: int = 0

class Node:
    def __init__(self, tag: str, attrs: dict[str, str], line: int, parent: "Node | None") -> None:
        self.tag = tag
        self.attrs = attrs
        self.line = line
        self.parent = parent
        self.children: list[Node] = []
        self.text_parts: list[str] = []
        if parent:
            parent.children.append(self)
    @property
    def text(self) -> str:
        return " ".join(t.strip() for t in self.text_parts if t.strip())
    def ancestors(self) -> Iterable["Node"]:
        cur = self.parent
        while cur:
            yield cur
            cur = cur.parent
    def has_ancestor(self, tag: str) -> bool:
        return any(a.tag == tag for a in self.ancestors())
    def find_all(self, tag: str) -> list["Node"]:
        found = []
        for child in self.children:
            if child.tag == tag:
                found.append(child)
            found.extend(child.find_all(tag))
        return found

class AuditParser(HTMLParser):
    VOID = {"area","base","br","col","embed","hr","img","input","link","meta","param","source","track","wbr"}
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.root = Node("document", {}, 1, None)
        self.stack = [self.root]
        self.nodes: list[Node] = []
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Node(tag.lower(), {k.lower(): v or "" for k, v in attrs}, self.getpos()[0], self.stack[-1])
        self.nodes.append(node)
        if node.tag not in self.VOID:
            self.stack.append(node)
    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return
    def handle_data(self, data: str) -> None:
        if data.strip():
            self.stack[-1].text_parts.append(data)

def line_snippet(lines: list[str], line: int | None, fallback: str = "") -> str:
    if line and 1 <= line <= len(lines):
        return lines[line - 1].strip()[:240]
    return re.sub(r"\s+", " ", fallback).strip()[:240]

def text_of(node: Node) -> str:
    parts = [node.text]
    for child in node.children:
        parts.append(text_of(child))
    return " ".join(p for p in parts if p).strip()

def add_issue(issues: list[Issue], file: str, severity: str, rule_id: str, line: int | None, message: str, snippet: str, suggestion: str) -> None:
    issues.append(Issue(file, severity, rule_id, line, message, snippet, suggestion))

def audit_file(path: Path, base: Path) -> tuple[list[Issue], TableMetric, Counter[str]]:
    rel = path.relative_to(base).as_posix()
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = raw.splitlines()
    parser = AuditParser(); parser.feed(raw)
    issues: list[Issue] = []
    repeated = Counter()

    for node in parser.nodes:
        if node.tag in {"row", "cell"}:
            add_issue(issues, rel, "Critical", "OUT-TABLE-001", node.line, f"非標準の疑似tableタグ <{node.tag}> が残っています。", line_snippet(lines, node.line), "HTML生成時に標準の table/tr/td/th 構造へ正規化してください。")
        if node.tag in {"tr", "td", "th"} and not node.has_ancestor("table"):
            add_issue(issues, rel, "Critical", "OUT-TABLE-002", node.line, f"table外に <{node.tag}> が存在する疑いがあります。", line_snippet(lines, node.line), "table断片の抽出・差し戻し処理を確認してください。")
    for m in re.finditer(r"&lt;\s*/\s*(?:tr|td|th|table)\s*&gt;|</\s*(?:row|cell)\s*>", raw, re.I):
        line = raw.count("\n", 0, m.start()) + 1
        add_issue(issues, rel, "Critical", "OUT-TABLE-005", line, "エスケープされた壊れた閉じタグらしき断片があります。", line_snippet(lines, line), "HTML断片を文字列として混入させていないか確認してください。")

    metric = TableMetric(rel)
    for table in parser.root.find_all("table"):
        metric.table_count += 1
        captions = table.find_all("caption")
        if not captions:
            metric.caption_missing += 1
            add_issue(issues, rel, "High", "OUT-TABLE-003", table.line, "captionなしtableです。", line_snippet(lines, table.line), "表の目的を表す具体的な caption を付与してください。")
        elif text_of(captions[0]).strip() in {"表", "一覧", "テーブル", "table"}:
            add_issue(issues, rel, "High", "OUT-TABLE-006", captions[0].line, "captionが汎用的すぎます。", line_snippet(lines, captions[0].line), "ページ内容に応じた具体的な caption にしてください。")
        if not table.find_all("thead"):
            metric.thead_missing += 1
        ths = table.find_all("th")
        if not ths:
            metric.th_missing += 1
            add_issue(issues, rel, "Medium", "OUT-TABLE-004", table.line, "th がない、または見出しセルが不足しているtableです。", line_snippet(lines, table.line), "見出し行・見出し列を th と scope で表現してください。")
        for th in ths:
            if not th.attrs.get("scope"):
                metric.scope_missing += 1
                add_issue(issues, rel, "Medium", "OUT-TABLE-004", th.line, "scopeなしthです。", line_snippet(lines, th.line), "th に scope=\"col\" または scope=\"row\" を付与してください。")
        widths = []
        for tr in table.find_all("tr"):
            widths.append(len([c for c in tr.children if c.tag in {"td", "th"}]))
        if len(widths) >= 3 and max(widths) - min(widths) >= 3:
            metric.unstable_tables += 1
            add_issue(issues, rel, "High", "OUT-TABLE-007", table.line, "table内の行ごとの列数が極端に不安定です。", line_snippet(lines, table.line), "rowspan/colspan や抽出欠落により表構造が壊れていないか確認してください。")

    patterns = {
        "OUT-EXTRACT-001": ("High", ["本文へスキップ", "このサイトではJavaScript", "サイト内検索", "ページID検索", "緊急情報", "パンくず", "印刷用ページ", "Adobe Reader"]),
        "OUT-CMS-001": ("High", ["EndClear", "ParentBack", "LTitle_cap", "Item end", "BrowserItemList", "先頭にもどる", "先頭に戻る"]),
        "OUT-ENC-001": ("High", ["���", "�"]),
    }
    for rule_id, (sev, pats) in patterns.items():
        for pat in pats:
            for m in re.finditer(re.escape(pat), raw):
                line = raw.count("\n", 0, m.start()) + 1
                add_issue(issues, rel, sev, rule_id, line, f"{pat} が出力に残っています。", line_snippet(lines, line), "本文抽出範囲または共通部品除去ルールを見直してください。")
    back_count = len(re.findall("先頭に(?:もどる|戻る)", raw))
    if back_count >= 5:
        repeated["back_links"] = back_count
        add_issue(issues, rel, "High", "OUT-CMS-002", None, f"戻りリンクが大量に残っています（{back_count}件）。", "先頭に戻る", "繰り返しナビゲーションを除去してください。")

    for img in parser.root.find_all("img"):
        alt = img.attrs.get("alt", "")
        src = img.attrs.get("src", "")
        if alt and (len(alt) >= 20 or re.search(r"(icon|ico|pdf|external|blank|arrow)", src, re.I)):
            add_issue(issues, rel, "Medium", "OUT-ALT-001", img.line, "装飾アイコンと思われる画像に過剰なaltがあります。", line_snippet(lines, img.line), "装飾アイコンは alt=\"\"、意味のある画像は簡潔な代替テキストにしてください。")
            repeated[f"icon_alt:{alt[:40]}"] += 1
    ambiguous = {"こちら", "ここ", "詳細", "詳しくはこちら", "リンク", "PDF", "Excel"}
    for a in parser.root.find_all("a"):
        label = text_of(a).strip()
        if label in ambiguous or re.fullmatch(r"https?://\S+", label):
            add_issue(issues, rel, "Medium", "OUT-LINK-001", a.line, f"曖昧なリンク文言「{label}」があります。", line_snippet(lines, a.line), "リンク先の内容が分かる具体的な文言にしてください。")
    if len(raw.encode("utf-8")) > 500_000:
        add_issue(issues, rel, "Medium", "OUT-SIZE-001", None, "出力HTMLが大きすぎます。", f"{len(raw.encode('utf-8'))} bytes", "共通部品や重複ノイズの混入を確認してください。")
    return issues, metric, repeated

def write_reports(issues: list[Issue], metrics: list[TableMetric], repeated: dict[str, Counter[str]], output_md: Path, output_csv: Path) -> None:
    output_md.parent.mkdir(parents=True, exist_ok=True); output_csv.parent.mkdir(parents=True, exist_ok=True)
    counts = Counter(i.severity for i in issues)
    files = sorted({m.file for m in metrics})
    by_file = {f: Counter(i.severity for i in issues if i.file == f) for f in files}
    sorted_issues = sorted(issues, key=lambda i: (SEVERITY_ORDER[i.severity], i.file, i.line or 0, i.rule_id))
    with output_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["file","severity","rule_id","line","message","snippet","suggestion"])
        for i in sorted_issues: w.writerow([i.file,i.severity,i.rule_id,i.line or "",i.message,i.snippet,i.suggestion])
    with output_md.open("w", encoding="utf-8") as f:
        f.write("# Output HTML Quality Audit\n\n## Summary\n\n")
        status = "FAIL" if counts["Critical"] or counts["High"] else "PASS"
        f.write(f"- status: {status}\n- files: {len(files)}\n- critical: {counts['Critical']}\n- high: {counts['High']}\n- medium: {counts['Medium']}\n- low: {counts['Low']}\n\n")
        f.write("## File Results\n\n| file | critical | high | medium | low |\n| --- | ---: | ---: | ---: | ---: |\n")
        for file in files: f.write(f"| {file} | {by_file[file]['Critical']} | {by_file[file]['High']} | {by_file[file]['Medium']} | {by_file[file]['Low']} |\n")
        for sev in ["Critical", "High", "Medium"]:
            f.write(f"\n## {sev} Issues\n\n")
            rows = [i for i in sorted_issues if i.severity == sev]
            if not rows: f.write("No issues.\n"); continue
            f.write("| file | rule_id | line | message | snippet | suggestion |\n| --- | --- | ---: | --- | --- | --- |\n")
            for i in rows:
                vals = [i.file, i.rule_id, str(i.line or ""), i.message, i.snippet, i.suggestion]
                f.write("| " + " | ".join(v.replace("|", "\\|").replace("\n", " ") for v in vals) + " |\n")
        f.write("\n## Table Metrics\n\n| file | tables | caption_missing | thead_missing | th_missing | scope_missing | unstable_tables |\n| --- | ---: | ---: | ---: | ---: | ---: | ---: |\n")
        for m in metrics: f.write(f"| {m.file} | {m.table_count} | {m.caption_missing} | {m.thead_missing} | {m.th_missing} | {m.scope_missing} | {m.unstable_tables} |\n")
        f.write("\n## Repeated Noise\n\n")
        any_noise = False
        for file, counter in repeated.items():
            for key, count in counter.items():
                if count >= 2:
                    any_noise = True; f.write(f"- {file}: {key} x {count}\n")
        if not any_noise: f.write("No repeated noise detected.\n")
        f.write("\n## Suggested Next Actions\n\n- Critical がある場合は table構造破壊を優先して修正してください。\n- High が多い場合は本文抽出範囲とCMS共通部品除去を見直してください。\n- 5ページ再試験で Critical が1件でも残る場合、250ページ本検証へ進まないでください。\n")

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Audit generated HTML output quality.")
    p.add_argument("--input-dir", required=True, type=Path)
    p.add_argument("--output-md", required=True, type=Path)
    p.add_argument("--output-csv", required=True, type=Path)
    p.add_argument("--no-fail", action="store_true", help="Always exit 0 after writing reports.")
    args = p.parse_args(argv)
    html_files = sorted([*args.input_dir.glob("*.html"), *args.input_dir.glob("*.htm")])
    all_issues: list[Issue] = []; metrics: list[TableMetric] = []; repeated: dict[str, Counter[str]] = {}
    for path in html_files:
        issues, metric, noise = audit_file(path, args.input_dir)
        all_issues.extend(issues); metrics.append(metric); repeated[metric.file] = noise
    write_reports(all_issues, metrics, repeated, args.output_md, args.output_csv)
    counts = Counter(i.severity for i in all_issues)
    status = "FAIL" if counts["Critical"] or counts["High"] else "PASS"
    print(f"status: {status}\nfiles: {len(html_files)}\ncritical: {counts['Critical']}\nhigh: {counts['High']}\nmedium: {counts['Medium']}\nlow: {counts['Low']}\nreport_md: {args.output_md}\nreport_csv: {args.output_csv}")
    return 0 if args.no_fail or status == "PASS" else 1
if __name__ == "__main__":
    raise SystemExit(main())
