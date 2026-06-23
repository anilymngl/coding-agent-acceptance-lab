# Laguna XS.2 vs North Mini — First Comparison Report

**3B-active vs 3B-active. Two Apache 2.0 MoE coding agents. Same harness. Same hidden tests. Same structural pattern.**

---

## Models

| | Laguna XS.2 | North Mini Code |
|---|---|---|
| **Company** | Poolside (2026) | Cohere |
| **Architecture** | 33B total / **3B active** MoE | 30B total / **3B active** MoE |
| **Experts** | 256 + 1 shared, mixed SWA attention | Not disclosed |
| **Context** | 262K in / 32K out | 256K in / 64K out |
| **Reasoning** | Native interleaved thinking | Not mentioned |
| **SWE-bench Verified** | 69.9% | Not published |
| **License** | Apache 2.0 | Apache 2.0 |
| **Pricing** | Free (limited time via OpenRouter) | Free tier via OpenCode |
| **Avg speed (our harness)** | **44s** | **16s** |

---

## Evidence Status

**Matrix: `laguna-xs2-vs-north-mini-2026-06-22`. 12 cells, 396 max attempts.**

| Model | Pack | Lane | Rows | Status |
|---|---|---|---|---|
| `laguna-xs2` | `ci_forensics` | `sparse` | 36/36 | **complete** |
| `laguna-xs2` | `ci_forensics` | `contract_visible` | 36/36 | **complete** |
| `north-mini` | `ci_forensics` | `sparse` | 36/36 | **complete** |
| `north-mini` | `ci_forensics` | `contract_visible` | 36/36 | **complete** |
| Both | `maintenance_value` | spare + cv | ~13 | running |
| — | `product_workflows` | — | 0 | not started |

**This report:** ci_forensics, both models, both lanes. pass@1, pass@3, and contract-visible comparison. DeepSeek V4 Pro as reference. Evaluator verdicts (DeepSeek judging Laguna) complete.

---

## Pass@1 Head-to-Head — ci_forensics sparse

| | Pub | Hid | False-Green | Speed |
|---|---|---|---|---|
| **Laguna XS.2** | 12/12 | 8/12 | **4 (33%)** | 44s |
| **North Mini** | 12/12 | 8/12 | **4 (33%)** | 16s |
| DeepSeek V4 Pro | 12/12 | 9/12 | 3 (25%) | 30s |

**Identical score.** Both 3B-active MoE models hit 33% false-green on exactly the same 4 scenarios: `csv_header_contract`, `decimal_money_rounding`, `dependency_api_change`, `env_bool_parser`. Zero difference in which scenarios failed.

---

## Laguna Pass@1→2→3 Variance

| | Pub | Hid | False-Green |
|---|---|---|---|
| pass@1 | 12 | 8 | 4 (33%) |
| pass@2 | 12 | 9 | 3 (25%) |
| pass@3 | 12 | 9 | 3 (25%) |
| **best-of-3** | 12 | 9 | 3 (25%) |

- **Recovered:** `dependency_api_change` — false-green on pass@1, real fix on pass@2 and 3.
- **Unconquered (×3):** `csv_header_contract`, `decimal_money_rounding`, `env_bool_parser` — failed every attempt. Not random. Structural.
- **Pass@1→3 delta:** +1 hidden pass. Marginal improvement from retrying.

---

## North Mini Pass@1→2→3 Variance (ci_forensics sparse)

| | Pub | Hid | False-Green |
|---|---|---|---|
| pass@1 | 12 | 9 | 3 (25%) |
| pass@2 | 12 | 8 | 4 (33%) |
| pass@3 | 12 | 8 | 4 (33%) |
| **best-of-3** | 12 | 9 | 3 (25%) |

- **No recoveries.** Unlike Laguna which recovered `dependency_api_change`, North Mini's false-greens were stable or worsened on retry. Pass@1 had 3 false-greens (`csv_header_contract`, `decimal_money_rounding`, `dependency_api_change`). Pass@2 lost `env_bool_parser` (previously solved) while gaining no new solves. The model re-sampled in the wrong direction.
- **Stubborn: `csv_header_contract`, `decimal_money_rounding`, `dependency_api_change`** — all 3 attempts on each.
- **North Mini is not helped by retry.** While Laguna improved pass@2 by +1, North Mini lost ground.

---

## Contract-Visible Effect (ci_forensics)

| | Sparse FG% | CV FG% | Delta |
|---|---|---|---|
| **Laguna XS.2** | 33% | **0%** | -33 |
| **North Mini** | 33% | **8%** | -25 |
| DeepSeek V4 Pro | 25% | 0% | -25 |

**Laguna with clear specs: 12/12 hidden pass, zero false-greens.** The contract collapses the gap completely. Same as DeepSeek. The model knew the specs — it just wasn't told.

**North Mini with clear specs: 11/12 hidden pass, 1 false-green (`decimal_money_rounding`).** The same scenario that Laguna couldn't solve across 3 sparse attempts remains a gap even with explicit acceptance criteria. The hidden contract for `decimal_money_rounding` (cent rounding with half-up semantics) appears to be genuinely hard for North Mini — not solvable by telling it the rule.

**Both models scraped `env_bool_parser` under sparse but solved it under cv.** The contract-visible prompt exposes the matrix of truthy/falsey values and whitespace normalization. Both models implemented it correctly when told what to do.

---

## False-Green Overlap Across Models

```
Laguna        : csv_header, decimal_money, dependency_api_change, env_bool
North Mini    : csv_header, decimal_money, dependency_api_change, env_bool
DeepSeek      : csv_header, decimal_money, env_bool
```

- **Laguna ∩ North Mini:** 4/4 identical.
- **All 3 share:** 3 — `csv_header_contract`, `decimal_money_rounding`, `env_bool_parser`.
- **DeepSeek alone solved:** `dependency_api_change` at pass@1. Laguna solved it at pass@2.
- **No model solved pass@1:** `csv_header_contract`, `decimal_money_rounding`, `env_bool_parser`.

These 3 scenarios are the wall. Same wall for a free coding model, a laptop model, and a frontier API model.

---

## DeepSeek Evaluator Verdicts — Judging Laguna's False-Greens

7 of 10 reviews complete. All confirmed as valid false-greens. Mean confidence: **0.96**.

| Scenario | Attempt | Root Cause | Detail (DeepSeek's words) |
|---|---|---|---|
| `csv_header_contract` | 1 | missed_hidden_contract | "Fixed the visible header-order symptom but missed the contract requirements to return the header for empty exports and to handle rows with extra fields outside EXPORT_COLUMNS." |
| `csv_header_contract` | 2 | incomplete_domain_policy | "Used EXPORT_COLUMNS for header order but kept an early-return guard that skips the header on empty rows and did not add extrasaction to exclude internal fields." |
| `decimal_money_rounding` | 1 | edge_case_gap | "int(total * 100) truncates toward zero instead of rounding half-up, so Decimal('0.005') * 100 → 0.500 → int truncates to 0 instead of the expected 1." |
| `decimal_money_rounding` | 2 | missed_hidden_contract | "int(total * 100) truncates toward zero; half-cent values like 0.005×100=0.500 truncate to 0 instead of rounding half-up to 1." |
| `dependency_api_change` | 1 | incomplete_domain_policy | "Adapted the error-check to the new gateway response shape but failed to propagate the real charge id from the gateway result, leaving the hardcoded 'legacy-charge' in place." |
| `env_bool_parser` | 1 | incomplete_domain_policy | "The fix only recognizes 'false', '0', and '' as falsy, missing 'no', 'off', and whitespace normalization." |
| `env_bool_parser` | 2 | edge_case_gap | "The model's deny-list approach lacked whitespace normalization and did not handle empty strings." |

**Evaluator taxonomy:**
- `incomplete_domain_policy`: 3 (the model partially implemented the rule)
- `edge_case_gap`: 2 (the model missed specific boundary cases)
- `missed_hidden_contract`: 2 (the model didn't recognize the contract existed)

**Same scenario, different failure on retry.** `csv_header_contract` went from "didn't know the contract existed" (pass@1) to "knew the contract but implemented it incompletely" (pass@2). Progress of a sort — but still wrong.

---

## Key Findings

### 1. The trust gap is structural, not model-specific.

Same active parameter count. Same pass@1. Same 4 false-green scenarios. Two independently trained MoE coding agents from different companies. The model doesn't matter — the task does.

### 2. Three scenarios are the wall — by design.

`csv_header_contract`, `decimal_money_rounding`, `env_bool_parser` — no model in this matrix has solved any of these at pass@1. DeepSeek, North Mini, Gemma 12B, Gemma 31B, Laguna — all fail the same 3. The frontier model doesn't crack them either (25% false-green vs 33% for the small models — a 1-scenario delta). These are task features, not model weaknesses.

This is not an accident. The challenge design (see [docs/challenge-design.md](../docs/challenge-design.md)) intentionally constructs scenarios where *the hidden contract is richer than the visible test*. You cannot infer "must handle empty exports" from a test that checks header order on one row. You cannot infer "half-up cent rounding" from a test that checks `0.29 × 3 = 87`. The public test checks one path. The hidden test checks everything else. The gap between them *is* the measurement.

The key finding from the North Mini evidence: *"The dividing line is whether the spec is richer than the visible test, not model size."* This report confirms it with a second 3B-active MoE model — identical score, identical scenarios. The model doesn't matter. The spec density does.

### 3. Laguna's reasoning doesn't buy accuracy.

Interleaved thinking between tool calls. 2.8× slower than North Mini (44s vs 16s). Same output. The extra cycles don't translate to better pass@1 scores. They might help on harder packs — but on ci_forensics, it's just latency with no payoff.

### 4. Retry helps modestly. Exactly once.

Laguna recovered `dependency_api_change` on pass@2 (false-green → real fix). That's the only recovery across 4 false-greens. Pass@3 added nothing new. `dependency_api_change` is the easiest of the 4 — DeepSeek solved it at pass@1. The other 3 resisted all 3 Laguna attempts.

### 5. The evaluator sees the failure evolution.

`csv_header_contract` pass@1: "missed_hidden_contract" — the model didn't know the contract existed. Pass@2: "incomplete_domain_policy" — knew the contract, botched the implementation. The evaluator is not just rubber-stamping false-greens — it's distinguishing between ignorance and incompetence, even within the same scenario.

### 6. The open question: contract-visible — ANSWERED.

DeepSeek cv: 0% false-green (perfect). North Mini cv: 8% (1 false-green). **Laguna cv: 0% false-green (perfect).** Both models benefit dramatically from explicit specs. Laguna matches DeepSeek — the contract collapses the gap. North Mini's remaining gap is `decimal_money_rounding`, the same cent-rounding scenario Laguna couldn't solve across 3 sparse attempts. The hidden contract is richer than the visible test, and even the explicit spec doesn't fully convey the half-up rounding requirement to North Mini.

### 7. North Mini retries: worse than Laguna.

Where Laguna improved pass@1→2 (recovering `dependency_api_change`), North Mini went the other direction — losing `env_bool_parser` on pass@2 without gaining any new solves. The model does not converge on correctness with more attempts. re-sampling from a distribution of wrong answers can produce worse outcomes.

---

## Runtime Realities

### Provider Stack

Neither model runs locally in this matrix. Both are API calls through proxies:

```
Laguna XS.2:   OpenCode CLI → OpenRouter proxy → Poolside API
North Mini:    OpenCode CLI → OpenCode proxy  → Cohere API
```

Both are free tiers. Both have rate limits. The failure modes differ.

### Speed Reality

| | Sparse | Contract-Visible |
|---|---|---|
| **Laguna** | avg 43s (min 18s, p50 34s, max 172s) | avg 96s so far (max 400s) |
| **North Mini** | avg 18s (min 9s, max 46s) | not yet run |

Laguna is **2.4× slower** on sparse, **~5× slower** on contract_visible (larger prompts amplify the interleaved reasoning overhead). The `tenant_cache_leak` scenario took 172s on pass@3 — 10× longer than North Mini's same scenario.

### Rate Limit Incidents

**Laguna (OpenRouter free tier):** Hit `free-models-per-min` rate limits multiple times during ci_forensics cv runs. OpenRouter auto-retries — the agent continues but with latency spikes. No runs lost to rate limiting, just slower.

**North Mini (OpenCode free tier):** Hard stop at 27/36 rows. `"Rate limit exceeded. Please try again later."` Also hit `"Insufficient balance"` on gpt-5-nano (title model, non-critical — titles just default to placeholder). Cell stalled at 75% complete. Needs `--resume` with bumped `delay_seconds`.

**Neither model lost completed work.** Both `--resume` cleanly. Operational friction, not data loss.

### Model ID Discovery

Took **3 attempts** to find the correct model ID string:

```
Attempt 1: openrouter/laguna-xs.2:free  → ProviderModelNotFoundError
Attempt 2: poolside/laguna-xs.2:free    → ProviderModelNotFoundError  
Attempt 3: openrouter/poolside/laguna-xs.2:free → ✓
```

OpenCode's error messages include `suggestions` — the correct ID was visible after attempt 2 but the prefix was wrong. One `opencode models | grep laguna` would have solved it immediately.

### The Cost of Free

| Cost Category | Laguna | North Mini |
|---|---|---|
| API cost per scenario | $0.00 (free tier) | $0.00 (free tier) |
| Average wall time per scenario | 43-96s | 18s |
| Rate limit risk | Moderate (auto-retry) | High (hard stop) |
| Model ID discovery time | ~15 min (3 failed runs) | 0 (known ID) |
| Total wall time for 1 cell (36 runs) | ~26 min | ~11 min (estimated) |

"Free" means zero API cost. It does not mean zero time cost. The operational overhead of rate limits, model ID discovery, and retry latency adds up. For a full 12-cell matrix at pass@3, the gap between free and paid becomes a wall-clock multiplier, not a dollar multiplier.

---

## The Second Trust Gap: The Model Doesn't Know It's Wrong

Every false-green run ends with the model's own summary (sparse prompt asks: "leave a short summary of what changed and why"). 3 of 4 declare success. One just describes the change without a verdict:

| Scenario | Model's Summary (snippet) | Ends With |
|---|---|---|
| `csv_header_contract` | "Changed from `sorted(rows[0].keys())` to `EXPORT_COLUMNS`... **Tests pass.**" | Success declaration |
| `decimal_money_rounding` | "Fixed by replacing `float` with `Decimal`... **CI is now green.**" | Success declaration |
| `dependency_api_change` | "Changed from `result is not True` to `not result.get('ok')` to match the new gateway API..." | No verdict (just facts) |
| `env_bool_parser` | "**Tests pass. Fix complete.**" | Success declaration |

**The model is factually accurate about what it changed.** It's not hallucinating. It's not lying. But 3 of 4 summaries declare victory based on CI green — treating the visible test signal as the definition of correctness. The model has no mechanism to flag uncertainty about unstated requirements. It doesn't say "I changed the header order, but I'm not sure if there are other edge cases." It says "Tests pass."

`dependency_api_change` is interestingly different. The model passed CI but stopped at a factual description — no declaration of completion. The evaluator found it missed charge_id propagation. The model knew what it did but had just enough restraint to not claim "fixed."

This is the **second trust gap**: not just between public and hidden tests, but between the model's own explanation and reality. The model is confidently wrong in 3 of 4 cases — not about what it did, but about whether what it did is sufficient. CI green becomes a cognitive offramp.

Future runs will store `model_summary` natively (added to harness during this investigation). The evaluator prompt now includes it, enabling cross-check: "the model claims X, the patch shows Y, the hidden test shows Z."

### The Deterministic False-Green

`decimal_money_rounding` attempts 1 and 2 produced **byte-identical patches**. Same 3-line change. Same `int(total * 100)` truncation. The model independently wrote the exact same wrong code from scratch, twice. This is not random. It's a stable attractor — the model converges to the same wrong solution when given the same problem. Retrying doesn't help because the public test signal doesn't push it out of the attractor.

`env_bool_parser` oscillated: attempt 2 added `"no"` and `"off"` to the deny list (better), attempt 3 removed them (worse). No convergence. Just re-sampling from a distribution of incomplete solutions.

`csv_header_contract` — same single-line fix all 3 times. Never addressed empty rows or extra fields. The model locked onto the visible symptom and never explored beyond it.

**Across 9 false-green attempts (3 scenarios × 3 passes): zero successful escapes.** The model's wrong-attractor is stronger than its variance.

---

## What This Cannot Claim

- **One pack.** 12 scenarios (ci_forensics). No product_workflows, no maintenance_value yet for Laguna/North Mini in this matrix.
- **Both models now complete on ci_forensics sparse + cv.** 144 runs across 4 cells. Pass@1, pass@3, and contract-visible comparison available.
- **System comparison, not model ranking.** North Mini runs on its native tool surface. Laguna runs through a foreign OpenRouter proxy. Speed asymmetry (2.8×) confounds raw capability.
- **pass@1 is noisy.** Gemma 12B's maintenance hidden pass swung 4/10 → 7/10 across two same-day runs. Single-attempt numbers are snapshots.
- **First-stage evidence.** 33 scenarios. One evaluator. No external audit.

---

## Next

- Wait for evaluator to finish 10/10 reviews
- Wait for Laguna ci_forensics cv cell → compare sparse vs cv gap
- Run North Mini pass@2/3 for retry comparison
- Run evaluator on North Mini false-greens
- Generate full matrix leaderboard once enough cells complete

---

*Matrix: `laguna-xs2-vs-north-mini-2026-06-22`. 75 runs stored of 396. pass@1. Not a benchmark. Not a leaderboard. A behavior microscope.*
