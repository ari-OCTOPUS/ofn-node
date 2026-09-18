# Hook: hash self-cert before observation-trial pre-registration

GOV_VERSION=V8 · LADDER=L2 · VERIFIED_CASH=0  
Lane: L7 · flags: unchanged · live services: unchanged

## Required call (fail closed)

Before writing any `source_file_sha256` / `harness_file_sha256` into a
MEMABL-OBS or generic observation-trial preregistration record:

1. Run `python -m pytest tests/contract/test_memabl_obs_preflight_hash_selfcert.py -q --noconftest` (this instrument).
2. For each frozen file, call `assert_ready_to_preregister(path.read_bytes(), name=relative)` from `tests/contract/memabl_obs_hash_selfcert.py`.
3. Only if every file returns `ok: true`, write hashes with **`read_bytes()`** (never `read_text`).

If step 2 raises `HashAgreementError`, do **not** pre-register. That is the
class that invalidated N3-B: `frozen source module hash mismatch`.

## Historical miss

Command action `n3b-preregistration-preflight` (COMMAND-CHAIN sequence 108,
`F:\octo-exec\N3-REPRO-20260905\receipts\COMMAND-CHAIN.jsonl`) hashed with
`hashlib.sha256(p.read_bytes())` only, matched
`N3B-PREREGISTRATION.json` `source_file_sha256`, printed `preflight: OK`,
and therefore **did not** compare text-hash vs byte-hash.

The runner `F:\octo-exec\N3-REPRO-20260905\n3b_memabl_obs.py` lines 91–96 then
compared `sha256_text(Path.read_text(encoding="utf-8"))` to those byte hashes
and exited 1. The named preflight and the runner used **different hash methods**.

## Where to wire later (not done this pass)

`status: open, requires: owner_decision`

- `F:\octo-exec\N3-REPRO-20260905` historical tree: do not patch a frozen invalid run.
- Next new-seed pre-register (PROMPT 2, **not this pass**): invoke this hook inside
  any successor of `n3b-preregistration-preflight` **and** keep the runner on
  `read_bytes()` (as N3V2 `harness/n3b_memabl_obs.py` lines 91–96 already does).
- Do not enable `OCTOPUS_WIRE_*` / `OFN_WIRE_*`. Do not change live services.

## PROMPT 2 (package locked, trial not executed)

Prereg `09-LANES/L7/MEMABL-OBS-PREREG-314159.json` is locked. Scientific run **not** executed:
`body_not_on_this_lane` + `assert_ready_to_preregister` FAIL on CRLF sources + runner allowlist.
See `MEMABL-OBS-PROMPT2-STOP-RECEIPT.json`.
