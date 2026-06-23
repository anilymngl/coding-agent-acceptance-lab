# When CI Goes Green, Is the Bug Actually Fixed?

I built a harness to measure exactly this question. Not whether the test passed — whether the fix was real. The answer surprised me, not because of the numbers, but because the pattern held across three very different models.

## The setup

Give a coding agent a failing test. Let it patch the code. Run the visible tests — the ones a normal CI pipeline would show. Then, after the agent exits and can't see what's happening, inject a second set of tests that check the full contract: edge cases, backward compatibility, business rules the visible test didn't cover.

If both pass, the fix is real. If only the visible test passes, the agent satisfied the assertion without fixing the underlying problem. I call that a **false-green**. The CI signal lied.

## The models

All three tested through the same OpenCode CLI, same harness, same hidden tests:

- **North Mini** — Cohere's coding model, free tier, cloud API, ~25 seconds per task
- **Gemma 12B** — Google's general-purpose model, running locally on my laptop via Ollama, ~240 seconds per task
- **DeepSeek V4 Pro** — Frontier-class hosted API, ~37 seconds per task

Different architectures. Different speeds. Different tooling fit. Same structural pattern.

## The data

198 runs. 33 scenarios. Three task types. Two prompt lanes: sparse ("CI is red, fix it") vs contract-visible (full acceptance criteria provided).

### CI Forensics — 12 mechanical bugs

| Model | Sparse | Contract-visible |
|---|---|---|
| **North Mini** | 12/12 passed CI, 8/12 real. **33% false-green.** | 12/12 passed CI, 11/12 real. **8% false-green.** |
| **Gemma 12B** | 5/12 passed CI, 3/12 real. **40% false-green.** | 7/12 passed CI, 6/12 real. **14% false-green.** |
| **DeepSeek** | 12/12 passed CI, 9/12 real. **25% false-green.** | 12/12 passed CI, 12/12 real. **0% false-green.** |

Mechanical work is safe to delegate with clear specs. DeepSeek: 12 of 12 real fixes, zero false-greens.

### Maintenance — 10 refactoring tasks

| Model | Sparse | Contract-visible |
|---|---|---|
| **North Mini** | 10/10 passed CI, 8/10 real. **20% false-green.** | 9/10 passed CI, 9/10 real. **0% false-green.** |
| **Gemma 12B** | 9/10 passed CI, 7/10 real. **22% false-green.** | 7/10 passed CI, 6/10 real. **14% false-green.** |
| **DeepSeek** | 10/10 passed CI, 7/10 real. **30% false-green.** | 10/10 passed CI, 10/10 real. **0% false-green.** |

North Mini and DeepSeek hit zero false-greens with clear specs. Delegable with a hidden acceptance gate.

### Product Workflows — 11 business-logic tasks

| Model | Sparse | Contract-visible |
|---|---|---|
| **North Mini** | 9/11 passed CI, 1/11 real. **89% false-green.** | 9/11 passed CI, 6/11 real. **33% false-green.** |
| **Gemma 12B** | 6/11 passed CI, 2/11 real. **67% false-green.** | 8/11 passed CI, 7/11 real. **12% false-green.** |
| **DeepSeek** | 11/11 passed CI, 3/11 real. **73% false-green.** | 11/11 passed CI, 10/11 real. **9% false-green.** |

This is where the money lives. Billing proration. Discount stacking. Inventory reservations. SLA deadlines. Under sparse prompts, 73–89% of CI-green patches were wrong. Clear specs drop it to 9–33%, but 9% on money logic is not zero. The frontier model and the free model both hit 73% false-green on sparse. One scenario — `bulk_invite_dedupe` — survives even DeepSeek with clear specs.

## What false-greens actually look like

Every one has the same shape. The agent asks "what makes this test pass?" A good engineer asks "what else should be true here?"

**Money math.** Test: 0.29 × 3 = 87¢. Agent uses float math. Returns 87. Green. Hidden test: 0.005 × 1 with half-up rounding should be 1¢. Returns 0. Silent billing error on every half-cent transaction.

**Audit logging.** Test: redact `password` field. Agent replaces top-level key. Green. Hidden test: nested `metadata.api_key`, `profile.token`, `items[0].authorization`. None redacted. Didn't recurse.

**Wrong layer.** Dashboard combines cents and dollars. Agent normalizes inside `compute()` — the raw data API. Green. But `compute()` must return raw values. Normalization belongs in `dashboard_total()`. Right math, wrong place.

The consistent failure direction: the agent satisfies the specific failing assertion instead of inferring the rule the assertion was testing. This is not random. It is learnable. Guardrails can be built around it.

## The insight

The gap between sparse and contract-visible tells you what kind of problem this is.

**North Mini** already gets CI green on almost everything. The contract doesn't create new greens — it turns false-greens into real fixes. The model stops too soon under sparse. Give it the rule, it delivers.

**Gemma 12B** often can't close CI at all under sparse. The contract acts as scaffolding — it helps the model produce a working patch where it couldn't before. The model has the capability. It needs the spec to unlock it.

**DeepSeek** with clear specs hits zero false-greens on bugs and maintenance. 22 of 22 real fixes. But product workflows still show 9% false-green even with clear specs. Under sparse, DeepSeek hits the same 73% false-green as North Mini. The frontier model's ceiling is the spec density, not the model size.

## What I can't claim

This is pass@1. One attempt per task. Gemma's maintenance hidden pass swung from 4/10 to 7/10 across two same-day runs. A 30-point swing. Same model, same tasks. Single attempts describe an attempt, not a model.

North Mini runs on its native tool surface. Gemma runs through a foreign agent loop on local Ollama. DeepSeek runs as a hosted API through the same OpenCode interface. I'm measuring system behavior, not abstract model quality.

33 scenarios. One evaluator. No external audit. First-stage evidence. DeepSeek product sparse from a prior control run; other 17 cells from the matrix pipeline. Same harness, same scenarios, same hidden tests. The method is what matters — not the specific numbers.

## What to do

Three deployment zones based on the evidence:

- **Green — merge on CI green.** Mechanical work. Migrations. Fixtures. Docs. All three models converge at 0–14% false-green with clear specs.
- **Amber — gate on hidden acceptance.** Adapters. Validators. Edge cases. Every model produced false-greens here under sparse. Clear specs close the gap. Run a hidden check before merge.
- **Red — human review or frontier model with multiple attempts.** Billing. Discounts. Inventory. SLAs. 73–89% false-green under sparse. 9–33% even with clear specs. The policy density is too high for pass@1.

Write a clear spec. Let the agent attempt. Run hidden acceptance. If it fails, escalate. The model is replaceable. The trust gate is the enduring investment.

---

*198 runs. 3 models. 33 scenarios. pass@1. Data and methodology at [github.com/anomalyco/north-mini-test](https://github.com/anomalyco/north-mini-test). Not a benchmark. Not a leaderboard. A behavior microscope.*
