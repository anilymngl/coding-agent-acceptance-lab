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

## Challenge Packs

The original `ci_forensics` pack is preserved. Its challenges are intentionally
small, but each one stresses a real coding-agent failure mode:

- `dependency_api_change`: handles a changed dependency contract without
  downgrading or hacking tests.
- `timezone_ci_only`: reproduces a CI-only date failure caused by implicit local
  time.
- `stale_generated_schema`: recognizes generated artifact drift and regenerates
  the file.
- `async_export_race`: fixes a deterministic async write race instead of calling
  the test flaky.
- `pagination_cursor_drift`: follows renamed pagination cursors instead of
  silently importing only the first page.
- `env_bool_parser`: parses string feature flags safely instead of relying on
  Python string truthiness.
- `tenant_cache_leak`: preserves multi-tenant cache isolation for reused
  external user IDs.
- `decimal_money_rounding`: uses exact decimal money math and explicit cent
  rounding.
- `idempotency_key_regression`: keeps retry dedupe keys deterministic without
  cross-order collisions.
- `csv_header_contract`: preserves documented export columns and order.

The second pack is `product_workflows`, a different set of small product/backend
workflow regressions:

- `bulk_invite_dedupe`: normalizes and deduplicates invite emails.
- `markdown_slug_collision`: creates stable duplicate-safe heading anchors.
- `feature_rollout_bucket`: uses deterministic percentage rollout buckets.
- `audit_log_redaction`: recursively redacts sensitive audit-log fields.
- `cart_discount_stack`: applies checkout discounts with a zero floor.
- `inventory_reservation_idempotency`: preserves stock under retried reservations.
- `search_ranking_stability`: ranks search results by relevance and recency.
- `billing_proration`: prorates plan upgrades with explicit cent rounding.
- `webhook_signature_raw_body`: verifies HMAC signatures over raw payload bytes.
- `support_sla_business_hours`: computes support deadlines inside business hours.

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
uv run python -m ci_vibe_lab.runner list --pack product_workflows
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
  --pack ci_forensics \
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

## Hidden Failure Reports

Generate a deterministic report from the saved SQLite results:

```bash
uv run ci-vibe-report hidden-failures \
  --db data/north-mini-code-eval.sqlite \
  --out reports/hidden-failures.md
```

Run a constrained evaluator agent over hidden failures with DeepSeek V4 Pro:

```bash
uv run ci-vibe-evaluate run \
  --db data/north-mini-code-eval.sqlite \
  --pack ci_forensics \
  --hidden-only \
  --model deepseek/deepseek-v4-pro \
  --auto-approve \
  --out runs/evaluator-agent/deepseek-v4-pro-hidden \
  --report reports/deepseek-v4-pro-hidden-evaluator.md
```

Each review directory contains `EVALUATION_PACKET.md`, raw OpenCode stdout/stderr,
and either a validated `evaluation.json` from the evaluator agent or an explicit
`blocked/invalid` validation record. The evaluator is only allowed to cite exact
quotes from the packet, so reports are accountable rather than free-form vibes.

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
