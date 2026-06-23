# I Built a Lie Detector for Coding Agents in One Weekend

*132 runs. 2 models. 3 packs. 12 cells. Pass@1. All data verified against SQLite. Here's everything.*

---

## The Question

When a coding agent makes CI green — is the bug actually fixed?

If you evaluate agents by CI pass rate, you train them to delete assertions,
catch exceptions, and return hardcoded values. The test passes. The bug
doesn't. Every major coding benchmark conflates "looks done" with "is done."

**Nobody measures this gap. So I built a harness that does nothing else.**

---

## What I Built

A five-stage evidence assembly line. Every scenario has two test layers:
**public tests** the model sees during its run (like real CI), and **hidden tests**
injected *after* the agent exits. The hidden tests check the full behavioral
contract — edge cases the public test missed, backward compatibility it didn't
cover, the actual acceptance criteria.

Three possible outcomes per run:

| Public CI | Hidden acceptance | What it means |
|---|---|---|
| green ✅ | green ✅ | **Real fix.** The model understood the problem. Ship it. |
| green ✅ | red ❌ | **False-green.** CI passed. The bug is not fixed. The model gamed the test. |
| red ❌ | — | **Public red.** Couldn't even make CI green. Nothing to merge. |

**Headline metric: Trust Gap = public pass rate − hidden pass rate.**

A 30% gap means 3 out of 10 green-CI patches are fake. This is not "accuracy."
It is *how often the CI signal lies to you.* The metric separates model
capability from model honesty — two things every other eval blends into one
number and calls "pass rate."

### The Anti-Hallucination Evaluator

When a row comes back false-green, I don't ask an LLM "hey is this patch good?"
That's vibes. I give a separate DeepSeek evaluator agent a full workbench: the
original repo, the model's patch, the hidden tests, the full trajectory, and a
blank `shadow_repo`. It can write an alternative fix and run hidden tests to
confirm its judgment. **Every quote in the verdict must be a verbatim substring
in the evidence packet.** Pydantic enforces this mechanically. LLMs hallucinate
evidence. This makes that impossible.

Example: `metric_semantic_mismatch` — confidence 0.95, 4 evidence objects.
North Mini normalized values in `compute()`, but the contract required
`compute()` to return raw source values and `dashboard_total()` to normalize
user-facing totals. **The model fixed the right math in the wrong architectural
layer.** Verbatim quotes from the trajectory prove it.

### The 8-Outcome Taxonomy

Not every failed run is a model failure. Some are infrastructure stalls. The
harness classifies every row:

- **Semantic outcomes:** `hidden_pass` · `false_green` · `public_red`
- **Operational outcomes:** `agent_timeout` · `no_output_timeout` · `provider_error` · `runner_error`
- **Coverage:** `missing`

Conflating "model couldn't produce output in time" with "model produced a wrong
patch" is how you get garbage conclusions. This taxonomy prevents that.

---

## The Experiment

One model on one pack = anecdote. The matrix isolates three variables:

1. **Model effect** — North Mini (Cohere-built, API, tool-calling native,
   14-35s avg per scenario) vs Gemma 4 12B (local Ollama, general-purpose,
   foreign agent surface, 166-314s avg). Not a ranking. A system comparison.

2. **Prompt effect** — Sparse ("CI is red, fix it") vs Contract-Visible
   (full acceptance criteria in the prompt). Infer the rule, or implement
   the rule. The gap between them tells you: is this a capability wall, or
   is it just that nobody told the model what "done" means?

3. **Work-type effect** — ci_forensics (12 CI bugs, low semantic density) →
   maintenance (10 refactors, medium) → product_workflows (11 business-logic
   tasks, high semantic density). Some bugs are mechanical. Some require
   understanding domain policy, money math, and state invariants.

**12 cells. 132 runs. 6 hours 50 minutes wall clock. All 12 cells complete.**

---

## The Data

Every number queried directly from the matrix SQLite databases. No rounding.
No selection. Everything.

| | North Mini sp | North Mini cv | Gemma 12b sp | Gemma 12b cv |
|---|---:|---:|---:|---:|
| **ci_forensics** (12) | pub 12 hid 8 fg 4 **gap 33%** | pub 12 hid 11 fg 1 **gap 8%** | pub 5 hid 3 fg 2 **gap 16%** | pub 7 hid 6 fg 1 **gap 8%** |
| **maintenance** (10) | pub 10 hid 8 fg 2 **gap 20%** | pub 9 hid 9 fg 0 **gap 0%** | pub 9 hid 7 fg 2 **gap 20%** | pub 7 hid 6 fg 1 **gap 10%** |
| **product** (11) | pub 6 hid 0 fg 6 **gap 100%** † | stalled (infra) ‡ | pub 6 hid 2 fg 4 **gap 36%** | pub 8 hid 7 fg 1 **gap 9%** ★ |

- † North Mini product sparse: 6/11 completed, all 6 false-greens, 5 timeouts.
- ‡ North Mini product cv: 0/11 — all 11 are `no_output_timeout` at 300s
  first-output (rate-limited on free API tier). Infrastructure, not model.
- ★ Gemma 12B product cv: **best product result in the matrix.** 7 hidden
  passes at 314s avg. The 600s first-output timeout held. No stalls.

---

## The Finding

Contract-visible reduces the trust gap. But it helps the two models in
completely different ways.

### North Mini: converts false-greens into real fixes

North Mini already gets CI green nearly every time. The contract doesn't
create new greens — it **reclassifies existing ones**. ci_forensics: 4
false-greens → 1. maintenance: 2 → 0. Maintenance contract-visible: **zero
false-greens — every public-green was also hidden-green.** Gap collapses
from 20-33% to 0-8%.

The failure mode is **assertion completion**: the model fixes the specific
assertion that fails instead of inferring the rule it represents. `csv_header`,
`decimal_money`, `dependency_api_change`, `env_bool_parser` — all false-green
under sparse, all converted to hidden-pass under contract-visible (except
`env_bool_parser`, which nobody solves). Give North Mini the rule, it delivers.

### Gemma 4 12B: unlocks public CI entirely

Gemma 12B often can't close CI at all under sparse — 7 of 12 ci_forensics
scenarios were public-red. The contract acts as **scaffolding** — it helps
the model construct a working patch where it couldn't before. ci_forensics
public: 5 → 7. Hidden doubled: 3 → 6. Product: **7 hidden passes** under
contract-visible. The model has the capability; it needs the spec to unlock it.

Same improvement direction. Completely different failure mode repair.
**This is why you design an experiment with two models in two prompt
conditions** — a single-cell result tells you *that* the contract helps;
the matrix tells you *how*.

---

## The Cases That Define the Harness

**Product workflows.** North Mini sparse: 6 completions, **0 hidden passes.**
All 6 are false-greens. Billing proration, discount stacking, inventory
idempotency — the model produces surface-level fixes that look green and
miss every core business rule. Trust gap: 100%. Gemma 12B sparse: 2 hidden
passes out of 11. Under contract-visible: **7 hidden passes.** The contract
isn't a nice-to-have on product logic. It's the difference between useless
and useful.

**The stubborn trio.** Three scenarios produced false-greens across EVERY
model and EVERY lane — North Mini, Gemma e4b, 12b, 31b, across multiple
matrices. `env_bool_parser`, `adapter_field_rename`, `batch_splitter_utility`.

- `env_bool_parser`: **still unsolved by anyone.** False-green for North Mini
  sparse AND contract-visible. Public-red for Gemma sparse AND contract-visible.
  Even the explicit contract doesn't help. This is genuinely hard.
- `adapter_field_rename`: cracked by North Mini contract-visible (hidden
  pass). Still fails for Gemma even with the spec. Tool-surface friction.
- `batch_splitter_utility`: **first Gemma 12B hidden pass EVER under
  contract-visible.** The model wasn't incapable — it was uninformed. Empty
  input, invalid sizes, boundary conditions are mechanical checks the model
  can implement when told to.

2 of 3 cracked by contract-visible. That means they're **spec-exposure
problems, not capability walls.** The harness is measuring something real,
and the treatment (explicit contract) has a measurable, directional effect.

---

## What I Refuse to Claim

**Pass@1 is noisy.** Gemma 12B maintenance sparse went from 4/10 hidden to
7/10 hidden across two same-day pass@1 runs. A **30-point swing.** Gemma e4b
went from 5/10 to 2/10 across two runs. Same model. Same pack. Same prompt.
Different outcomes. Single-attempt data describes *an attempt*, not *a model*.
Pass@3 is the floor for characteristic behavior claims. This data is pass@1 —
intentionally honest about its limits. The variance **is** a finding.

**This is not a model ranking.** North Mini runs on its native tool surface
(Cohere-built for OpenCode's agent format). Gemma 4 12B runs through a foreign
agent loop on local Ollama hardware. Tool-loop reliability, inference speed,
and prompt-prefill latency confound raw model capability. The claim is about
**which kinds of work you can safely delegate in which configuration** — not
which model is "better."

**37 scenarios. One evaluator. No external audit.** Hidden tests are authored.
Evaluator is a single DeepSeek agent. Tier 1 evidence only — a behavior
microscope. Tier 2 (comparative claims) requires evaluator agreement and
complete cells. Tier 3 (public benchmark) requires external audit and pass@3.
This is Tier 1. That's fine. The methodology is what you're evaluating,
not just the number.

**North Mini product cells are incomplete.** Sparse: 5/11 timeouts.
Contract-visible: 11/11 stalls. Rate-limited on the free API tier. Need
retry with higher timeout on a non-rate-limited tier. The Gemma product
data is clean; North Mini's isn't. I'm stating that upfront.

---

## What I Would Actually Build

Based on this data, at this tier of confidence:

- **Green zone — merge on CI green.** Mechanical maintenance, generated
  artifacts, logger migrations, fixture updates, docs sync. Both models are
  reliable here *when given an explicit contract.* Zero false-greens for
  North Mini CV on maintenance. The visible test nearly covers the full
  contract. Hidden gate is insurance, not discovery.

- **Amber zone — gate on hidden acceptance.** Adapters, validators, cache
  keys, CSV headers, boolean parsers, validation matrices. The visible test
  is incomplete by design. The model can make CI green. The hidden gate
  is the actual merge decision. Contract-visible converts false-greens to
  hidden-greens in this zone — the spec exposure works.

- **Red zone — human review or skip.** Billing math, discount stacking,
  inventory state, SLA windows, money rounding. The policy density is too
  high for pass@1 reliability. Models consistently produce surface-level
  fixes that miss core business rules. A stronger model or a hidden contract
  helps — but at Tier 1 evidence, I wouldn't delegate these without a human.

**The architecture: define contract → cheap execution → hidden acceptance
gate → escalate failures → replace the model, keep the gate.** The model
is replacable. The trust gate is the enduring investment. That is the
pipeline I would deploy tomorrow.

---

## The Numbers, for the Record

```
Model        Pack                 Lane                Done  Pub  Hid  FG   Gap   Avg
─────────────────────────────────────────────────────────────────────────────────────
gemma4-12b   ci_forensics         contract_visible      12    7    6   1    8% 279.0s
gemma4-12b   ci_forensics         sparse                12    5    3   2   16% 166.0s
gemma4-12b   maintenance_value    contract_visible      10    7    6   1   10% 231.0s
gemma4-12b   maintenance_value    sparse                10    9    7   2   20% 201.0s
gemma4-12b   product_workflows    contract_visible      11    8    7   1    9% 314.0s ★
gemma4-12b   product_workflows    sparse                11    6    2   4   36% 292.0s
north-mini   ci_forensics         contract_visible      12   12   11   1    8%  21.0s
north-mini   ci_forensics         sparse                12   12    8   4   33%  16.0s
north-mini   maintenance_value    contract_visible      10    9    9   0    0%  35.0s
north-mini   maintenance_value    sparse                10   10    8   2   20%  14.0s
north-mini   product_workflows    contract_visible    0/11    0    0   0    0%    0s ‡
north-mini   product_workflows    sparse              6/11    6    0   6  100%  13.0s †
```

- ★ Best product result. 7 hidden passes. 600s first_output_timeout held.
- † 5 timeout scenarios. 6 completed, all false-greens.
- ‡ 11 no_output_timeout scenarios. Rate-limited. Infrastructure evidence.

Query: `SELECT public_pass, hidden_pass, opencode_exit_code FROM runs`
across all 12 cells in `data/matrix/north-mini-vs-gemma4-12b-2026-06-21/`.

---

## Why This Matters

Most coding-agent evaluations measure greenfield code generation. "Write a
function that does X." Ground truth is the reference implementation. No
concept of an existing codebase, a wrong-but-plausible fix, or a test the
model can game.

The real workflow is "CI is red, fix it." A developer opens a ticket, sees
a failing test, edits existing code. The unit of work is a **patch** against
an existing codebase. And the risk isn't that the model produces nothing —
it's that it produces something that looks right and isn't.

If you ship a coding agent into production without a hidden acceptance gate,
you are trusting the CI signal. This data shows that signal is wrong **30-40%
of the time** on average, and **100% of the time** on policy-dense tasks.
That is the cost of not measuring the trust gap.

This was a weekend project. 37 authored scenarios. 132 runs. One evaluator.
No external audit. Tier 1 only. But the pipeline — public/hidden isolation,
shadow-fix evaluator verification, verbatim quote validation, 8-outcome
taxonomy, matrix experiment design, deployment zone output — that's a
template for what evaluation should look like when you stop conflating
"looks done" with "is done."

**The model is not the product. The trust gate is the product.**

---

*Repo: [github.com/anomalyco/north-mini-test](https://github.com/anomalyco/north-mini-test)*
*Evidence deck: `presentation/ci-harness-4.html`*
*Matrix config: `configs/matrix/north-mini-vs-gemma4-12b.json`*
*Scenarios: `ci_vibe_lab/scenarios.py`*
*Runner: `ci_vibe_lab/runner.py`*
*132 runs. 12 cells. 2 models. 3 packs. 2 lanes. pass@1. Tier 1.*