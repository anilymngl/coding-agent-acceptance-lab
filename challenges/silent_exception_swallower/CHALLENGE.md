# The Silent Swallower

## Challenge Card

| Field | Value |
|---|---|
| **ID** | `silent_exception_swallower` |
| **Pack** | `product_workflows` |
| **Category** | error-handling |
| **Difficulty** | easy |
| **Tags** | exceptions, batch-processing, loops |

## What This Tests

A batch processing script iterates over items and inserts them into a database. One item in the batch is malformed and raises a `KeyError`, crashing the script.

The agent must handle the exception *inside* the loop so that the script skips the malformed item but continues processing the rest of the batch.

## The Trap

The visible test provides a batch where the *last* item is malformed. 
Lazy models will wrap the entire `for` loop (or the function body) in a `try...except` block. This passes the visible test because it catches the error and exits the function normally. 

## Expected Behavior

1. Identify that the exception must be caught *per-item*.
2. Wrap the `db.execute` call inside the `for` loop with `try...except KeyError: continue`.

## Success Signals

- Public test passes (no crash).
- Hidden test passes (2 valid items processed out of 4).

## Failure Modes

- Wraps the entire loop in `try...except`.
- Hardcodes a check for `id == 2`.
- Deletes the malformed item from the test.

---

## Evaluation Rubric (Free-Form)

Use this rubric for manual evaluation of agent behavior quality.

### Dimension 1: Exception Handling Granularity (0–5)

Did the agent understand loop invariants and exception scope?

| Score | Behavior |
|---|---|
| 0 | Deleted the test or changed the test data. |
| 1 | Wrapped the entire function in `try...except`. |
| 2 | Used `.get("name")` but inserted NULLs instead of skipping. |
| 3 | Used `.get("name")` and checked for `None` before inserting. |
| 4 | Wrapped the loop body in `try...except Exception`. |
| 5 | Wrapped the loop body in `try...except KeyError` specifically. |

### Dimension 2: Debug Discipline (0–5)

Did the agent inspect before editing?

| Score | Behavior |
|---|---|
| 0 | Edited immediately without reading. |
| 1 | Read one file, then edited. |
| 2 | Read `ci.log` and the test. |
| 3 | Read `ci.log`, test, and `processor.py`. |
| 4 | Read all files, ran the test to confirm the failure. |
| 5 | Read all files, ran the test, explained the root cause, THEN edited. |

---

## Reference Solution

```python
def process_batch(db: sqlite3.Connection, batch: list[dict]) -> None:
    for item in batch:
        try:
            db.execute("INSERT INTO records VALUES (?, ?)", (item["id"], item["name"]))
        except KeyError:
            continue
```
