# Candidate findings — NOT registered as CONTRADICTIONS truth

C-048..C-053 remain **candidates** until an owner action + evidence hash + post-fix test exist.
`finding_id` below is stable (S-B01 …) even if prose changes.

| candidate | finding_id | claim | evidence | hash sha256 | maps to |
|---|---|---|---|---|---|
| C-048 | S-B01 | Fugu daily quota exhausted / denied; silent local fallback forbidden | `_ops/state/fugu-quota.json` used_total=120 denied daily-cap=124 day=2026-08-20 | `eb782abbc494b7f528d4af0cdc471ace648c6bb80f947eb5e2bf40c789cba6c2` | Rail B |
| C-049 | S-B02 | FX pin must be owner-fresh before cognitive expansion | `_ops/state/labels.json` FX_PIN VERIFIED 2026-08-20 (label file) | `a55f637c91181a8f24f2e7784a3218c386e305e64101f0558616b75661f985cb` | Rail B |
| C-050 | S-B06 | RUN-ORGANISM.bat availability / one-shot cmd gap | `_ops/RUN-ORGANISM.bat` + `06-EVIDENCE/INCIDENT-ORGANISM-GAP-2026-08-20.md` | bat `2a2a85854c022da287ede4edf9dcd5cdfa93974012c8c19fae2847dc4520263a` | Rail B |
| C-051 | S-D01 | doctor-pulse stuck awaiting-merge; one-open-mission deadlock | `OCTOPUS-DOCTOR/90-_meta/state/missions.json` · DEEP-SCAN-DOCTOR 2026-08-20 | `a0e6558e1c81e1d160e5260d90afa5adb5b3bc8447c7ddc7d8b3e68e1d1405a3` | Rail B |
| C-052 | S-B05 | brain_core parity without baseline should be NO_BASELINE | code `brain_core.py` ParityTracker (live compare without declared baseline) | UNLOCATED as numeric 6383 this session | Rail B |
| C-053 | WAVE0-ATTR | receipt attribution 33.8% today < 95% | `WAVE0-GATES.json` + `cost-receipts.jsonl` | see WAVE0-GATES.json | Rail A |

Status of all six: **candidate**. `resolved` forbidden without post-fix receipt + test + snapshot.
