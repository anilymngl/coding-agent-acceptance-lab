# Local Ollama Opponent Lane

This lane exists for periods when hosted model limits are exhausted. It lets the
harness keep moving with local models while keeping the evidence caveats clear.

## Why This Lane

The local lane should answer a narrower question than the hosted-model report:

> Can a local model drive the OpenCode coding-agent loop well enough to become a
> useful opponent in the trust-gap leaderboard?

It should not be mixed into hosted-model rankings until coverage and runtime
conditions are comparable.

## Configured OpenCode Models

The repository includes `opencode.json` with an Ollama provider:

- `ollama/gemma4:e4b`
- `ollama/gemma4:12b`
- `ollama/gemma4:26b`
- `ollama/gemma4:31b`

Recommended first opponents:

1. `ollama/gemma4:e4b`
   - Installed and validated as the fast local iteration model.
   - Completed the sparse maintenance matrix at 5/10 hidden.
2. `ollama/gemma4:31b`
   - Installed and validated as the stronger local opponent.
   - Completed the sparse maintenance matrix at 7/10 hidden.
3. `ollama/gemma4:12b`
   - Installed after upgrading Ollama to `0.30.10`.
   - First sparse `docs_cli_sync` smoke produced no patch, but a direct rerun
     passed public and hidden acceptance.
   - Sparse smallest-two matrix completed with one `agent_timeout`, so report
     12B as mixed local-runtime evidence.

Do not mix Gemma 3, Qwen, DeepSeek, or other local models into the Gemma-only
lane. If 12B is not viable, use a separate fallback lane. The configured Qwen
fallback is `ollama/qwen3.6:27b`, because Ollama currently lists `qwen3.6:27b`
as the smallest Qwen3.6 tag. This is a role-equivalent coding-agent opponent,
not a size-equivalent replacement for Gemma 4 12B.

## Local State Observed On 2026-06-20

Current machine checks:

- `ollama` binary exists at `/opt/homebrew/bin/ollama`.
- `curl -s http://0.0.0.0:11434/api/tags` later showed the local server and installed models.
- `ollama --version` crashed in MLX initialization before printing a version in one Codex shell.
- A first harness smoke against `ollama/gemma4:31b` failed because OpenCode did not see the repo-root `opencode.json` from generated worktrees.
- The harness was then fixed to pass repo-root config through `OPENCODE_CONFIG`.
- A retry against `ollama/gemma4:31b` reached the local path but produced no OpenCode stdout/stderr within 120 seconds.
- A 300-second first-output smoke against `ollama/gemma4:31b` succeeded:
  - DB: `data/local-ollama-gemma4-31b-smoke.sqlite`
  - run id: `20260620T113108Z-docs_cli_sync-b3b1c215`
  - duration: 224.8 seconds
  - OpenCode exit: `0`
  - public pass: `1`
  - hidden pass: `1`
  - patch: one-file README flag update
- The matrix runner was then updated to prewarm Ollama before each model cell,
  so model-load time is logged in `matrix-run.log` and not counted in SQLite
  row `duration_seconds`.
- The completed two-model sparse maintenance matrix used
  `configs/matrix/local-gemma4-two-model.json`:
  - `ollama/gemma4:e4b`: 8/10 public, 5/10 hidden, 3 false-greens, ~62s avg
  - `ollama/gemma4:31b`: 10/10 public, 7/10 hidden, 3 false-greens, ~300s avg
  - integrity: 120/120 artifacts present, all 6 false-greens evaluator-reviewed

This means `ollama/gemma4:31b` is viable for the local Gemma 4 lane, but it has
high first-token latency. Use `--first-output-timeout 300` for 31B unless a
later warm-cache run proves a shorter threshold is safe.

## Pull Models

Installed on this machine:

- `gemma4:31b`
- `gemma4:e4b`
- `gemma4:12b`

Observed on 2026-06-20:

- `gemma4:12b` initially failed to pull under Ollama `0.21.0`.
- Ollama was upgraded to `0.30.10`.
- `ollama pull gemma4:12b` then succeeded.
- `opencode models` lists `ollama/gemma4:12b`.
- The first configured 12B smoke completed but produced no patch, so public and
  hidden both failed. This is a no-edit smoke failure, not a false-green.
- A direct 12B rerun passed public and hidden:
  - DB: `data/local-ollama-gemma4-12b-smoke-rerun.sqlite`
  - run id: `20260620T160915Z-docs_cli_sync-51838e9d`
  - duration: 113.7s
  - public pass: `1`
  - hidden pass: `1`
- The sparse smallest-two matrix then completed e4b and produced a mixed 12B
  row set because `explicit_validation_matrix` hit the 900s agent timeout.

Optional smaller Gemma 4 candidates to pull if 31B is too slow:

```bash
ollama pull gemma4:12b
```

Optional Qwen fallback if 12B is not viable:

```bash
ollama pull qwen3.6:27b
uv run ci-vibe-matrix validate configs/matrix/local-gemma4-e4b-qwen36-fallback.json
uv run ci-vibe-matrix plan configs/matrix/local-gemma4-e4b-qwen36-fallback.json
```

Avoid pulling `gemma4:26b` unless the machine has enough unified memory and you
are willing to wait.

## Health Checks

Ollama service:

```bash
curl -s http://0.0.0.0:11434/api/tags
```

Direct Ollama chat:

```bash
curl -s http://localhost:11434/api/chat \
  -d '{"model":"gemma4:31b","messages":[{"role":"user","content":"Reply with READY only."}],"stream":false}'
```

OpenCode model listing:

```bash
opencode models | rg '^ollama/'
```

Expected model ID for the harness:

```text
ollama/gemma4:31b
```

## First Matrix Smoke

Use the small Gemma 4 smoke before the 31B lane:

```bash
uv run ci-vibe-matrix run configs/matrix/local-gemma4-e4b-smoke.json --stop-on-failure
```

This cell runs only `docs_cli_sync` in the sparse lane. The matrix runner
prewarms Ollama before invoking `ci-vibe-run`, so model-load time is logged in
`matrix-run.log` rather than counted in the run row's `duration_seconds` or
first-output timeout.

Observed on 2026-06-20:

- model: `ollama/gemma4:e4b`
- config: `configs/matrix/local-gemma4-e4b-smoke.json`
- run id: `20260620T121600Z-docs_cli_sync-6bb20fc9`
- warmup: 2.73s in `matrix-run.log`
- run duration: 62.8s in SQLite
- OpenCode exit: `0`
- public pass: `1`
- hidden pass: `1`

Use the 12B smoke before the local smallest-two matrix:

```bash
uv run ci-vibe-matrix run configs/matrix/local-gemma4-12b-smoke.json --stop-on-failure
```

Observed on 2026-06-20:

- model: `ollama/gemma4:12b`
- config: `configs/matrix/local-gemma4-12b-smoke.json`
- run id: `20260620T160329Z-docs_cli_sync-2d774a99`
- warmup: 4.3s before timed `ci-vibe-run`
- run duration: 55.1s in SQLite
- OpenCode exit: `0`
- public pass: `0`
- hidden pass: `0`
- patch: empty
- classification: no-edit smoke failure; do not count as semantic success or
  false-green

A direct rerun against a separate diagnostic DB passed:

- DB: `data/local-ollama-gemma4-12b-smoke-rerun.sqlite`
- run id: `20260620T160915Z-docs_cli_sync-51838e9d`
- duration: 113.7s
- OpenCode exit: `0`
- public pass: `1`
- hidden pass: `1`
- patch: one-file README flag update

The full local-small comparison config is:

```bash
uv run ci-vibe-matrix validate configs/matrix/local-gemma4-smallest-two.json
uv run ci-vibe-matrix plan configs/matrix/local-gemma4-smallest-two.json
```

Run it after both e4b and 12B invocation smokes are classified:

```bash
uv run ci-vibe-matrix run configs/matrix/local-gemma4-smallest-two.json --resume
```

Observed sparse lane on 2026-06-20:

- config: `configs/matrix/local-gemma4-smallest-two.json`
- e4b sparse: complete, 10/10 rows, 3/10 public, 2/10 hidden,
  1 false-green
- 12B sparse: mixed, 10 rows stored, 9 completed attempts,
  1 `agent_timeout`, 5/9 public, 3/9 hidden, 2 false-greens
- runtime failure: `explicit_validation_matrix`,
  `20260620T162844Z-explicit_validation_matrix-8a003bc4`, 900.3s
- integrity: `reports/integrity-local-gemma4-smallest-two.md`, PASS,
  120/120 artifacts present

If the goal is to replace 12B rather than report it as mixed local-runtime
evidence, use the separate fallback config:

```bash
uv run ci-vibe-matrix run configs/matrix/local-gemma4-e4b-qwen36-fallback.json --resume
```

## Completed Sparse Maintenance Matrix

The first full local Gemma 4 comparison is complete. Do not rerun it unless
refreshing evidence intentionally.

```bash
uv run ci-vibe-matrix status configs/matrix/local-gemma4-two-model.json
uv run ci-vibe-report leaderboard \
  --matrix configs/matrix/local-gemma4-two-model.json \
  --out reports/leaderboard-local-gemma4-two-model.md \
  --include-artifact-index
uv run ci-vibe-report integrity \
  --matrix configs/matrix/local-gemma4-two-model.json \
  --out reports/integrity-local-gemma4-two-model.md
```

Observed on 2026-06-20:

- `gemma4:e4b`: public 8/10, hidden 5/10, 3 false-greens
- `gemma4:31b`: public 10/10, hidden 7/10, 3 false-greens
- North Mini reference on the same scenarios: public 10/10, hidden 7/10,
  3 false-greens
- shared trust gap: 30%
- reports:
  - `reports/gemma4-matrix-analysis-2026-06-20.md`
  - `reports/leaderboard-local-gemma4-two-model.md`
  - `reports/integrity-local-gemma4-two-model.md`

## First Direct Harness Smoke

Run one small scenario before a full pack:

```bash
uv run ci-vibe-run run \
  --challenge docs_cli_sync \
  --model ollama/gemma4:31b \
  --agent build \
  --auto-approve \
  --timeout 900 \
  --first-output-timeout 300 \
  --prompt-mode sparse \
  --db data/local-ollama-gemma4-31b-smoke.sqlite \
  --runs-dir runs/local-ollama/gemma4-31b/smoke
```

Inspect the full agent envelope:

```bash
uv run ci-vibe-run inspect \
  --db data/local-ollama-gemma4-31b-smoke.sqlite \
  --latest \
  --model ollama/gemma4:31b \
  --full
```

Do not proceed if the smoke row has:

- `opencode_exit_code=124`
- empty `opencode_stdout`
- provider connection errors
- no patch when the public test is still red

## Next Leaderboard Cells

Use the matrix runner for new evidence cells. The highest-value next local lane
is `contract_visible` on `maintenance_value`, because the sparse run showed a
stable 30% trust gap across Gemma 4 e4b, Gemma 4 31B, and North Mini.

After contract-visible maintenance, expand to broader packs:

- `ci_forensics`
- `product_workflows`
- repeated attempts / pass@3 consistency

## Leaderboard Rules

Local rows must be shown with evidence status:

- `valid`: OpenCode emitted a normal stream and produced a completed attempt.
- `agent_timeout`: OpenCode emitted output but hit the timeout.
- `no_output_timeout`: OpenCode produced no stdout/stderr before
  `--first-output-timeout`.
- `runtime_invalid`: Ollama or OpenCode failed before a model attempt was valid.

Do not count `runtime_invalid` or `no_output_timeout` rows as false-greens.
They are operational reliability evidence, not semantic acceptance evidence.

## Sources Checked

- OpenCode Ollama provider docs: `https://opencode.ai/docs/providers/`
- Ollama Gemma 4 library: `https://ollama.com/library/gemma4`
