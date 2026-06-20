# Reports Index

All evaluation reports for North Mini Code runs using this harness.
Start with the current full-run report. Older reports are preserved with
surfacing conditions so historical partial evidence does not get mixed into
the current canonical readout.

For implementation handoff and current project direction, start with
[../docs/README.md](../docs/README.md) and
[../docs/model-comparison-eval-pipeline-plan-2026-06-20.md](../docs/model-comparison-eval-pipeline-plan-2026-06-20.md).

## Start Here

### [north-mini-ultimate-eval-report-2026-06-20.md](north-mini-ultimate-eval-report-2026-06-20.md)
**Current canonical full-run analysis.** Use this when you need the defensible
model readout: North Mini full evidence, DeepSeek controls across the same
stress packs, partial GLM caveat, claim ledger, deployment policy, and the
"why was DeepSeek not dramatically better?" analysis.

Surface this report when the question is: what is North Mini Code capable of,
where does it fail, how strong is the public-green/hidden-red trust-gap claim,
and what can we defend with current evidence?

---

## Gemma 4 Local Matrix (Multi-Model Comparison)

### [gemma4-matrix-analysis-2026-06-20.md](gemma4-matrix-analysis-2026-06-20.md)
**First multi-model local comparison.** Gemma 4 e4b (small) vs 31b on
`maintenance_value` sparse. Key finding: 31b matches North Mini at 7/10 hidden,
e4b at 5/10. The same 3 scenarios fail hidden across all models. Trust gap
is stable at 30% regardless of model. Read this for the cross-model picture.

### [leaderboard-local-gemma4-two-model.md](leaderboard-local-gemma4-two-model.md)
Auto-generated leaderboard report from the matrix pipeline. Contains the
raw scorecard, false-green breakdown with evaluator verdicts, operational
reliability, and scenario-level comparison tables.

### [integrity-local-gemma4-two-model.md](integrity-local-gemma4-two-model.md)
Artifact integrity verification for the Gemma 4 matrix. All 120 artifacts
present, 0 issues, 6/6 false-greens evaluator-reviewed.

### [leaderboard-local-gemma4-smallest-two.md](leaderboard-local-gemma4-smallest-two.md)
Auto-generated evidence for the smallest configured Gemma 4 pair,
`gemma4:e4b` and `gemma4:12b`, across sparse and `contract_visible` lanes.
Sparse: e4b completed 10/10 rows; 12B stored 10 rows but one was a 900s
`agent_timeout`, so treat 12B sparse as mixed local-runtime evidence. The
`contract_visible` lane ran but stalled: all 20 rows were
`no_output_timeout` on local Ollama, so they are operational reliability
evidence, not semantic failures. Lanes are kept separate in every scorecard.

### [integrity-local-gemma4-smallest-two.md](integrity-local-gemma4-smallest-two.md)
Artifact integrity verification for the smallest-two matrix. 240/240 artifacts
present, 120 SHA256 hashes, 0 missing. The 3 sparse false-greens are
evaluator-reviewed (3/3 coverage via `opencode/deepseek-v4-pro`).

### [benchmark-quality-research-report-2026-06-20.md](benchmark-quality-research-report-2026-06-20.md)
Tier 1 (internal behavior microscope) research report. Presents the trust-gap
pattern across North Mini, DeepSeek, and the local Gemma 4 matrices, with a
claim ledger and explicit "what cannot be defended" section. Notes the open
`contract_visible` question and pass@1 variance (e4b went 5/10 -> 2/10 hidden
across two runs). Not a public benchmark leaderboard.

### [post.md](post.md)
LinkedIn-postable summary, Tier 1 caveated. States the trust gap in plain
language, includes the local runtime caveat ("not a public benchmark
leaderboard"), and points back to the research report. No model ranking and no
public-leaderboard claim.

---

## Preserved Conditional Reports

### [north-mini-analysis.md](north-mini-analysis.md)
**Historical narrative analysis.** Keep this report for the earlier narrative
framing and first-pass operating policy. Do not surface it as the current
canonical scorecard because it predates the full DeepSeek control evidence and
newer full-run synthesis.

---

## Evaluation Reports

### [north-mini-fresh-run-harness-audit-2026-06-20.md](north-mini-fresh-run-harness-audit-2026-06-20.md)
Fresh-run harness audit. Surface this when the question is whether the recent
fresh data can be trusted. Key point: completed sparse maintenance attempts
show real semantic misses, but several later rows were OpenCode/provider runtime
stalls and must not be counted as semantic model failures.

### [north-mini-maintenance-value-v2-2026-06-20.md](north-mini-maintenance-value-v2-2026-06-20.md)
Positive-value maintenance report. Surface this when the question is specifically
about useful bounded maintenance tasks, best-of-3 maintenance success, patch
review cost, and accepted patches per review hour.

### [north-mini-code-xray-2026-06-19.md](north-mini-code-xray-2026-06-19.md)
Deep-dive x-ray on the primary + expanded run sets. Per-scenario public/hidden
breakdown, false-green taxonomy, trust-gap headline metrics, and an artifact
index linking every run to its raw patch, prompt, and test output.

### [north-mini-code-evidence-pack-2026-06-20.md](north-mini-code-evidence-pack-2026-06-20.md)
Defensible evidence pack combining the primary and expanded databases.
Includes severity-weighted scoring and scenario audit status.
Surface this when you need evaluator review tables, audit status, or artifact
index detail rather than the full-run model interpretation.

### [north-mini-code-opencode-2026-06-19.md](north-mini-code-opencode-2026-06-19.md)
Original primary run report (`ci_forensics` pack, 10 runs).
Surface only as a historical primary-run artifact.

---

## Evaluator Agent Reports

These reports were generated by a separate DeepSeek evaluator agent that
reviewed the model's patches and diagnosed root causes beyond pass/fail.

### [deepseek-v4-pro-live-smoke-2026-06-19.md](deepseek-v4-pro-live-smoke-2026-06-19.md)
Evaluator verdict on `metric_semantic_mismatch`. Key finding: the model placed
unit normalization in `compute()` (raw API) instead of `dashboard_total()`
(user-facing layer). Confidence 0.95, 4 evidence objects.

### [deepseek-v4-pro-north-mini-expanded-pghr-2026-06-20.md](deepseek-v4-pro-north-mini-expanded-pghr-2026-06-20.md)
Evaluator review of the expanded run set — all public-green/hidden-red cases
diagnosed with root cause categories.

### [deepseek-v4-pro-north-mini-primary-pghr-2026-06-20.md](deepseek-v4-pro-north-mini-primary-pghr-2026-06-20.md)
Evaluator review of the primary (ci_forensics) false-green cases.

### [deepseek-v4-pro-hidden-evaluator-2026-06-19.md](deepseek-v4-pro-hidden-evaluator-2026-06-19.md)
Hidden test evaluator run — using evaluator agent to grade hidden acceptance
independently of the automated harness.

### [deepseek-v4-pro-results-evaluator-2026-06-19.md](deepseek-v4-pro-results-evaluator-2026-06-19.md)
Consolidated evaluator results across the full run set.

---

## Methodology

The key distinction across all reports: **public pass ≠ acceptance**.

Every scenario has:
- **Public tests** — visible to the model during its run (like normal CI)
- **Hidden tests** — injected after the model exits, never seen by it

A model that makes CI green on a broken implementation registers as
`public_pass=1, hidden_pass=0` — a **false-green**. The trust gap
(public pass rate minus hidden pass rate) is the headline metric,
not overall accuracy.

See [docs/challenge-design.md](../docs/challenge-design.md) for
the full challenge design philosophy.
