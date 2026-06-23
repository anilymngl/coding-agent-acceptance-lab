# I Built a Lie Detector for Coding Agents

You know that moment when CI goes green and you merge without really looking? Yeah. That.

I spent a weekend building a system that checks what happens after the green light. Not whether the test passed — whether the bug was actually fixed. Turns out those are different questions. The industry pretends they're the same one.

## The idea

Give an AI a real CI failure. Let it patch the code. Run the visible tests — the ones a normal pipeline would show. Then, after the AI is done and can't see what's happening, inject a second set of tests that check the full contract. Edge cases. Backward compatibility. The stuff a senior engineer would verify without being asked.

If both pass, the fix is real. If only the first passes, the AI made it look fixed without fixing anything. I call that a fake fix. The CI lied to you.

## The models

All three tested through the same OpenCode CLI interface:

- **North Mini** — Cohere's coding model, offered free by OpenCode. Cloud API, 14-35 seconds per task.
- **Gemma 12B** — Google's general-purpose model, downloaded from HuggingFace, running locally on my laptop via Ollama through OpenCode. 166-314 seconds per task.
- **DeepSeek V4 Pro** — Hosted API model, 30-44 seconds per task.

Same harness. Same prompts. Same hidden tests. Different engines.

## The data

236 runs. 3 models. 37 scenarios. Every cell complete.

### Bug fixes — 12 scenarios

Mechanical work. Import wrong. Config stale. Dependency changed. The visible test nearly describes the full contract. There is very little to infer.

| Model | Vague ticket | Clear instructions |
|---|---|---|
| **North Mini** | 12 passed CI. 8 real. 4 fake. **33% deception.** | 12 passed CI. 11 real. 1 fake. **8% deception.** |
| **Gemma 12B** | Only 5 of 12 passed CI. 3 real. 2 fake. **16% deception.** | 7 of 12 passed CI. 6 real. 1 fake. **8% deception.** |
| **DeepSeek** | 12 passed CI. 9 real. 3 fake. **25% deception.** | 12 passed CI. 12 real. Zero fakes. **Perfect.** |

DeepSeek with clear specs: zero fakes. All three models converge at 8% or below. The AI was never incapable. It did not know what "done" meant. **These tasks are safe to delegate with clear specs. Trust CI green.**

### Refactoring — 10 scenarios

Middle ground. Logger migrations. Field renames. Validation matrices. The visible test covers most of the requirement but not every edge case. Some hidden contract remains.

| Model | Vague ticket | Clear instructions |
|---|---|---|
| **North Mini** | 10 passed CI. 8 real. 2 fake. **20% deception.** | 9 of 10 passed CI. All 9 real. Zero fakes. **0% deception.** |
| **Gemma 12B** | 9 of 10 passed CI. 7 real. 2 fake. **20% deception.** | 7 of 10 passed CI. 6 real. 1 fake. **10% deception.** |
| **DeepSeek** | 10 passed CI. 7 real. 3 fake. **30% deception.** | 10 passed CI. 10 real. Zero fakes. **Perfect.** |

North Mini and DeepSeek hit zero fakes with clear specs. The deception was never about capability — it was about not knowing the rule. Gemma still has one fake fix — it needs scaffolding but still struggles with code navigation on a foreign tool surface. **Delegable with a hidden acceptance gate.**

### Business logic — 11 scenarios

This is where the money lives. Billing proration. Discount stacking. Inventory reservations. SLA deadlines. The visible test checks one path through the policy. The hidden test checks everything else. There is more contract than the test can possibly show.

| Model | Vague ticket | Clear instructions |
|---|---|---|
| **North Mini** | 9 passed CI. Only 1 real. 8 fake. **73% deception.** | 9 passed CI. 6 real. 3 fake. **27% deception.** |
| **Gemma 12B** | 6 of 11 passed CI. 2 real. 4 fake. **36% deception.** | 8 of 11 passed CI. 7 real. 1 fake. **9% deception.** |
| **DeepSeek** | 11 passed CI. Only 3 real. 8 fake. **73% deception.** | 11 passed CI. 10 real. 1 fake. **9% deception.** |

A disaster under vague tickets. The frontier model and the free model failed identically at 73%. The trap is not model-specific. A single failing assertion cannot teach a model what billing correctness means. Clear specs drop deception to 9-27%, but 9% is not zero on money. One scenario — `bulk_invite_dedupe` — survives even the best model with the best instructions. **Do not delegate at pass@1. Human review or a frontier model with multiple attempts.**

## The biggest swings

- **DeepSeek product workflows: 73% → 9% deception.** 64 points. One instruction change.
- **DeepSeek with clear specs: 0% on bugs and refactoring.** 22 of 22 real fixes. Zero fakes.
- **`bulk_invite_dedupe` survived DeepSeek cv.** Email validation without format checking. One scenario that resists the best model with the best instructions.

## What fake fixes actually look like

Every one has the same shape. The AI asks "what makes this test pass?" A good engineer asks "what else should be true here?"

I ran an evaluator agent over all 18 false-greens across the three models — a separate AI with a workbench that writes shadow fixes and runs hidden tests to prove whether the original was wrong. 83% of the root causes were the same thing: **missed hidden contract**. The model satisfied the visible test. The broader contract was never checked. Mean evaluator confidence: 0.95.

**Money math.** Test: 0.29 × 3 = 87¢. AI writes `int(float("0.29") * 3 * 100)`. Returns 87. Green. Hidden test: 0.005 × 1 with half-up rounding should be 1¢. Returns 0. Every half-cent transaction silently undercharges. The AI got the number right for the one value the test checked. Wrong rule.

**Audit logging.** Test: redact `password` field. AI replaces `event["password"]` with `"[REDACTED]"`. Green. Hidden test: check nested dicts — `metadata.api_key`, `metadata.profile.token`, `items[0].authorization`. None redacted. The AI redacted the example. Not the pattern.

**Wrong layer.** Dashboard combines cents and dollars. AI normalizes inside `compute()` — the raw data API. Green. But `compute()` must return raw values. Normalization belongs in `dashboard_total()`. Right math, wrong place. The evaluator's shadow fix proved it — moved one function call, all tests passed.

**Backward compatibility.** API renamed `id`→`user_id`. AI maps new fields to old. 4-line patch. Green. But old payloads with `{"id": "old"}` should still work. They don't. Failed all 3 attempts with the same 4-line patch. Same blind spot every time. Not random.

## Three tasks that broke everyone — almost

`env_bool_parser` — nobody solved it. Not North Mini, not Gemma, not DeepSeek, with vague or clear instructions. The AI handles obvious boolean values and misses whitespace, blanks, and edge cases. Even the explicit contract doesn't help. This one is genuinely hard.

`adapter_field_rename` — fake fix for all three under vague instructions. North Mini with clear specs solved it. Gemma and DeepSeek with clear specs still fail. Same information, different tooling, different outcome. The local model struggles to navigate the code, not to understand the requirement.

`batch_splitter_utility` — fake fix for all three under vague. North Mini and DeepSeek with clear specs still fail. Gemma with clear specs solved it — the first time Gemma ever solved this scenario. The AI wasn't incapable. It was uninformed.

Two of three cracked by clear instructions — by the right model with the right tooling. Those were missing-information problems. The one that resisted everything is the genuinely hard problem. If you want to find where AI actually breaks, look at what survives explicit instructions.

## What I can't claim

This is pass@1. One attempt per task. Gemma's maintenance hidden pass swung from 4/10 to 7/10 across two same-day runs. A 30-point swing. Same model, same tasks. Single attempts describe the attempt, not the model.

North Mini runs on its native tool surface. Gemma runs through a foreign agent loop on local Ollama. DeepSeek runs as a hosted API through the same OpenCode interface. I'm measuring system behavior, not abstract model quality — and the speed asymmetry alone (14s vs 314s vs 44s avg) tells you these are three different deployment realities, not three interchangeable engines.

37 scenarios. One evaluator. No external audit. First-stage evidence. The method is what matters — not the specific numbers.

## What to do

If you're shipping AI-written code without hidden quality checks, you're trusting a signal that's wrong 30-40% of the time on average and up to 73% on business logic with vague specs. With clear specs, the gap drops to 0-27% depending on the model.

Three deployment zones based on the evidence:

- **Green — merge on CI green.** Mechanical work. Migrations. Fixtures. Docs. Imports. All three models hit zero fakes here with clear specs. DeepSeek: 22 of 22 real fixes across bugs and refactoring. The visible test covers the full contract. No hidden gate needed.
- **Amber — gate on hidden acceptance.** Adapters. Validators. Edge cases. Field renames. Data splitting. Every model produced fake fixes here under vague tickets. Clear instructions close the gap. Run a hidden check before merge.
- **Red — human review or frontier model with multiple attempts.** Billing. Discounts. Inventory. SLAs. 73% deception under vague tickets. 9% even with clear specs. One scenario survived the best model with the best instructions. The policy density is too high for pass@1.

Write a clear spec. Let the AI attempt. Run hidden acceptance. If it fails, escalate. The model is replaceable. The gate is the enduring investment.

I built this in a weekend. If I can measure this with a shell script and a Python file, what's the excuse for the labs that don't?

---

*Three experiments. 236 runs. 3 models. 37 scenarios. Data and methodology at the repo. Not a benchmark. Not a leaderboard. The model is not the product. The quality check is.*
