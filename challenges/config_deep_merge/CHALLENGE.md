# Config Deep Merge

## Challenge Card

| Field | Value |
|---|---|
| **ID** | `config_deep_merge` |
| **Pack** | `ci_forensics` |
| **Category** | data-structure-contract |
| **Difficulty** | medium |
| **Tags** | recursive, immutability, state, config |

## What This Tests

A basic configuration merging function uses `dict.update()`. This performs a shallow merge, replacing nested dictionaries entirely rather than merging their keys. The agent must implement a recursive deep merge that also preserves the immutability of the base dictionary.

## The Trap

`dict.update()` replaces nested dicts wholesale. Most agents will:
1. Use `{**base, **override}` — exact same bug, just different syntax.
2. Special-case the `"database"` key from the test — hardcoded and fragile.
3. Use `copy.deepcopy` + `update` — still a shallow merge.
4. Mutate the original base dict during the merge process — side-effect bug.

## Expected Behavior

1. Read the code and recognize that `update()` is shallow.
2. Implement a recursive merge function.
3. Ensure the base dictionary is not mutated in place during the recursive steps.
4. Support arbitrary nesting depth, not just 2 levels.

## Success Signals

- Public 2-level merge test passes.
- Hidden test verifies 3-level deep merge.
- Hidden test verifies new nested keys can be added.
- Hidden test verifies base dictionary is not mutated.
- No test weakening.

## Failure Modes

- Hardcodes `if key == "database"`.
- Modifies `base` in place, causing side effects.
- Assumes maximum depth of 2.

---

## Evaluation Rubric (Free-Form)

Use this rubric for manual evaluation of agent behavior quality.

### Dimension 1: Recursive Reasoning (0–5)

Did the agent recognize the need for recursion?

| Score | Behavior |
|---|---|
| 0 | Didn't realize `update()` was shallow. |
| 1 | Changed syntax to `{**base, **override}`. |
| 2 | Hardcoded `"database"` key merge. |
| 3 | Added a loop for 2-level depth only. |
| 4 | Implemented proper recursion. |
| 5 | Implemented proper recursion and explicitly explained why depth is arbitrary. |

### Dimension 2: Immutability Preservation (0–5)

Did the agent respect the implied immutability contract of the function signature?

| Score | Behavior |
|---|---|
| 0 | Mutated `base` aggressively. |
| 1 | Mutated `override` aggressively. |
| 2 | Returned mutated `base` but added a superficial `copy()` call somewhere that didn't help. |
| 3 | Created a new dict for the top level, but mutated nested dicts of `base`. |
| 4 | Correctly preserved immutability throughout all recursive calls. |
| 5 | Explicitly mentioned immutability / pure functions in their summary. |

### Dimension 3: Debug Discipline (0–5)

Did the agent inspect before editing?

| Score | Behavior |
|---|---|
| 0 | Edited immediately without reading. |
| 1 | Read one file, then edited. |
| 2 | Read `ci.log` and the test. |
| 3 | Read `ci.log`, test, and `config.py`. |
| 4 | Read all files, ran the test to confirm the failure. |
| 5 | Read all files, ran the test, explained the root cause, THEN edited. |

---

## Reference Solution

```python
def merge_config(base: dict, override: dict) -> dict:
    """Recursively merge override config into base config."""
    result = {}
    for key in set(base) | set(override):
        if key in base and key in override:
            if isinstance(base[key], dict) and isinstance(override[key], dict):
                result[key] = merge_config(base[key], override[key])
            else:
                result[key] = override[key]
        elif key in base:
            result[key] = base[key]
        else:
            result[key] = override[key]
    return result
```

---

## Automated Pipeline

This challenge is also registered in `ci_vibe_lab/scenarios.py` under the
`ci_forensics` pack. Run it through the harness:

```bash
uv run python -m ci_vibe_lab.runner run \
  --challenge config_deep_merge \
  --model "provider/model" \
  --auto-approve
```
