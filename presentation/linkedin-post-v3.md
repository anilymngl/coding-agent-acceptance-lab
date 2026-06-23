# I gave an AI a failing test. It made CI green. Then I ran the hidden tests.

Last weekend I built something I didn't expect to build. It started as a question: when a coding agent turns your CI green, is the bug actually fixed? Or did it just make the light turn green?

I gave three different AI models the same failing test. A money calculation bug. The test said 0.29 × 3 should equal 87 cents. The agent wrote the fix, ran the tests, and got a green checkmark. CI passed.

Then I ran the hidden tests. The ones the agent never saw.

The hidden test asked: what about 0.005 × 1? With proper half-up rounding, that should be 1 cent. The agent's code returned 0. Every half-cent transaction silently undercharges. The test passed. The bug didn't.

I call that a false-green. The CI signal lied.

## The setup

I built a harness that measures exactly this gap. Not whether the test passed — whether the fix was real.

Here's how it works. Every scenario has two layers of tests. Public tests — the ones the agent sees during the run. This is what a normal CI pipeline would show. Hidden tests — injected after the agent exits. These check the full contract. Edge cases. Backward compatibility. Business rules the visible test didn't cover.

Three outcomes. Real fix: both tests pass. False-green: public test passes, hidden test fails. Public red: the agent couldn't make CI green at all.

The headline metric is the trust gap. Public pass rate minus hidden pass rate. A 30% gap means 3 out of 10 green-CI patches are wrong. This is not "accuracy." It's "how often the CI signal lies to you."

## The models

I tested three very different models through the same harness, same prompts, same hidden tests:

North Mini — Cohere's coding model, free tier, cloud API, about 25 seconds per task.

Gemma 12B — Google's general-purpose model, running locally on my laptop via Ollama, about 240 seconds per task.

DeepSeek V4 Pro — Frontier-class hosted API, about 37 seconds per task.

Different architectures. Different speeds. Different tooling fit. I wanted to see if the pattern held across all three.

## The data

198 runs. 33 scenarios. Three task types. Two prompt lanes: sparse ("CI is red, fix it") vs contract-visible (full acceptance criteria provided).

### CI Forensics — 12 mechanical bugs

Mechanical bugs. Dependency changes. Stale configs. Import errors. The visible test nearly covers the full contract.

North Mini sparse: 12/12 passed CI, 8/12 real. 33% false-green.
North Mini contract-visible: 12/12 passed CI, 11/12 real. 8% false-green.

Gemma 12B sparse: 5/12 passed CI, 3/12 real. 40% false-green.
Gemma 12B contract-visible: 7/12 passed CI, 6/12 real. 14% false-green.

DeepSeek sparse: 12/12 passed CI, 9/12 real. 25% false-green.
DeepSeek contract-visible: 12/12 passed CI, 12/12 real. 0% false-green.

Mechanical work is safe to delegate with clear specs. DeepSeek with clear specs: 12 of 12 real fixes, zero false-greens.

### Maintenance — 10 refactoring tasks

Logger migrations. Field renames. Generated artifacts. The visible test covers most but not every edge.

North Mini sparse: 10/10 passed CI, 8/10 real. 20% false-green.
North Mini contract-visible: 9/10 passed CI, 9/10 real. 0% false-green.

Gemma 12B sparse: 9/10 passed CI, 7/10 real. 22% false-green.
Gemma 12B contract-visible: 7/10 passed CI, 6/10 real. 14% false-green.

DeepSeek sparse: 10/10 passed CI, 7/10 real. 30% false-green.
DeepSeek contract-visible: 10/10 passed CI, 10/10 real. 0% false-green.

North Mini and DeepSeek hit zero false-greens with clear specs. Delegable with a hidden acceptance gate.

### Product Workflows — 11 business-logic tasks

This is where the money lives. Billing proration. Discount stacking. Inventory reservations. SLA deadlines. The visible test checks one path through the policy. The hidden test checks everything else.

North Mini sparse: 9/11 passed CI, 1/11 real. 89% false-green.
North Mini contract-visible: 9/11 passed CI, 6/11 real. 33% false-green.

Gemma 12B sparse: 6/11 passed CI, 2/11 real. 67% false-green.
Gemma 12B contract-visible: 8/11 passed CI, 7/11 real. 12% false-green.

DeepSeek sparse: 11/11 passed CI, 3/11 real. 73% false-green.
DeepSeek contract-visible: 11/11 passed CI, 10/11 real. 9% false-green.

Under sparse prompts, 73–89% of CI-green patches were wrong. Clear specs drop it to 9–33%, but 9% on money logic is not zero. The frontier model and the free model both hit 73% false-green on sparse. One scenario — bulk_invite_dedupe — survives even DeepSeek with clear specs.

## What false-greens actually look like

Every one has the same shape. The agent asks "what makes this test pass?" A good engineer asks "what else should be true here?"

Money math. Test: 0.29 × 3 = 87¢. Agent uses float math. Returns 87. Green. Hidden test: 0.005 × 1 with half-up rounding should be 1¢. Returns 0. Silent billing error on every half-cent transaction.

Audit logging. Test: redact password field. Agent replaces top-level key. Green. Hidden test: nested metadata.api_key, profile.token, items[0].authorization. None redacted. Didn't recurse.

Wrong layer. Dashboard combines cents and dollars. Agent normalizes inside compute() — the raw data API. Green. But compute() must return raw values. Normalization belongs in dashboard_total(). Right math, wrong place.

The consistent failure direction: the agent satisfies the specific failing assertion instead of inferring the rule the assertion was testing. This is not random. It is learnable. Guardrails can be built around it.

## The insight

The gap between sparse and contract-visible tells you what kind of problem this is.

North Mini already gets CI green on almost everything. The contract doesn't create new greens — it turns false-greens into real fixes. The model stops too soon under sparse. Give it the rule, it delivers.

Gemma 12B often can't close CI at all under sparse. The contract acts as scaffolding — it helps the model produce a working patch where it couldn't before. The model has the capability. It needs the spec to unlock it.

DeepSeek with clear specs hits zero false-greens on bugs and maintenance. 22 of 22 real fixes. But product workflows still show 9% false-green even with clear specs. Under sparse, DeepSeek hits the same 73% false-green as North Mini. The frontier model's ceiling is the spec density, not the model size.

## What I can't claim

This is pass@1. One attempt per task. Gemma's maintenance hidden pass swung from 4/10 to 7/10 across two same-day runs. A 30-point swing. Same model, same tasks. Single attempts describe an attempt, not a model.

North Mini runs on its native tool surface. Gemma runs through a foreign agent loop on local Ollama. DeepSeek runs as a hosted API through the same OpenCode interface. I'm measuring system behavior, not abstract model quality.

33 scenarios. One evaluator. No external audit. First-stage evidence. DeepSeek product sparse from a prior control run; other 17 cells from the matrix pipeline. Same harness, same scenarios, same hidden tests. The method is what matters — not the specific numbers.

## What to do

Three deployment zones based on the evidence:

Green — merge on CI green. Mechanical work. Migrations. Fixtures. Docs. All three models converge at 0–14% false-green with clear specs.

Amber — gate on hidden acceptance. Adapters. Validators. Edge cases. Every model produced false-greens here under sparse. Clear specs close the gap. Run a hidden check before merge.

Red — human review or frontier model with multiple attempts. Billing. Discounts. Inventory. SLAs. 73–89% false-green under sparse. 9–33% even with clear specs. The policy density is too high for pass@1.

Write a clear spec. Let the agent attempt. Run hidden acceptance. If it fails, escalate. The model is replaceable. The trust gate is the enduring investment.

---

198 runs. 3 models. 33 scenarios. pass@1. Data and methodology at github.com/anomalyco/north-mini-test. Not a benchmark. Not a leaderboard. A behavior microscope.
