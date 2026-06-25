#!/usr/bin/env python3
"""Validate the curated Pages artifact."""

from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urldefrag

REPO_ROOT = Path(__file__).resolve().parent.parent
PAGES = REPO_ROOT / ".pages-site"
EXPECTED_HTML = {
    "index.html",
    "paper.html",
    "harness-built-target.html",
    "scenario-catalog.html",
    "evidence-index.html",
    "evaluator-findings.html",
}
REQUIRED_DATA = {
    "data/source-manifest.json",
    "data/study-a-summary.json",
    "data/study-b-summary.json",
    "data/study-b-cells.json",
    "data/releases/v1/study-b.sqlite",
    "data/releases/v1/exports/study-b-attempts.csv",
    "data/releases/v1/exports/study-b-cells.csv",
    "data/releases/v1/provenance.json",
    "data/releases/v1/checksums.sha256",
}
FORBIDDEN_SUBSTRINGS = [
    "file:" + "///",
    "/" + "Users/",
    "publishables/archive/",
    "archive/",
    "paper_" + "v2.html",
    "paper_" + "academic.html",
    "PUBLISHABLES" + "_PLAN.md",
    "REVIEW" + "_PRE_MERGE.md",
]


class Parser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if "id" in attrs_dict and attrs_dict["id"]:
            self.ids.add(attrs_dict["id"])
        if tag == "a" and attrs_dict.get("name"):
            self.ids.add(attrs_dict["name"] or "")
        if tag == "a" and attrs_dict.get("href"):
            self.links.append(attrs_dict["href"] or "")


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def parse_pages() -> dict[str, Parser]:
    if not PAGES.exists():
        fail(".pages-site does not exist; run scripts/build_pages_site.py first")
    html_files = {p.name for p in PAGES.glob("*.html")}
    if html_files != EXPECTED_HTML:
        fail(f"expected HTML pages {sorted(EXPECTED_HTML)}, found {sorted(html_files)}")
    parsed = {}
    for name in sorted(EXPECTED_HTML):
        text = (PAGES / name).read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_SUBSTRINGS:
            if forbidden in text:
                fail(f"{name} contains forbidden text/link {forbidden}")
        parser = Parser()
        parser.feed(text)
        parsed[name] = parser
    return parsed


def validate_links(parsed: dict[str, Parser]) -> int:
    count = 0
    for source, parser in parsed.items():
        for href in parser.links:
            count += 1
            if href.startswith(("https://", "http://", "mailto:")):
                continue
            target, fragment = urldefrag(href)
            target = target or source
            if target.startswith("#"):
                target = source
            if target.startswith("/") or target.startswith("../"):
                fail(f"{source} has non-staged relative link {href}")
            if target.endswith(".md"):
                fail(f"{source} links to markdown planning/doc file {href}")
            if target in parsed:
                if fragment and fragment not in parsed[target].ids:
                    fail(f"{source} link {href} has missing fragment")
                continue
            if target.startswith("data/"):
                if not (PAGES / target).exists():
                    fail(f"{source} link {href} targets missing data file")
                continue
            fail(f"{source} link {href} targets missing file")
    return count


def validate_hash_targets(parsed: dict[str, Parser]) -> None:
    scenario_ids = {i for i in parsed["scenario-catalog.html"].ids if not i.startswith("filter-")}
    evidence_ids = parsed["evidence-index.html"].ids
    missing_evidence = sorted(sid for sid in scenario_ids if sid not in evidence_ids and "_" in sid)
    if missing_evidence:
        fail("Evidence page missing scenario anchors: " + ", ".join(missing_evidence))


def main() -> None:
    parsed = parse_pages()
    for rel in REQUIRED_DATA:
        if not (PAGES / rel).exists():
            fail(f"missing required data file {rel}")
    links = validate_links(parsed)
    validate_hash_targets(parsed)
    print(f"Pages site validation passed: {len(parsed)} HTML pages, {links} links.")


if __name__ == "__main__":
    main()
