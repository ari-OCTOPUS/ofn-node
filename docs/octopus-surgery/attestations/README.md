# Partner voice attestations

`partner_voices_independently_observed` stays **false** until three
receipts exist here, one each for `maliheh`, `abbas`, and `saba`, each
with a 64-character `media_sha256` of a raw voice file **and**
`independently_observed=true` after a verifier actually accessed that
file. Owner hashes and owner identity confirmation do not flip the flag.

Do not put the audio, Telegram screenshots, consent scans, or absolute
Windows home paths in git. Store media owner-private
(`$OFN_STATE_DIR/attestations/`, mode `0700`). Keep only receipt JSON
here (`receipts/`). Device paths belong in gitignored
`WINDOWS-PATHS.local.json`.

Owner attested 2026-09-02 that **Sume is Abbas** (legal name, AU-NSW).
The system id stays `abbas`. Official documents use `Sume`. A leftover
`partner_id=sume` file is extra, not a second person.

`path_assignment` is still inferred from the original folder walk.
After the alias merge, alphabetical order would change. Mark
`path_assignment_risk: reordering_after_alias_merge` until the owner
verifies each file individually.

Voices do **not** block painting, wave 1, or wave 2. They are required
for opening studio `partner_precondition` and for revenue split.

Run `python3 tools/partner_attestation.py` to measure, not to declare.
