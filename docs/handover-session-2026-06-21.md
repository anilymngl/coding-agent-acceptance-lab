# Session Handover — 2026-06-21

## 1. Project Goal & Initial State

**Primary Objective:** Run a full-model comparison matrix between North Mini
(`opencode/north-mini-code-free`, Cohere-built) and Gemma 4 12b
(`ollama/gemma4:12b`) across three packs (`ci_forensics`, `maintenance_value`,
`product_workflows`) in two prompt modes (`sparse`, `contract_visible`) at
pass@1, then generate a comparison report.

**Starting Point:** Multiple prior Gemma 4-only matrices already completed
(e4b, 12b smoke, two-model, smallest-two, full). North Mini had historical runs
(primary + expanded) in `data/fresh-2026-06-20-north-mini-sparse.sqlite` and
`data/north-mini-code-eval.sqlite`. No matrix config existed combining North
Mini with a local model on all packs.

**Success Criteria:**
- All 12 matrix cells populated (2 models × 3 packs × 2 lanes)
- Runtime failures classified and retriable (not lost evidence)
- False-greens evaluator-reviewed
- Leaderboard report generated comparing both models

## 2. Key Decisions & Architectural Pivots

**Decision 1: Matrix config for multi-model comparison (not ad-hoc commands)**
- Rationale: The manual `ci-vibe-run run` approach scatters DBs across paths and
  requires manual report assembly. A matrix config gives a single `run` command
  plus unified `status`/`leaderboard`/`evaluate`/`integrity` tooling.
- Alternatives ruled out: Running 12 separate `ci-vibe-run run` commands
  manually — error-prone, no unified status view, no automatic leaderboard.
- Trade-offs: Matrix config locks the experiment shape upfront (packs, lanes,
  models). Changing it mid-run requires a new config.
- Impact radius: `configs/matrix/north-mini-vs-gemma4-12b.json`, 12 SQLite DBs
  under `data/matrix/north-mini-vs-gemma4-12b-2026-06-21/`, 12 artifact
  directories under `runs/matrix/...`.

**Decision 2: Per-model timeout tuning**
- Rationale: North Mini (API, fast) uses `timeout=900, first_output_timeout=300`.
  Gemma 4 12b (local Ollama, slow prefill on contract_visible) uses
  `timeout=1800, first_output_timeout=600`. Prior smallest-two matrix showed
  contract_visible stalls at 240s first_output.
- Alternatives ruled out: Single shared timeout — would either waste time on
  North Mini (too long) or timeout 12b (too short).
- Trade-offs accepted: Different latency profiles confound "model speed"
  comparisons, but the metric is correctness (trust gap), not speed.
- Impact radius: Matrix config defaults + per-model overrides.

**Decision 3: `--resume` skips all stored rows, runtime failures included**
- Rationale: The harness treats every stored row as permanent evidence. Deleting
  runtime failures manually is the only current retry path.
- Trade-offs accepted: A run that hits 5 runtime failures and 6 successes is
  "complete enough" for evidence but can't be retried without manual SQL.
- Impact radius: Catalyst for the `ci-vibe-matrix retry` proposal (see §10).

**Decision 4: `--live` flag for `check-opencode.sh`**
- Rationale: The full health check prints 11+ sections (ollama, models, config,
  processes, usage, tracker, matrix scope, totals, evaluator, disk, dashboard).
  During a run, only sections 4 (processes) and 6 (active run tracker) matter.
  `--live` gates all other sections when an `opencode run` agent is active.
- Alternatives ruled out: Separate script — duplicates logic and diverges.
- Trade-offs accepted: Section 4 (processes) still shows in live mode because
  it defines `oc_run` which section 6 depends on.
- Impact radius: `check-opencode.sh` — added `MODE_LIVE`, `live_skip()` guard
  function, and `live_skip || { ... }` wrappers around sections 1-3, 5, 7, 7b,
  8, 9, 10, integrity, deep. ~15 lines changed.

**Decision 5: The harness is a "CI-repair fidelity harness," not a coding benchmark**
- Rationale: Models are asked to fix red CI with only public tests visible.
  Hidden acceptance tests are injected after exit. `public=1, hidden=0` is a
  **false-green** — CI is green but the bug isn't fixed. The headline metric is
  **trust gap** (public pass rate minus hidden pass rate).
- Impact radius: All interpretation of results, all future evaluation design.

**Decision 6: The matrix is the experiment grid**
- Rationale: Single model × single pack × single lane = anecdote. Matrix =
  comparison across models, packs, lanes. It isolates variables: model effect
  (north-mini vs 12b), prompt effect (sparse vs contract_visible), pack
  difficulty (ci_forensics vs product_workflows).
- Impact radius: All matrix config design, all report interpretation.

## 3. Key Terminology & Domain Vocabulary

| Term | Definition | Context |
|------|------------|---------|
| **Trust gap** | public_pass_rate − hidden_pass_rate | Headline metric. >0 means the model makes CI green without fixing the bug. |
| **False-green** | public_pass=1, hidden_pass=0 | A specific scenario where the model gamed the visible test. |
| **Hidden pass** | public_pass=1, hidden_pass=1 | The model actually solved the problem. |
| **Public red** | public_pass=0 | The model couldn't even make CI green. |
| **Sparse** | Minimal prompt — just "CI is red, fix it" + scenario title | Tests independent problem-solving. |
| **Contract visible** | Prompt includes acceptance criteria (expected behavior, success signals, failure modes) | Tests whether explicit specs reduce false-greens. |
| **Audit visible** | Prompt includes full solution hints | Maximum hand-holding. Not used in this session. |
| **Pack** | A themed set of 10-12 scenarios. `ci_forensics` (CI bugs), `maintenance_value` (refactoring), `product_workflows` (business logic), `data_semantics` (data pipeline bugs). | Unit of matrix configuration. |
| **Cell** | One (model × pack × prompt_mode) combination in the matrix | Each cell produces one SQLite DB and one artifact directory. |
| **Pass@1** | One attempt per scenario. No retries, no best-of-N selection. | Measures first-attempt reliability. High variance. |
| **Runtime failure** | `agent_timeout`, `no_output_timeout`, `provider_or_config_error`, `runner_error` | Not a semantic model failure. Retriable. |
| **Completed outcome** | `hidden_pass`, `false_green`, `public_red` | Semantic result from a model attempt. Not retriable. |
| **First-output timeout** | Harness kills the run if OpenCode produces zero stdout/stderr within this window | Prevents model prefill stalls from consuming the full wall-clock timeout. |
| **Experiment ID** | Unique string per (matrix_id × model_alias × pack × lane) cell | Scopes `--resume` so different matrix configs never collide. |

## 4. Development Journey

### Phase 1: Situation Assessment
Explored existing matrix results. Found that `local-gemma4-full` had fresh
pass@1 on maintenance_value sparse with e4b (2/10 hidden) and 12b (4/10
hidden) — no report generated yet. The `local-gemma4-smallest-two` matrix had
a full leaderboard report. North Mini historical data existed but was stale
(ci_forensics + maintenance_value from prior runs, no product_workflows, no
contract_visible comparison).

### Phase 2: Manual ci_forensics Pilot
Ran North Mini and Gemma 4 12b on `ci_forensics contract_visible` as a manual
smoke test before committing to the full matrix. Results:
- North Mini: 11/12 hidden (92%), 1 false-green (`env_bool_parser`), trust gap 8%
- Gemma 4 12b: 4/12 hidden (33%), 4 false-greens, trust gap 33%

Pilot validated that (a) contract_visible prompts don't stall 12b with the
higher timeouts, (b) North Mini dramatically benefits from explicit specs,
(c) 12b's trust gap persists even with specs. Proceeded to full matrix.

### Phase 3: Full Matrix Run
Created `configs/matrix/north-mini-vs-gemma4-12b.json` — 2 models, 3 packs, 2
prompt modes, 12 cells, ~132 scenario runs. Validated with `ci-vibe-matrix plan`.
Ran with `uv run ci-vibe-matrix run configs/matrix/north-mini-vs-gemma4-12b.json`.

North Mini completed all 6 cells (cells 1-6). Gemma 4 12b completed cells 7-8
(ci_forensics sparse + contract_visible) and was in flight on cell 9 at session
end. Issues discovered during run:
- North Mini `product_workflows sparse`: 5 runtime failures (first_output_timeout
  at 300s on large scenarios like `search_ranking_stability`)
- North Mini `product_workflows contract_visible`: all 11 rows stored as
  runtime failures (no_output_timeout — the larger contract_visible prompts
  exceeded the 300s first-output window)
- Conclusion: 300s first_output_timeout is too tight for product_workflows.
  Cell results are operational evidence, not semantic failures.

### Phase 4: Tooling Improvements
Created `docs/matrix-retry-runtime-failures-proposal-2026-06-21.md` — a design
proposal for a `ci-vibe-matrix retry` subcommand that uses the existing
`classify_row()` function to DELETE only runtime-failure rows, then re-runs
with `--resume`. Preserves semantic evidence, retries only infrastructure
failures. Zero schema changes, ~40 lines of new code.

Added `--live` flag to `check-opencode.sh` — gates all diagnostic/aggregate
sections when an agent is running, showing only the active run tracker.

### Phase 5: Conceptual Discussion
Articulated the harness philosophy: it's a CI-repair fidelity harness measuring
trust gap (not a coding benchmark measuring accuracy). The matrix is the
experiment grid that turns anecdotes into comparisons by isolating model effect,
prompt effect, and pack difficulty. The end goal is a packaged "study runner"
that orchestrates run → retry → evaluate → report in one command.

## 5. Technical Architecture & Design Patterns

**High-Level Architecture:**

```
ci-vibe-matrix run ──► ci-vibe-run run ──► opencode run ──► model
     (orchestrator)       (per-cell)        (agent loop)    (LLM)
         │                     │                  │
         ▼                     ▼                  ▼
    matrix-run.log        SQLite DB          worktree/
                         (per cell)         artifacts/
                              │
                              ▼
                    ci-vibe-matrix evaluate
                    ci-vibe-report leaderboard
                    ci-vibe-report integrity
```

**Data Flow:**
1. Matrix config (JSON) → `ci-vibe-matrix run` parses into cells
2. Per cell: spawns `ci-vibe-run run` with experiment_id, model, pack, prompt_mode
3. `ci-vibe-run` per scenario: prepares worktree → runs baseline tests →
   invokes `opencode run` with the prompt → captures output → runs public tests →
   injects hidden tests → runs hidden tests → stores everything in SQLite + artifacts
4. After all cells complete: `ci-vibe-matrix evaluate` runs evaluator agent on
   false-green rows. `ci-vibe-report leaderboard` generates Markdown report.
5. `check-opencode.sh --live` queries the active run's worktree + DB for
   real-time progress (not part of the pipeline, sidecar monitoring).

**Design Patterns:**
- **Evidence preservation**: Every attempt is stored forever. No overwrites.
  Runtime failures are preserved as evidence of operational reliability.
  Semantic failures are preserved as evidence of model behavior.
- **Experiment isolation**: `experiment_id` prevents different matrix configs
  from colliding in the same DB. `--resume` is scoped to experiment_id.
- **Classification facade**: `classify_row()` in `ci_vibe_lab/matrix.py:502-543`
  is the single source of truth for row outcome classification. Used by
  `status`, `leaderboard`, `evaluate`, and the proposed `retry` subcommand.
- **Config-driven matrix**: The matrix config JSON is the declarative
  specification. `plan`, `run`, `status`, `evaluate`, `dbs` all consume it.
  No imperative scripting needed between pipeline stages.

## 6. Current State & Concrete Artifacts

**Implementation Status:** Running. North Mini cells 1-6 complete. Gemma 4 12b
cells 7-8 complete, cell 9 in-flight, cells 10-12 pending at session end.

**Matrix Config — `configs/matrix/north-mini-vs-gemma4-12b.json`:**
```json
{
  "matrix_id": "north-mini-vs-gemma4-12b-2026-06-21",
  "description": "Full comparison matrix: North Mini vs Gemma 4 12b on ci_forensics + maintenance_value + product_workflows, sparse and contract_visible, pass@1.",
  "output_root": "data/matrix/north-mini-vs-gemma4-12b-2026-06-21",
  "runs_root": "runs/matrix/north-mini-vs-gemma4-12b-2026-06-21",
  "defaults": {
    "agent": "build",
    "auto_approve": true,
    "timeout": 900,
    "delay_seconds": 15,
    "runs": 1,
    "prompt_modes": ["sparse", "contract_visible"],
    "packs": ["ci_forensics", "maintenance_value", "product_workflows"],
    "warmup": true,
    "warmup_timeout": 600,
    "warmup_keep_alive": "30m"
  },
  "models": [
    {
      "alias": "north-mini",
      "id": "opencode/north-mini-code-free",
      "runtime": "opencode",
      "first_output_timeout": 300,
      "timeout": 900
    },
    {
      "alias": "gemma4-12b",
      "id": "ollama/gemma4:12b",
      "runtime": "ollama",
      "first_output_timeout": 600,
      "timeout": 1800
    }
  ],
  "packs": {
    "ci_forensics": { "runs": 1, "prompt_modes": ["sparse", "contract_visible"] },
    "maintenance_value": { "runs": 1, "prompt_modes": ["sparse", "contract_visible"] },
    "product_workflows": { "runs": 1, "prompt_modes": ["sparse", "contract_visible"] }
  }
}
```

**Completed Results (mid-run snapshot):**

| Model | Pack | Lane | Done | Public | Hidden | Trust Gap | False-Green |
|---|---|---|---|---|---|---|---|
| north-mini | ci_forensics | sparse | 12/12 | 12 | 8 | 33% | 4 |
| north-mini | ci_forensics | contract_visible | 12/12 | 12 | 11 | 8% | 1 |
| north-mini | maintenance_value | sparse | 10/10 | 10 | 8 | 20% | 2 |
| north-mini | maintenance_value | contract_visible | 10/10 | 9 | 9 | 0% | 0 |
| north-mini | product_workflows | sparse | 6/11 | 7 | 0 | — | 7* |
| north-mini | product_workflows | contract_visible | 0/11 | — | — | — | 11 runtime failures |
| gemma4-12b | ci_forensics | sparse | 12/12 | 5 | 3 | 17% | 2 |
| gemma4-12b | ci_forensics | contract_visible | 0/12 (in-flight) | — | — | — | — |

*5 rows are runtime failures (first_output_timeout), not semantic false-greens.
The actual completed scenarios had 7 public passes, 0 hidden passes = 7
false-greens among the 6 valid completions (some rows have duplicates).

**Retry Proposal — `docs/matrix-retry-runtime-failures-proposal-2026-06-21.md`:**
Full proposal for `ci-vibe-matrix retry CONFIG` subcommand. Key points:
- Uses existing `classify_row()` and `is_runtime_failure_outcome()` from
  `ci_vibe_lab/matrix.py:502-543`
- Deletes only runtime-failure rows (agent_timeout, no_output_timeout,
  provider_or_config_error, runner_error)
- Never touches semantic evidence (hidden_pass, false_green, public_red)
- After deletion, runs `ci-vibe-matrix run --resume` to fill gaps
- `--dry-run` flag for preview
- ~40 lines of new code, no schema changes

**Live Monitor — `check-opencode.sh --live`:**
Added `MODE_LIVE=0`, `SKIP_IN_LIVE`, `live_skip()` guard function.
When `--live` is set and an `opencode run` agent is active, sections 1-3, 5,
7, 7b, 8, 9, 10, integrity, and deep are gated behind `live_skip || { ... }`.
Only sections 4 (processes) and 6 (active run tracker) print.

**File structure changed:**
```
check-opencode.sh                    # +15 lines (--live flag + guards)
docs/
├── matrix-retry-runtime-failures-proposal-2026-06-21.md  # NEW
├── handover-session-2026-06-21.md                         # (this file)
└── README.md                       # +1 line (retry proposal reference)
configs/matrix/
└── north-mini-vs-gemma4-12b.json   # NEW
data/matrix/
└── north-mini-vs-gemma4-12b-2026-06-21/  # 8 DBs created so far
    ├── north-mini/
    │   ├── ci_forensics-sparse.sqlite
    │   ├── ci_forensics-contract_visible.sqlite
    │   ├── maintenance_value-sparse.sqlite
    │   ├── maintenance_value-contract_visible.sqlite
    │   ├── product_workflows-sparse.sqlite
    │   └── product_workflows-contract_visible.sqlite
    └── gemma4-12b/
        ├── ci_forensics-sparse.sqlite
        └── ci_forensics-contract_visible.sqlite
```

## 7. Dependencies, Constraints & External Factors

**Technical Dependencies:**
- `uv` — Python package manager. Must be in PATH or use `.venv/bin/python`.
  (Note: `uv` was not found in the session shell; `.venv/bin/activate` worked.)
- `ollama serve` — local Ollama runtime (pid 7081, v0.30.10) on port 11434.
  Required for `ollama/gemma4:12b` model. Uses `gemma4:12b` with Q4_K_M
  quantization, 8.4GB VRAM, 32768 context.
- `opencode` — web daemon (pid 15231, port 4096) and agent run loop.
- `openai/north-mini-code-free` — API model via OpenCode provider. Free tier,
  no explicit rate limit documented but risk of throttling.
- `sqlite3` — local evidence storage. DB at
  `~/.local/share/opencode/opencode.db` (192MB, 485 sessions).

**Hard Constraints:**
- Gemma 4 12b is single-GPU local inference. Ollama serializes requests.
  Contract_visible prompts are ~3-5× larger than sparse — prefill time
  dominates. 600s first_output_timeout needed to avoid stalls.
- North Mini free tier: unknown rate limit. 15s delay between scenarios
  with ~5-8 API calls per scenario ≈ 300+ calls in 2 hours. Risk of
  throttling on larger matrices. Recommend 30-60s delay for pass@3.
- Total wall clock for this matrix: ~6h (North Mini ~2h, Gemma 4 ~4h).

**Environment:**
- macOS, Apple Silicon. Ollama uses llama-server with GPU acceleration.
- Python 3.12.2 via `.venv`. Project managed with `pyproject.toml`.

## 8. Stakeholder Perspectives & Requirements

*Not applicable — single-user research session. No conflicting requirements.*

## 9. Performance, Metrics & Quality Attributes

**Headline Metric:** Trust gap = public_pass_rate − hidden_pass_rate.
- North Mini contract_visible: 8% on ci_forensics, 0% on maintenance_value.
- North Mini sparse: 33% on ci_forensics, 20% on maintenance_value.
- Contract_visible dramatically reduces North Mini's trust gap.
- Gemma 4 12b: trust gap stable at 17-33% regardless of prompt mode.

**Operational Reliability:**
- North Mini sparse product_workflows: 5/11 runtime failures (300s first_output
  timeout too tight).
- North Mini contract_visible product_workflows: 11/11 runtime failures
  (large contract prompt + 300s first_output).
- Learn: different packs need different first_output thresholds.

**Pass@1 Variance:** e4b went 5→2→2 hidden across three sparse runs.
Single-attempt results are noisy. Trust gap needs repeated measures (pass@3
minimum) for defensible claims.

## 10. Open Items & Next Steps

- [ ] **[High]** Wait for matrix cells 9-12 to complete (gemma4-12b: ci_forensics
  contract_visible in-flight, then maintenance_value sparse/contract_visible,
  product_workflows sparse/contract_visible).
- [ ] **[High]** Re-run North Mini product_workflows cells with
  `first_output_timeout=600` after updating config or using manual `--resume
  --skip-timeouts` commands. The 5 sparse + 11 contract_visible runtime
  failures need retry.
- [ ] **[High]** Run `uv run ci-vibe-matrix evaluate configs/matrix/north-mini-vs-gemma4-12b.json`
  after all cells complete to get evaluator reviews on false-greens.
- [ ] **[High]** Run `uv run ci-vibe-report leaderboard --config configs/matrix/north-mini-vs-gemma4-12b.json`
  to generate the comparison report.
- [ ] **[Medium]** Implement `ci-vibe-matrix retry` subcommand per the proposal
  in `docs/matrix-retry-runtime-failures-proposal-2026-06-21.md`. Unblocks
  clean retry workflows without manual SQL.
- [ ] **[Medium]** Package the full pipeline as a "study runner":
  `uv run ci-vibe-study run study.json` that orchestrates run → retry →
  evaluate → report in one shot with live progress streaming.
- [ ] **[Low]** Fix `PACK_SCENARIOS` hardcoding in `check-opencode.sh` (line 49)
  to support non-maintenance_value packs. Currently `ci_forensics` shows
  wrong scenario names in the live tracker.
- [ ] **[Low]** Add `data_semantics` pack (4 scenarios) to future matrices
  for broader coverage.
- [ ] **[Low]** Run pass@3 on key cells to quantify pass@1 variance.

## 11. Risks, Ambiguities & Points of Confusion

**Technical Risks:**
- North Mini free tier rate limiting: 132 runs × ~5-8 API calls each = 660-1056
  calls. The 15s delay helps but may not be enough. Already seeing
  product_workflows contract_visible stalls — could be rate limiting disguised
  as first_output timeout. Separating into two diagnosis buckets needs evidence.
- Gemma 4 12b contract_visible product_workflows will likely hit the same
  prefill stall as the smallest-two matrix. The 600s first_output and 1800s
  overall timeout should suffice based on ci_forensics contract_visible success,
  but product_workflows has larger codebases.
- `check-opencode.sh --live` section 4 (processes) must run before section 6
  because section 6 uses `$oc_run` defined in section 4. This coupling means
  the processes section always shows in live mode. Acceptable but noted.

**Ambiguities:**
- Is North Mini's product_workflows contract_visible failure truly a
  first_output_timeout (model thinking too long) or a rate-limit block from
  the free tier? The harness classifies it as no_output_timeout because
  OpenCode produced zero output within 300s. Can't distinguish without API
  response inspection.
- The 7 false-greens in North Mini product_workflows sparse need re-examination:
  5 of the 11 rows are runtime failures. The remaining 6 completions show 7
  public passes and 0 hidden passes. Some rows appear duplicated in the DB.

**Dead Ends:**
- Manual individual `ci-vibe-run run` commands for the full matrix were
  considered and rejected — too many paths to track, too error-prone.
  The matrix config approach is the correct abstraction.

**Mitigation Strategies:**
- Bump `first_output_timeout` to 600 for North Mini product_workflows before
  retry.
- Increase `delay_seconds` to 30-60s if rate limiting proves to be the issue.
- Use `--skip-timeouts` flag (only skips exit_code=124, not no_output_timeout)
  as a partial retry mechanism. Full fix awaits `ci-vibe-matrix retry`.

## 12. Testing & Quality Assurance

**Testing Approach:** Not applicable — this is an evaluation harness, not
application code. The harness itself has a test suite (`uv run python -m unittest
discover -s tests -v`). No new harness code was written in this session beyond
the `--live` flag (syntax-checked with `bash -n`, manually tested).

**Quality Gates:**
- Matrix config validated with `ci-vibe-matrix validate`
- Matrix planned with `ci-vibe-matrix plan` to verify cell count (12 cells, 132
  max attempts)
- `check-opencode.sh --live` syntax-verified and manually tested with active agent

## 13. Security & Compliance

*Not applicable — local-only research tooling. No production deployment, no
user data, no auth.*

## 14. References, Resources & Knowledge Gaps

| Type | Name / Path | How It Influenced | Affected Area |
|------|-------------|-------------------|---------------|
| Report | `reports/leaderboard-local-gemma4-smallest-two.md` | Showed prior contract_visible stalls, informed 12b timeout tuning | Matrix config |
| Report | `reports/gemma4-matrix-analysis-2026-06-20.md` | Established the 30% trust gap pattern across models | Result interpretation |
| Doc | `docs/ultimate-harness-audit-fresh-run-plan-2026-06-20.md` | Provided North Mini run recipes and model ID | Initial commands |
| Code | `ci_vibe_lab/matrix.py:502-543` | `classify_row()` and outcome classification — reused in retry proposal | Retry design |
| Code | `ci_vibe_lab/runner.py:447-477` | `_completed_attempts()` — defines `--resume` matching logic, scoped to experiment_id | Retry design |
| Config | `configs/matrix/local-gemma4-full.json` | Template for multi-model, multi-pack matrix config | Matrix config design |
| Script | `check-opencode.sh` | Full health check script, modified for `--live` | Live monitoring |

**Knowledge Gaps:**
- North Mini free tier rate limit specifics (requests/min, tokens/min). Could
  affect product_workflows retry strategy.
- Gemma 4 12b contract_visible prefill time on product_workflows pack
  (unknown codebase size). May need even higher timeouts.
- Exact duplicate-row behavior in North Mini product_workflows sparse DB
  (7 public passes from 6 completed scenarios). Needs investigation.

## 15. Session Metadata

**Depth Reached:** Implementation (running matrix, tooling improvements) +
  Design (retry proposal, study runner concept) + Conceptual (harness
  philosophy, trust gap as metric, matrix as experiment grid).

**Key Inflection Points:**
1. Discovery that `--resume` skips runtime failures too — sparked the retry
   proposal.
2. North Mini product_workflows contract_visible going 0/11 completed —
   exposed the first_output_timeout as a pack-dependent variable, not a
   constant.
3. Articulation of the harness as a "lie detector for coding agents" —
   reframed the entire evaluation philosophy.
4. Decision to add `--live` to check-opencode.sh on-the-fly during the run
   because the full output was too verbose for active monitoring.

**Confidence Level:** High on the matrix design, config, tooling, and harness
philosophy. Medium on the retry proposal — classified but not implemented.
Low on the "study runner" packaging concept — identified as a need but not
designed. Medium on North Mini product_workflows diagnosis — need more evidence
to distinguish rate limiting from genuine first_output_timeout.
