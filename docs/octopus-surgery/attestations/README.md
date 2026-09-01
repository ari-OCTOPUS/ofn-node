# Partner voice attestations

`partner_voices_independently_observed` stays **false** until three
receipts exist here, one each for `maliheh`, `abbas`, and `saba`, each
with a 64-character `media_sha256` of a raw voice file that this
vantage did not rewrite.

Do not put the audio in git. Store it owner-private
(`state/attestations/`, mode `0700`) and keep only the receipt JSON here.

Voices do **not** block painting, wave 1, or wave 2. They are required
for opening studio `partner_precondition` and for revenue split.

Run `python3 tools/partner_attestation.py` to measure, not to declare.
