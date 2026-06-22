"""Hybrid a11y rule loader and report-only candidate detector."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Iterable
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from .config import HYBRID_RULES_REPORT_MAX_PREVIEW

LOGGER = logging.getLogger(__name__)

DEFAULT_RULES_PATH = Path(__file__).resolve().parent / "rules" / "a11y_hybrid_detect_fix.jsonl"
REQUIRED_KEYS = {
    "id", "検出ID", "検出方式", "検出", "候補ペイロード", "LLMタスク", "修正プロンプト", "出力契約",
}
VAGUE_LINK_TEXTS = {"こちら", "ここ", "詳細", "詳しくはこちら", "続き", "リンク", "more", "click here"}
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg")
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class _Node:
    def __init__(self, tag: str, attrs: dict[str, str] | None = None, parent: "_Node | None" = None):
        self.tag = tag.lower()
        self.attrs = attrs or {}
        self.parent = parent
        self.children: list[_Node | str] = []

    def get(self, name: str, default: str = "") -> str:
        return self.attrs.get(name, default)


class _MiniHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = _Node("document")
        self.current = self.root

    def handle_starttag(self, tag, attrs):
        node = _Node(tag, {k: v or "" for k, v in attrs}, self.current)
        self.current.children.append(node)
        if node.tag not in VOID_TAGS:
            self.current = node

    def handle_endtag(self, tag):
        tag = tag.lower()
        node = self.current
        while node.parent is not None:
            if node.tag == tag:
                self.current = node.parent
                return
            node = node.parent

    def handle_data(self, data):
        if data:
            self.current.children.append(data)


def load_hybrid_rules(path: str | None = None) -> list[dict]:
    """Load JSONL rule definitions, validating required top-level keys."""
    rules_path = Path(path) if path else DEFAULT_RULES_PATH
    rules: list[dict] = []
    with rules_path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                item = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{rules_path}:{lineno}: invalid JSON: {exc.msg}") from exc
            missing = sorted(REQUIRED_KEYS - set(item))
            if missing:
                raise ValueError(f"{rules_path}:{lineno}: missing required keys: {', '.join(missing)}")
            rules.append(item)
    return rules


def get_hybrid_rule_ids(rules: list[dict]) -> list[str]:
    """Return rule IDs in JSONL order and reject duplicates."""
    ids: list[str] = []
    seen: set[str] = set()
    for idx, rule in enumerate(rules, start=1):
        rid = str(rule.get("id", ""))
        if rid in seen:
            raise ValueError(f"duplicate hybrid rule id at item {idx}: {rid}")
        seen.add(rid)
        ids.append(rid)
    return ids


def _parse(html: str) -> _Node:
    parser = _MiniHTMLParser()
    parser.feed(html or "")
    parser.close()
    return parser.root


def _walk(node: _Node) -> Iterable[_Node]:
    for child in node.children:
        if isinstance(child, _Node):
            yield child
            yield from _walk(child)


def _desc(node: _Node, tag: str | None = None) -> list[_Node]:
    return [n for n in _walk(node) if tag is None or n.tag == tag]


def _text(node: _Node | None) -> str:
    if node is None:
        return ""
    parts: list[str] = []
    def rec(n: _Node):
        for child in n.children:
            if isinstance(child, str):
                if child.strip():
                    parts.append(child.strip())
            else:
                rec(child)
    rec(node)
    return " ".join(parts)


def _serialize(node: _Node) -> str:
    attrs = "".join(f' {escape(k)}="{escape(v, quote=True)}"' for k, v in node.attrs.items())
    inner = "".join(escape(c) if isinstance(c, str) else _serialize(c) for c in node.children)
    return f"<{node.tag}{attrs}>{inner}</{node.tag}>"


def _preview(node: _Node) -> str:
    text = re.sub(r"\s+", " ", _serialize(node)).strip()
    return text[:HYBRID_RULES_REPORT_MAX_PREVIEW]


def _previous_heading(node: _Node) -> str:
    root = node
    while root.parent is not None:
        root = root.parent
    last = ""
    for n in _walk(root):
        if n is node:
            return last
        if n.tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            last = _text(n)
    return last


def _add(candidates: list[dict], rule_id: str, detect_id: str, kind: str, summary: str, node: _Node | None = None, **extra) -> None:
    item = {"rule_id": rule_id, "detect_id": detect_id, "kind": kind, "summary": summary, "auto_fix": False}
    if node is not None:
        item["node_preview"] = _preview(node)
    item.update(extra)
    candidates.append(item)


def _enabled(rule_ids: set[str], rid: str) -> bool:
    return rid in rule_ids


def detect_hybrid_candidates(html: str, *, base_url: str = "", rules: list[dict] | None = None) -> list[dict]:
    """Detect report-only hybrid rule candidates without modifying HTML."""
    try:
        active_rules = rules if rules is not None else load_hybrid_rules()
        rule_ids = set(get_hybrid_rule_ids(active_rules))
        doc = _parse(html)
        candidates: list[dict] = []

        if _enabled(rule_ids, "HTML-R-15"):
            for table in _desc(doc, "table"):
                captions = _desc(table, "caption")
                if not captions or not _text(captions[0]).strip():
                    heading = _previous_heading(table)
                    summary = "caption missing" + (f"; previous heading: {heading[:80]}" if heading else "")
                    _add(candidates, "HTML-R-15", "DET-R15-CAPTION", "table", summary, table)

        if _enabled(rule_ids, "HTML-R-16"):
            for table in _desc(doc, "table"):
                if any((n.get("rowspan").isdigit() and int(n.get("rowspan")) > 1) or (n.get("colspan").isdigit() and int(n.get("colspan")) > 1) for n in _desc(table)):
                    _add(candidates, "HTML-R-16", "DET-R16-MERGE", "table", "rowspan/colspan table", table)

        if _enabled(rule_ids, "LINK-R-02"):
            for a in _desc(doc, "a"):
                href = a.get("href")
                label = _text(a).strip()
                if href and label.lower() in VAGUE_LINK_TEXTS:
                    _add(candidates, "LINK-R-02", "DET-L02-VAGUE", "link", f"vague link text: {label}", a, href=href, anchor_text=label, context=_text(a.parent)[:HYBRID_RULES_REPORT_MAX_PREVIEW])

        if _enabled(rule_ids, "LINK-R-04"):
            for a in _desc(doc, "a"):
                href = a.get("href")
                label = _text(a).strip()
                if href.lower().startswith("mailto:"):
                    match = EMAIL_RE.search(label) or EMAIL_RE.search(href)
                    if match and label.lower() == match.group(0).lower():
                        _add(candidates, "LINK-R-04", "DET-L04-MAIL", "link", "mailto label is raw email", a, email=match.group(0), context=_text(a.parent)[:HYBRID_RULES_REPORT_MAX_PREVIEW])
            for node in _walk(doc):
                if node.tag == "a":
                    continue
                for child in node.children:
                    if isinstance(child, str):
                        for match in EMAIL_RE.finditer(child):
                            _add(candidates, "LINK-R-04", "DET-L04-MAIL", "text", "raw email address", node, email=match.group(0), context=_text(node)[:HYBRID_RULES_REPORT_MAX_PREVIEW])

        base_path = urlparse(base_url).path
        ids = {n.get("id") for n in _walk(doc) if n.get("id")}
        for a in _desc(doc, "a"):
            href = a.get("href")
            parsed = urlparse(href)
            if href.startswith("#") and len(href) > 1 and _enabled(rule_ids, "LINK-R-09"):
                frag = href[1:]
                _add(candidates, "LINK-R-09", "DET-L09-INPAGE", "link", f"in-page fragment; target_exists={frag in ids}", a, href=href, anchor_text=_text(a), fragment=frag, target_exists=frag in ids)
            elif parsed.fragment and (parsed.path or parsed.netloc) and parsed.path != base_path and _enabled(rule_ids, "LINK-R-08"):
                _add(candidates, "LINK-R-08", "DET-L08-XANCHOR", "link", "cross-page fragment link", a, href=href, anchor_text=_text(a), fragment=parsed.fragment)

        for a in _desc(doc, "a"):
            href = a.get("href")
            imgs = _desc(a, "img")
            for img in imgs:
                if _enabled(rule_ids, "IMG-R-05"):
                    _add(candidates, "IMG-R-05", "DET-I05-LINKIMG", "image-link", "linked image", a, href=href, img_src=img.get("src"), alt=img.get("alt"))
                if _enabled(rule_ids, "IMG-R-09") and urlparse(href).path.lower().endswith(IMAGE_EXTS):
                    _add(candidates, "IMG-R-09", "DET-I09-ZOOM", "image-link", "thumbnail links to image file", a, full_image_href=href, thumbnail_src=img.get("src"), alt=img.get("alt"))

        return candidates
    except Exception as exc:  # report-only must never stop page processing
        LOGGER.warning("hybrid rule report-only detection skipped: %s", exc)
        return []
