#!/usr/bin/env python3
"""Build the curated GitHub Pages artifact."""

from __future__ import annotations

import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLISHABLES = REPO_ROOT / "publishables"
PAGES = REPO_ROOT / ".pages-site"

HTML_PAGES = [
    "index.html",
    "paper.html",
    "harness-built-target.html",
    "scenario-catalog.html",
    "evidence-index.html",
    "evaluator-findings.html",
]

PUBLISHABLE_DATA = [
    "source-manifest.json",
    "study-a-summary.json",
    "study-b-summary.json",
    "study-b-cells.json",
]


def copy_html(name: str) -> None:
    text = (PUBLISHABLES / name).read_text(encoding="utf-8")
    text = text.replace("../data/releases/v1/", "data/releases/v1/")
    (PAGES / name).write_text(text, encoding="utf-8")


def main() -> None:
    if PAGES.exists():
        shutil.rmtree(PAGES)
    (PAGES / "data").mkdir(parents=True)
    (PAGES / "assets").mkdir()

    for page in HTML_PAGES:
        copy_html(page)

    for filename in PUBLISHABLE_DATA:
        shutil.copy2(PUBLISHABLES / "data" / filename, PAGES / "data" / filename)

    release_src = REPO_ROOT / "data" / "releases" / "v1"
    release_dst = PAGES / "data" / "releases" / "v1"
    shutil.copytree(release_src, release_dst)

    print(f"Built Pages site at {PAGES}")


if __name__ == "__main__":
    main()
