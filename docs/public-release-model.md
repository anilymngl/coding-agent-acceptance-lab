# Public Release Model

This repository separates supported public artifacts from mutable operational evidence.

## Branches

- `main`: stable public release branch and GitHub default branch.
- `develop`: integrated next-release work; must pass CI and must not accumulate runtime debris.
- `feature/*`: short-lived implementation branches from `develop`.
- `hotfix/*`: emergency fixes from `main`, merged back to `main` and then `develop`.
- `archive/*` and annotated tags: historical checkpoints only.

## Data Layers

- `data/matrix/`: mutable local execution databases. Ignored.
- `runs/`: raw prompts, model streams, generated worktrees, and artifacts. Ignored.
- `data/releases/`: frozen public reproducibility datasets. Committed.
- `publishables/data/`: derived publication JSON. Committed, but not the empirical source.
- `publishables/*.html`: canonical publication pages.
- `.pages-site/`: generated deployment artifact. Ignored and never edited by hand.

## Release Rule

Every central published number must recompute from `data/releases/v1/`:

```bash
uv run python scripts/verify_release_data.py
```

Raw provider streams, generated worktrees, mutable operational databases, local absolute paths, and private credentials are outside the public release boundary.
