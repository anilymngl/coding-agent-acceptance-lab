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

1. `ollama/gemma4:31b`
   - Installed Gemma 4 candidate on this machine.
   - Use this as the immediate local opponent because the lane is Gemma 4 only.
2. `ollama/gemma4:12b`
   - Optional smaller Gemma 4 pull if 31B has slow first-token latency.
3. `ollama/gemma4:e4b`
   - Optional light Gemma 4 pull if the goal is quick iteration.

Do not mix Gemma 3, Qwen, DeepSeek, or other local models into this lane. If
those rows exist from scratch testing, treat them as non-canonical and exclude
them from Gemma 4 reports.

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

This means `ollama/gemma4:31b` is viable for the local Gemma 4 lane, but it has
high first-token latency. Use `--first-output-timeout 300` for 31B unless a
later warm-cache run proves a shorter threshold is safe.

## Pull Models

Installed on this machine:

- `gemma4:31b`

Optional smaller Gemma 4 candidates to pull if 31B is too slow:

```bash
ollama pull gemma4:12b
ollama pull gemma4:e4b
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

## First Harness Smoke

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

## First Leaderboard Cell

Start with `maintenance_value`, sparse lane, one attempt per scenario:

```bash
uv run ci-vibe-run run \
  --challenge all \
  --pack maintenance_value \
  --model ollama/gemma4:31b \
  --agent build \
  --auto-approve \
  --timeout 900 \
  --first-output-timeout 300 \
  --runs 1 \
  --prompt-mode sparse \
  --db data/local-ollama-gemma4-31b-sparse.sqlite \
  --runs-dir runs/local-ollama/gemma4-31b/sparse \
  --delay-seconds 30
```

Then run the contract-visible lane:

```bash
uv run ci-vibe-run run \
  --challenge all \
  --pack maintenance_value \
  --model ollama/gemma4:31b \
  --agent build \
  --auto-approve \
  --timeout 900 \
  --first-output-timeout 300 \
  --runs 1 \
  --prompt-mode contract_visible \
  --db data/local-ollama-gemma4-31b-contract.sqlite \
  --runs-dir runs/local-ollama/gemma4-31b/contract-visible \
  --delay-seconds 30
```

If `gemma4:12b` or `gemma4:e4b` are pulled later, repeat the same pattern with
model-specific DB and runs-dir names.

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
