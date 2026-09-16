# 🐙 GLM-TELBOT-ROLE-AUDIT — فاز H

- **تاریخ:** 2026-07-18
- **موضوع:** نقش‌بندیِ Octopus (commander) و TelBot (assistant) + وضعیتِ ماژول‌های موجود

---

## ۱. مدلِ دو-باتِ پروژه

طبق `_octopus/config/bots.yaml`:

| بات | نقش | can_execute | can_propose | must_route_to_octopus |
|-----|-----|:-----------:|:----------:|:---------------------:|
| **Octopus** | commander | ✅ | — | — |
| **TelBot**  | assistant | ❌ | ✅ | ✅ |

یعنی قراردادِ امنیتی: TelBot **نباید** عملیات حساس مستقیم اجرا کند؛ فقط پیشنهاد/تحلیل بدهد و actionها را به Octopus و صفِ تأیید منتقل کند.

---

## ۲. وضعیتِ کدِ فعلی

جستجو در `_ops` نشان می‌دهد که **کدِ TelBotِ جداگانه‌ای در repo وجود ندارد**. در عوض، دو باتِ تولیدی واقعی این‌ها هستند:

| ماژول | توکن | نقش |
|-------|------|-----|
| `_ops/budget/approval_channel.py` | `TELEGRAM_BOT_TOKEN` | باتِ اصلیِ organism (budget approvals, RFC router, owner commands) — عملیاتی، **commander-grade** |
| `_ops/telegram_center/` (`center.py` + `tg_api.py`) | `TG_CENTER_BOT_TOKEN` | باتِ مرکزِ فرماندهی (منوی context-aware، ناوبری، /menu) — **commander-grade** UI |

یعنی در عمل، هر دو بات موجود نقشِ **commander** دارند. TelBot به‌معنای «دستیارِ مکالمه‌ایِ محدود» هنوز پیاده‌سازی نشده است.

---

## ۳. ارزیابیِ امنیتیِ وضعِ فعلی

✅ **مثبت‌ها:**
- هر دو بات از allowlistِ `is_owner` (fail-closed) عبور می‌کنند — غیرمالک هیچ اثری ندارد.
- اکشن‌های حساس (restart/stop/panic/budget-apply) پشتِ `OCTOPUS_TG_POWER=1` + دوکلیک (`pw`/`pwc`) قفل‌اند.
- مکث/ادامهٔ پا برگشت‌پذیر است (فایل flag).
- containment (`_BANNED_ECHO`) در سه لایه (render → tg_api → events) حفظ می‌شود.
- audit در `power-audit.jsonl` و `_octopus/logs/audit.log` content-free نوشته می‌شود.

⚠️ **ریسک‌های نهفته (که این ایجنت نشانه‌گذاری کرد):**
- اگر روزی TelBot (مکالمه‌ای) با `TELEGRAM_BOT_TOKEN` پیاده‌سازی شود، باید محدود شود که:
  - `can_execute=False` باشد (طبق config) — یعنی هیچ دستورِ حساسی را مستقیم اجرا نکند.
  - هر actionی که کاربر درخواست کند، به جای اجرا، یک **job در `_octopus/state/approvals.json`** بسازد (که حالا با `approval_store.add_pending` ممکن است).
  - کارتِ پیشنهاد بسازد با لینک به Octopus (مثلاً `ap:detail:<id>`).
- ریسکِ 409 Conflict اگر TelBot و approval_channel هر دو با `TELEGRAM_BOT_TOKEN` poll کنند (الان `TG_CENTER_BOT_TOKEN` مستقل این را حل کرده).

---

## ۴. ماژول‌هایِ پیش‌موجود که با فاز F هم‌پوشانند

در حینِ کار، دو ماژول کشف شد که پیش از این ایجنت وجود داشتند:

| ماژول | نقش | هم‌پوشانی با فاز F من |
|-------|-----|----------------------|
| `_ops/telegram_center/action_graph.py` | ژنومِ حرکتی: `ActionSpec` dataclass با `action_id/risk/requires_approval/handler` | هم‌پوشانیِ مفهومی با `actions.py` من؛ ولی `action_graph` بر risk/handler متمرکز است، `actions.py` من بر **callback_data generation** و risk helpers |
| `_ops/telegram_center/mission.py` | Mission Genome: Intent → Mission → Action Card → Approval → Execution | لایهٔ بالاتر از actions؛ propose-only و برای code-autonomy |

**ارزیابی:** `actions.py` من (فاز F) **مکمل** است نه رقیب:
- `action_graph.py` تعریفِ سنتیِ action (با dataclass و handler path).
- `actions.py` من نگاشتِ **callback_data واقعی** (که render/intent نیاز دارند) + helperهای risk/direct/double_confirm.

**توصیه برای ایجنتِ بعدی:** این سه را در یک لایهٔ منسجم統合 کن: `action_graph` تعریف می‌دهد، `actions` callback می‌سازد، `mission` orchestration می‌کند. فعلاً هر سه سبز و مستقل کار می‌کنند.

---

## ۵. پیشنهاد معماری برای TelBotِ آینده (اگر پیاده‌سازی شود)

اگر روزی TelBotِ مکالمه‌ای ساخته شود، این قرارداد را رعایت کند:

1. **ورودی:** پیام آزادِ مالک → `intent.classify(text)` (ماژولِ فاز C).
2. **اگر intent = read-only (status/help/budget/revenue/scan/approvals):**
   - مستقیماً کارت/صفحه نشان بده (مثل Octopus).
3. **اگر intent = pause/resume (low risk):**
   - فقط دکمهٔ `lg:{leg}:p|r` بساز (نه اجرا).
4. **اگر intent = scan_metadata (read but side-effect):**
   - کارتِ `map:start` نشان بده (اجرا بعد از کلیک).
5. **اگر intent = حساس/مبهم (high risk):**
   - به‌جای اجرا، یک job در `approval_store.add_pending(risk="high")` بساز.
   - کارت نشان بده: «این کار نیاز به تأیید دارد — در صف است» با دکمهٔ `ap:detail:<id>`.
6. **هیچ‌گاه:** فایل کاربر را حذف/جابه‌جا/ویرایش نکند؛ `power.py` را مستقیم صدا نزند؛ `_scrub`/containment را دور نزند.

این قرارداد با `bots.yaml` هم‌خوان است و با زیرساختِ فاز C/D/E که حالا موجود است، قابل‌پیاده‌سازی است بدونِ кодِ جدیدِ خطرناک.

---

## ۶. جمع‌بندیِ فاز H

- TelBot به‌معنای دستیارِ مکالمه‌ایِ محدود **هنوز موجود نیست** — هر دو بات فعلی commander-grade هستند.
- قراردادِ امنیتیِ `bots.yaml` به‌عنوان سندِ مرجع برای TelBotِ آینده مستند شد.
- هم‌پوشانیِ `actions.py` با `action_graph.py`/`mission.py` پیش‌موجود شناسایی و به‌عنوان مکمل توصیف شد.
- هیچ ادغامِ مخرب انجام نشد (طبق دستور: «اگر زمان کم است، فقط مستند و TODO دقیق بگذار»).
