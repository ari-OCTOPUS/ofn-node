# CORRECTION — anatomy disputes (additive; does not overwrite prior claims)

node_id: 180
vantage: local-disk
scope: this_host_only
claim_type: observation
task_id: f05a3671-91f3-45fd-a7b8-1d4465fb7c44
supersedes_unexecuted: 4f61da18-6dea-43b3-ae27-61e134ea9960 (expired, untouched)
witness_verdict_ref: cee23c6f
generated_at: 2026-08-26T13:27:28Z
may_authorize: false
external_actions: 0

This file is additive errata. Prior claims in CURRENT-TRUTH.md and FIRST-VERDICT.md remain as historical records. They are not deleted.

## Correction 1 — identity / machine-id

| field | old claim (historical) | registration |
|---|---|---|
| machine_id_short=bb41a9407b4f | published as identity field | **incorrect_unsupported** |
| verified_by=`ip -o -4 addr show eth0` | used as identity envelope method | **invalid_method_for_machine_id** |

Why the method is invalid:
- `ip addr` reports interface addresses. It does not produce `/etc/machine-id`.
- Mixing eth0 IPv4 verification with machine-id identity in one envelope is unsupported.

Fresh measurement (this_host_only):
- method: `cat /etc/machine-id` (also compared to `/var/lib/dbus/machine-id`; equal)
- machine_id_value: **redacted in public artifacts** (32 hex chars)
- machine_id_sha256: `bb41a9407b4fc1a86a53b43b9a0ec215d9b503c8728a4354db692bcbf33d924a`
- derived_short_hash_12: `bb41a9407b4f` (sha256 of the real machine-id; this hash coincidentally equals the old published short string)
- No intentional deception is inferred. The error is method/labeling: an IP command was cited as machine-id verification.

## Correction 2 — tests

| field | old claim (historical) | registration |
|---|---|---|
| 145 passed / 1 skipped | published as anatomy test result | **not_reproduced** (not an independently confirmed system-wide fact) |
| school import/loader failure (witness) | reported by 182 | **collection_or_loader_error**, not a functional test failure |

Fresh measurement (this_host_only; does not rehabilitate the old claim as system-wide):

```
command: env -i PATH=/usr/bin:/bin HOME=/root PYTHONPATH=/opt/octopus/lab python3 -m unittest discover -s ofn/organism/tests -p test_*.py -v
cwd: /opt/octopus/lab
commit: 36e579ef10206cd578b6b5060e7c860b18a48126
branch: ofn/evolve-20260826-anatomy-180
timestamp: 2026-08-26T13:27:28Z
discovered: 145
passed: 144 ok-lines + 1 skipped => Ran 145, OK (skipped=1)
failed: 0
errors: 0
skipped: 1 (test_sha256_cbor_has_stable_bytes_for_reordered_keys: cbor2 not installed)
exit: 0
transcript_sha256: 95dcbb812a23dbc4c9bd62f60a396d50ba9e6ff2cf1e361643c7c0fa9d60425c
```

On this host, `import ofn.organism.school` succeeded. The witness school error is classified as collection_or_loader_error, not as a failing test case. pytest is absent (`No module named pytest`), which is itself a collection/loader environment difference.

No intentional deception is claimed by any party.
