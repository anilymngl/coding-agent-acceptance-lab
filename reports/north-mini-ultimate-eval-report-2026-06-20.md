# North Mini Code Ultimate Eval Report

## Technical Summary

**Main result:** North Mini Code behaves like a credible small-active coding agent, not like a
semantic acceptance oracle. In this harness it is extremely good at reaching visible public
green states, but hidden acceptance exposes a large trust gap on product and business contracts.

- North Mini canonical evidence: 57 attempts across 4 packs; public pass 57/57 (100.0%); hidden pass 31/57 (54.4%); false-green 26/57 (45.6%).
- Like-for-like stress control set: North Mini hidden pass 16/33 (48.5%) versus DeepSeek hidden pass 19/33 (57.6%).
- Product workflows are the failure microscope: North Mini hidden pass 2/11 (18.2%) and false-green 9/11 (81.8%); DeepSeek control is only 3/11 (27.3%) hidden-pass.
- Maintenance work is the positive-value counterexample: North Mini reaches 6/10 (60.0%) best-of-3 scenario success and 11.32 accepted patches per review hour on bounded, explicit maintenance tasks.

**Defensible interpretation:** the model is useful when a workflow supplies narrow tasks, fast
public feedback, deterministic hidden gates, and human review. It is risky when public green is
treated as acceptance for policy-heavy product logic, money math, authorization, audit, or data
semantic boundaries.

## What Was Measured

The harness measures the gap between visible CI repair and hidden contract repair.

- Public tests are visible to the OpenCode agent during the run.
- Hidden tests are injected after the agent exits.
- A false-green is `public_pass=1` and `hidden_pass=0`.
- Trust gap is public pass rate minus hidden pass rate.
- The maintenance pack reports both attempt-level pass rate and scenario-level best-of-3 success.
- The like-for-like control set uses 33 scenario units: 12 `ci_forensics`, 11 `product_workflows`, and 10 `maintenance_value` units.
- `data_semantics` is included for North Mini's own capability readout, but excluded from the DeepSeek comparison because no matching control run is present.

This report is generated from local SQLite run databases and should be read as a behavior
microscope, not a public leaderboard benchmark.

## Official Model-Card Connection

Cohere's public North Mini Code page, checked on 2026-06-20, identifies `north-mini-code-1-0`
as a 30B total / 3B active Mixture-of-Experts model with a 256K token context window and
64K max output tokens. It describes the model as trained for agentic coding, repo-level
software engineering in harnesses like SWE-Agent and OpenCode, terminal-based agents, local
coding, and code generation.

That official framing is consistent with what this harness sees: the model can drive the
coding-agent loop. The missing piece is acceptance reliability under sparse semantic contracts.
The Cohere page says it is competitive on software-engineering and terminal-agent benchmarks,
but it does not publish a numeric benchmark table on that page, so this report does not claim
an official Cohere accuracy number.

Reference links:

- Cohere North Mini Code docs: https://docs.cohere.com/docs/north-mini-code-1.0
- OpenCode docs: https://opencode.ai/docs/
- SWE-bench leaderboard methodology context: https://www.swebench.com/
- Terminal-Bench methodology context: https://www.tbench.ai/

## North Mini Scorecard

| Pack | Runs | Public Pass | Hidden Pass | Trust Gap | False-Green Rate | Extra Readout |
|---|---:|---:|---:|---:|---:|---|
| `ci_forensics` | 12 | 12/12 (100.0%) | 8/12 (66.7%) | 33.3% | 4/12 (33.3%) |  |
| `data_semantics` | 4 | 4/4 (100.0%) | 3/4 (75.0%) | 25.0% | 1/4 (25.0%) |  |
| `product_workflows` | 11 | 11/11 (100.0%) | 2/11 (18.2%) | 81.8% | 9/11 (81.8%) |  |
| `maintenance_value` | 30 | 30/30 (100.0%) | 18/30 (60.0%) | 40.0% | 12/30 (40.0%) | best-of-3 6/10; 11.32 accepted/hr |

**Readout:** public success is not the problem. North Mini made all 57 canonical public
attempts green. The problem is acceptance reliability after public green: 26 of those 57
public-green attempts were hidden-red.

## Strong-Model Control Scorecard

| Pack | Runs | Public Pass | Hidden Pass | Trust Gap | False-Green Rate | Extra Readout |
|---|---:|---:|---:|---:|---:|---|
| `ci_forensics` | 12 | 12/12 (100.0%) | 9/12 (75.0%) | 25.0% | 3/12 (25.0%) |  |
| `product_workflows` | 11 | 11/11 (100.0%) | 3/11 (27.3%) | 72.7% | 8/11 (72.7%) |  |
| `maintenance_value` | 30 | 30/30 (100.0%) | 18/30 (60.0%) | 40.0% | 12/30 (40.0%) | best-of-3 7/10; 10.73 accepted/hr |

**Readout:** DeepSeek is better on the like-for-like stress set, but not by enough to
invalidate the harness. It reduces false-greens, but the semantic trap remains visible.

## Like-For-Like Control Comparison

This comparison uses scenario units so the maintenance pack's three attempts do not dominate
the denominator. For `maintenance_value`, a scenario is counted as hidden-pass if any of the
three attempts produced an accepted hidden-passing patch.

| Model | Scenario Units | Public Pass | Hidden Pass | False-Green | Trust Gap |
|---|---:|---:|---:|---:|---:|
| North Mini Code | 33 | 33/33 (100.0%) | 16/33 (48.5%) | 17/33 (51.5%) | 51.5% |
| DeepSeek V4 Pro | 33 | 33/33 (100.0%) | 19/33 (57.6%) | 14/33 (42.4%) | 42.4% |

DeepSeek solved +3 more scenario units (9.1% hidden-pass-rate delta) and produced -3 false-green scenario units versus North Mini.

### North Mini Scenario-Level Pack Breakdown

| Pack | Scenario Units | Hidden Pass | False-Green | Note |
|---|---:|---:|---:|---|
| `ci_forensics` | 12 | 8/12 (66.7%) | 4/12 (33.3%) | single run per scenario |
| `product_workflows` | 11 | 2/11 (18.2%) | 9/11 (81.8%) | single run per scenario |
| `maintenance_value` | 10 | 6/10 (60.0%) | 4/10 (40.0%) | best hidden-passing result across three attempts |

### DeepSeek Scenario-Level Pack Breakdown

| Pack | Scenario Units | Hidden Pass | False-Green | Note |
|---|---:|---:|---:|---|
| `ci_forensics` | 12 | 9/12 (75.0%) | 3/12 (25.0%) | single run per scenario |
| `product_workflows` | 11 | 3/11 (27.3%) | 8/11 (72.7%) | single run per scenario |
| `maintenance_value` | 10 | 7/10 (70.0%) | 3/10 (30.0%) | best hidden-passing result across three attempts |

## Why DeepSeek Was Not Dramatically Better

**The control result is the most important sanity check in the whole report.** If a much larger
control model had crushed these tasks, the report would mostly be about North Mini's model
limit. Instead, DeepSeek improves the result but still fails many public-green cases.

Facts:

- `ci_forensics`: North Mini 8/12 (66.7%) hidden-pass; DeepSeek 9/12 (75.0%).
- `product_workflows`: North Mini 2/11 (18.2%) hidden-pass; DeepSeek 3/11 (27.3%).
- `maintenance_value`: North Mini 6/10 (60.0%) best-of-3; DeepSeek 7/10 (70.0%).
- Attempt-level maintenance hidden pass is identical: North Mini 18/30 (60.0%); DeepSeek 18/30 (60.0%).

Interpretation:

- The tasks compress frontier-model advantages. Repos are small, context is short, and the main question is not search depth; it is whether the agent infers the unstated contract behind weak visible tests.
- Visible public tests create an optimization attractor. Both models often stop when public CI is green, even when a stronger semantic reading would imply additional changes.
- Product workflows are policy-dense. They encode business rules like proration, audit redaction, idempotency, raw-body signatures, SLA calendars, and inventory conservation. These are small-code tasks but high-contract tasks.
- Maintenance tasks are explicit and local. That is why North Mini gets close to DeepSeek there: the job is bounded, the contract is clear, and the verifier is deterministic.

The conclusion is not that DeepSeek is weak. The conclusion is that this harness is probing a
different axis than many leaderboard-style coding evals: not raw repo repair, but whether public
green can be trusted as acceptance when the visible tests under-specify the product contract.

## Failure X-Ray

### North Mini False-Green Scenarios By Pack

**Product workflows are the sharpest warning sign.** Hidden failures there are not syntax
or import problems; they are missed domain rules.

`ci_forensics`:

- `csv_header_contract`
- `decimal_money_rounding`
- `dependency_api_change`
- `env_bool_parser`

`data_semantics`:

- `metric_semantic_mismatch`

`product_workflows`:

- `audit_log_redaction`
- `billing_proration`
- `bulk_invite_dedupe`
- `cart_discount_stack`
- `feature_rollout_bucket`
- `inventory_reservation_idempotency`
- `markdown_slug_collision`
- `search_ranking_stability`
- `support_sla_business_hours`

`maintenance_value` scenario-level false-greens:

- `adapter_field_rename`
- `batch_splitter_utility`
- `explicit_validation_matrix`
- `logger_warn_migration`

### Failure Categories

| Category | What It Means | Evidence Pattern |
|---|---|---|
| Assertion completion | The agent fixes the visible assertion and stops. | High public pass with hidden failures after injection. |
| Policy boundary miss | The patch handles the shown case but misses edge policy. | Product workflow false-greens in billing, SLA, discounts, inventory, audit, and webhook cases. |
| Semantic ownership error | The model changes the wrong layer of the system. | Data semantics tasks where raw APIs and user-facing aggregators need different treatment. |
| Local maintenance success | The agent performs bounded, explicit, low-blast-radius work well. | Maintenance best-of-3 success and accepted patches per review hour. |

## What North Mini Is Capable Of

**Operational loop competence is high.** It can read a small repository, identify failing tests,
edit code, run the loop, and return a patch. On the canonical North Mini evidence set, every
public test suite passed after the agent run.

**It is valuable for bounded maintenance.** The maintenance pack is deliberately not a trap
benchmark. It asks for useful chores: generated artifacts, deprecated API migrations, fixture
updates, doc/CLI sync, import hygiene, validation matrices, and pure helper implementation.
North Mini accepted 6 of 10 maintenance scenarios after three attempts each.

**It is not safe as an autonomous product-logic merger.** Product workflows are the opposite
shape: sparse visible tests, business policy under-specification, and acceptance conditions that
matter to users. North Mini passed all visible product tests but only 2 of 11 hidden acceptance
suites.

## What This Eval Does Differently

Most coding benchmarks ask whether the final submitted patch resolves a task. This harness asks
a narrower operational question: when the model makes CI green, how often is that green state
actually trustworthy?

| Standard Benchmark Lens | This Harness Lens | Why It Matters |
|---|---|---|
| Pass/fail resolution | Public-green versus hidden-red split | Separates visible repair from acceptance repair. |
| Broad task corpus | Curated semantic stress packs | Makes specific failure modes inspectable. |
| Single score | Trust gap plus false-green rate | Exposes confidently wrong patches. |
| Leaderboard comparison | Behavior microscope with controls | Supports deployment policy, not model marketing. |
| Hidden tests as final grade | Hidden tests as trust audit | Measures whether public CI can be trusted. |

## Deployment Policy

| Zone | Recommended Use | Required Gate | Rationale |
|---|---|---|---|
| Green | Mechanical maintenance, generated artifacts, fixture/doc sync, small pure utilities | Public tests, hidden acceptance, patch review | Evidence shows useful positive-value behavior. |
| Amber | Adapter changes, finite validation logic, low-blast-radius product helpers | Hidden tests plus reviewer who understands the contract | The model often gets close, but boundary cases matter. |
| Red | Money movement, auth, audit logging, tenant isolation, inventory, SLA, raw security signatures | Stronger model/control run plus domain review | Product-workflow false-greens are too frequent. |

## Harness Quality Check

The current evidence does not support dismissing the harness as simply unfair. Three checks point
the other way:

1. The maintenance pack is passable and useful, so hidden tests are not universally impossible.
2. The `ci_forensics` pack lands in the middle, so the harness is not only testing product policy.
3. The DeepSeek control improves results but still struggles on product workflows, so the product pack is broadly hard under this setup.

Still, the harness is not a public benchmark yet. It needs more seeds, more control models,
scenario audits by someone other than the author, and evaluator agreement checks before it can
support broad model-ranking claims.

## Partial GLM-5.2 Snapshot

The GLM-5.2 run is partial: 4 `ci_forensics` rows only. It is useful as
a smoke signal, not as a comparison baseline.

| Model | Pack | Runs | Public Pass | Hidden Pass | False-Green |
|---|---|---:|---:|---:|---:|
| GLM-5.2 | `ci_forensics` | 4 | 4/4 (100.0%) | 2/4 (50.0%) | 2/4 (50.0%) |

## Claim Ledger

| Claim | Evidence | Confidence | Caveat |
|---|---|---|---|
| North Mini can execute the OpenCode repair loop | Public pass 57/57 (100.0%) | high | Small curated repos; not a full production workload sample. |
| North Mini has a large trust gap after public green | False-green 26/57 (45.6%) | high | Hidden tests encode authored contracts; external audit would strengthen legitimacy. |
| Product workflows are the main red zone | North Mini product hidden pass 2/11 (18.2%) | high | The pack is intentionally policy-dense and not a random sample of backend work. |
| DeepSeek improves but does not collapse the trust gap | Like-for-like hidden pass 19/33 (57.6%) vs North 16/33 (48.5%) | medium-high | Single control model and mostly single-seed outside maintenance. |
| North Mini has positive maintenance value | Maintenance best-of-3 6/10 (60.0%) and 11.32 accepted/hr | medium-high | Review-hour estimate is heuristic unless manually overridden. |

## What Can And Cannot Be Defended

**Can defend from this evidence:**

- North Mini Code is operationally competent inside the OpenCode loop on these small repos.
- Public pass alone is not a reliable acceptance signal for the semantic/product packs.
- The product-workflow pack reveals a large public-green/hidden-red trust gap.
- Bounded maintenance tasks are a realistic useful operating zone for the model.
- DeepSeek's control run shows these semantic traps are not only a North Mini artifact.

**Cannot defend yet:**

- A broad leaderboard ranking of North Mini versus DeepSeek or GLM.
- A statistically stable model accuracy estimate.
- That all product/backend work has this failure rate.
- Official Cohere benchmark accuracy; no numeric official table was present on the checked public page.

## Reproduce This Report

Generate the report:

```bash
uv run ci-vibe-report ultimate --out reports/north-mini-ultimate-eval-report-2026-06-20.md
```

The command uses these default source databases when present.

### North Mini Sources

| Source DB | Exists | Runs |
|---|---:|---:|
| `data/ci-forensics-v2.sqlite` | yes | 12 |
| `data/product-workflows-v2.sqlite` | yes | 11 |
| `data/maintenance-value-v2.sqlite` | yes | 30 |
| `data/results.sqlite` | yes | 19 |

### DeepSeek Control Sources

| Source DB | Exists | Runs |
|---|---:|---:|
| `data/ci-forensics-deepseek.sqlite` | yes | 12 |
| `data/control-results.sqlite` | yes | 11 |
| `data/maintenance-deepseek.sqlite` | yes | 30 |

### Partial Control Sources

| Source DB | Exists | Runs |
|---|---:|---:|
| `data/ci-forensics-glm52.sqlite` | yes | 4 |

## Recommended Next Work

1. Finish the GLM-5.2 control run or remove it from comparison materials.
2. Run one additional strong model on `product_workflows` to test whether DeepSeek's product failures are model-specific or task-family-specific.
3. Add external scenario audit notes for every hidden test in product workflows and data semantics.
4. Add evaluator-agreement checks: DeepSeek evaluator plus at least one second evaluator model on the false-green set.
5. Only after that, run multi-seed scaling and publish a leaderboard-style summary.

