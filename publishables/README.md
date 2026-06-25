# Publishables — Trust Gap Research Suite

Self-contained HTML research exhibit. No build step. No CDN dependencies (Georgia is a system font). Open any file in a browser.

## What's here

| File | What it is |
|---|---|
| `index.html` | Entry point. Thesis, findings, signposts to everything. |
| `paper_v2.html` | Research paper. Pass@3 head-to-head: Laguna XS.2 vs North Mini on 33 CI-repair scenarios. |
| `paper.html` | Prior paper (v1). Pass@1 across 5 models, 4 families. Original trust gap finding. |
| `harness-built-target.html` | System inventory. Pipeline flow, data flow diagram, all 10 components with I/O, 6 gaps named, 5 targets. |
| `scenario-catalog.html` | All 33 scenarios as cards. Trap description, difficulty, category. |
| `evidence-index.html` | 132-row matrix. Every scenario × model × prompt mode as a cell. Filterable by pack, lane, outcome. |
| `evaluator-findings.html` | 10 reviewed false-greens. Root causes, confidence scores, patch quality. All confirmed genuine. |

## How to use

Open `index.html` in a browser. Every page links to every other page via the nav bar at the top. Current page is bolded.

## Design

- **Signal style**: truth labels on every claim (Built, Observed, Not built, Target, Recommendation). No filler words. Plain language. Honest about what's missing.
- **System font stack**: Inter, SF Mono. No external font CDNs.
- **Color as semantics**: green = pass/good, rose = fail/false-green, blue = info, amber = warning, gray = missing/not-run.

## Evidence status

- **Tier 1**: behavior microscope. 33 scenarios, one harness, one team. Hidden tests and evaluator verdicts from same authors.
- **Tier 2** (comparative claims): needs evaluator agreement on false-greens. Only 10/101 reviewed.
- **Tier 3** (public benchmark): needs external audit. Not yet.

## Data source

All numbers from two matrix configs: `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/` (ci_forensics + maintenance_value) and `data/matrix/north-mini-openrouter-completion/` (product_workflows). Run databases in 12+ SQLite files.

## Prior work

Older slide decks and presentations live in `presentation/`. The Gemma 4 matrix reports are in `reports/`. Methodology docs in `docs/`.
