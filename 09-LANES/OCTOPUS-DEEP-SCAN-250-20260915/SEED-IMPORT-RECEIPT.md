# SEED IMPORT RECEIPT — FORGOTTEN-250 into the live deep-scan ledger

- seed file: `138:~/ofn/state/deep-scan/seed/FORGOTTEN-250.json`
- sha256 (both sides byte-identical): `74278f6baaca12a26dc1868f87b5229a1b3e92faff2a98ba00bac5d90c85daf4`
- command: `python3 state/deep-scan/deep_scan_tick.py --import-seed state/deep-scan/seed/FORGOTTEN-250.json`
- result: `{"seed_imported": 150}` — the 100 carried ids already existed (morning seed) and were skipped, not duplicated
- post-state: `findings-current.json` = 160 findings; `findings-events.jsonl` = 249,722 bytes
- standing guard: `octopus-deep-scan.timer` (Mon 04:00Z) now tracks this registry
