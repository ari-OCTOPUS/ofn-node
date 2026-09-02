# Partner voice attestations

`partner_voices_independently_observed` stays **false** until three
receipts exist here, one each for `maliheh`, `abbas`, and `saba`, each
with a 64-character `media_sha256` of a raw voice file **and**
`independently_observed=true` after a verifier actually accessed that
file. Owner hashes alone do not flip the flag.

Do not put the audio, Telegram screenshots, or consent scans in git.
Store them owner-private (`$OFN_STATE_DIR/attestations/`, mode `0700`)
and keep only the receipt JSON here (`receipts/`).

`sume` is a known extra subject. Do **not** map it to `abbas` unless
the owner explicitly confirms that SUME is Abbas. A `sume` receipt
must not count as the Abbas slot.

Voices do **not** block painting, wave 1, or wave 2. They are required
for opening studio `partner_precondition` and for revenue split.

Run `python3 tools/partner_attestation.py` to measure, not to declare.
