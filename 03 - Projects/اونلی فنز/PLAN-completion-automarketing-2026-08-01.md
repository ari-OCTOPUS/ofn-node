---
type: plan
project: "[[03 - Projects/اونلی فنز/PROJECT]]"
status: active
tags: [project-f, plan, completion, auto-marketing, contained]
created: 2026-08-01
updated: 2026-08-01
created_by: agent
containment: "Project-F only — صفر PII/هویتِ پارتنر؛ کدِ عمومی = Project-F"
---

# پلنِ تکمیل + مارکتینگِ خودکارِ Project-F — ۲۰۲۶-۰۸-۰۱

> ⚠️ Containment: این سند فقط با کدِ «Project-F» و «پارتنر (C)» کار می‌کند — صفر نام/PII/عکس.

## ۰. خلاصهٔ اجرایی

**عینِ لید:** همه‌چیز **ساخته شده و تست‌شده** — مشکل «ساختن» نیست، «**بازکردنِ GATE 0 + مسلح‌سازیِ
سازگار با ToS**» است. آنچه از قبل هست: دو کاکپیتِ propose-only (لنگر + استودیوی Creator)،
موتورِ اکتساب (`brain/acquisition_pipeline.py`)، VaultBank با **۲۲ asset برند**، KPI/funnel
قابل‌سنجش، **۲۰۹/۲۰۹ تست سبز**، ۹/۹ safety-net با اثبات، compliance-tick از manifest.

**گلوگاهِ #۱ = GATE 0** (باز): «محلِ اقامتِ پارتنر + انتخابِ Branch A/B» + **۳ امضای انسانیِ A**
(G0 · REVOKE/RATIFY برای PF-V5 · توافقِ دونفره). تا این بسته نشود، `outward_actions_allowed=false`
است — این عمدی و درست است، نه باگ.

**«مارکتینگِ خودکار» این‌جا چه معنایی دارد (مهم):** ToS اونلی‌فنز **AI-chat را ممنوع** کرده و
پلتفرم‌ها اتوماسیونِ پست/DM را جریمه می‌کنند. پس «خودکار» = **auto-draft + scheduling + queue +
analytics**، و **انسان دستی پست/پیام می‌زند** (الگوی «درفت در کنسولِ جدا + paste دستی»). این معماری
شما از قبل همین است و **باید همین بماند** — اتوماسیونِ کامل = بن + مرگِ برند.

---

## ۱. وضعیتِ فعلی (چی ساخته شده)

| لایه | وضعیت | شاهد |
|---|---|---|
| کاکپیتِ لنگر (`langar/langar_bot.py`، ۷۳KB) | ✅ propose-only، سخت‌شده | دستورهای `/pf_*`، ۸/۸ تستِ منطق |
| استودیوی Creator (`studio/creator_studio.py`) | ✅ neutral-named، shadow-mode | تستِ سبا ۱۶، pf_admin ۸ |
| موتورِ اکتساب (`brain/acquisition_pipeline.py`) | ✅ draft→queue→approve→ready | flow `/pf_plan→/pf_queue→/pf_ok→/pf_ready` |
| VaultBank (برند asset) | ✅ **۲۲ asset** (۱۲ reddit SFW + ۷ x + ۳ of soft-cta) | commit `0a871e0`، fair rotation |
| KPI/funnel + audit HITL | ✅ `/kpi_import`، `approvals.jsonl`، کدِ tracking | — |
| pf_os (actuator/brain/bridge/saba_link) | ✅ کامل، ولی incubating | ADR `PF_OS_CANONICALITY` |
| تست | ✅ **۲۰۹/۲۰۹ سبز** (خط‌پایه ۱۵۲) | `08_TEST_REPORT` |
| اجرای بیرونی | ⛔ **صفر** — پشتِ GATE 0 | `outward_actions_allowed:false` |

---

## ۲. چی «تکمیل» را باز می‌کند (فقط تصمیمِ انسانیِ مالک/پارتنر — ایجنت هرگز)

| # | بلاکر | کار | چه‌کسی |
|---|---|---|---|
| ۱ | **GATE 0** | ثبتِ محلِ اقامتِ پارتنر + انتخابِ Branch A/B (بلوپرینت §۱) | مالک + پارتنر |
| ۲ | **۳ امضای A** | G0 · REVOKE/RATIFY برای PF-V5 · توافقِ مکتوبِ دونفره | مالک |
| ۳ | OWNER-BALLOT ۱۲سؤالی | پرکردنِ برگهٔ رأی (`OWNER-BALLOT-2026-07-20`) | مالک |
| ۴ | ۱۱ verdict معلق | THREAD-CLOSURE §۹ (برند، بلاک AU، لنگر، body-freeze، …) | مالک |
| ۵ | PII در tracked | انتقالِ ۲ سند + ۸ عکسِ `test/` (R10) — الزامی قبل از هر remote | مالک |
| ۶ | `index.lock` قدیمی در `.git` | پاک کن تا commit/merge روی درختِ زنده ممکن شود | مالک |
| ۷ | R9 «Sydney» در کپیِ عمومی | scrub قبل از bio | مالک/ایجنت (گیت‌دار) |

> تا GATE 0 بسته نشود، بقیهٔ زنجیره (Day-Zero infra، warm-up، اکتساب) قفل است. **مرحلهٔ ۱ ROADMAP
> کلِ زنجیره را باز می‌کند.**

---

## ۳. موتورِ مارکتینگِ خودکار (سازگار با ToS، HITL)

**لوله (همه propose-only؛ انسان پست می‌کند):**
```
VaultBank(asset برند) → /pf_plan N → /pf_queue → رأیِ مالک /pf_ok → /pf_ready (payload + کدِ tracking)
                                                                        → پستِ دستیِ انسان → KPI import
```

**کانال‌ها (از corpus تحقیقِ P1–P10، همه SFW/soft-CTA):**
| کانال | نقش | سند |
|---|---|---|
| Reddit | موتورِ کشفِ اصلی (SFW teaser → link hub) | `P3-reddit-engine`، `01-reddit-growth-plan` |
| X (Twitter) | growth + repurposing | `P2-x-growth-engine`، `02-x-playbook` |
| S4S network | رشدِ متقابل | `P8-s4s-network` |
| Repurposing pipeline | یک محتوا → چند کانال | `P9-repurposing-pipeline` |
| Owned audience (link hub) | مالکیتِ مخاطب، ضدِ ریسکِ پلتفرم | `P6-owned-audience` |
| FeetFinder + OF | فروش (PPV/custom = پولِ واقعی) | `COMPETITOR-MARKET-LANDSCAPE` |

**اجزای «خودکار» که مسلح می‌شوند (بعد از GATE 0):**
- **Auto-draft:** موتورِ اکتساب از VaultBank با fair-rotation درفت می‌سازد (نه از hookهای امن).
- **Scheduling/queue:** cadence روزانه؛ صفِ تأیید؛ رأیِ مالک → آمادهٔ پست.
- **DM (HITL):** `dm_pipeline.py` درفتِ پاسخ می‌سازد؛ **انسان paste می‌کند** (ToS). PPV ladder در `ppv-ladder.md`.
- **Analytics/experiment loop:** `P10-analytics-experiment-loop` + KPIها: unlock-rate، $/script-start، چرخهٔ custom، $/ساعتِ DM. **retention = گافِ اصلیِ شما** (تمرکزِ ویژه).
- **Learning:** `LearningBridge` را در `pf_admin._default_pipe()` پیش‌فرض کن (الان اختیاری) + تستِ regression — این «مرحلهٔ ۵ بی‌نیاز به گیت» است، همین حالا قابلِ انجام.

**فلگ‌های مسلح‌سازی (پیش‌فرض خاموش — رأیِ مالک):** `PF_LEARNING_WIRED` · `PF_LIVE_*` ·
`OCTOPUS_WIRE_SABA_BRIDGE` · `OCTOPUS_WIRE_EVENT_BRIDGE` (ترتیبِ رسمی در `_ops/ARMING-ORDER-2026-07-29.md`).

---

## ۴. سیم‌کشی به اختاپوس (کنترل از تلگرام)

- **الان:** کنترلِ زندهٔ این پا فقط از باتِ دوم (دستورهای لنگر `/pf_*`) + pause/resume مرکز؛ در مرکز
  فقط **دایجستِ content-free** با نامِ «استودیو» (عمداً بدونِ هویت/محتوا).
- **بعد از فلگ‌ها:** `bridge.py`→`saba-bridge.jsonl`→`bridge_beat` و `event_bus`→`event_bridge` زنده
  می‌شوند → کنترلِ کاملِ پا از مرکز، همچنان content-free بیرونِ پوشه.

---

## ۵. نقشهٔ راهِ ترتیب‌دار

| فاز | کار | تلاش | ROI | ریسک | گیت |
|---|---|---|---|---|---|
| **۰** | GATE 0 + ۳ امضا + ballot + PII cleanup + index.lock | کم (تصمیم) | قفل‌گشا | — | انسانی |
| **۱** | مرحلهٔ ۵ بی‌گیت: LearningBridge پیش‌فرض + تستِ regression | کم | متوسط | کم | — |
| **۲** | Day-Zero infra (بلوپرینت §۵، ~۴–۵h) → warm-up هفتهٔ ۱ | متوسط | بالا | متوسط | بعد از G0 |
| **۳** | مسلح‌سازیِ اکتساب (فلگ‌ها) → درفت/صف/تأیید زنده → **اولین پستِ واقعی** | کم | بالا | متوسط (بیرونی، HITL) | رأی |
| **۴** | فروش + **retention** (گافِ اصلی) + analytics loop | متوسط | بالا | کم | — |
| **۵** | بهینه‌سازیِ کانال‌ها با bandit/learning | زیاد | متوسط | کم | — |

---

## ۶. قدم‌های فوریِ مالک

1. **OWNER-BALLOT ۱۲سؤالی** را پر کن — این تکِ سند کلِ GATE 0 و ۳ امضا را حل می‌کند.
2. `index.lock` را از `.git` پاک کن (وگرنه هیچ merge/commit ممکن نیست).
3. **PII cleanup** (R10): ۲ سند + ۸ عکسِ `test/` را با رأیت منتقل کن — الزامی قبل از هر remote.
4. تصمیمِ Branch A/B را ثبت کن (محلِ اقامتِ پارتنر).

---

## ۷. خطوطِ قرمزِ ثابت (سازگاری/ایمنی — هرگز ضعیف نشوند)

- **ToS:** هیچ AI-chat/auto-DM؛ فقط draft+paste دستی. هیچ auto-postِ پلتفرمی.
- **بدونِ fake engagement / bot follow / ban-evasion / خریدِ فالوور** — رشدِ ارگانیک و پایدار.
- **geo-block** (ایران) · **no face/body** (فقط پا، در فازِ فعلی) · **body-freeze** فعال.
- **PII containment:** صفر هویت/عکس/پلتفرم/نامِ پارتنر بیرونِ این پوشه؛ کدِ عمومی = Project-F.
- **اجرای پرمخاطره = انسان (A)**؛ ایجنت فقط propose + رصد + قطعِ اضطراری.

---

*ساخته‌شده ۲۰۲۶-۰۸-۰۱ بر پایهٔ: `PROJECT.md` · `HOME.md` · `WEEKLY-BRIEF.md` ·
`ACQUISITION-ENGINE-2026-07-05` · `05-Acquisition/AUTO-ACQUISITION-BLUEPRINT` · corpus تحقیقِ P1–P10.*
