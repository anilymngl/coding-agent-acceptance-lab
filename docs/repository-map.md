# Repository Map

This map records why each retained public-tree path belongs on `main` and which path families were removed during the information-architecture cleanup.

Admission rule: a file remains on public `main` only if it runs, tests, configures, reproduces, verifies, documents, publishes, licenses, cites, or operates the current supported system.

## Retained Paths

| Path | Role | Audience | Authority | Required on `main` | Maintenance | Action |
|---|---|---|---|---|---|---|
| `.github/` | CI and manual Pages deployment workflows | Maintainers | Source | Verifies PRs and deploys the curated site | Edit with release process changes | Keep |
| `ci_vibe_lab/` | Harness implementation | Contributors, maintainers | Source | Runs scenarios, matrices, reports, evaluator workbench, dashboard | Code review and tests | Keep |
| `configs/` | Matrix definitions | Researchers, maintainers | Source | Defines reproducible experiment matrices | Review before new evidence runs | Keep |
| `data/releases/v1/` | Frozen public data release | Researchers, reviewers | Source evidence | Recomputes published metrics | Regenerate only through release process | Keep |
| `docs/` | Current public documentation | Users, contributors | Source docs | Explains architecture, methodology, data, and contribution rules | Update with supported behavior | Keep consolidated |
| `publishables/` | Canonical six-page publication source and JSON summaries | Readers, reviewers | Publication source / derived data | Builds the public Pages artifact | Regenerate catalog and verify | Keep curated |
| `reports/` | Release audit and report index | Reviewers, maintainers | Historical release record | Preserves final release audit | Update only for release audit facts | Keep minimal |
| `scripts/` | Release, publication, catalog, and Pages tooling | Maintainers, CI | Source | Builds and verifies public artifacts | Test through CI | Keep supported scripts |
| `tests/` | Unit and harness tests | Contributors, CI | Source | Prevents regressions | Run with `uv run python -m unittest discover -s tests -v` | Keep |
| `AGENTS.md` | Stable agent/contributor operating rules | Coding agents, maintainers | Source docs | Prevents evidence and branch-policy mistakes | Keep stable, not session diary | Keep |
| `README.md` | Public entry point | Users, readers | Source docs | Explains project, findings, commands, and data | Update with release-visible changes | Keep |
| `CITATION.cff` | Citation metadata | Researchers | Metadata | Supports citation | Update on release identity/version changes | Keep |
| `LICENSE` | MIT and CC BY 4.0 license notice | All users | Legal | Defines reuse terms | Update only intentionally | Keep |
| `check-opencode.sh` | Operator health check | Maintainers | Source tooling | Supported local operations aid | Keep executable and documented | Keep |
| `opencode.json` | Local OpenCode/Ollama config | Maintainers | Source config | Supports documented local execution | Update with supported local runtime config | Keep |
| `pyproject.toml`, `uv.lock` | Python package and lockfile | Contributors, CI | Source / lockfile | Installs CLI and dependencies | Use `uv lock` after dependency changes | Keep |

## Removed Path Families

| Path family | Why removed from `main` | Preservation |
|---|---|---|
| `.opencode/skills/` | Internal authoring skills, not required to run or verify the project | Git history and `archive/pre-main-cleanup-2026-06-25` |
| `presentation.html`, `presentation/` | Slide decks and post drafts are communication artifacts, not supported release surface | Git history and archive snapshot |
| `publishables/archive/` | Superseded publication snapshots duplicate history | Git history and archive snapshot |
| `publishables/paper_v2.html`, `publishables/paper_academic.html` | Unsupported publication variants; `paper.html` is canonical | Git history and archive snapshot |
| `publishables/PUBLISHABLES_PLAN.md`, `publishables/REVIEW_PRE_MERGE.md` | Completed planning/review notes, not current public docs | Git history and archive snapshot |
| Dated docs plans and handovers | Development archaeology superseded by current docs | Durable content extracted into current docs |
| Generated/intermediate reports | Overlapping historical analyses superseded by public data, paper, and final audit | Git history, archive snapshot, and release data |
| `scripts/analyze_gemma.py`, `scripts/query_gemma.py` | One-off local analysis helpers tied to removed scratch reports | Git history and archive snapshot |
| `app/`, `tests/test_dates.py` | Root-level leftover scenario fixture, not package API or harness implementation | Git history and archive snapshot |

## Notes

- Historical `north-mini-test` names may still appear in release provenance or Git history.
- Deleted files are not lost; the cleanup removes them from current public `main` only.
- The archive branch and annotated tag were created before cleanup at `67c48a00a2ae584735acc75549336971bc667432`.
