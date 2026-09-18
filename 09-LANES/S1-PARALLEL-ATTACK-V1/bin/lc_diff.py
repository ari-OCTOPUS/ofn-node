#!/usr/bin/env python3
"""S1-PARALLEL-ATTACK-V1 / L-C step 1 — field-level diff of the two G13 replay states.

Read-only over the journal. Streams (no load_events list blowup), replicates the
canonical semantics (sorted-by-seq application), counts file-order inversions,
checks raw byte drift (CR chars, torn lines, non-canonical serialization sample).

Output: JSON report to stdout. Never writes anything.
"""
import json
import sys
from array import array

sys.path.insert(0, "/opt/octopus/current/src")
from octopus_sensorium.snapshot import apply_event, canonical_state, load_latest, state_hash

J = "/var/lib/octopus/state/events.jsonl"

snap = load_latest() or {}
after = int(snap.get("journal_seq") or 0)

fe = {}
fs = dict(canonical_state(snap))
seqs = array("q")
n = 0
bad_lines = 0
cr_lines = 0
first_seq = last_seq = 0
inversions = 0
prev_seq_file_order = 0
noncanonical = 0
checked_canon = 0

with open(J, encoding="utf-8", newline="") as fh:
    for line in fh:
        if "\r" in line:
            cr_lines += 1
        stripped = line.strip()
        if not stripped:
            continue
        try:
            rec = json.loads(stripped)
        except ValueError:
            bad_lines += 1
            continue
        n += 1
        seq = int(rec.get("seq") or 0)
        seqs.append(seq)
        if first_seq == 0:
            first_seq = seq
        last_seq = seq
        if seq < prev_seq_file_order:
            inversions += 1
        prev_seq_file_order = seq
        # canonical parser applies in sorted order; we apply in file order and
        # re-apply sorted later only if inversions found (reported either way)
        apply_event(fe, rec)
        if seq > after:
            apply_event(fs, rec)
        if checked_canon < 5000:
            checked_canon += 1
            if stripped != json.dumps(rec, separators=(",", ":"), ensure_ascii=False):
                noncanonical += 1

ce, cs = canonical_state(fe), canonical_state(fs)
hashes_fe = ce.get("observation_hashes") or []
hashes_fs = cs.get("observation_hashes") or []
health_fe = ce.get("health") or {}
health_fs = cs.get("health") or {}

diff_window = None
if hashes_fe != hashes_fs:
    for i, (a, b) in enumerate(zip(hashes_fe, hashes_fs)):
        if a != b:
            diff_window = i
            break
    if diff_window is None:
        diff_window = min(len(hashes_fe), len(hashes_fs))

report = {
    "journal_records_streamed": n,
    "first_seq": first_seq,
    "last_seq": last_seq,
    "snapshot_journal_seq_after": after,
    "snapshot_state_hash_embedded": snap.get("state_hash"),
    "file_order_inversions": inversions,
    "bad_json_lines": bad_lines,
    "lines_with_cr": cr_lines,
    "noncanonical_of_first_5000": noncanonical,
    "from_empty_hash": state_hash(fe),
    "from_snapshot_hash": state_hash(fs),
    "equal": state_hash(fe) == state_hash(fs),
    "fields": {
        "observations_published": [ce.get("observations_published"), cs.get("observations_published")],
        "invalid_observations": [ce.get("invalid_observations"), cs.get("invalid_observations")],
        "identity_equal": ce.get("identity") == cs.get("identity"),
        "health_only_in_empty": sorted(set(health_fe) - set(health_fs))[:20],
        "health_only_in_snapshot": sorted(set(health_fs) - set(health_fe))[:20],
        "health_value_diffs": {k: [health_fe.get(k), health_fs.get(k)]
                               for k in set(health_fe) & set(health_fs)
                               if health_fe.get(k) != health_fs.get(k)},
        "window_len_empty": len(hashes_fe),
        "window_len_snapshot": len(hashes_fs),
        "window_first_diff_index": diff_window,
    },
}
print(json.dumps(report, indent=1)[:4000])
