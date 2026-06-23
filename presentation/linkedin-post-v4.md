# Field Notes: The Trust Gap

Weekend project. Started Saturday morning. Didn't stop until Monday.

## The question that wouldn't leave me alone

When a coding agent turns your CI green, is the bug actually fixed?

I've been asking this for months. Everyone measures pass rate. Nobody measures whether the fix is real. So I built something to measure exactly this.

## Saturday: The harness

Public tests. The agent sees them. This is what CI shows. Hidden tests. Injected after the agent exits. The agent never sees these. They check the full contract.

Three outcomes:
- Real fix: both pass
- False-green: public passes, hidden fails
- Public red: couldn't even make CI green

Trust gap = public pass rate − hidden pass rate. A 30% gap means 3 of 10 green patches are wrong.

## Sunday: The models

Three very different models. Same harness. Same prompts. Same hidden tests.

**North Mini** — Cohere's coding model. Free tier. Cloud API. 25 seconds per task.

**Gemma 12B** — Google's general-purpose model. Running locally on my laptop via Ollama. 240 seconds per task.

**DeepSeek V4 Pro** — Frontier-class hosted API. 37 seconds per task.

## Sunday night: The data

198 runs. 33 scenarios. Three task types. Two prompt lanes: sparse vs contract-visible.

### Mechanical bugs (12 scenarios)

DeepSeek with clear specs: 12/12 real fixes. Zero false-greens. Perfect.

North Mini sparse: 33% false-green. Contract-visible: 8%.

Gemma sparse: 40% false-green. Contract-visible: 14%.

**Finding:** Mechanical work is safe to delegate with clear specs.

### Refactoring (10 scenarios)

North Mini and DeepSeek with clear specs: zero false-greens.

Gemma: 14% false-green even with clear specs.

**Finding:** The deception was never about capability. It was about not knowing the rule.

### Business logic (11 scenarios)

This is where it gets ugly.

North Mini sparse: 89% false-green. Contract-visible: 33%.

Gemma sparse: 67% false-green. Contract-visible: 12%.

DeepSeek sparse: 73% false-green. Contract-visible: 9%.

**Finding:** All three models hit the same wall. 73–89% false-green under sparse. Even with clear specs, 9–33%. One scenario — bulk_invite_dedupe — survives even DeepSeek with clear specs.

## Monday morning: What I learned

The agent asks "what makes this test pass?" A good engineer asks "what else should be true here?"

**Money math.** Test: 0.29 × 3 = 87¢. Agent uses float math. Returns 87. Green. Hidden: 0.005 × 1 should be 1¢. Returns 0. Silent billing error.

**Audit logging.** Test: redact password. Agent redacts top-level key. Green. Hidden: nested api_key, token, authorization. None redacted. Didn't recurse.

**Wrong layer.** Dashboard combines cents + dollars. Agent normalizes in compute() — the raw API. Green. But compute() must return raw values. Right math. Wrong place.

## Monday afternoon: The deployment policy

**GREEN** — merge on CI green. Mechanical work. Migrations. Fixtures. Docs. 0–14% false-green with clear specs.

**AMBER** — gate on hidden acceptance. Adapters. Validators. Edge cases. Every model produced false-greens under sparse. Clear specs close the gap.

**RED** — human review required. Billing. Discounts. Inventory. SLAs. 73–89% false-green under sparse. 9–33% even with clear specs.

## What I can't claim

Pass@1. One attempt per task. Gemma's maintenance hidden pass swung 4/10 → 7/10 across two same-day runs. 30-point swing. Same model. Same tasks. Single attempts describe an attempt, not a model.

North Mini runs on its native tool surface. Gemma runs through a foreign agent loop. DeepSeek runs as a hosted API. I'm measuring system behavior, not abstract model quality.

33 scenarios. One evaluator. No external audit. First-stage evidence. DeepSeek product sparse from a prior control run; other 17 cells from the matrix pipeline. Same harness, same scenarios, same hidden tests.

## The takeaway

The model is replaceable. The trust gate is the enduring investment.

Write a clear spec. Let the agent attempt. Run hidden acceptance. If it fails, escalate.

---

198 runs. 3 models. 33 scenarios. pass@1.

Data and methodology: github.com/anomalyco/north-mini-test

Not a benchmark. Not a leaderboard. A behavior microscope.
