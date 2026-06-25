# Methodology

The lab measures whether visible CI success is trustworthy.

## Public And Hidden Tests

Each scenario has:

- **Public tests**: visible to the agent, runnable during the session, equivalent to normal CI.
- **Hidden tests**: injected only after the agent exits, never visible during the repair attempt.

A run where public tests pass and hidden tests fail is a **false-green**. It means the patch made CI green without satisfying the broader authored contract.

## Metrics

| Metric | Meaning |
|---|---|
| Public pass rate | How often the agent made visible tests green |
| Hidden pass rate | How often the patch satisfied hidden acceptance |
| Trust gap | Public pass rate minus hidden pass rate |
| False-green rate | False-greens divided by public-green attempts |
| Retained attempts | Attempts included in semantic analysis |
| Missing attempts | Planned attempts excluded for audited operational reasons |

The trust gap is the headline because it measures how often "looks fixed" differs from "is fixed."

## Interpretation Rules

- Do not count no-output timeouts as false-greens.
- Do not count provider/config failures as semantic model failures.
- Keep operational reliability separate from acceptance reliability.
- Preserve incomplete-cell denominators.
- Treat evaluator reviews as diagnostic evidence, not external truth.
- Do not present this as a public benchmark leaderboard.

## Study A And Study B

Study A is breadth evidence across multiple configurations and packs. Study B is the canonical 391-retained-attempt depth matrix comparing Laguna XS.2 and North Mini across 33 scenarios, two prompt lanes, and pass@3 attempts.

Study B central metrics recompute from `data/releases/v1/study-b.sqlite` using:

```bash
uv run python scripts/verify_release_data.py
```

## Contract Visibility

The sparse lane measures how well agents infer the broader contract from visible tests and prompt context. The contract-visible lane measures how much explicit acceptance criteria reduce false-greens. Lower false-green rates under contract-visible prompting support the claim that many failures are contract-recovery failures, not just random coding failures.

## Evaluator Reviews

Evaluator workbench reviews reconstruct selected false-greens, validate quoted evidence, and classify failure causes. They are useful for diagnosis and examples, but the acceptance gate remains the deterministic hidden-test result.
