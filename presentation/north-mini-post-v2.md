# What a coding-agent eval should look like

*Weekend project. 132 runs. 37 scenarios. One question.*

Most coding-agent evals measure whether the model can generate code. But the
thing you'll actually ask an agent to do is **fix red CI**. And nobody tests
whether the fix is real — or whether the model just made the light turn green.

If you optimize for CI pass rate, you get models that delete assertions,
catch-and-swallow exceptions, and return hardcoded values. The test passes.
The bug doesn't.

So I built a harness that measures exactly this gap.

## The idea: public vs hidden

Every scenario has two test layers.

Public tests — the model sees them during the run. This is what a real CI
pipeline would show. Hidden tests — injected **after** the agent exits. These
check the full contract. Edge cases the public test missed. Backward
compatibility it didn't cover.

Three outcomes:

| Public CI | Hidden acceptance | What it means |
|---|---|---|
| green | green | real fix |
| green | red | **false-green — CI passed, bug not fixed** |
| red | — | couldn't close CI at all |

Headline metric: **trust gap** = public pass rate − hidden pass rate. A 30%
gap means 3 out of 10 green-CI patches are fake. This is not "accuracy."
It's "how often the CI signal lies to you."

Why is the gap structural? Because visible tests create an **optimization
attractor**. The model optimizes for what it can see — the public test. It
stops when CI is green. It doesn't know there's more to check. The hidden
test measures what it would have caught if it kept going.

## The pipeline: make the evaluator prove it

When a row comes back false-green, a separate DeepSeek evaluator agent gets
a workbench: the original repo, the model's patch, the hidden tests, the
trajectory, and a blank `shadow_repo`. It can write an alternative fix and
run hidden tests against it. The verdict — and every quote it cites — must
appear **verbatim** in the evidence packet. Pydantic enforces this. LLMs
hallucinate evidence. This makes that impossible.

Runtime failures get classified separately. A `no_output_timeout` (model
produced zero output within the first-output window) is not a false-green.
It is deployability data. Conflating stalls with wrong answers produces
garbage. Every row carries an outcome classification: semantic (hidden_pass,
false_green, public_red) or operational (timeout, stall, config error).

## The matrix: isolate what actually matters

One model on one pack = anecdote. The matrix isolates three things:

1. **Model** — North Mini (Cohere-built, tool-calling native, API) vs
   Gemma 4 12B (general-purpose, local Ollama, foreign agent surface)
2. **Prompt** — sparse ("CI is red, fix it") vs contract-visible (full
   acceptance criteria in the prompt). Infer the rule or implement the rule.
3. **Work type** — ci_forensics (12 CI bugs), maintenance (10 refactors),
   product_workflows (11 business-logic tasks). Low to high semantic density.

The contract-visible lane is the treatment. The sparse lane is the control.
The gap between them tells you: is this a capability wall, or is it just
that nobody told the model what "done" means?

## The finding

132 pass@1 runs. SQLite, queried directly:

| | North Mini sp | North Mini cv | Gemma 12b sp | Gemma 12b cv |
|---|---:|---:|---:|---:|
| ci_forensics (12) | pub 12 hid 8 **gap 33%** | pub 12 hid 11 **gap 8%** | pub 5 hid 3 **gap 16%** | pub 7 hid 6 **gap 8%** |
| maintenance (10) | pub 10 hid 8 **gap 20%** | pub 9 hid 9 **gap 0%** | pub 9 hid 7 **gap 20%** | pub 7 hid 6 **gap 10%** |
| product (11)* | pub 6 hid **0** gap 100% | stalled (infra) | pub 6 hid 2 **gap 36%** | pub 6 hid 5 **gap 11%** |

Contract-visible works. But it helps the two models differently:

**North Mini already gets CI green.** The contract doesn't create new greens —
it reclassifies existing ones. ci_forensics: 4 false-greens → 1. maintenance:
2 → 0. The model stops too soon under sparse — fixes the specific assertion
that failed, not the rule it represents. Give it the rule, it delivers.

**Gemma 12B often can't close CI at all under sparse.** The contract acts as
scaffolding — it helps the model produce a working patch where it couldn't
before. ci_forensics: 7 public-reds → 5 public-reds. Hidden pass: 3 → 6.
The model has the capability; it needs the spec to unlock it.

**Product workflows are the red zone.** North Mini completed 6 sparse
scenarios. All 6 false-greens. Zero hidden passes. Direct business logic
(billing math, discount stacking, inventory state) without explicit
acceptance criteria — the model consistently produces surface-level fixes
that don't hold.

Three scenarios (`env_bool_parser`, `adapter_field_rename`, `batch_splitter_utility`)
failed across **every** model and lane. Contract-visible cracked at least
one of them per model. These are spec-exposure problems — the model wasn't
incapable, it was uninformed.

## What this cannot tell you (honestly)

**pass@1 is noisy.** Gemma 12B's maintenance hidden pass swung from 4/10 to
7/10 across two same-day runs. A 30-point delta. Same model, same pack.
Single-attempt numbers describe an attempt. pass@3 is the floor for saying
anything about a model's characteristic behavior.

**This is a system comparison, not a model ranking.** North Mini runs on
its native tool surface (Cohere-built for OpenCode's agent format). Gemma
12B runs through a foreign agent loop on local Ollama. Tool-loop reliability
and inference speed confound raw capability. I am measuring system behavior,
not abstract model quality — and the deployment claim is about which work
you can safely delegate, not which model is "better."

**37 scenarios. One evaluator. No external audit.** The hidden tests and
evaluator verdicts are mine. Tier 1 evidence — behavior microscope only.
Tier 2 (comparative claims) needs evaluator agreement. Tier 3 (public
benchmark) needs external audit. This is Tier 1.

## Deploy it like this

The finding isn't "use X model." It's: partition your CI repair by task type.

- **Green: merge on CI green.** Mechanical maintenance — generated artifacts,
  logger migrations, fixture updates, docs sync. Both models are reliable here
  with an explicit contract.
- **Amber: gate on hidden acceptance.** Adapters, validators, cache keys,
  CSV headers. The visible test is incomplete. The hidden test catches gaps.
- **Red: human review or skip.** Billing, discounts, inventory, SLA windows,
  money math. The policy density is too high for current pass@1 reliability.

The model is replacable. The trust gate is the enduring investment. That is
the pipeline I would build if I were shipping this into production tomorrow.

---

*Repo: [github.com/anomalyco/north-mini-test](https://github.com/anomalyco/north-mini-test)*
*Evidence deck: ci-harness-4.html (in /presentation)*
*132 runs. 2 models. 3 packs. 2 lanes. pass@1. Tier 1.*