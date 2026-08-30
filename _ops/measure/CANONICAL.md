# CANONICAL measurement instrument

**File:** `_ops/measure/swap_consistency.py`  
**Confirmed:** 2026-08-20T00:28+10:00 · GATE-0 MEGA-DISCOVERY-v1  
**sha256:** `8c2f76dccd6ca38715c4f4e1667dbd8042c03a04f15186a37579a8b590851944`

Do not import island/panel copies. Retired ledger: `_ops/state/measure/retired-instruments.jsonl`.
Evidence: `06-EVIDENCE/D6-CANONICAL-MEASURE-2026-08-20.md`.

`judge_pilot.py` in this folder is a paid runner that **must** call this module’s `classify_swap`; it is not a second classifier.
