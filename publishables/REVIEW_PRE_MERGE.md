# Publishables Review — Pre-Merge Fixes

## Source: external review of `publishables-v2-matrix-update` branch

## Summary

The data is now stronger than the paper's metric language. The publishables mix attempt-level reliability, individual attempt index, and any-of-three scenario success as though they were the same quantity. Fix that, narrow the structural claim, remove stale tool-call table, consolidate papers.

---

## P0 — Correctness Issues

### 1. Evidence-index JavaScript is broken
- Data stores lane as `"cv"`, filter checks `r.lane === "contract"` → contract filter returns nothing
- Data stores verdicts as `hidden_pass`/`false_green`, renderer checks `false-green`/`pass` → Outcome column renders `-`
- `pass` filter means `h === r` (perfect 3/3), not "has hidden pass"
- Title says "All Runs" but contains 132 aggregated scenario-model-lane rows, not 391 attempt rows
- Fix: rename to "Evidence Matrix — Scenario Cells", fix filter strings, fix verdict strings

### 2. "Zero false-greens" is false in several places
- Laguna product CV: 11/11 any-of-3, but `support_sla_business_hours` has 2 false-green attempts
- North Mini product CV: 10/11 any-of-3, but contains 10 false-green attempts
- North Mini maintenance CV: 10/10 any-of-3, but contains 1 false-green attempt, only 25/30 attempts exist
- Fix: distinguish "no scenario remained unsolved" from "zero false-green attempts"

### 3. Table 4 contradicts Table 13
- Table 4 says 11/12 on ci_forensics CV with 8% FG
- Actual any-of-3 is 12/12; attempt-level is 34/36 with 2 FG (5.6%)
- Table 13 says 0% best-of-3 FG (closer to scenario-level)
- Fix: choose one unit per table, label clearly

### 4. pass@1→pass@2 "regression" is wrong terminology
- Cumulative pass@k cannot regress
- Table is comparing attempt 1 vs attempt 2 vs attempt 3 (independent samples)
- Fix: rename section "Independent retries are not monotonically better", table columns "Attempt 1/2/3/Any-of-3"

### 5. Tool-call KPI section is stale
- Table 11 N values sum to 377, not 391
- Laguna split 131/67 — should be 152/46 with final data
- Section was not regenerated after product CV completion
- Fix: recompute, or remove section until recomputed
- Also: use median not mean, stratify by pack/lane, state trace coverage, avoid causal language
- Label patch-size as "tracked-file diff statistics" (untracked files historically omitted)

---

## P0 — Claims Too Large

### 6. "The trust gap is structural, not model-specific"
- Too strong. Data supports: "pattern recurred across both systems, more sensitive to prompt lane and task pack than model identity in several matched cells"
- Does NOT establish causation from model size/training/reasoning
- Models differ on product_workflows: Laguna has fewer FG + 3 more any-of-3 successes
- Fix: scoped interpretation

### 7. "Same architecture"
- 33B total vs 30B total — similar class, not same
- Fix: "similar architecture class (3B-active MoE)"

### 8. "Product workflows resist everything" (homepage)
- Contradicts CV results (11/11, 10/11 any-of-3)
- Fix: "Sparse product workflows produced persistent false-greens. Explicit contracts recovered most scenarios."

### 9. Title "wall they cannot climb"
- Obsolete — they climbed most with contracts
- Suggested: "Measuring Acceptance Reliability in Coding-Agent CI Repair"

---

## Gateway Caveat Needs Stronger Treatment

### 10. Remove "No behavioral difference was observed across the switch boundary"
- No matched switch-boundary experiment exists
- Pack and gateway changed together — cannot estimate gateway effects
- Treat tested unit as: North Mini/OpenCode Zen (ci+maint), North Mini/OpenRouter (product)
- Every product table needs gateway footnote
- Update: models table, model disclosure footer, data availability, evidence index with gateway/config column

---

## Paper Consolidation

### 11. paper.html is NOT clean Part I
- Already contains pass@3 retry claims, structural conclusions, Laguna pass@3 variance, North Mini pass@3 analysis
- It's an older omnibus paper, not a pre-pass@3 Part I
- Recommendation: ONE canonical paper with Study A (breadth) + Study B (depth) + failure analysis + operational analysis + threats to validity
- Archive current versions to `publishables/archive/`

---

## Stale Suite Pages

### 12. evaluator-findings.html
- Says 49 unreviewed, not 91
- Incorrect: says evaluator cannot see source code (it can)
- Incorrect: says exact evidence quotes mean "cannot make things up"
- Incorrect: says shadow fix proves hidden tests aren't broken
- Fix: "The evaluator diagnoses whether the patch violates the authored benchmark contract. It does not independently establish that the contract is fair, complete or representative."

### 13. harness-built-target.html
- Still says 239 runs, 59 FG, 49 unreviewed
- Correct implementation claims needed:
  - baseline result recorded but not enforced
  - historical patches may omit untracked files
  - integrity hashes computed later, not compared with run-time digests
  - resume treats stored attempts as complete
  - evaluator fallback reviews must not count as valid agent reviews

### 14. README.md
- Says 81 rows, 10/59 evaluator coverage, one matrix root, Georgia is web font (it's system)
- paper.html labeled as "clean pass@1 prior paper" — it's not

### 15. index.html
- References `v11.html` which doesn't exist
- Labels `paper.html` as "Prior Paper v1" despite mixed contents

### 16. Signal skill examples
- Still says 49 unreviewed, treats old pages as verified
- Either update or freeze as dated snapshots with warning

---

## Metric Vocabulary (use consistently)

1. **Attempt-level hidden pass rate** — retained attempts that passed hidden acceptance
2. **Attempt-level false-green rate** — false-green attempts / public-green attempts
3. **Any-of-3 scenario success** — at least one of three attempts passed hidden acceptance
4. **All-of-3 scenario reliability** — every retained attempt passed hidden acceptance

Stop using one generic `FG%` column for all four meanings.

---

## Recommended Merge Sequence

### Commit 1 — fix factual/rendering bugs
- Evidence-index filters, verdict strings, lane values
- Broken/missing references
- Stale counts
- Gateway metadata
- Data availability paths

### Commit 2 — fix metric semantics
- Formal definitions (4 terms above)
- Attempt vs any-of-three tables
- Rename Attempt 1/2/3
- Recompute ci_forensics CV
- Remove "zero false-green" where only any-of-3 is zero
- Recompute or remove tool KPI section

### Commit 3 — rewrite claims
- Replace structural certainty with scoped interpretation
- Remove "same architecture"
- Replace obsolete wall title
- Revise homepage thesis
- Narrow delegation recommendations

### Commit 4 — consolidate suite
- Choose one canonical paper
- Update README
- Update evaluator and harness pages
- Archive old papers
- Sync or freeze Signal examples

### Commit 5 — add verification
Create `scripts/verify_publishables.py` that checks:
- All internal links exist
- Data row count is 132
- Retained attempts sum to 391
- False-greens sum to 101
- Paper headline numbers match generated JSON
- No forbidden stale strings remain
- Lane filters match actual values
- Verdict values match renderer cases
- Gateway caveats appear wherever North product data is used
