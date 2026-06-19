# North Mini Code in OpenCode: Capability X-Ray

Date: 2026-06-19  
Harness: `ci_vibe_lab.runner` plus OpenCode CLI  
Model under test: `opencode/north-mini-code-free`  
Primary database: `data/north-mini-code-eval.sqlite`  
Expanded database: `data/results.sqlite`  
Evaluator model: `deepseek/deepseek-v4-pro`

## Executive Read

North Mini Code looks strong when the task is "make visible CI green." Across 27
curated local coding-agent runs, it passed public tests in 26 cases. That is the
good news: it can operate through OpenCode, inspect a small repo, make focused
edits, and usually finish the basic workflow.

The hidden acceptance layer changes the trust picture. Only 12 of 27 runs passed
hidden tests. Fourteen runs were public-green/hidden-red. The dominant failure
mode is not syntax, tool use, or inability to edit files. It is semantic
incompleteness: the model fixes the visible symptom, then misses the fuller
contract behind the task.

My practical read: North Mini Code is a useful cheap first-pass coding agent for
small local repairs, but it needs hidden acceptance, model review, or human
review around product semantics, money, state mutation, auth/security-ish
boundaries, business calendars, ranking, and data contracts.

## What The Model Is

Facts from Cohere's North Mini Code documentation:

- Model ID: `north-mini-code-1-0`.
- Architecture claim: 30B total / 3B active parameter mixture-of-experts model.
- Context and output: 256K context window and 64K max output tokens.
- Intended use: agentic software engineering inside harnesses such as SWE-Agent
  and OpenCode, terminal-based agents, local/on-device coding, and code
  generation.
- Release posture: Apache 2.0 license, free until rate limits, production through
  Cohere Model Vault.
- Cohere says it was trained against multiple harnesses and is meant to
  generalize across agent scaffolds rather than overfit one harness.

Important limitation: on the official Cohere page checked on 2026-06-19, I found
qualitative claims about competitiveness on software-engineering and
terminal-agent benchmarks, but no numeric benchmark table for North Mini Code.
This report should therefore not pretend to compare against official North Mini
scores. It compares our observed local OpenCode behavior to the model card's
intended use.

Sources:

- Cohere North Mini Code docs: https://docs.cohere.com/docs/north-mini-code-1.0
- OpenCode docs: https://opencode.ai/docs/
- SWE-bench leaderboard design: https://www.swebench.com/
- Terminal-Bench overview: https://www.tbench.ai/
- Aider leaderboard design: https://aider.chat/docs/leaderboards/

## What We Evaluated

This is not a leaderboard benchmark. It is a small, deterministic behavior
microscope for coding agents.

The runner creates a disposable repo for each challenge, confirms the visible
test starts red, asks OpenCode to fix it, captures the final patch and all
OpenCode output, runs public tests, injects hidden acceptance tests, then runs
the full suite again. The hidden tests are not present during the model call.

The saved model-under-test envelope includes:

- `prompt.txt`: full prompt sent to OpenCode.
- `opencode_stdout.jsonl`: raw OpenCode event stream.
- `opencode_stderr.txt`: stderr and timeout messages.
- `public.txt`: visible CI output after the agent exits.
- `hidden.txt`: hidden acceptance output after hidden tests are injected.
- `patch.diff`: final model patch.

The evaluator-agent layer is now a second agent workflow, not a one-shot JSON
classifier. Each evaluation directory includes:

- `BUDGET.md`: hard timeout plus soft working-time, token, tool-call, and
  shadow-fix budgets.
- `WORKING_BOARD.md`: evaluator's live working board.
- `workbench/model_repo`: original visible repo plus model patch plus hidden
  tests.
- `workbench/shadow_repo`: scratch repo where the evaluator can test a better
  fix.
- `evaluation.agent.json`: raw evaluator JSON, preserved before normalization.
- `evaluation.json`: Pydantic-validated summary JSON.
- `evaluator_stdout.jsonl`: full evaluator-agent stream.

The JSON schema is enforced with Pydantic models in `ci_vibe_lab/evaluator.py`.
It forbids extra keys, constrains enum values, bounds scores and confidence, and
requires evidence objects. The harness then adds semantic validation: evidence
quotes must be exact substrings from `EVALUATION_PACKET.md`; hidden failures
must cite hidden-test output and either patch or challenge-contract evidence.

Loose mode is deliberately loose around process behavior, not loose around
accountability. The evaluator may spend more time, inspect files, and use a
shadow fix. If it fails the JSON contract, the raw working board and stream are
kept, and the report falls back to deterministic summary JSON.

## Result Summary

| Dataset | Cases | Public Pass | Hidden Pass | Public Green / Hidden Red | Public Red | Read |
|---|---:|---:|---:|---:|---:|---|
| Primary `ci_forensics` | 10 | 10/10 | 6/10 | 4/10 | 0/10 | Strong visible CI repair; hidden tests expose contract misses. |
| Expanded packs | 17 | 16/17 | 6/17 | 10/17 | 1/17 | Product workflows are much harder than CI-forensics. |
| Combined | 27 | 26/27 | 12/27 | 14/27 | 1/27 | Public success rate is high; trust rate is much lower. |

The combined public-pass rate is 96.3 percent. The combined hidden-pass rate is
44.4 percent. Among public-green runs, 14 of 26 were hidden-red. That is the
central signal: public green is not enough for this model on these tasks.

## Expanded Pack Breakdown

| Pack | Cases | Public Pass | Hidden Pass | Public Green / Hidden Red | Public Red |
|---|---:|---:|---:|---:|---:|
| `ci_forensics` additions | 2 | 2/2 | 2/2 | 0/2 | 0/2 |
| `data_semantics` | 4 | 4/4 | 3/4 | 1/4 | 0/4 |
| `product_workflows` | 11 | 10/11 | 1/11 | 9/11 | 1/11 |

The product-workflow pack is the stress test that mattered most. It revealed
that the model can often satisfy the public example while missing the real
business rule. Examples:

- `audit_log_redaction`: shallow secret replacement missed nested/list secrets.
- `billing_proration`: rounded/clamped incorrectly at a cent boundary.
- `bulk_invite_dedupe`: did not fully normalize email casing/spacing.
- `cart_discount_stack`: allowed a negative total instead of applying a zero floor.
- `feature_rollout_bucket`: used the wrong stable bucket boundary.
- `inventory_reservation_idempotency`: mutated stock on insufficient inventory.
- `markdown_slug_collision`: did not normalize punctuation and repeated collisions.
- `search_ranking_stability`: missed deterministic recency tie-break behavior.
- `support_sla_business_hours`: missed weekend and business-hour edge cases.

## Capability X-Ray

### 1. Agent Workflow: Strong

The model consistently performed the basic coding-agent loop: inspect files, run
tests, edit narrowly, rerun tests, exit. In the primary 10-case run, every
OpenCode process exited 0 and every public test suite passed.

This aligns with Cohere's positioning: North Mini Code is explicitly meant for
repo-level code changes in OpenCode/SWE-Agent-like harnesses and terminal-based
agents.

### 2. Local Bug Repair: Strong

It did well when the correct fix was local and the contract was visible:

- `pagination_cursor_drift`: followed `next_cursor` until exhaustion.
- `timezone_ci_only`: used the account timezone explicitly.
- `tenant_cache_leak`: moved cache identity to tenant/user composite keys.
- `stale_generated_schema`: updated the generated artifact.
- `webhook_signature_raw_body`: verified HMAC against raw bytes.
- `scd_temporal_join`: handled temporal joins correctly.
- `api_pagination_boundary`: handled pagination boundaries correctly.

This is the useful operating zone: small repos, clear local contract, narrow
patch, visible tests that actually represent the rule.

### 3. Semantic Completeness: Weak To Mixed

The hidden failures are mostly places where the public test was only one example
of a broader rule:

- Money math: `Decimal` was used, but half-up cent policy was missed.
- Unit semantics: cents/dollars normalization was placed in the wrong API layer.
- CSV export: header ordering was fixed, but empty export and extra-field
  filtering were missed.
- Dependency boundary: `ok` was checked, but the new response `id` was not
  propagated as `charge_id`.
- Boolean config: common false strings were handled, but empty/whitespace cases
  still enabled flags.

This means the model often identifies the right neighborhood, then stops too
soon.

### 4. Product Workflow Reasoning: Weak

The product-workflow result is the hardest evidence against blind trust: 10 of
11 public tests passed, but only 1 of 11 hidden suites passed. These were not
large systems. They were small but semantically loaded functions: invitations,
discounts, reservations, ranking, audit logs, SLA calendars.

That is exactly the work real engineering teams care about. The model can make
CI happy while leaving product behavior wrong.

### 5. Debug Discipline: Adequate, But Public-Test Anchored

The model generally reruns tests after editing. The weakness is not that it
ignores tests. The weakness is that it treats the visible test suite as the
contract boundary. It rarely expands from "this assertion fails" to "what full
policy does this represent?"

## Evaluator-Agent Smoke Result

The live DeepSeek evaluator smoke was run on `metric_semantic_mismatch`:

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

The evaluator streamed its work, inspected the packet and workbench, reproduced
the model failure in `model_repo`, edited only `shadow_repo`, ran hidden tests
there, and wrote valid Pydantic JSON.

Its verdict was `public_green_hidden_red`: North Mini normalized values inside
`compute()`, but the challenge contract required `compute()` to return raw source
values and `dashboard_total()` to normalize user-facing totals.

Key artifact paths:

- `runs/evaluator-agent/deepseek-v4-pro-live-smoke/*/WORKING_BOARD.md`
- `runs/evaluator-agent/deepseek-v4-pro-live-smoke/*/evaluation.json`
- `runs/evaluator-agent/deepseek-v4-pro-live-smoke/*/evaluation.agent.json`
- `runs/evaluator-agent/deepseek-v4-pro-live-smoke/*/evaluator_stdout.jsonl`
- `reports/deepseek-v4-pro-live-smoke-2026-06-19.md`

## How This Differs From Standard Evals

SWE-bench reports percent of resolved software-engineering instances across
large issue-derived tasks. The current SWE-bench site describes `% Resolved` as
the core metric, with sets such as 2294 Full, 500 Verified, and 300 Lite.

Terminal-Bench measures terminal-agent task success across terminal
environments; the site lists Terminal-Bench 2.0 as 89 high-quality tasks across
software engineering, machine learning, security, data science, and more.

Aider's polyglot benchmark uses 225 challenging Exercism coding exercises across
C++, Go, Java, JavaScript, Python, and Rust.

Those evals are useful for broad comparison. This harness is different:

- It is small by design.
- It is deterministic and easy to replay locally.
- It isolates the public-green/hidden-red split.
- It preserves the full agent I/O envelope.
- It treats hidden failure analysis as an audited second-agent workflow.
- It measures the trust gap between "CI is green" and "the contract is correct."

That trust gap is not a replacement for leaderboard score. It is a missing axis.

## Challenge To The Status Quo

Current coding-agent reporting overweights "resolved" and underweights "why the
patch was trustworthy." For agentic coding models, a model card should report
more than a single pass rate:

- public-pass rate
- hidden-pass rate
- public-green/hidden-red rate
- timeout rate
- average patch size
- test rerun behavior
- cost/time/tool-call profile
- evaluator-agent verdict distribution
- examples of shadow fixes for failed runs

For North Mini Code specifically, the official story is "small active footprint,
agentic coding, terminal agents, competitive with larger open-source models."
Our local evidence supports the workflow part. It challenges the implicit trust
part: being an effective terminal coding agent does not mean the model reliably
infers unstated domain contracts from sparse public tests.

## Reproduce And Inspect

Run unit tests for the harness:

```bash
uv run python -m unittest discover -s tests -v
```

Inspect the latest model-under-test envelope:

```bash
uv run ci-vibe-run inspect \
  --db data/results.sqlite \
  --latest \
  --scenario metric_semantic_mismatch \
  --model opencode/north-mini-code-free \
  --full
```

Rebuild the evaluator report from existing evaluator artifacts:

```bash
uv run ci-vibe-evaluate report \
  --reviews runs/evaluator-agent/deepseek-v4-pro-live-smoke \
  --out reports/deepseek-v4-pro-live-smoke-2026-06-19.md
```

Watch a fresh evaluator run stream live:

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

## Caveats

This is a curated local eval, not a statistically representative public
benchmark. Most challenges have one run, not multiple seeds. The hidden tests
are authored by us, so their quality matters. The evaluator-agent has been smoke
tested on one live streamed workbench run after the architecture change; broader
evaluator coverage should be run before using its aggregate scores as a
publication-grade metric.

OpenCode currently enforces the hard process timeout. The token and tool-call
budgets in `BUDGET.md` are prompt-level operating budgets because `opencode run`
does not expose native token/tool-call limit flags in the local CLI help.

## Bottom Line

North Mini Code is credible as a fast local coding-agent model for focused,
visible CI repair. It is not yet credible, from this eval alone, as an
autonomous product-semantics maintainer. The failure signature is useful and
actionable: give it tight repos, clear contracts, and tests that represent the
real policy; do not trust public-green alone.

