# 2026-07-31 · MASTER UMBRELLA — Telegram Agent Advisory
**From:** Master/Architect session · **To:** Telegram-build agent · **SoT:** F:\backup
**Status:** ADVISORY — you (TG agent) own the build; this is the umbrella you operate under.

> من تلگرامِ جدیدِ شما را ندیده‌ام (D7). پس این سند **چتر و توصیه** است، نه پرامپتِ دقیقِ ساخت.
> شما صاحبِ کدِ تلگرام هستید؛ من چارتر، قراردادِ دسترسی و اولویت‌ها را نگه می‌دارم (D9).

---

## 0. THREE TRUTHS YOU MUST OPERATE ON

1. **EFE/Active-Inference وجود ندارد.** PolicyPFE، efe_scores، kuramoto، reward_engine، audit_label —
   هیچ‌کدام در کد نیستند (فقط research docs). HEART_PRECISION_WEIGHT=0. **هرگونه ارجاع به EFE
   در تلگرام باید به‌عنوان «چشم‌انداز» باشه، نه قابلیتِ موجود.** UI نباید ادعای EFE کند.
2. **تلگرام از پیش غول‌پیکر است.** ~۱۸٬۰۰۰ خط کد (telegram_center 13,445 + approval_channel 4,718)
   + ۳۴ فایل تست. کارِ شما **بستن gap + arm flag** است، نه بازنویسی (D2).
3. **اوونِ درست:** Owner دسکتاپ فقط بک‌آپ است. همه‌ی تغییرات در F:\backup (D16).

---

## 1. THE ACCESS CONTRACT v1 (confirms existing TG-UI-CHARTER — do not violate)
Three tiers, ratified by 24 owner votes (commit f0680c6):
| Tier | Bot | Surface | Allowed |
|------|-----|---------|---------|
| OUTER | TelBot | Owner DM | natural-language chat, decisions, vote cards, capture, lead machine |
| INNER | Octopus | Owner DM (tech) + alerts | health/alerts/approval/receipts ONLY |
| GROUP | Forum | topic-per-leg | legs only — status/queue/receipts, NO owner-decision bypass |

**Invariants (immutable):**
- Owner = sole authority for money, external actions, Orange/Red, kill/rollback.
- Every buy/sell/withdraw = HARD_STOP, human only. (The D10 meter does NOT auto-move money.)
- T3 (money/outbound/destroy) = instant vote card, never autonomous.
- One writer per file; center.py serial-only (existing MEGAPROMPT-TG-UI-BUILD contract).

---

## 2. AUTONOMY MODEL (D3 + D14) — wire this into the action path
| Tier | Behavior | Failure mode |
|------|----------|--------------|
| T0 — silent read/analyze | autonomous | n/a (no effect) |
| T1 — reversible internal change | autonomous | **auto-revert + notify** (D14) |
| T2 — owner opinion needed | queued → vote card | **pause + Owner card** (no auto-revert) |
| T3 — money/outbound/destroy | instant vote card | **HARD_STOP** (D14) |

PATCH_CARD (4th self-fix lock) arms **T0/T1 only**. T2/T3 stays fail-closed.
Resolves VQ-AUTONOMY-QUEUE-001 toward this tiered model.

---

## 3. GAP CLOSURE PRIORITY (D5 — risks first, then features)
Build in THIS order (Wave 0 of MASTER-PLAN gates Wave 3):
1. **(Wave 0, blocking)** send-audit: tri-state (attempted/held/blocked) on the 8 remaining red
   send sites. Your lane already ratcheted 17→9; finish to ≤9 target.
2. **split arm** — OCTOPUS_TG_SPLIT_V1 (foundation of two-bot model).
3. **capture module** — text/image/link → classify → vault (D6: local whisper for voice).
4. **reminder engine + morning/evening brief** (rhythm per charter).
5. **lead machine arm** — owner ARM vote on daily outbound cap; اونلی فنز/langar in scope (D8).
6. **callback HMAC arm** — OCTOPUS_WIRE_CB_TOKEN (security).
7. **Mini App** — already built by you (D7); just ensure it honors the access contract + autonomy tiers.

---

## 4. WHAT I NEED FROM YOU (so my umbrella stays accurate)
Since I haven't seen your new TG build:
- Where did the Mini App land? Which files? Does it respect the 3-tier access contract?
- Did you decompose center.py (3,611 LOC monolith) or keep it serial? (charter Wave-1 planned decomposition.)
- What flags did you arm? Confirm OCTOPUS_TG_SPLIT_V1 / MISSION_RUNNER / CB_TOKEN / EVENT_BRIDGE states.
- Did lead-machine outbound cap get an ARM vote, or still pending?

Answer these and I'll tighten the umbrella. Until then this advisory stands.

---

## 5. AUDIT BAR FOR YOUR CHANGES (D13 — for specialist grading)
Every change you ship must carry:
- **diff** (clear, reviewable)
- **rationale** (why, tied to a charter vote or gap id)
- **test** (the 34-file suite must stay green; add coverage for new code)
- **rollback plan** (how to revert, especially for armed flags)
- **owner sign-off** for T2/T3 / armed flags
This is non-negotiable — specialists will grade completeness against it.

---

## 6. WHAT I EXPLICITLY DO NOT DO
- I do not write your build megaprompt (you own TG build).
- I do not touch telegram_center/ or approval_channel.py code (your files).
- I do not pretend EFE exists in any doc or UI.
- I keep TG-UI-CHARTER + TELEGRAM-ACCESS-CONTRACT.v1.json coherent with reality.

If your build diverges from the charter, surface it here so we reconcile before owner sees drift.
