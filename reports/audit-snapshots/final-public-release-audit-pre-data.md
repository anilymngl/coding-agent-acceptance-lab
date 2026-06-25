# Final Public Release Audit

Date: 2026-06-25

Branch audited: `audit/final-public-release`

Base commit audited: `b809763`

Repository remote: `https://github.com/anilymngl/north-mini-test.git`

## Verdict

**Ready after branch review and manual GitHub release actions.**

No open P0 or P1 blocker remains after the fixes in this branch. The tracked public artifact now states the correct lifecycle order, avoids over-authoritative evaluator wording, and makes the public reproducibility boundary explicit.

This is an **audited evidence release**, not a full public raw-attempt archive. The public repository contains harness code, authored scenario contracts, generated publication pages, and derived JSON summaries. The raw model streams, generated worktrees, and local SQLite run databases were audited locally and are not part of the public artifact.

## Audit Scope

Included:

- Current `main` as of `b809763`, with this audit performed on fresh branch `audit/final-public-release`.
- Full tracked source tree, generated publishable HTML, generated JSON summaries, reports, docs, and repo configuration.
- Local ignored evidence inputs under `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/` and `data/matrix/north-mini-openrouter-completion/`.
- Curated GitHub Pages staging directory built from selected `publishables/` files.
- Git history and current filesystem secret scans.

Excluded by design:

- Publishing the repository or changing GitHub visibility.
- Deploying Pages.
- Re-running model evaluations.
- Weakening hidden tests or rewriting empirical outcomes.
- Restoring archived `challenges/` content.

## Source-Of-Truth Map

| Layer | Source | Role | Public? |
|---|---|---|---|
| Scenario contracts | `ci_vibe_lab/scenarios.py` | Authored scenario definitions, prompt modes, public tests, hidden tests, metadata | Yes |
| Harness lifecycle | `ci_vibe_lab/runner.py` | Materialize repo, run baseline, run OpenCode, run public tests, capture patch, inject hidden tests, persist artifacts | Yes |
| Matrix orchestration | `ci_vibe_lab/matrix.py` plus `configs/matrix/*.json` | Expands model/prompt/pack cells and runs attempts | Yes |
| Attempt records | Local SQLite under `data/matrix/...` | Attempt-level rows used to derive publication data | No, ignored local evidence |
| Raw artifacts | Local `runs/...` paths referenced from SQLite | Prompts, outputs, patches, worktrees | No, ignored local evidence |
| Publication snapshot | `publishables/data/*.json` | Derived, machine-readable publication data | Yes |
| Publication pages | `publishables/*.html` | Reader-facing research exhibit | Yes |
| Historical archive | `publishables/archive/` | Superseded snapshots retained for local provenance | Excluded from curated Pages staging |

## Harness Lifecycle Check

Fact: the runner captures the model patch before hidden-test injection.

Evidence: `ci_vibe_lab/runner.py` now shows the sequence:

- `write_scenario(...)`
- baseline test
- OpenCode invocation
- public test
- `patch = git_diff(workdir)`
- `write_hidden_test(...)`
- hidden test
- artifact persistence

Current code reference: `ci_vibe_lab/runner.py:368-409`.

Correction made: `publishables/paper.html` and `publishables/paper_academic.html` previously described the lifecycle as if hidden tests were injected before patch extraction and as if all workspace states were hashed in real time. That was stronger than the implementation. The paper now says patch diff is captured before hidden-test injection and integrity hashes are computed after the run for retained artifacts.

## Evidence Freeze Manifest

The local ignored SQLite inputs were frozen by SHA256 and row counts on 2026-06-25. These DBs are the empirical inputs used to validate the publication JSON. `duplicate_run_ids` was zero for every DB.

| DB | SHA256 | bytes | schema | rows | model | pack | mode | started min | started max | duplicate_run_ids |
|---|---|---:|---:|---:|---|---|---|---|---|---:|
| `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics-contract_visible.sqlite` | `d4ac03c4b2c87a9f5e82245ca751e773c29348929cf31480de75dd81025d4e2e` | 3297280 | 16 | 36 | `openrouter/poolside/laguna-xs.2:free` | `ci_forensics` | `contract_visible` | `2026-06-22T21:31:23+00:00` | `2026-06-23T00:57:20+00:00` | 0 |
| `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/ci_forensics-sparse.sqlite` | `417b5ecb67da8d621b6f9fab8b4b65cdf53b42b6480ef4efc902acaad1d3faca` | 1708032 | 16 | 36 | `openrouter/poolside/laguna-xs.2:free` | `ci_forensics` | `sparse` | `2026-06-22T20:56:42+00:00` | `2026-06-22T21:30:58+00:00` | 0 |
| `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/maintenance_value-contract_visible.sqlite` | `ccc0544ce7972b1097477fd771de283c53dca07f10021f3027d870df39c4b4b7` | 2142208 | 14 | 30 | `openrouter/poolside/laguna-xs.2:free` | `maintenance_value` | `contract_visible` | `2026-06-23T01:34:41+00:00` | `2026-06-23T02:39:29+00:00` | 0 |
| `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/maintenance_value-sparse.sqlite` | `145e7beac32c51c315136bc2fd0a683f9f1328330427642585e7e0bd2a7a4d28` | 1564672 | 14 | 30 | `openrouter/poolside/laguna-xs.2:free` | `maintenance_value` | `sparse` | `2026-06-23T00:58:28+00:00` | `2026-06-23T01:33:48+00:00` | 0 |
| `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows-contract_visible.sqlite` | `c9494017b4088147dccdd7f78fbeb5cd87297ce10ca2170aa4ed127e27021e95` | 2707456 | 14 | 33 | `openrouter/poolside/laguna-xs.2:free` | `product_workflows` | `contract_visible` | `2026-06-24T19:00:15+00:00` | `2026-06-24T22:13:22+00:00` | 0 |
| `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/laguna-xs2/product_workflows-sparse.sqlite` | `234adaa11dde36796abc776c560e244113d9fc3d5a651b490d39a4b68e72eedf` | 1773568 | 14 | 33 | `openrouter/poolside/laguna-xs.2:free` | `product_workflows` | `sparse` | `2026-06-23T02:39:57+00:00` | `2026-06-23T03:20:36+00:00` | 0 |
| `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/ci_forensics-contract_visible.sqlite` | `6ea34e8564a820bb18921f9686270cdd8373f7a8dbe3f9fb2418634b83f91e16` | 1908736 | 14 | 36 | `opencode/north-mini-code-free` | `ci_forensics` | `contract_visible` | `2026-06-23T00:19:53+00:00` | `2026-06-23T00:42:49+00:00` | 0 |
| `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/ci_forensics-sparse.sqlite` | `a5bf61f497d6b4091bf403b27b174e6d21a0be157951cde1c4c676761212e184` | 1376256 | 16 | 36 | `opencode/north-mini-code-free` | `ci_forensics` | `sparse` | `2026-06-22T20:59:06+00:00` | `2026-06-23T00:19:39+00:00` | 0 |
| `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/maintenance_value-contract_visible.sqlite` | `3eb965e1f3e585a2144994946c14346074b1c3f56ba3936b4e7002beb552513b` | 1277952 | 14 | 25 | `opencode/north-mini-code-free` | `maintenance_value` | `contract_visible` | `2026-06-24T17:24:54+00:00` | `2026-06-24T18:00:04+00:00` | 0 |
| `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/maintenance_value-sparse.sqlite` | `1eb1507222865ad565401521176a0368978bfcda3a513915dc69641c59a3a830` | 1486848 | 14 | 30 | `opencode/north-mini-code-free` | `maintenance_value` | `sparse` | `2026-06-23T00:44:47+00:00` | `2026-06-24T17:24:30+00:00` | 0 |
| `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/product_workflows-contract_visible.sqlite` | `ee38ea0d0339ed1778480c74d3042ccbaa1869cbd6731f368d6a74164369d332` | 98304 | 14 | 0 | `(none)` | `(none)` | `(none)` |  |  | 0 |
| `data/matrix/laguna-xs2-vs-north-mini-2026-06-22/north-mini/product_workflows-sparse.sqlite` | `9478084c32cf9b2b651095928c4741e4bb5241b36ab963805d232f5ae8a74c53` | 102400 | 14 | 0 | `(none)` | `(none)` | `(none)` |  |  | 0 |
| `data/matrix/north-mini-openrouter-completion/north-mini/product_workflows-contract_visible.sqlite` | `9e99dc8c3783ae36fa922a0120e5b7607b7510cc116b61a7c5284d461eaf6b6f` | 2818048 | 14 | 33 | `openrouter/cohere/north-mini-code:free` | `product_workflows` | `contract_visible` | `2026-06-24T21:30:49+00:00` | `2026-06-24T22:07:57+00:00` | 0 |
| `data/matrix/north-mini-openrouter-completion/north-mini/product_workflows-sparse.sqlite` | `02a68a7920476db9aa201e54115559c785de5416c108ad244eb039c8f6f4ccc1` | 1900544 | 14 | 33 | `openrouter/cohere/north-mini-code:free` | `product_workflows` | `sparse` | `2026-06-24T20:46:43+00:00` | `2026-06-24T21:30:24+00:00` | 0 |

Note: the two zero-row `north-mini/product_workflows-*` DBs are placeholders from the original matrix route. The publication rows for North Mini product workflows come from `data/matrix/north-mini-openrouter-completion/`.

## Metric Lineage Check

Recomputed from the local SQLite inputs and compared to `publishables/data/study-b-cells.json`:

| Metric | Recomputed |
|---|---:|
| Cells | 132 |
| Planned attempts | 396 |
| Retained attempts | 391 |
| Public-green attempts | 385 |
| Hidden passes | 284 |
| False-greens | 101 |
| Missing attempts | 5 |
| Sparse false-greens/public-green | 84/194 = 43.3% |
| Contract-visible false-greens/public-green | 17/191 = 8.9% |
| North Mini product sparse false-greens/public-green | 24/30 = 80.0% |
| North Mini product contract-visible false-greens/public-green | 10/31 = 32.3% |
| North Mini product improvement | 47.7 percentage points |

Result: no missing cells, no extra cells, and no mismatched stable publication fields.

## Public Reproducibility Boundary

Direct answer: a third party can reproduce the generated public exhibit structure and inspect the authored harness and scenario contracts from GitHub, but cannot independently re-derive every empirical attempt from GitHub alone because raw model streams, generated worktrees, and local SQLite DBs are intentionally ignored and not published.

That boundary is now stated in `publishables/paper.html` and `publishables/paper_academic.html`. The verifier now checks the canonical paper for the boundary phrase.

Recommendation: if full external recomputation or third-party audit of every attempt is required later, publish a sanitized raw-attempt evidence bundle with hashes and a documented retention policy. Do not imply that current GitHub contents already provide that.

## Curated Pages Staging

Validated staging directory: `/tmp/north-mini-pages-site`

Included files:

- `index.html`
- `paper.html`
- `harness-built-target.html`
- `scenario-catalog.html`
- `evidence-index.html`
- `evaluator-findings.html`
- `data/source-manifest.json`
- `data/study-a-summary.json`
- `data/study-b-summary.json`
- `data/study-b-cells.json`

Excluded:

- `publishables/archive/`
- `paper_academic.html`
- markdown reports and docs
- local ignored `data/` and `runs/`

Static validation result:

- 6 HTML pages parsed.
- 100 internal links checked.
- No missing links or fragments.
- No links to `archive/`.
- No links to markdown reports.
- No local file URLs.
- No local absolute user paths.

Browser smoke result:

- Desktop pages loaded with no console errors: `index.html`, `paper.html`, `harness-built-target.html`, `scenario-catalog.html`, `evidence-index.html`, `evaluator-findings.html`.
- Scenario fragments resolved for `dependency_api_change`, `audit_log_redaction`, `generated_openapi_refresh`, and `support_sla_business_hours`.
- Evidence index exposed 132 rows.
- Catalog search/filter interactions worked for `billing`.
- Mobile viewport `390x844` had no horizontal overflow on `index.html` or `scenario-catalog.html#support_sla_business_hours`.

## Security Scan

Tool: `gitleaks 8.30.1`.

Git history:

- Command: `gitleaks git . --redact`
- Result: 77 commits scanned, no leaks found.

Current filesystem:

- Command: `gitleaks dir . --redact`
- Result: 2 findings, both in `.venv/share/jupyter/nbextensions/pydeck/index.js.map`.
- Classified false positives: `GLTF_KEYS`, `getS2CellIdFromToken`.

Project plus ignored evidence, excluding third-party dependency environment:

- Command: copied repo to `/tmp/north-mini-gitleaks-scan` excluding `.git` and `.venv`, including ignored `data/` and `runs/`; ran `gitleaks dir /tmp/north-mini-gitleaks-scan --redact`.
- Result: no leaks found.

Additional tracked-file checks:

- No tracked raw SQLite or DB files except publication JSON under `publishables/data/`.
- No tracked `.env`, `.pem`, `.key`, `.p12`, credential, or secret files found.
- No secret-like object names found in `git rev-list --objects --all`.
- Local absolute repository path prefix was removed from tracked reports/docs.

## Findings

| ID | Severity | Status | Finding | Evidence | Fix |
|---|---|---|---|---|---|
| FPR-001 | P1 | Fixed | Paper overstated the harness lifecycle by implying hidden tests were injected before patch extraction and that workspace states were hashed in real time. | Actual order in `ci_vibe_lab/runner.py:368-409`. | Updated `publishables/paper.html` and `publishables/paper_academic.html` to match implemented lifecycle. |
| FPR-002 | P1 | Fixed | Paper claimed raw run artifacts were maintained as part of the public GitHub artifact. | `.gitignore` excludes `/data/` and `/runs/`; `git ls-files` shows only publication JSON under `publishables/data/`. | Replaced with explicit public boundary: code/contracts/pages/derived JSON are public; raw streams/worktrees/SQLite are audited locally but not public. |
| FPR-003 | P2 | Fixed | Evaluator language used over-authoritative confirmation wording. | `publishables/paper.html`, `publishables/harness-built-target.html`, `publishables/README.md`, and one report line. | Replaced with evidence-validated / packet-validated wording. |
| FPR-004 | P2 | Fixed | Historical docs/reports contained an absolute local repository path prefix. | `rg` over tracked docs/reports. | Mechanically converted to repo-relative wording. |
| FPR-005 | P2 | Documented | No `.github/` Pages workflow exists. Pages readiness was validated through a curated local staging directory, but deployment remains a manual release action. | `find .github` returned no files. | Documented exact next release actions below. |
| FPR-006 | P2 | Documented | Full external raw-attempt reproduction is not available from GitHub alone. | Raw DBs and run artifacts are ignored and local. | Public boundary is now explicit; future improvement is a sanitized evidence bundle if needed. |
| FPR-007 | P2 | Fixed | Scenario catalog evidence links used `evidence-index.html#scenario_id`, but the evidence page had no static fragment anchors for those IDs. | Curated Pages static validator found missing evidence-index fragments. | Added static scenario anchors and hash-based row highlighting to `publishables/evidence-index.html`. |

No open P0 or P1 findings remain.

## Final Gates Run

Commands already run successfully before report finalization:

- `git fetch --all --prune`
- `git switch main`
- `git pull --ff-only origin main`
- `git switch -c audit/final-public-release`
- `git merge-base --is-ancestor 42f21b8 HEAD`
- `git merge-base --is-ancestor 6b777f4 HEAD`
- `uv run python scripts/verify_publishables.py`
- `uv run python -m unittest discover -s tests -v`
- `gitleaks git . --redact`
- `gitleaks dir . --redact`
- `gitleaks dir /tmp/north-mini-gitleaks-scan --redact`
- curated Pages static validator
- in-app browser desktop and mobile smoke test

Final commands to rerun after this report is written:

```bash
uv run python scripts/verify_publishables.py
uv run python scripts/build_scenario_catalog.py
git diff --exit-code publishables/scenario-catalog.html
uv run python -m unittest discover -s tests -v
```

## Exact Release Actions Not Performed

Do these only after reviewing and merging this audit branch:

```bash
git status --short
git add docs/model-comparison-eval-pipeline-plan-2026-06-20.md \
  publishables/README.md \
  publishables/harness-built-target.html \
  publishables/paper.html \
  publishables/paper_academic.html \
  reports/final-public-release-audit.md \
  reports/laguna-xs2-vs-north-mini-first-comparison.md \
  reports/laguna-xs2-vs-north-mini-leaderboard.md \
  reports/leaderboard-local-gemma4-smallest-two.md \
  reports/leaderboard-local-gemma4-two-model.md \
  reports/north-mini-code-evidence-pack-2026-06-20.md \
  reports/north-mini-maintenance-value-v2-2026-06-20.md \
  scripts/verify_publishables.py
git commit -m "audit: final public release readiness"
git push -u origin audit/final-public-release
```

Then open a PR from `audit/final-public-release` to `main`, review the diff, and merge.

After merge:

```bash
git switch main
git pull --ff-only origin main
uv run python scripts/verify_publishables.py
uv run python -m unittest discover -s tests -v
gitleaks git . --redact
```

Manual GitHub actions:

1. Change repository visibility only after the merged `main` passes the final commands.
2. Do not enable GitHub Pages yet. Pages readiness is validated only as a local staged artifact until separate approval.
3. When Pages is approved later, configure it to publish only the curated staged site, not the whole repository and not `publishables/archive/`.
4. If using a future GitHub Actions workflow, copy only the curated files listed in "Curated Pages Staging" into the deployment artifact.
