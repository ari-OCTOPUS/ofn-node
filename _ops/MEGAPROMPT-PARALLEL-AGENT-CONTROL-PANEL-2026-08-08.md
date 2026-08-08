# مگاپرامپت — ایجنتِ موازی: تبِ کنترل‌پنل + endpoint

> **تاریخ:** ۲۰۲۶-۰۸-۰۸ · **نوع:** مگاپرامپت برای ایجنتِ موازی (کپی‌پیست) · **وضعیت:** آماده

---

## ⚠️ هماهنگ‌سازیِ حیاتی با ایجنتِ اصلی (الزامی)

قبل از هرچیزی بدان: یک ایجنتِ دیگر (ایجنتِ اصلی) همین‌الان کارِ زیر را روی همین فایل‌ها انجام داده و commit کرده (کامیت `e798722`):

### کارِ انجام‌شده (کامیت `e798722` — روی master):
1. **فیکس ۴ باگ** در `get_cognitive_scan_state()` و `get_agent_log_state()`:
   - `_runtime()`/`_read_json()`/`_now_iso()` تعریف‌نشده بودند → حالا `STATE_DIR`/`_read_json_safe()`/`time.strftime` استفاده می‌شود
   - `self_accuracy` یک object بود نه عدد → حالا `.accuracy` استخراج می‌شود
2. **لایهٔ ۱ SDK بومیِ تلگرام** در `app.js`:
   - `setBottomButton(text, onClick)` / `hideBottomButton()` — wrapper برای BottomButton||MainButton
   - `hapticSelect()` — `selectionChanged()` روی کلیکِ چیپ
   - `enableClosingGuard(on)` — `enableClosingConfirmation` روی focus/blur
   - این‌ها در تب‌های tasks و notifications فعال شده‌اند
   - `render()` هنگام تب‌عوضی `hideBottomButton()` + `enableClosingGuard(false)` را صدا می‌زند

### قاعدهٔ طلایی: هیچ‌چیز را حذف نکن
تو قرار است **اضافه کنی** (تبِ کنترل‌پنل + endpoint)، نه حذف کنی. وقتی `app.js` یا `miniapp_state.py` را ویرایش می‌کنی:
- توابعِ `setBottomButton`، `hideBottomButton`، `hapticSelect`، `enableClosingGuard` را دست‌نزن
- توابعِ `renderCognitiveScan`، `renderAgentLog`، `viewScans` را دست‌نزن
- `get_cognitive_scan_state`، `get_agent_log_state` را دست‌نزن
- الگوی `dispatch_api` را حفظ کن — فقط branch جدید اضافه کن

---

## مرزهای سخت (بدون استثنا، نقض نکن)
- هرگز به `.git`، `_code`، یا فایلِ حاویِ secret دست نزن.
- `_ops/legs/**` را فقط بخوان.
- `_ops/telegram_center/center.py` و `_ops/wiring.py` را فقط بخوان (داغِ مشترک).
- هرگز فلگی آرم/خاموش نکن — فقط توصیه کن.
- `git add -A` هرگز. بیش از ~۵ فایل ⇒ `agent-checkpoint:` commit.
- هیچ ادعایی بدونِ اجرای واقعی باور نکن — خروجیِ واقعیِ تست را ضمیمه کن.
- هیچ فایلی حذف نکن (کارِ این مأموریتِ فقط افزودن/ادغام است، نه حذف).

## دامنهٔ فایلیِ تو (فقط این‌ها)
- `_ops/telegram_center/miniapp_gateway.py` (ویرایش — اضافه‌کردنِ مسیر به `READ_API_PATHS`)
- `_ops/telegram_center/miniapp_state.py` (ویرایش — اضافه‌کردنِ handler در `dispatch_api`، بدون دست‌زدن به handler‌های موجود)
- `_ops/telegram_center/miniapp/index.html` (ویرایش — اضافه‌کردنِ تبِ نو)
- `_ops/telegram_center/miniapp/app.js` (ویرایش — رندرِ تبِ نو، بدون دست‌زدن به لایهٔ ۱)
- `_ops/telegram_center/miniapp/style.css` (ویرایش — استایلِ تبِ نو، فقط اگه لازم باشد)
- `_ops/tests/test_miniapp_*.py` (نو یا ویرایش — تستِ endpoint + رندر)
- `_ops/control_plane/live_snapshot.py` (**فقط خواندن** — منبعِ داده؛ دست نزن)

## معماریِ موجود (برای هماهنگی — این‌ها را اول بخوان)

### ۱. snapshot() — منبعِ داده
```python
from control_plane import live_snapshot
live_snapshot.snapshot(use_cache=True) -> dict
```
- خروجی: `{schema, ts, epoch, sections, organism, budget, brain, flags, approvals, memory, health, processes}`. هر مقدار JSON-serializable.
- کاملاً read-only، $0، fail-soft، cache TTL ۵s.
- دسترسی تست:
```bash
python -X utf8 -c "import sys; sys.path.insert(0,'_ops'); from control_plane import live_snapshot as ls; import json; print(json.dumps(ls.snapshot(use_cache=False), ensure_ascii=False, indent=2))"
```

### ۲. الگوی endpoint (READ_API_PATHS)
در `miniapp_gateway.py` خط ~۵۸: `READ_API_PATHS` یک set از مسیرهای read-only است.
هر مسیر پشتِ دیوارِ HMAC owner-auth است (هیچ استثنا). الگوی اضافه‌کردن:
```python
# در READ_API_PATHS:
"/api/control-plane",   # مسیرِ نو
```
سپس در `miniapp_state.py::dispatch_api()` یک branch اضافه کن که `snapshot()` را صدا بزند و JSON برگرداند. الگوی موجود (مثلاً `/api/cognitive-scan` یا `/api/selfmap`) را کپی کن.

⚠️ **حتماً از `_read_json_safe` و `STATE_DIR` استفاده کن** (نه `_runtime` یا `_read_json` که وجود ندارند — این باگی بود که قبلاً فیکس شد). برای snapshot که یک تابع است نه فایل، الگوی مستقیم:
```python
def get_control_plane_state(root=None):
    out = {"status": "ok", "schema": "control-plane.v1", "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    try:
        from control_plane import live_snapshot as ls
        snap = ls.snapshot(use_cache=True)
        out["snapshot"] = snap
    except Exception as e:
        out["status"] = "error"
        out["reason"] = str(e)[:200]
    return out
```

### ۳. الگوی تب (index.html)
در `miniapp/index.html` خط ~۴۶: تب‌ها به‌صورتِ `<div class="tab" data-tab="NAME">` هستند. **یک تبِ نو اضافه کن: `data-tab="control"` (بعد از `scans` یا بعد از `system`)**. سپس در `app.js` رندرِ آن تب را اضافه کن که `/api/control-plane` را fetch کند و بخش‌ها را به‌صورتِ کارت نشان دهد.

⚠️ در `app.js` این موارد را حفظ کن:
- `renderers` map را فقط اضافه کن (`control:viewControl`)، کلیدهای موجود را دست‌نزن
- اگر از `setBottomButton` استفاده می‌کنی عالیست (تبِ کنترل‌پنل می‌تونه «↻ تازه‌سازی» داشته باشه)، ولی `hideBottomButton()` در `render()` از قبل هنگام تب‌عوضی صدا زده می‌شود
- stale-fetch guard (`_renderSeq`) را در رندرِ async استفاده کن (الگوی `viewHome`/`renderCognitiveScan` را کپی کن)

---

## مأموریت: تبِ کنترل‌پنل + endpoint

### مرحلهٔ ۱ — endpoint (read-only)
۱. در `miniapp_gateway.py::READ_API_PATHS` مسیرِ `"/api/control-plane"` را اضافه کن.
۲. در `miniapp_state.py::dispatch_api()` branchِ نو اضافه کن:
```python
"/api/control-plane": get_control_plane_state,
```
۳. fail-soft: اگه import/snapshot خطا داد، `{"status":"error",...}` برگردان، نه crash.

### مرحلهٔ ۲ — تبِ frontend
۱. در `index.html` یک تبِ `data-tab="control"` اضافه کن (بعد از `system` یا `scans`).
۲. در `app.js` رندرِ تب را اضافه کن. بخش‌ها را به‌صورتِ کارت نشان بده:
- **ارگانیسم**: beat، frozen، n_legs، legs (live/dead)
- **بودجه**: fugu used/cap/remaining، monthly_cap
- **مغز**: local_llm reachable، keys_present، paid_gate
- **فلگ‌ها**: n_armed/n_total
- **تأییدها**: pending count، oldest_pending_age
- **حافظه**: bcm n_keys، consolidation n_cycles، self_model pct
- **سلامت**: n_dark_gates، n_partial_gates
- **پروسه‌ها**: هر ۵ — pid، alive
۳. فقط read-only. هیچ دکمهٔ toggle/action در این فاز نیست.
۴. اگر دادهٔ بخشی `status: unknown` بود، صادقانه «نامشخص» نشان بده، نه صفرِ فیک.
۵. stale-fetch guard `_renderSeq` الزامی است (الگوی `viewHome`).

### مرحلهٔ ۳ — تست
۱. `test_miniapp_gateway.py` یا فایلِ نو: endpoint را صدا بزن، assert کن:
- status ۲۰۰ (با owner-auth معتبر) یا ۴۰۳ (بدون auth).
- بدنه JSON است و بخش‌های snapshot دارد.
- snapshot در پروسهٔ تست crash نمی‌کند.
۲. mutation-test: branch را حذف کن → تست باید ۴۰۴/fail بدهد.

### مرحلهٔ ۴ — قواعد
- همهٔ داده‌ها از `snapshot()` می‌آیند — هیچ منبعِ جدا ساخته نشوند (اصلِ «جمع‌کنندهٔ واحد»).
- endpoint پشتِ همان HMAC owner-auth بماند (هیچ استثنا).
- هیچ writeای — این فقط خواندن است.
- fail-soft: اگه snapshot بخشی را ندهد، UI «نامشخص» نشان دهد نه crash.
- cache: snapshot از `use_cache=True` استفاده کن (در پروسهٔ gateway، TTL ۵s).

### قدمِ آخر (اجباری)
۱. نوت در `07 - Knowledge/شناخت-اختاپوس/` با شمارهٔ بعدیِ آزاد (۳۳).
۲. `HANDOFF.md` + `architect/PROJECT.md` را تازه کن.
۳. `validate_contract.py` + frontmatter ratchet را اجرا کن.
۴. هر دو validator باید سبز (یا صفر regression) بمانند.

### گزارشِ نهایی
- شاهدِ واقعی: endpoint با auth معتبر چه برمی‌گرداند (بخش‌ها).
- آیا تب در مرورگر رندر می‌شود (اگر قابلِ تستی).
- لیستِ commitها.
- آیا هیچ تب/endpoint موجودی خراب شد (regression-check).
- **تأییدِ صریح** که توابعِ لایهٔ ۱ (`setBottomButton`، `hapticSelect`، `enableClosingGuard`) دست‌نخورده ماندند.

---

## ترتیبِ اجرا
۱ → ۲ → ۳ → ۴. هر مرحله به‌صورت جداگانه کامیت‌نشده در working tree رها شود (طبق منشور §۱.۳) و گزارش دهد.

## منابع
- `live_snapshot.py` را اول بخوان تا ساختارِ snapshot را بفهمی.
- الگوی endpoint: `get_cognitive_scan_state` در `miniapp_state.py`.
- الگوی تب: `viewScans`/`renderCognitiveScan` در `app.js`.
