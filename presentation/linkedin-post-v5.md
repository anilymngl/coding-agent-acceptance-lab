# When CI goes green, is the bug actually fixed?

We tested 5 coding-agent models through the same evaluation harness. 33 scenarios. Hidden acceptance tests injected after the agent exits. Two prompt lanes: sparse ("CI is red, fix it") vs contract-visible (full acceptance criteria).

The pattern holds for all of them.

## The data

### CI Forensics — 12 mechanical bugs

| Model | Sparse | Contract-Visible |
|---|---|---|
| **North Mini** (Cohere 30B/3B) | 8/12 hid · **33% false-green** | 11/12 hid · **8%** |
| **Gemma 12B** (local Ollama) | 3/12 hid · **40%** | 6/12 hid · **14%** |
| **DeepSeek V4 Pro** (frontier API) | 9/12 hid · **25%** | 12/12 hid · **0%** |
| **Laguna XS.2** (Poolside 33B/3B) | 8/12 hid · **33%** | 12/12 hid · **0%** |

### Product Workflows — 11 business-logic tasks

| Model | Sparse | Contract-Visible |
|---|---|---|
| **North Mini** | 1/11 hid · **89% false-green** | 6/11 hid · **33%** |
| **Gemma 12B** | 2/11 hid · **67%** | 7/11 hid · **12%** |
| **DeepSeek** | 3/11 hid · **73%** | 10/11 hid · **9%** |

Under sparse prompts, the free model and the frontier model fail identically on business logic. 73–89% of CI-green patches don't actually fix the problem.

### Maintenance — 10 refactoring tasks

| Model | Sparse | Contract-Visible |
|---|---|---|
| **North Mini** | 8/10 hid · **20%** | 9/10 hid · **0%** |
| **Gemma 12B** | 7/10 hid · **22%** | 6/10 hid · **14%** |
| **DeepSeek** | 7/10 hid · **30%** | 10/10 hid · **0%** |

North Mini and DeepSeek: zero false-greens with clear specs. Mechanical work is safe to delegate.

## The contract-visible effect

Telling the model what "done" means changes everything:

- DeepSeek product workflows: **73% → 9%** false-green. One instruction change.
- North Mini product workflows: **89% → 33%**.
- Laguna ci_forensics: **33% → 0%**.

The contract is the intervention. Not the model size. Not the reasoning capability. The spec.

## 3 scenarios no model solved

`csv_header_contract`, `decimal_money_rounding`, `env_bool_parser` — failed by all 5 models at pass@1. Not the free model, not the frontier model, not the local model.

The hidden contract cannot be inferred from the public test alone. You can't deduce "half-up cent rounding" from seeing `0.29 × 3 = 87`. The challenges were designed to create this gap.

From `docs/challenge-design.md`: "The dividing line is whether the spec is richer than the visible test, not model size."

## The speed reality

| Model | Type | Avg Speed |
|---|---|---|
| North Mini | API (Cohere free) | 17s |
| DeepSeek | API (hosted) | 36s |
| Laguna XS.2 | API (OpenRouter free) | 44s |
| Gemma 12B | Local (Ollama) | 211s |

Speed doesn't correlate with accuracy. Laguna is 2.5× slower than North Mini with identical output.

## Deployment zones

**Green — merge on CI green.** Mechanical work. Migrations. Fixtures. Docs. All models converge at 0–14% false-green with clear specs.

**Amber — gate on hidden acceptance.** Adapters. Validators. Edge cases. Every model produced false-greens here under sparse. Clear specs close the gap.

**Red — human review or frontier model with clear specs.** Billing. Discounts. Inventory. SLAs. 67–89% false-green under sparse. 9–33% even with clear specs.

The model is replaceable. The trust gate is the enduring investment.

---

5 models. 3 packs. 2 lanes. ~600 total runs across all matrices. pass@1. github.com/anomalyco/north-mini-test
