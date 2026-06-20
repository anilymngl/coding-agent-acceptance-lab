# North Mini Test

A deterministic coding-agent evaluation harness built around a single question:
**does the model actually fix the problem, or does it just make CI green?**

Every scenario has two test layers: **public tests** (visible to the model,
like normal CI) and **hidden tests** (injected after the agent exits, never
seen). A model that satisfies the public tests without satisfying the hidden
ones is logged as a false-green. The headline metric is the trust gap —
public pass rate minus hidden pass rate.

Standard benchmarks score pass/fail. This harness scores *how often you can
trust a pass*.

> This is a behavior microscope, not a leaderboard benchmark. Treat results as
> directional, not statistically stable.

## Findings (North Mini Code — `opencode/north-mini-code-free`)

38 runs across four challenge packs:

| Pack | Runs | Public | Hidden | False-green |
|---|---:|---:|---:|---:|
| `ci_forensics` | 12 | 100% | 67% | 4 |
| `data_semantics` | 5 | 80% | 60% | 1 |
| `product_workflows` | 11 | 91% | 9% | 9 |
| `maintenance_value` | 10 | 100% | 70% | 3 |
| **Combined** | **38** | **95%** | **50%** | **17** |

**The central finding:** the model is disciplined at the agent loop and
reliable for mechanical maintenance work. It fails when the hidden contract
is richer than what the visible test covers — which is most product and
business-logic tasks. 17 of 36 public-green patches were still
contract-broken — a 47% false-green rate.

**Where it works autonomously:** mechanical migrations (`logger.warn`,
`utcnow`, deprecated APIs), stale artifact regeneration, fixture/doc sync,
import hygiene, missing regression tests.

**Where it needs a hidden-acceptance gate before merge:** adapter contracts,
validation completeness, money math, SLAs, auth/audit correctness, any task
where the spec is richer than the visible assertion.

See [reports/north-mini-analysis.md](reports/north-mini-analysis.md) for the
full breakdown, evaluator-agent verdicts, DeepSeek control comparison, and
a recommended deployment policy. Start with
[reports/REPORTS.md](reports/REPORTS.md) for the per-report index.

---

## How It Works

The harness creates deterministic challenge repos, asks OpenCode to fix them,
captures the resulting patch and test output, stores results in SQLite, writes
per-run artifacts, and shows the runs in a Streamlit dashboard.

The runner pipeline (`ci_vibe_lab/runner.py`) is:

1. write visible scenario repo
2. run baseline tests (must be red)
3. run OpenCode with the public prompt
4. run public tests
5. capture the `git diff` patch
6. inject hidden tests into the worktree
7. run hidden tests
8. persist all artifacts and metrics to SQLite

Hidden tests are **never present during the OpenCode call**. The model cannot
see them. A run where public tests pass and hidden tests fail is a
**false-green** — the model made CI green without fixing the contract.

See [docs/challenge-design.md](docs/challenge-design.md) for the eval
philosophy, pivots away from pass@1, and glimpses from the evidence.

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
- `config_deep_merge`: recursive config merge instead of shallow `dict.update`.
- `mutable_default_leak`: fixes Python mutable default argument state leak.

The `product_workflows` pack is a different set of small product/backend
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
- `silent_exception_swallower`: handles exceptions per-item instead of swallowing.

The `data_semantics` pack tests reasoning about what data *means* across
service boundaries:

- `metric_semantic_mismatch`: normalizes units between cents and dollars across
  API layers without breaking the raw metric API.
- `join_fanout`: fixes SQL Cartesian product inflation without dividing by counts.
- `api_pagination_boundary`: fetches all pages including the last partial page.
- `scd_temporal_join`: joins on temporal bounds for slowly changing dimensions.

The `maintenance_value` pack is the positive-value counterpart. These scenarios
are deliberately low-risk and non-adversarial: explicit contract, local blast
radius, deterministic verification, and cheap review.

- `generated_openapi_refresh`: refreshes stale generated OpenAPI output.
- `logger_warn_migration`: migrates deprecated `logger.warn()` calls.
- `utcnow_timezone_migration`: replaces naive UTC timestamps with aware UTC.
- `regression_test_gap`: adds a regression test for an already-fixed bug.
- `adapter_field_rename`: normalizes old/new third-party response fields.
- `fixture_schema_migration`: migrates stale JSON fixtures to the new schema.
- `docs_cli_sync`: synchronizes README command examples with the CLI parser.
- `import_hygiene_fix`: repairs package-safe imports without path hacks.
- `explicit_validation_matrix`: implements a small finite validation matrix.
- `batch_splitter_utility`: implements a pure batching helper.

## The Evaluator Agent

A separate agent reviews the model-under-test's patch. It is not a one-shot
classifier — it gets a workbench and can test a better fix before judging.

Each review directory contains:

- `EVALUATION_PACKET.md`: run metadata, challenge intent, trap, expected
  behavior, the model's patch, public/hidden test output, and a worktree
  snapshot.
- `BUDGET.md`: hard timeout plus soft working-time, token, tool-call, and
  shadow-fix budgets.
- `WORKING_BOARD.md`: visible notes for reproduction, contract hypothesis,
  shadow fix, and verdict.
- `workbench/seed_visible_repo`: original challenge repo before the model patch.
- `workbench/model_repo`: visible repo plus the model patch plus hidden
  acceptance tests.
- `workbench/shadow_repo`: scratch repo where the evaluator can test a better
  fix.
- `workbench/model_patch.diff`: exact patch produced by the model under test.
- `workbench/model_repo_test.txt`: reproduced public+hidden test result for
  the patched repo.

Final evaluator JSON is validated with Pydantic models in
`ci_vibe_lab/evaluator.py`. The schema forbids extra keys, bounds numeric
scores, constrains enum fields, and then checks evidence quotes against
exact packet substrings. In `--loose` mode, the raw evaluator output, stream,
and working board are preserved even if the summary JSON fails validation;
the report falls back to deterministic summary data so a bad evaluator
response does not hide the run.

## Setup

```bash
uv venv
source .venv/bin/activate
uv sync --extra app
```

You also need the OpenCode CLI installed and configured with at least one
model:

```bash
opencode providers
opencode models
```

## Run An Eval

List challenges:

```bash
uv run python -m ci_vibe_lab.runner list
uv run python -m ci_vibe_lab.runner list --pack product_workflows
uv run python -m ci_vibe_lab.runner list --pack maintenance_value
```

Prepare a single disposable challenge repo for inspection:

```bash
uv run python -m ci_vibe_lab.runner prepare \
  --challenge timezone_ci_only \
  --out /tmp/timezone-ci-only
```

Run all scenarios against a configured OpenCode model:

```bash
uv run ci-vibe-run run \
  --challenge all \
  --pack ci_forensics \
  --model "provider/model" \
  --agent build \
  --auto-approve
```

The model string must match the provider/model name from `opencode models`.
If you omit `--model`, OpenCode uses its configured default.

For a no-model harness smoke test:

```bash
uv run ci-vibe-run run --challenge dependency_api_change --no-opencode
```

That records the failing baseline and post-test state without invoking
OpenCode.

Run the positive-value maintenance pack with three attempts per task:

```bash
uv run ci-vibe-run run \
  --challenge all \
  --pack maintenance_value \
  --model opencode/north-mini-code-free \
  --agent build \
  --auto-approve \
  --timeout 900 \
  --runs 3 \
  --db data/maintenance-value-north-mini.sqlite \
  --runs-dir runs/maintenance-value-north-mini
```

Use `--resume` to skip (scenario, attempt) pairs already in the DB — safe to
re-run after an interruption. Use `--skip-timeouts` to skip scenarios that
previously timed out. Experiment IDs are printed at the start of every run;
reattach with `--experiment-id`.

## Inspect A Run

The runner stores the exact agent input/output envelope for every run:

- `prompt.txt`: the full prompt sent to OpenCode.
- `opencode_stdout.jsonl`: raw OpenCode event stream.
- `opencode_stderr.txt`: OpenCode stderr and timeout messages.
- `public.txt`: visible CI output after the agent exits.
- `hidden.txt`: hidden acceptance output after hidden tests are injected.
- `patch.diff`: the final `git diff` produced by the agent.

To test the harness yourself without spending model tokens:

```bash
uv run ci-vibe-run run \
  --challenge dependency_api_change \
  --no-opencode \
  --db /tmp/ci-vibe-smoke.sqlite \
  --runs-dir /tmp/ci-vibe-smoke-runs

uv run ci-vibe-run inspect \
  --db /tmp/ci-vibe-smoke.sqlite \
  --latest \
  --full
```

To inspect the latest real North Mini Code run for one challenge:

```bash
uv run ci-vibe-run inspect \
  --db data/results.sqlite \
  --latest \
  --scenario metric_semantic_mismatch \
  --model opencode/north-mini-code-free \
  --full
```

## Reports

Generate a deterministic hidden-failure report:

```bash
uv run ci-vibe-report hidden-failures \
  --db data/north-mini-code-eval.sqlite \
  --out reports/hidden-failures.md
```

Generate the defensible evidence-pack report (combines multiple DBs, includes
severity-weighted scoring and scenario audit status):

```bash
uv run ci-vibe-report xray \
  --db data/north-mini-code-eval.sqlite \
  --db data/results.sqlite \
  --db data/control-results.sqlite \
  --model opencode/north-mini-code-free \
  --out reports/north-mini-code-evidence-pack-2026-06-20.md \
  --include-artifact-index
```

Generate the positive maintenance-value report:

```bash
uv run ci-vibe-report value \
  --db data/maintenance-value-north-mini.sqlite \
  --model opencode/north-mini-code-free \
  --pack maintenance_value \
  --out reports/north-mini-maintenance-value-2026-06-20.md \
  --include-artifact-index
```

## Evaluator Agent

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

Watch the evaluator stream live on one public-green/hidden-red run:

```bash
uv run ci-vibe-evaluate run \
  --db data/results.sqlite \
  --hidden-only \
  --public-green-only \
  --target-model opencode/north-mini-code-free \
  --model deepseek/deepseek-v4-pro \
  --auto-approve \
  --out runs/evaluator-agent/deepseek-v4-pro-live-smoke \
  --report reports/deepseek-v4-pro-live-smoke-2026-06-19.md \
  --timeout 120 \
  --max-rows 1 \
  --stream \
  --loose \
  --budget-minutes 4 \
  --token-budget 6000 \
  --tool-call-budget 18 \
  --shadow-fix-mode optional \
  --shadow-fix-budget-minutes 2
```

Index completed evaluator-agent review directories into SQLite:

```bash
uv run ci-vibe-evaluate ingest \
  --db data/results.sqlite \
  --reviews runs/evaluator-agent/deepseek-v4-pro-north-mini-expanded-pghr
```

Inspect the full evaluator envelope after the run:

```bash
find runs/evaluator-agent/deepseek-v4-pro-live-smoke -maxdepth 2 -type f
cat runs/evaluator-agent/deepseek-v4-pro-live-smoke/*/WORKING_BOARD.md
cat runs/evaluator-agent/deepseek-v4-pro-live-smoke/*/evaluation.json
```

## Dashboard

```bash
uv run --extra app streamlit run ci_vibe_lab/dashboard.py
```

Five tabs:

- **Report**: trust gap, false-green rate, severity-weighted failure,
  product-workflow stress, maintenance value mode, and result matrices.
- **Runs**: run table, failure inbox, and model-vs-model comparison.
- **Inspector**: challenge card, prompt, test logs, OpenCode trace, patch,
  human review scores, review decision, and manual review minutes.
- **Evidence**: evaluator reviews, review artifacts, and scenario audit status.
- **Exports**: filtered CSVs and Markdown report downloads.

By default the dashboard reads `data/results.sqlite`. Override with
`CI_VIBE_DB`:

```bash
# Single DB
CI_VIBE_DB=/path/to/results.sqlite uv run --extra app streamlit run ci_vibe_lab/dashboard.py

# Compare multiple DBs
CI_VIBE_DB="data/north-mini-code-eval.sqlite,data/results.sqlite,data/control-results.sqlite" \
  uv run --extra app streamlit run ci_vibe_lab/dashboard.py

# Include maintenance-value results
CI_VIBE_DB="data/maintenance-value-north-mini.sqlite,data/north-mini-code-eval.sqlite,data/results.sqlite" \
  uv run --extra app streamlit run ci_vibe_lab/dashboard.py
```

## Files Written By Runs

Runtime output is intentionally ignored by git:

- `runs/worktrees/`: generated scenario worktrees (each is a tiny git repo so
  the runner can capture the patch with `git diff`)
- `runs/artifacts/`: prompts, test logs, OpenCode output, and patches
- `runs/evaluator-agent/`: per-run evaluator review directories
- `data/*.sqlite`: SQLite result databases

See `AGENTS.md` for repo-wide agent guidance, project rules, and deeper
documentation pointers.

## Verify The Harness

```bash
uv run python -m unittest discover -s tests -v
```

This runs the harness self-tests — scenario validity, DB migration, evaluator
schema validation, report generation — without spending model tokens.
