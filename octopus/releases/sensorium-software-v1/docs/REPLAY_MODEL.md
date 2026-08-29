# REPLAY_MODEL

G13 PASS requires hash(full_replay) == hash(snapshot_plus_tail_replay).
diagnose_journal reports missing sequences, duplicates, and corrupt lines on a copy.
apply_event ignores duplicate content_hash. Original journals are never rewritten.
