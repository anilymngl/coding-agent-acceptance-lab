# Architecture

Coding Agent Acceptance Lab is organized around deterministic scenario generation, agent execution, hidden acceptance, and public evidence verification.

## Core Flow

1. A scenario definition writes a small repository with source files and public tests.
2. The runner verifies the public tests start red.
3. The runner invokes the coding agent with only the visible repo and prompt.
4. The runner executes public tests.
5. The runner captures the patch diff.
6. Hidden acceptance tests are injected after the agent exits.
7. Hidden tests run against the model patch.
8. Results, artifacts, and metrics are persisted.

Hidden tests are never present in the model-under-test path before the agent exits.

## Components

| Component | Responsibility |
|---|---|
| `ci_vibe_lab/scenarios.py` | Scenario registry, generated repo files, hidden tests, prompt modes, metadata |
| `ci_vibe_lab/runner.py` | Single-attempt lifecycle, OpenCode invocation, public/hidden test execution, artifact capture |
| `ci_vibe_lab/db.py` | SQLite connection and run persistence helpers |
| `ci_vibe_lab/matrix.py` | Config-driven multi-model, multi-pack, multi-lane orchestration |
| `ci_vibe_lab/report.py` | Markdown reports from run or matrix databases |
| `ci_vibe_lab/integrity.py` | Artifact presence, SHA256, and audit coverage checks |
| `ci_vibe_lab/evaluator.py` | Evaluator-agent workbench and structured review ingestion |
| `ci_vibe_lab/dashboard.py` | Streamlit inspection UI |
| `scripts/build_release_data.py` | Public release-data construction |
| `scripts/verify_release_data.py` | Public metric recomputation and parity checks |
| `scripts/build_scenario_catalog.py` | Generated scenario catalog page |
| `scripts/verify_publishables.py` | Publication consistency checks |
| `scripts/build_pages_site.py` | Curated Pages artifact build |
| `scripts/validate_pages_site.py` | Curated Pages artifact validation |

## Data Flow

Operational run data is mutable and local:

- `data/matrix/`
- `runs/`

Public release data is frozen and committed:

- `data/releases/v1/*.sqlite`
- `data/releases/v1/exports/*.csv`
- `data/releases/v1/schema.sql`
- `data/releases/v1/provenance.json`
- `data/releases/v1/checksums.sha256`

Publication pages and JSON are derived from release data and scenario metadata. The empirical source is the release SQLite/CSV layer, not copied numbers in prose.

## Prompt Lanes

The harness currently supports:

- `sparse`: visible failing context without explicit acceptance criteria.
- `contract_visible`: visible acceptance contract, success signals, and failure modes.
- `audit_visible`: contract-visible plus scenario intent metadata for audit work.

Do not merge sparse and contract-visible rows by default. They answer different questions.

## Operational Boundaries

- OpenCode config is passed to generated worktrees through `OPENCODE_CONFIG`.
- Provider, config, no-output, and timeout failures are operational evidence.
- Public-green / hidden-red is semantic acceptance evidence.
- Raw provider streams and generated worktrees are not public release artifacts.
