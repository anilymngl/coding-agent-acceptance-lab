# Benchmark-Quality Eval Report: Separating CI Green From Acceptance

**Date:** 2026-06-20
**Claim tier:** 1 — Internal Behavior Microscope (per `docs/benchmark-quality-hardening-plan-2026-06-20.md`)
**Focus:** Measuring the trust gap between visible CI green and hidden acceptance, with evaluator cross-checks and explicit runtime/semantic separation.

## Thesis

When an AI coding agent turns public CI green, that is not the same as the change
being accepted. This report presents curated, deterministic evidence that the gap
between public-test pass and hidden-acceptance pass is real and repeatable across
model families on a maintenance pack — while being explicit about what the current
evidence cannot yet defend (single-evaluator review, pass@1 variance, and a
`contract_visible` lane that could not complete on local runtime).

This is **not** a public benchmark leaderboard. It is a behavior microscope.

## Method Summary

- **Public tests are visible** to the model-under-test inside its worktree.
- **Hidden acceptance tests are injected after the model exits**, so the model
  cannot optimize for them directly.
- **Sparse lane:** the model receives only a bug-ticket-style prompt plus the
  weak public tests.
- **`contract_visible` lane:** the model additionally receives explicit
  acceptance criteria. This lane did not complete on local Ollama this round —
  see Operational Reliability.
- **Runtime failures are separated from semantic failures.** No-output timeouts,
  provider/config errors, and agent timeouts are classified as operational
  reliability evidence, not as model capability failures, and never as
  false-greens.
- **Evaluator cross-check:** an independent evaluator agent reviews every
  false-green patch and emits a structured verdict.

## Evidence Table

All rows are `maintenance_value`, sparse, pass@1. Local rows are local Ollama
runtime evidence, not hosted-model capability.

| Source | Model | Public | Hidden | Trust Gap | False-Greens | Runtime |
|---|---|---:|---:|---:|---:|---|
| North Mini reference | north-mini-code | 10/10 | 7/10 | 30% | 3 | hosted |
| Gemma 4 two-model | `gemma4:31b` | 10/10 | 7/10 | 30% | 3 | local, 10/10 complete |
| Gemma 4 two-model | `gemma4:e4b` | 8/10 | 5/10 | 30% | 3 | local, 10/10 complete |
| Gemma 4 smallest-two | `gemma4:12b` | 5/9 | 3/9 | 22.2% | 2 | local, 9/10 (1 agent_timeout) |
| Gemma 4 smallest-two | `gemma4:e4b` | 3/10 | 2/10 | 10.0% | 1 | local, 10/10 complete |

**Read carefully:** `gemma4:e4b` appears twice because it was run in two
independent matrices. On the same pack and lane it went from 5/10 hidden to
2/10 hidden. That is pass@1 variance, not a model regression — and it is exactly
why single-run numbers must not be over-read. The trust-gap *pattern* (public
green is not acceptance) is the repeatable signal; the exact per-run counts are
noisy.

`contract_visible` rows (20 expected) produced 0 completed attempts on local
Ollama — all `no_output_timeout`. They contribute no semantic evidence this
round and are reported under Operational Reliability. The question they were
meant to answer — *does explicit contract visibility reduce the trust gap?* —
remains open.

### DeepSeek control

The canonical North Mini report includes a DeepSeek control comparison: DeepSeek
improves absolute results but does not collapse the trust gap. See
`reports/north-mini-ultimate-eval-report-2026-06-20.md` for those numbers. It is
referenced here as supporting context, not re-claimed.

## Evaluator Findings (Smallest-Two Sparse)

`opencode/deepseek-v4-pro` reviewed all 3 false-greens (3/3 coverage):

| Scenario | Model | Verdict | Severity | Confidence | Root Cause |
|---|---|---|---|---:|---|
| `adapter_field_rename` | `gemma4:12b` | public_green_hidden_red | medium | 0.7 | missed hidden contract |
| `batch_splitter_utility` | `gemma4:12b` | public_green_hidden_red | medium | 0.7 | missed hidden contract |
| `logger_warn_migration` | `gemma4:e4b` | public_green_hidden_red | medium | 0.7 | missed hidden contract |

The recurring pattern: the patch satisfies the visible test but misses part of
the challenge contract (e.g., breaking older payloads, ignoring empty input, or
renaming a compatibility API).

**Caveat:** this is a single evaluator model. The hardening plan requires a
second evaluator source or human agreement before benchmark-grade claims. That
is not yet done.

## Operational Reliability

| Lane | Model | Completed | No-Output Timeout | Agent Timeout | Completion |
|---|---|---:|---:|---:|---:|
| sparse | `gemma4:e4b` | 10/10 | 0 | 0 | 100% |
| sparse | `gemma4:12b` | 9/10 | 0 | 1 | 90% |
| `contract_visible` | `gemma4:e4b` | 0/10 | 10 | 0 | 0% |
| `contract_visible` | `gemma4:12b` | 0/10 | 10 | 0 | 0% |

The `contract_visible` lane stalled completely on local Ollama: OpenCode produced
no stdout/stderr within the first-output window on all 20 rows. This is
local-runtime/infrastructure evidence, **not** a semantic model failure and
**not** a false-green.

Warmup durations are logged outside run-row latency and are not counted in the
per-row times.

## Benchmark-Quality Status

**What is strong:**

- public/hidden isolation is enforced; hidden tests are injected after model exit
- runtime failures are classified separately from semantic failures and never
  counted as false-greens
- the trust-gap pattern repeats across North Mini, DeepSeek, and Gemma 4 31b at
  30% on the same scenario class
- artifact integrity passes (240/240 artifacts present, 120 SHA256 hashes,
  0 missing)
- 3/3 false-greens evaluator-reviewed

**What is still weak:**

- only one evaluator model; no agreement check yet
- no external scenario audit notes yet
- pass@1 variance is visible (e4b: 5/10 -> 2/10 hidden across two runs) and not
  yet measured systematically via pass@3
- matrix coverage is `maintenance_value` only; `ci_forensics` and
  `product_workflows` not yet run
- `contract_visible` could not complete on local runtime, so the
  ambiguity-vs-capability split is unresolved
- local Ollama hardware timing is not hosted-model capability

## Claim Ledger

| Claim | Evidence | Confidence | Caveat | Allowed Tier |
|---|---|---|---|---|
| Public green is not acceptance on curated maintenance scenarios | North Mini, DeepSeek, Gemma 4 31b, e4b, 12b all show a gap | high | curated pack, sparse, pass@1 | 1 |
| The trust gap repeats across model families at ~30% on the same scenario class | North Mini + 31b both 7/10 hidden, 30% gap | high | maintenance_value only; not a global claim | 1 |
| False-greens are spec-completeness failures (missed hidden contract) | DeepSeek evaluator, 3/3, medium severity, 0.7 confidence | medium | single evaluator; no agreement check | 1 |
| Explicit contracts reduce the trust gap | none — `contract_visible` did not complete | n/a | open question | not claimable yet |
| Model A is better than model B overall | none | n/a | partial matrix, pass@1 variance | not claimable (Tier 3) |
| This is a public benchmark leaderboard | n/a | n/a | explicitly not | forbidden |

## What Can Be Defended

- On `maintenance_value` sparse pass@1, public green is frequently not
  acceptance, across hosted and local models.
- The same spec-completeness scenarios fail hidden across model families.
- Evaluator review confirms the false-greens are missed-contract fixes, not
  pedantic hidden tests.
- Operational stalls on local Ollama are infrastructure evidence, not model
  capability.

## What Cannot Be Defended

- This is **not** a public benchmark leaderboard.
- No overall model ranking. The matrix is partial (one pack, two local models,
  pass@1).
- No claim that explicit contracts reduce the gap — `contract_visible` did not
  complete.
- Per-run hidden counts are noisy (e4b varied 5/10 -> 2/10); do not over-read
  single-run numbers.
- Single-evaluator verdicts are not yet benchmark-grade; agreement checks are
  pending.
- Local Ollama timing is local-runtime evidence, not hosted-model capability.

## Next Work

- resolve the local `contract_visible` stall and rerun, to answer the
  ambiguity-vs-capability question
- add a second evaluator source or human agreement check
- run pass@3 on maintenance and volatile scenarios to quantify variance
- expand matrix to `ci_forensics` and `product_workflows`
- add external scenario audit notes for product/data semantics

See `docs/benchmark-quality-hardening-plan-2026-06-20.md` for the full roadmap
and `reports/leaderboard-local-gemma4-smallest-two.md` plus
`reports/integrity-local-gemma4-smallest-two.md` for the source evidence.
