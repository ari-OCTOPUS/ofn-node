# 🎛️ control_plane — سطحِ واحدِ حاکمیتِ runtime (راهنمای ایجنتِ بعدی)

> این سند برای **ایجنتِ بعدی** و مالک (Armin) نوشته شده. اگر عدد/مسیری با واقعیت
> نخواند، **کد و تست مرجع‌اند، نه این سند**. راستی‌آزمایی: `python tests/run_all.py`.
> تاریخِ آخرین به‌روزرسانی: ۲۰۲۶-۰۷-۱۲.

---

## ۰) این چیست و چرا هست

`control_plane/` یک پکیجِ **additive** است که روی اپِ پژوهشیِ `4d_system` سوار شده.
دکترین: **«تمرکزِ کنترل، نه تمرکزِ هوش.»**

- هوش/reasoning/autonomy داخلِ `brain/*` می‌ماند — black box محفوظ است.
- authority/policy/observability/audit/approval/kill-switch/self-heal این‌جا متمرکز است.
- **صفر بازنویسی، صفر دست‌زدن به TCB** (`core/`, `config/`, `brain/{guardrails,budget,
  daemon,telegram_bot,self_code,self_evolve,events,automation}`, `run.py`, `llm/router`…).
- **`.env`/secrets هرگز خوانده یا چاپ نمی‌شود.**

هدفِ نهاییِ مالک: لپ‌تاپ ۲۴/۷ روشن، ارتباط فقط از تلگرامِ ساده، سیستم خودش را ارتقا
می‌دهد، و اگر چیزی افتاد خودش ترمیم می‌شود.

## ۱) خطوطِ قرمزِ ایمنی (لازم‌الاجرا برای هر ایجنت)

1. **همه‌ی flagهای live پیش‌فرض خاموش‌اند** (`control_plane/flags.py`). با flagِ خاموش
   هیچ اکشنِ live ممکن نیست — حتی اگر `confirmed=True` باشد. گیت هم در لایه‌ی اجرا
   (`_default_spawn`) هست، نه فقط در حلقه.
2. **self-heal هرگز restart نمی‌کند** بعد از: HALT حفاظتی (`daemon_state.halted_at`)،
   وجودِ `outputs/daemon.stop` یا `outputs/owner_intent_stop.flag` (نیتِ مالک)، یا
   خروجِ تمیزِ daemon (rc=0). kill-switch همیشه بر self-heal می‌چربد.
3. **apply کدِ self_code فقط از مسیرِ امنِ خودش** (`brain/self_code`: sandbox + tamper
   detection). control plane فقط تصمیم را mirror/gate می‌کند؛ apply جدیدی ندارد.
4. **لایه‌ی observe هرگز در storeهای مشاهده‌شده نمی‌نویسد** (`snapshot.py` فقط SELECT با
   `mode=ro`، بدونِ import از `brain/*`). آینه‌ی registry در DB جداست، نه DB اصلی.
5. **TCB بدونِ اجازه‌ی مالک تغییر نمی‌کند.** تنها تغییرِ TCBِ پیشنهادی که هنوز تأیید
   نشده = heartbeatِ تلگرام (بخش ۶).

## ۲) نقشه‌ی ماژول‌ها

| فایل | نقش |
|---|---|
| `flags.py` | flagهای حاکمیتی، همه default-off جز observe؛ `governance_mode()` |
| `contracts.py` | ۱۲ schemaی داده (EventEnvelope, ActionEnvelope, ApprovalRequest, …) — فقط شکل، بدون رفتار |
| `policy.py` | نردبانِ policy L0–L5 + نگاشتِ action→level + لیستِ high-risk مالک. تابعِ pure، بدون I/O |
| `registry.yaml` + `registry.py` | ثبتِ ۲۷ subsystem + ۲۴ کانال (source of truth = YAML؛ mirror در SQLite جدا) |
| `snapshot.py` | جمع‌آورِ وضعیتِ **فقط‌خواندنی** (daemon/budget/events/workspace/approvals/evolution/notify/memory/supervisor) |
| `channel_doctor.py` | سلامتِ کانال‌ها PASS/WARN/FAIL/UNKNOWN → `outputs/control_plane/_reports/` |
| `shadow.py` | v2: policy روی جریانِ رویداد، **فقط گزارش**؛ اسکنِ اکشنِ مخرب در summary |
| `approvals.py` | v3: approve/reject زنده فقط برای high-risk (flag)، delegate به مسیرِ امن، audit کامل |
| `killswitch.py` | v4: pause/resume/stop روی قراردادِ فایلیِ daemon + نشانِ دائمیِ owner-stop |
| `supervisor.py` | v5: watchdogِ ترمیمِ خود (spawn/monitor daemon+telegram)، قفلِ تک‌نمونه‌ی OS |
| `ui/tab_control_plane.py` | تبِ Streamlit «🎛️ Control Plane» (فقط visibility + دکمه‌های flag-gated) |

تست‌ها: `tests/test_control_plane_*.py` + `tests/test_channel_doctor.py` (۹ فایل).

## ۳) flagها (در `.env`؛ برای فعال‌سازیِ live)

```
CONTROL_PLANE_OBSERVE_ONLY=1      # دیدن (بی‌خطر، پیش‌فرض روشن)
CONTROL_PLANE_SHADOW_POLICY=0     # v2: تحلیلِ خودکارِ shadow در UI
CONTROL_PLANE_APPROVALS_LIVE=0    # v3: approve/reject واقعی از تب
CONTROL_PLANE_KILL_SWITCH_LIVE=0  # v4: pause/stop از تب
CONTROL_PLANE_SELF_HEAL=0         # v5: watchdogِ ۲۴/۷
```

اجرا: `streamlit run run.py` → تبِ 🎛️ · watchdog: `python -m control_plane.supervisor`
(یا `--dry-run` فقط برای دیدنِ تصمیم‌ها) · autostart: `scripts\install_supervisor_task.bat`.
راهنمای کامل: `../SELF_HEAL.md`.

## ۴) وضعیتِ فعلی

- نردبان **v0..v5 کامل** + **سخت‌شده با ۴ راندِ بازبینیِ خصمانه‌ی fix→verify**.
- **۲۴۳ تستِ سبز** (از ۱۴۱ اولیه). AppTest تمیز (۱۰ تب). همه flagهای live **خاموش**.
- pre-commit hook (`scripts/hooks/pre-commit`) قبل از هر commit کلِ suite را می‌دواند.

### تاریخچه‌ی سخت‌سازی (چرا کد این‌شکلی است)
یک بازبینیِ خصمانه ۲۰ باگ در supervisor v5 پیدا کرد؛ ۴ راندِ fix→verify همه را +
regressionهای ناشی از تعمیر را بست:
- **pid-liveness + START_CONFIRM debounce** (`supervisor._daemon_alive`): daemonِ
  تکراری در پنجره‌ی startup/restart/DST ساخته نمی‌شود.
- **HUNG_FREEZE_S=600s** پنجره‌ی مطلقِ یخ‌زدگی: tickِ طولانیِ سالمِ LLM اشتباهاً kill نمی‌شود.
- **owner_intent_stop.flag** دائمی: چون daemon فایلِ `daemon.stop` را مصرف/حذف می‌کند،
  این نشان kill را دوام می‌دهد؛ `killswitch.cancel_stop` پاکش می‌کند.
- **gave_up با cooldown**: یک burstِ گذرا فرزند را برای همیشه خاموش نمی‌کند.
- **قفلِ تک‌نمونه‌ی OS** (`_os_try_lock`: msvcrt/fcntl، عمرِ فرایند، race-free).
- **terminate→kill (SIGKILL) escalation** + `KILL_UNCONFIRMED` اگر بی‌اثر بود.
- **shadow** با left-word-boundary: صرف‌ها (deleted/wiped) را می‌گیرد، preset/swipe را نه.

## ۵) قدم‌های دستیِ مالک (باقی‌مانده — کارِ Armin، نه ایجنت)

1. **token تلگرام** از BotFather در `.env` (طبق `../TELEGRAM_SETUP.md`) — ایجنت هرگز
   token/حساب نمی‌سازد.
2. روشن‌کردنِ flagهای بالا در `.env` (پیشنهاد: یکی‌یکی؛ اول SHADOW، بعد APPROVALS،
   آخر KILL_SWITCH و SELF_HEAL).
3. دوبار کلیک روی `scripts\install_supervisor_task.bat` (autostartِ ۲۴/۷).

## ۶) تنها تصمیمِ بازِ سطحِ TCB (نیازمندِ تأییدِ مالک)

**تشخیصِ تلگرامِ زنده‌ولی‌هنگ‌کرده** ممکن نیست مگر `brain/telegram_bot.py` هر چند
ثانیه یک فایلِ heartbeat بنویسد (تغییرِ کوچکِ additive در TCB). دوبل‌شدنِ بات (خطای
۴۰۹) — که خطرناک‌تر بود — از قبل کاملاً حل شده. تا وقتی مالک این تغییرِ TCB را تأیید
نکند، این محدودیت پذیرفته‌شده باقی می‌ماند.
باقی‌ماندهٔ پذیرفته‌شده‌ی کم‌اثر: `_os_try_lock` در حالتِ نادرِ سیستمِ‌فایلِ بدونِ‌قفل
`"NOLOCK"` برمی‌گرداند (در مسیرِ تولیدِ single-open رخ نمی‌دهد).

## ۷) اشاره‌ها

- حافظه‌ی بین‌سشنیِ Claude: `~/.claude/projects/C--Users-Armin/memory/`
  → `4d-control-plane-mission.md` (کاملِ این مأموریت).
- نقشه‌ی کلِ اکوسیستم (اختاپوس): `C:\Users\Armin\Desktop\OCTOPUS.md`.
  **توجه:** مالک گفت این پروژه از «اختاپوس» جداست و آن کار فعلاً معلق است — قاطی نکن.
- git این پروژه مستقل است (از ۲۰۲۶-۰۷-۱۱)؛ تاریخچه‌ی سخت‌سازی در commitهای
  `484ee03 → dd92af9`.

> صداقت: بدونِ sandboxِ سیستم‌عامل، اجرای کدِ approved مهارِ مطلق ندارد — مرزِ نهایی
> همان تأییدِ آگاهانه‌ی مالک است. Brain-OS هم testbed است، بدونِ ادعای consciousness.
