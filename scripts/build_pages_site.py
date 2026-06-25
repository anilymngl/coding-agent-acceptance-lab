#!/usr/bin/env python3
"""Build the curated GitHub Pages artifact."""

from __future__ import annotations

import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLISHABLES = REPO_ROOT / "publishables"
PAGES = REPO_ROOT / ".pages-site"
REPOSITORY_URL = "https://github.com/anilymngl/coding-agent-acceptance-lab"
REPO_LINK_CSS = """
  .repo-source-link {
    position: fixed;
    top: 14px;
    right: 14px;
    z-index: 1000;
    display: inline-flex;
    align-items: center;
    min-height: 34px;
    padding: 8px 12px;
    border: 1px solid #94a3b8;
    border-radius: 6px;
    background: #ffffff;
    color: #0f172a;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    font-size: 12px;
    font-weight: 700;
    line-height: 1;
    text-decoration: none;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);
  }
  .repo-source-link:hover {
    border-color: #2563eb;
    color: #1d4ed8;
  }
  @media (max-width: 640px) {
    .repo-source-link {
      position: static;
      display: flex;
      justify-content: center;
      margin: 12px 12px 0;
    }
  }
  @media print {
    .repo-source-link { display: none; }
  }
"""
REPO_LINK_HTML = (
    f'<a class="repo-source-link" href="{REPOSITORY_URL}" '
    'rel="noopener noreferrer">GitHub Repository</a>'
)

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
    if "</style>" not in text:
        raise ValueError(f"{name} does not contain a closing style tag")
    if "<body>" not in text:
        raise ValueError(f"{name} does not contain a body tag")
    text = text.replace("</style>", f"{REPO_LINK_CSS}\n</style>", 1)
    text = text.replace("<body>", f"<body>\n{REPO_LINK_HTML}", 1)
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
