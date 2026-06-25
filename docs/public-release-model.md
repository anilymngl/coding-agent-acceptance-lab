# Public Release Model

This repository separates mutable harness operations from public research evidence.

## Branches

- `main`: canonical public source after release review and merge.
- `dev/pre-open-source-main-2026-06-25`: frozen copy of pre-release `main`.
- `dev/final-public-release-audit-2026-06-25`: frozen copy of the completed pre-data audit.
- `release/open-source-v1`: active open-source release work.

## Data Layers

- `data/matrix/`: mutable local execution databases. Ignored.
- `runs/`: raw prompts, model streams, generated worktrees, and artifacts. Ignored.
- `data/releases/`: frozen public reproducibility datasets. Committed.
- `publishables/data/`: derived publication JSON. Committed, but not the empirical source.
- `publishables/*.html`: generated publication pages.

## Presentation Layers

- `.pages-site/`: generated deployment artifact. Ignored and never edited by hand.
- GitHub Pages: public presentation surface after owner-controlled enablement.
- GitHub Releases: optional future home for large source snapshots after separate review.

## Rule

Every central published number must recompute from `data/releases/v1/` with:

```bash
uv run python scripts/verify_release_data.py
```
