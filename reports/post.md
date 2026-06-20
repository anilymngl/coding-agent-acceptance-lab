When a coding agent turns your CI green, is the fix actually accepted? We ran a
small, curated eval to find out — and the gap is real.

Method: the model sees only weak public tests and a sparse bug ticket. Hidden
acceptance checks are injected *after* the model exits, so it can't optimize for
them. Runtime stalls are scored separately from capability.

On a maintenance pack (sparse, pass@1, local Ollama):

| Model | Public | Hidden | Trust Gap |
|---|---:|---:|---:|
| Gemma 4 31b | 10/10 | 7/10 | 30% |
| Gemma 4 e4b | 8/10 | 5/10 | 30% |
| Gemma 4 12b | 5/9 | 3/9 | 22% |

The same scenario class fails hidden across hosted and local models — the
trust-gap pattern repeats. One concrete false-green: an "adapter field rename"
patch passed the visible test but broke older payloads the hidden check covers.
An evaluator agent confirmed the root cause: the fix met the visible bar but
missed the full contract.

Honest caveats: this is a curated local-runtime eval, **not a public benchmark
leaderboard**. Per-run counts are noisy (the same e4b model went 5/10 -> 2/10
hidden across two runs), so read the pattern, not single numbers.
Single-evaluator reviews only; no model ranking.

Practical takeaway: green CI from an agent is a hypothesis, not a verdict.
Inject acceptance checks the agent can't see, separate runtime health from
capability, and don't rank models on pass@1.

Method and full evidence: reports/benchmark-quality-research-report-2026-06-20.md
