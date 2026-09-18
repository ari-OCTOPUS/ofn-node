# L7 MEMABL-OBS hash self-certification — pass criterion

Lane: L7 (contract and snapshot tests)  
GOV_VERSION=V8 · LADDER=L2 · VERIFIED_CASH=0  
Written: 2026-09-08 **before** running the new pytest.  
Forbidden: `src/` import or edit; live flags; network; MEMABL-OBS scientific rerun; new-seed pre-registration.

## Instrument, not capability

This instrument asks one question: would a frozen artifact get two different SHA-256 values if hashed as **raw bytes** versus as **text-mode decoded UTF-8** (the `pathlib.Path.read_text(encoding="utf-8")` then `encode("utf-8")` path used by historical `n3b_memabl_obs.py`)? If yes, pre-registration must **fail closed**.

Baselines (mandatory, frozen here):

- persistence: the 2026-09-05 N3-B invalidation receipt exists and is not rewritten.
- prior-only: the later N3V2 `H1_STRONG_FAIL` runs are a **different** execution after byte-hash plumbing; they are not this instrument’s pass.
- random: not used.

## PASS (all required)

1. `tests/contract/test_memabl_obs_preflight_hash_selfcert.py` is pytest-collectable and does not import `src`.
2. LF-only UTF-8 synthetic bytes: byte-hash equals text-mode hash; `assert_ready_to_preregister` returns ok.
3. Same payload with CRLF (`\r\n`): byte-hash **≠** text-mode hash; `assert_ready_to_preregister` **raises** (fail closed). This is the MEMABL-OBS invalidation class.
4. UTF-8 BOM (`EF BB BF`) on otherwise LF UTF-8: `utf-8-sig` round-trip hash ≠ byte-hash; fail closed.
5. NFC vs NFD of the same user-perceived string: NFC-normalized text hash ≠ raw NFD byte-hash; fail closed.
6. Hashing a Python `str` (`sha256(s.encode("utf-8"))`) versus hashing the file’s raw bytes is exercised; disagreement fails closed.
7. No call to `n3b_memabl_obs.py` as a trial runner; no live/real observation data; no new seed.

## FAIL

Any of (2)–(6) green when it should be red, or red when it should be green, or a test that executes the scientific MEMABL trial.

## Hook contract (documentation + assertion only)

Pre-registration of MEMABL-OBS or a generic observation-trial **must** invoke `assert_ready_to_preregister` on every frozen file **before** writing `source_file_sha256`. Historical command `n3b-preregistration-preflight` (COMMAND-CHAIN sequence 108) compared only `read_bytes()` to prereg byte hashes and therefore could not catch this class. Wiring that call into `F:\octo-exec\...` is an owner decision; this lane only ships the test and the hook document.
