# Checkpoint watcher fix

## Incident

At `2026-08-25T11:31:04Z` `deploy_live_skin.py` raised:

```text
KeyError: 'events'
File: artifacts/completion-phase3/deploy_live_skin.py
```

The organism had already restarted (PID `34330`) and health was `ok`. The observer died; the organism did not.

## Cause

Receipt `05_deployment_checkpoint.json` stored event head as `latest_event` and `database_schema.events`. The observer required top-level `events`.

This is an **observer schema mismatch**, not a truncated file and not a missing writer field for its own shape.

## Rules implemented

- Versioned parser: `checkpoint_schema_version` 0 (legacy aliases) and 1 (current).
- Known aliases (`latest_event` → `events`) are mapped. Missing mandatory fields are **not** filled with zeros or empty hashes.
- Optional fields use safe lookup.
- Mandatory miss, malformed JSON, truncated JSON, and unknown versions raise `CheckpointError`.
- `safe_load_checkpoint` quarantines the file and returns a report so the monitor continues.
- Organism runtime was not changed for this bug.

## Tests

See `ofn/organism/tests/test_checkpoint_watcher.py`.

`CHECKPOINT_WATCHER_TESTS=PASS`
