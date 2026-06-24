# Publishables — Merge and Update Plan

## The Problem

The publishables present two papers as peers. They're not. v1 is the question, v2 is the answer. The reader doesn't know that walking in. The narrative is split when it should be sequential.

## Current State

- paper.html (v1) — 5 models, 4 families, pass@1, ~600 runs. Discovery: the gap is universal.
- paper_v2.html (v2) — 2 models, pass@3, 391 runs, all 3 packs. Mechanism: the gap is structural, specs fix it, retries regress.
- Gemma 4 evidence — orphaned in reports/, not in either paper. Bridges v1 and v2.
- evidence-index.html — 132 rows, all v2 data. v1 evidence not shown.
- evaluator-findings.html — 10 reviewed false-greens, all from v1. 91 unreviewed.

## Planned Changes

### 1. index.html — reframe as a sequence

- Thesis: state the turn. "We thought model choice mattered. Two independently trained models proved it doesn't."
- Two paper cards:
  - v1: "Discovery — the gap is universal across 5 models, 4 families"
  - v2: "Mechanism — the gap is structural, specs fix it, retries regress"
- Remove "Prior Paper" framing — v1 is not obsolete, it's Part I.
- Add Gemma 4 corroboration as a third evidence pointer.
- Surface tool-call finding as headline: "False-greens use fewer tool calls and write larger patches."

### 2. paper.html (v1) — reframe as Part I

- Add forward pointer at top: "This paper established the trust gap pattern. The follow-up tests whether it's structural or model-specific. → paper_v2.html"
- Title: include "Part I" or "Discovery."
- Conclusion: add "we don't yet know if this is structural or model-specific — that's what v2 tests."
- Current conclusion reads as the complete story. It's the setup.

### 3. paper_v2.html (v2) — lead with structure, not comparison

- Title/abstract: lead with "the gap is structural" not "Laguna vs North Mini."
- Abstract opening: "Two independently trained coding agents from different companies converge to identical false-green patterns. The gap is between the visible test and the hidden contract, not between models."
- Introduction: add Part I → Part II turn. "The v1 study found a 20-62% trust gap across 5 models from 4 families. This suggested the gap is universal — but not whether it's structural or model-specific. We test that here."
- Add Gemma 4 as corroborating evidence in method or discussion.
- The model comparison is the method, not the finding.

### 4. evidence-index.html — add v1 data or note its absence

- Either add a second table/filter for v1 data, or note that v1 data lives in separate DBs and isn't shown here.
- Distinguish v1 (5 models, pass@1) from v2 (2 models, pass@3).

### 5. evaluator-findings.html — update the gap

- "49 unreviewed" → "91 unreviewed."
- Note that all 10 reviewed false-greens are from v1 (Laguna ci_forensics sparse pass@1).
- None of the v2 false-greens have been reviewed. This is a bigger honesty gap now.

### 6. harness-built-target.html — update status

- Update "49 unreviewed" mention.
- Update matrix completion status from "4 of 12 cells not built" to "98.5% complete."

### 7. README.md — update structure

- Reflect the two-paper sequence.
- Note the Gemma 4 evidence.
- Note the gateway caveat.
- Update evidence tier statement.

## What NOT to Change

- scenario-catalog.html — scenario designs haven't changed.
- The data in evidence-index — already correct.
- v1 paper's actual findings — still valid, just incomplete.
- v2 paper's data — already updated.

## Priority

The biggest single change is reframing v2's abstract and title from "model comparison" to "structural analysis." That's the one that would make the research story click.

## Verification Checklist

Before publishing:
- [ ] All numbers in v2 match DB queries.
- [ ] Both models reported wherever a cross-model claim is made.
- [ ] Gateway caveat stated wherever North Mini product_workflows is discussed.
- [ ] "Timeout wall" language fully removed — no stale claims.
- [ ] v1 forward pointer added.
- [ ] Gemma 4 corroborating evidence referenced.
- [ ] Evaluator coverage numbers accurate (10/101 reviewed).
