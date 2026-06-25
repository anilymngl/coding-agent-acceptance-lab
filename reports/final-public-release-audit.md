# Final Public Release Audit

Date: 2026-06-25

Repository: `anilymngl/coding-agent-acceptance-lab`

Final release branch merged: `release/open-source-v1`

Rename cleanup merged: `chore/repository-rename`

Public-tree cleanup snapshot: `archive/pre-main-cleanup-2026-06-25` and annotated tag `pre-main-cleanup-2026-06-25`

## Verdict

**READY FOR FINAL PAGES DEPLOYMENT AND `v1.0.0` TAG AFTER THE PUBLIC-TREE CLEANUP PR LANDS.**

The software, public data, publication source, CI verification, license, citation metadata, and release audit are present. The remaining release operations are:

1. merge the public-tree cleanup PR
2. create `develop` from cleaned `main`
3. configure GitHub Pages to deploy from GitHub Actions
4. run the manual Pages workflow
5. verify the live site
6. add the live URL to `README.md`
7. tag `v1.0.0`

## Public Evidence Boundary

- Authored contracts: `ci_vibe_lab/scenarios.py`
- Mutable operational evidence: ignored local `data/matrix/` and `runs/`
- Public release evidence: `data/releases/v1/*.sqlite` and `data/releases/v1/exports/*.csv`
- Derived publication JSON: `publishables/data/*.json`
- Publication pages: six canonical HTML pages in `publishables/`
- Pages artifact: generated `.pages-site/`

Raw provider streams, generated worktrees, mutable operational DBs, prompts, stdout/stderr, artifact paths, and local worktree paths remain excluded from the public release.

## Public Databases

| File | SHA256 | Size |
|---|---|---:|
| `data/releases/v1/study-a.sqlite` | `89ef0d8294bd01d8e361b5dc7b7e3b3304cda2f242705cd2a9fe071b0e1ad7f6` | 212K |
| `data/releases/v1/study-b.sqlite` | `76baccfbdd48447c99be27a42b708cdff0907eeff932be5c98573d1894e69526` | 284K |
| `data/releases/v1/evaluator-reviews.sqlite` | `8eddc84ce9ad91c013db58b0f68e9c3c6da62df15bc16923fa6be63e4167e613` | 12K |
| `data/releases/v1/supporting-gemma.sqlite` | `9465bedaeecb86b987dd8272b3e622832edf55e05b7d787674080f8dd4aa1c7b` | 92K |

Release directory size: `968K`.

## Row Counts

| Dataset | Attempts | Cells | Exclusions | Notes |
|---|---:|---:|---:|---|
| Study A | 222 | 222 | 0 | Pass@1 breadth evidence |
| Study B | 391 | 132 | 5 | Laguna XS.2 vs North Mini pass@3 depth matrix |
| Evaluator reviews | 10 | n/a | n/a | Diagnostic review coverage, not external truth |
| Supporting Gemma | 60 | 50 | 0 | Separate local evidence, not pooled with Study A/B |

## Metric Recompute

Canonical verifier output:

```text
Study B scenarios: 33
Study B cells: 132
Planned attempts: 396
Retained attempts: 391
Public-green attempts: 385
Hidden passes: 284
False-greens: 101
Missing attempts: 5

Sparse false-green:
84 / 194 = 43.3%

Contract-visible false-green:
17 / 191 = 8.9%

North Mini product sparse:
24 / 30 = 80.0%

North Mini product contract-visible:
10 / 31 = 32.3%

North Mini product improvement:
47.7 percentage points

SQLite integrity: PASS
CSV parity: PASS
Publication JSON parity: PASS
Publication HTML parity: PASS
```

Central empirical results are publicly recomputable from `data/releases/v1/`.

## Publication Integrity

- `publishables/paper.html` is the canonical technical report.
- `publishables/index.html` links to Study B SQLite, attempt CSV, cell CSV, provenance, and checksums.
- `publishables/evidence-index.html` links to the same release artifacts and declares release ID `coding-agent-acceptance-lab-v1`.
- `publishables/data/source-manifest.json` includes release-data paths and hashes.
- `scripts/verify_publishables.py` runs `scripts/verify_release_data.py` as part of publication verification.
- `scripts/validate_pages_site.py` validates exactly six primary HTML pages, required data files, links, fragments, excluded pages, and local-path leaks.

## Repository Information Architecture

The public-tree cleanup removed unsupported current-tree artifacts rather than moving them into an archive directory on `main`.

The retained/removed path rationale is in `docs/repository-map.md`.

Preservation is through:

- Git history
- `archive/pre-main-cleanup-2026-06-25`
- `pre-main-cleanup-2026-06-25`

## Security

Release verification includes:

```bash
gitleaks git . --redact
```

No mutable operational DBs or raw `runs/` artifacts are tracked outside `data/releases/`.

## Required Final Gate

Before tagging `v1.0.0`, run:

```bash
uv run python scripts/build_release_data.py --check
uv run python scripts/verify_release_data.py
uv run python scripts/build_scenario_catalog.py
git diff --exit-code publishables/scenario-catalog.html
uv run python scripts/verify_publishables.py
uv run python scripts/build_pages_site.py
uv run python scripts/validate_pages_site.py
uv run python -m unittest discover -s tests -v
gitleaks git . --redact
```
