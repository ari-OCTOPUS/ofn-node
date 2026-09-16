---
type: handoff+report
status: active
created: 2026-07-06
verdict_recorded: "آری «همه تغییراتو اعمال کن، برای Obsidian جا بیفته، تغییرلاگ/گزارش همه‌جا، ایجنتای دیگه بفهمن»"
tags: [handoff, applied, agent-awareness, governor, muse]
related: "[[GOVERNOR-MUSE-SYSTEM-INDEX]] · [[PROJECT]] · [[00-Home]]"
---

# اعمال‌شد + HANDOFF — سیستمِ GOVERNOR + MUSE

> **برای ایجنت‌های دیگر:** یک سیستمِ جدید اضافه شد. این نوت می‌گوید چه چیزی *اعمال* شد، چه چیزی *فقط-مالک* مانده، و بلوک‌های آماده‌ای که مالک باید به فایل‌های خارج از این پوشه (`_memory/HANDOFF`، `05 - Agents/AGENT_REGISTRY`) پیست کند.

## ۱. چه چیزی همین حالا اعمال شد ✅ (برگشت‌پذیر — git/backup)
| ناحیه | تغییر |
|---|---|
| ژنوم D1 | `LEARNING-CONTRACT.yaml`: `mode: active` → `mode: propose-only` + `mode_target: active-L3` + کامنتِ precedence (STATE مقدم) |
| ژنوم D2 | `LEARNING-STATE.json`: `security_gate_status: "OPEN"` → `"LIFTED"` (هم‌راستا با charter §۲) |
| ژنوم D3 | `ENGINE-PROMPT.md`: بنرِ precedence تقویت شد — حلقه internal-only، تک‌whitelist = MUTATION-WHITELIST |
| کد | ۶ اسکریپتِ تست‌شده در `scripts/` (+ `MUSE-QUARANTINE-LEDGER.md` خالی) |
| Obsidian | [[GOVERNOR-MUSE-SYSTEM-INDEX]] (MOC) + لینک در [[00-Home]] + ثبت در [[PROJECT]] Active Context |
| ledger | ۳ ردیف در `MUTATION-LEDGER.md` (propose/fix/apply) |

## ۲. فقط-مالک — مانده (من مجاز/قادر نیستم)
1. **پیستِ بلوکِ منشورِ فاز ۱** در `ARCHITECT_CHARTER.md` — charter برای ایجنت **immutable** است (خودِ منشور تصریح کرده). بلوک آماده: [[2026-07-06 PHASE1-GOVERNOR-MUSE-CHARTER-proposal]] §۱/§۲.
2. **`python scripts/genome_guard.py --init "..."`** — تأییدِ ژنومِ فعلی (عملِ approval).
3. **مقصدِ بک‌اپ + `rclone config`** (secret فقط در password manager).
4. **زمان‌بندیِ Task Scheduler** — طبق `scripts/SETUP-README.md`.

## ۳. بلوکِ آماده برای `_memory/HANDOFF` (پیست کن)
```
### جلسهٔ بعد باید — GOVERNOR+MUSE
- سیستمِ GOVERNOR+MUSE ساخته شد (propose): نقشه = [[GOVERNOR-MUSE-SYSTEM-INDEX]].
- اعمال‌شد: دریفت‌های ژنوم D1/D2/D3 + ۶ اسکریپت در scripts/ (تست‌شده) + ۸ باگ رفع‌شده.
- مانده (مالک): پیستِ منشورِ فاز۱، genome_guard --init، مقصدِ بک‌اپ، زمان‌بندی.
- ترتیبِ فعال‌سازی: بک‌اپ → گاردِ ژنوم → بودجه → GOVERNOR shadow → MUSE dry-run → (۳۰روز) live.
- تصمیمِ باز: جهتِ D1 (L1 محافظه‌کار اعمال شد؛ L3-active؟).
```

## ۴. بلوکِ آماده برای `05 - Agents/AGENT_REGISTRY` (پیست کن)
```
| GOVERNOR | always-on (NSSM) shadow | ops-read-only + propose-only | HEARTBEAT(خود)·Anchor Ledger(API)·build-proposals | تلگرام+ledger |
| MUSE | scheduled-rare + budget-gated | read-only-all + quarantine-write-only | MUSE-QUARANTINE-LEDGER فقط | دکترِ تکاملی |
```

## ۵. رابطه با کارِ موازیِ HYBRID-SPEC
هر دو «ژنوم»‌اند ولی هم‌پوشان نیستند: **HYBRID-SPEC** = یکتاسازیِ ارزش‌ها/محافظت/سنجش روی یک شیءِ کد (لایهٔ ارزش). **GOVERNOR+MUSE** = لایهٔ ایجنت/عملیاتِ همیشه‌روشن روی همان ژنوم. هر دو تحتِ یک قانون: propose→approve. اگر ادغام لازم شد، دکترِ تکاملی (این‌جا) و دکترِ HYBRID می‌توانند یک evaluatorِ مشترک شوند — verdictِ مالک.

## ۶. برگشت‌پذیری
همهٔ ویرایش‌های ژنوم کامنتِ `⟳ رفعِ Dx (2026-07-06)` دارند و با git/backup قابلِ برگشت‌اند. اگر جهتِ D1 را نمی‌پسندی (مثلاً L3 می‌خواهی)، یک کلمه بگو تا برگردانم.
