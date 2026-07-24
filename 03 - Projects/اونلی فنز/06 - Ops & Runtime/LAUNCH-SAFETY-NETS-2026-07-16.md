# 🛡 Launch Safety Nets — Project-F (2026-07-16)

> سه لایهٔ fail-closed که مسیر «Full Aggressive» را قابل‌اجرا می‌کنند بدونِ
> مرگِ زودهنگامِ پروژه. هر سه در کد پیاده‌سازی و تست شده‌اند (۱۰۰/۱۰۰ تست سبز).

---

## چرا این سه؟

پلن لانچ سه ریسکِ کشنده دارد که هر کدام به‌تنهایی می‌تواند پروژه را در <۱ ماه
بکشد:

| ریسک | علت | safety net |
|---|---|---|
| **Ban پلتفرم (OF) به‌خاطر AI-chat** | ToS OF ممنوعیت autonomous chat | #1: DM HITL |
| **Shadowban Reddit به‌خاطر لینکِ زودهنگام** | آکانت تازه + لینک فروش | #2: warm-up guard |
| **تشدیدِ warning → account death** | یک warning نادیده → دوم → ban | #3: warning kill-switch |

---

## Safety Net #1 — DM HITL (Human-In-The-Loop)

**اصل:** AI فقط draft می‌زند؛ آری قبل از ارسال تأیید می‌کند؛ هیچ DM خودکار.

**فایل‌ها:**
- `brain/dm_pipeline.py` — صف DM با جریان `draft → pending_review → ready_for_manual_send → sent`
- `langar/dm_admin.py` — دستورهای تلگرامی `/dm_*`

**دستورهای آری:**
| دستور | کار |
|---|---|
| `/dm_status` | خلاصهٔ صف |
| `/dm_queue` | draftهای منتظر review |
| `/dm_ok <id>` | تأیید → payload آمادهٔ copy-paste |
| `/dm_no <id>` | رد |
| `/dm_sent <id>` | ثبتِ ارسالِ دستی (آمار) |
| `/dm_new <ch> <kind> <body>` | ساختنِ draft دستی |

**گاردها:**
- هیچ متد `send/transmit/post` وجود ندارد (تضمینِ ساختاری)
- containment guard (rule #3/#6): paypal/cashapp/crypto/هویت/شهر → flag → approve نمی‌شود
- `auto_sent` همیشه `False`

---

## Safety Net #2 — Warm-up Guard

**اصل:** تا رسیدنِ کارمای Reddit به آستانه (۲۰)، هیچ آیتمِ فروشی finalize نمی‌شود.

**فایل‌ها:**
- `brain/guards.py` — `WarmupGuard` کلاس
- `brain/acquisition_pipeline.py` — `finalize()` چک می‌کند
- state: `langar/reddit_state.json`

**دستورهای آری:**
| دستور | کار |
|---|---|
| `/report_karma <n>` | ثبتِ کارمای دستی (هر جمعه از داشبورد) |
| `/guards` | snapshot کامل |

**منطق:**
- آیتم غیرفروشی (SFW) → همیشه مجاز (برای کارما‌سازی)
- آیتم فروشی + کارما < ۲۰ → **deny** (fail-closed)
- آیتم فروشی + کارما ≥ ۲۰ → مجاز
- کانال‌های غیر-Reddit (X/OF) → همیشه مجاز (warm-up جدا)

**تشخیصِ «آیتم فروشی»:** heuristic روی hook/caption/tag برای نشانه‌هایی مثل
"link in bio", "subscribe", "ppv", "$5", "DM me".

---

## Safety Net #3 — Platform-Warning Kill-Switch

**اصل:** هر warning پلتفرمی یک کانال را lock می‌کند؛ ۲ warning = full_stop.

**فایل‌ها:**
- `brain/guards.py` — `ChannelLocks` کلاس
- `langar/langar_bot.py` — `/report_warning`, `/clear_warning`, `/clear_full_stop`
- state: `langar/channel_locks.json`

**دستورهای آری:**
| دستور | کار |
|---|---|
| `/report_warning <ch> [reason]` | ثبتِ warning → lock کانال |
| `/clear_warning <ch>` | باز کردنِ lock کانال (اگه full_stop نباشد) |
| `/clear_full_stop` | باز کردنِ کل قیف (فقط با verdict) |

**منطق:**
- ۱ warning → کانال lock تا `/clear_warning`
- ≥۲ warning روی همان کانال → `full_stop = True` (کل قیف stop)
- وقتی full_stop فعال است، `finalize()` روی همهٔ کانال‌ها deny می‌کند
- fail-closed: فایل خراب = محتاطانه‌ترین حالت

---

## یکپارچگی با pipeline موجود

`acquisition_pipeline.AcquisitionPipeline.__init__` دو پارامتر جدید قبول می‌کند:

```python
AcquisitionPipeline(brain=..., warmup=WarmupGuard(), locks=ChannelLocks())
```

`finalize()` قبل از ready کردن، `check_all_guards()` را صدا می‌زند:
1. full_stop فعال؟ → deny
2. کانال locked؟ → deny
3. warm-up violated؟ → deny

هر deny آیتم را reject نمی‌کند — فقط `approved` می‌ماند برای retry وقتی شرایط جور شد.

`/pf_status` حالا وضعیت guards را هم نشان می‌دهد.

---

## تست‌ها (۱۰۰/۱۰۰ سبز)

| فایل | چه تست می‌کند | تعداد |
|---|---|---|
| `tests/test_warmup_guard.py` | warm-up logic + pipeline integration | ۱۲ |
| `tests/test_dm_hitl.py` | DM HITL + containment + dispatch | ۱۵ |
| `tests/test_warning_kill.py` | channel locks + full_stop + composite | ۱۳ |

---

## PROP-D2 (ضمایم)

همزمان، باگِ قدیمیِ «learning.py سیم‌نشده به acquisition.py» رفع شد:
- `AcquisitionBrain.with_bandit()` سازندهٔ جدید با `LearningBridge` (ThompsonBandit)
- `analyze()` حالا اگه learner وصل باشه، رتبه‌بندی exploration-aware اعمال می‌کنه
- `feedback_loop()` هم memory پر می‌کنه هم learner.observe
- backward-compatible: بدون learner، heuristic قدیمی کار می‌کنه
