# 17 — latent_space verification (blindspot #53)

Read `_ops/neural/latent_space.py` in full this session (194 lines) — not trusted from the
commit message alone.

## The fix, verified from source

`_load()` (lines 154-193), the `except` clause that used to be `except: pass` (silent wipe
on any corrupt/unreadable file — the P0):

```python
except (json.JSONDecodeError, OSError, ValueError) as _exc:
    # FIX (blindspot #53, 2026-08-04): silent wipe → fail-safe.
    ...
    _quarantine = _corrupt.with_suffix(f".corrupt.{int(_t.time())}.json")
    try:
        _os.replace(str(_corrupt), str(_quarantine))
    except OSError:
        pass
    # existing _vectors/_metadata دست‌نخورده باقی می‌مانند (no wipe)
    self._corrupt_load_error = {...}
```

Checklist from the master instruction:

| Question | Answer |
|---|---|
| `except: pass` removed / fail-closed? | **Yes** — now a narrow exception tuple, not a bare `except`, and it no longer silently discards data |
| no-write-on-error? | **Yes** — the corrupt file is renamed (quarantined), never overwritten by the load path |
| old data preserved? | **Yes** — `self._vectors`/`self._metadata` are only ever mutated by successful record parses inside the `try`; on exception, whatever was already loaded before the exception (or the empty dict on a from-scratch instance) is left as-is — no wipe |
| error ledger / record kept? | **Yes** — `self._corrupt_load_error` records `{ts, error, quarantine_path}` |
| synthetic-exception test passes? | **Yes** — `test_latent_space_fail_closed.py`, 6/6 (see `18-LATENT-SPACE-TESTS.md`) |
| silent wipe still possible? | **No** — confirmed by both source read and test |

## One residual, minor, NOT-P0 observation

`store()` (the *write/persist* path, not the load path this fix targets) still has:
```python
except OSError:
    pass  # fail-soft: persist نباید crash کند
```
This is a different code path (saving new state, not loading existing state) and is
explicitly documented as an intentional fail-soft choice so a transient disk error during
save can't crash the caller. It cannot cause the "silent wipe of existing data" the P0 was
about (there is no wipe here — worst case, a save silently fails and next boot's `_load()`
sees slightly stale data, not corrupted/deleted data). Flagging it for completeness, not
raising it as a new P0.

## Status

**FIXED — verified from source and from a synthetic-corruption test, not just from the
commit message.**
