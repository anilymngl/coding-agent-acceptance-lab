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
- `ollama/qwen3-coder:30b`

Recommended first opponents:

1. `ollama/gemma4:e4b`
   - Lightest Gemma 4 candidate in this config.
   - Good first smoke and baseline.
2. `ollama/qwen3-coder:30b`
   - Better coding-agent-shaped opponent if the machine has enough memory.
   - Use it to distinguish "Gemma general reasoner" from "local coding model".

If memory is tight, use `ollama/gemma4:e4b` first. If the goal is a stronger
Gemma-only ladder, try `ollama/gemma4:12b` after the E4B smoke passes.

## Local State Observed On 2026-06-20

Current machine checks:

- `ollama` binary exists at `/opt/homebrew/bin/ollama`.
- `curl -s http://0.0.0.0:11434/api/tags` failed, so the Ollama server was not reachable.
- `ollama --version` crashed in MLX initialization before printing a version.

This means no local model run should be interpreted until Ollama itself is
healthy. Fixing the Ollama runtime comes before any benchmark claim.

## Pull Models

Use one small local opponent first:

```bash
ollama pull gemma4:e4b
```

Optional heavier candidates:

```bash
ollama pull gemma4:12b
ollama pull qwen3-coder:30b
```

Avoid pulling `gemma4:26b`, `gemma4:31b`, or `qwen3-coder:30b` unless the
machine has enough unified memory and you are willing to wait.

## Health Checks

Ollama service:

```bash
curl -s http://0.0.0.0:11434/api/tags
```

Direct Ollama chat:

```bash
curl -s http://localhost:11434/api/chat \
  -d '{"model":"gemma4:e4b","messages":[{"role":"user","content":"Reply with READY only."}],"stream":false}'
```

OpenCode model listing:

```bash
opencode models | rg '^ollama/'
```

Expected model ID for the harness:

```text
ollama/gemma4:e4b
```

## First Harness Smoke

Run one small scenario before a full pack:

```bash
uv run ci-vibe-run run \
  --challenge docs_cli_sync \
  --model ollama/gemma4:e4b \
  --agent build \
  --auto-approve \
  --timeout 900 \
  --first-output-timeout 120 \
  --prompt-mode sparse \
  --db data/local-ollama-smoke.sqlite \
  --runs-dir runs/local-ollama/smoke
```

Inspect the full agent envelope:

```bash
uv run ci-vibe-run inspect \
  --db data/local-ollama-smoke.sqlite \
  --latest \
  --model ollama/gemma4:e4b \
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
  --model ollama/gemma4:e4b \
  --agent build \
  --auto-approve \
  --timeout 900 \
  --first-output-timeout 120 \
  --runs 1 \
  --prompt-mode sparse \
  --db data/local-ollama-gemma4-e4b-sparse.sqlite \
  --runs-dir runs/local-ollama/gemma4-e4b/sparse \
  --delay-seconds 30
```

Then run the contract-visible lane:

```bash
uv run ci-vibe-run run \
  --challenge all \
  --pack maintenance_value \
  --model ollama/gemma4:e4b \
  --agent build \
  --auto-approve \
  --timeout 900 \
  --first-output-timeout 120 \
  --runs 1 \
  --prompt-mode contract_visible \
  --db data/local-ollama-gemma4-e4b-contract.sqlite \
  --runs-dir runs/local-ollama/gemma4-e4b/contract-visible \
  --delay-seconds 30
```

Repeat the same pattern for `ollama/qwen3-coder:30b` only after the Gemma smoke
is healthy.

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
- Ollama Qwen3-Coder library: `https://ollama.com/library/qwen3-coder`
