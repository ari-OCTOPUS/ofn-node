# BOARD2-WIRE-SEND-IDB-FIX-2026-08-22

Status: **FIXED on DietPi**; Windows has no send script copy.

| File | Purpose |
|------|---------|
| BEFORE-snippet.txt | Bad LAST_B / 10#b003 arithmetic |
| AFTER-snippet.txt | Digits-only LAST_B + ## fallback |
| ofn-wire-send.sh.BEFORE | Full pre-fix script |
| ofn-wire-send.sh.AFTER | Full post-fix script (live) |
| REPRO-ARITH.txt | Local bash repro of bug vs fix |
| EXPLANATION.md | Root cause + constraints |
| VERIFY.txt | How to verify |
| PATCH-FOR-MARKETING.txt | Exact diff to apply / confirm |

Related prior note: `../BOARD2-WIRE-SEND-ID-BUG-2026-08-22/README.md` (proposed patch; now applied).