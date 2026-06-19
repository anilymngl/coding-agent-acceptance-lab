# North Mini Test

Local "vibe eval" harness for coding agents run through the OpenCode CLI.

The point is to build a curated local eval arcade: a few sharp workflow
challenges that reveal whether a coding agent can diagnose, patch, test, and
recover like a useful collaborator. The first pack is `ci_forensics`.

The harness creates deterministic challenge repos, asks OpenCode to fix them,
captures the resulting patch and test output, stores results in SQLite, writes
per-run artifacts, and shows the runs in a Streamlit dashboard.

See [Challenge Design](docs/challenge-design.md) for the eval philosophy and
challenge anatomy.

## Current Challenge Pack

The `ci_forensics` challenges are intentionally small, but each one stresses a
real coding-agent failure mode:

- `dependency_api_change`: handles a changed dependency contract without
  downgrading or hacking tests.
- `timezone_ci_only`: reproduces a CI-only date failure caused by implicit local
  time.
- `stale_generated_schema`: recognizes generated artifact drift and regenerates
  the file.
- `async_export_race`: fixes a deterministic async write race instead of calling
  the test flaky.

## Setup

```bash
uv venv
source .venv/bin/activate
uv sync --extra app
```

You also need the OpenCode CLI installed and configured with at least one model:

```bash
opencode providers
opencode models
```

## Run An Eval

List challenges:

```bash
uv run python -m ci_vibe_lab.runner list
```

Prepare a single disposable challenge repo for inspection:

```bash
uv run python -m ci_vibe_lab.runner prepare \
  --challenge timezone_ci_only \
  --out /tmp/timezone-ci-only
```

Run all scenarios against a configured OpenCode model:

```bash
uv run python -m ci_vibe_lab.runner run \
  --challenge all \
  --model "provider/model" \
  --agent build \
  --auto-approve
```

The model string must match the provider/model name available in your OpenCode
configuration. For North Mini Code, confirm the exact OpenCode/OpenRouter slug
from `opencode models` before running. If you omit `--model`, OpenCode uses its
configured default.

For a no-model harness smoke test:

```bash
uv run python -m ci_vibe_lab.runner run --challenge dependency_api_change --no-opencode
```

That command records the failing baseline and post-test state without invoking
OpenCode.

## Dashboard

```bash
uv run --extra app streamlit run ci_vibe_lab/dashboard.py
```

The dashboard has four tabs:

- **Report**: pass rates, focus priorities, result matrix, category/challenge summaries.
- **Runs**: run table, failure inbox, and model-vs-model comparison.
- **Inspector**: challenge card, prompt, test logs, OpenCode trace, patch, and human review scores.
- **Exports**: filtered CSVs and Markdown report downloads.

By default the dashboard reads:

```text
data/results.sqlite
```

You can override it:

```bash
CI_VIBE_DB=/path/to/results.sqlite uv run --extra app streamlit run ci_vibe_lab/dashboard.py
```

## Files Written By Runs

Runtime output is intentionally ignored by git:

- `runs/worktrees/`: generated scenario worktrees
- `runs/artifacts/`: prompts, test logs, OpenCode output, and patches
- `data/results.sqlite`: SQLite database

Each scenario worktree is also a tiny git repo, so the runner can capture the
agent patch with `git diff`.

## Verify The Harness

```bash
uv run python -m unittest discover -s tests -v
```
