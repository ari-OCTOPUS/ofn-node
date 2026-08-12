---
type: knowledge
status: active
tags: [octopus, megaprompt, deep-scan, miniapp, collab, deepseek, senior-agent]
created: 2026-08-12
updated: 2026-08-12
created_by: agent
sources:
  - "[[01 - Dashboard/HANDOFF]]"
  - "[[OCTOPUS/CURRENT-TRUTH]]"
  - "[[06 - Architecture Maps/OCTOPUS-COLLABORATOR-INTERACTION-CONTRACT]]"
  - "[[_ops/INTERACTION-CONTRACT]]"
---

# MEGAPROMPT — Senior Deep-Scan · MiniApp Collab · DeepSeek Talk · Zero-Bug Closeout

> این سند را **کامل** به ایجنت ارشد بده.
> منبع تجربه: جلسهٔ زندهٔ ۲۰۲۶-۰۸-۱۲ روی `F:\backup` (MiniApp collab، 403، stub،
> qwen-dزدی، timeout، tool-request loop، خودشناسی).
> هدف: deep-scan + فیکس + تست + verify زنده تا **هیچ کلاس باگ شناخته‌شدهٔ این جلسه باقی نماند**.

---

## نقش

تو **Senior Systems + Frontend/Backend Debugger + LLM Routing Engineer** برای اختاپوس هستی.

ماموریت: مسیر «مالک ↔ مینی‌اپ ↔ gateway ↔ collaborator ↔ model_router ↔ DeepSeek»
را طوری سخت کن که:

1. حرف مالک را **بفهمد** (نه stub کور، نه qwen hallucinate)
2. بداند **از چه تشکیل شده** (شواهد زنده، نه persona عمومی)
3. UI **هرگز** روی «در حال فکر کردن» یا `bad_json` گیر نکند
4. هیچ regression به کلاس‌های باگ زیر نیاید

---

## 0. HARD RULES

1. Live tree = `F:\backup`. Improve, don't rewrite. بدون بازنویسی gateway/center.
2. Secret / API key / initData خام در commit، لاگ، HANDOFF، evidence ممنوع.
3. `git add -A` ممنوع. فقط فایل‌های مربوط. Commit فقط اگر مالک بگوید.
4. WORKLOCK: `run_all.py` · `wiring.py` · `center.py` · `orphan_scan.py` — بدون نیاز
   ثبت تست را گزارش کن؛ ادیت گسترده نکن.
5. Fail-closed روی effect بیرونی؛ collab = draft · `external_effect=false`.
6. Memory ingest `may_authorize=false` را دست نزن.
7. Kill-switch / OTLP remote / money per-action approval را برندار.
8. حدس ممنوع: هر ادعا با شاهد فایل / تست / flags-loaded / paid-calls.
9. بعد از هر فیکس مسیر chat: **gateway را RESTART-PROCESS کن** و PID را گزارش بده.
10. مالک باید مینی‌اپ را ببند/باز کند تا `app.js` نسخهٔ hashed تازه بگیرد — این را
    در گزارش نهایی صریح بنویس.

---

## 1. GROUND TRUTH — وضعیت مورد انتظار بعد از جلسهٔ ۱۲/۰۸

| لایه | انتظار |
|------|--------|
| `OCTOPUS_WIRE_COLLAB` | `1` |
| `OCTOPUS_COLLAB_USE_MODEL` | `1` |
| `TASK_TIERS["collab_chat"]` | `"secondary"` → budgets `reason` = DeepSeek |
| `CORTEX_LOCAL_FIRST` | `1` برای بقیه؛ **برای `collab_chat` باید skip شود** |
| collab fallback به `local:qwen*` | **ممنوع** |
| `AUTH_MAX_AGE_S` | ≥ 3600 (env `OCTOPUS_MINIAPP_AUTH_MAX_AGE_S`) |
| inject JS | فقط `__OCTOPUS__.wire_collab` / `collab_use_model` — **بدون `window.fetch` wrapper** |
| کلاینت `apiPost` timeout | collab ≥ 60s · ask ≥ 45s |
| سرور `COLLAB_TIMEOUT_S` | ≥ 55s؛ روی timeout → `owner-console.reply.v1` با `kind=timeout` (نه 504 خام) |
| footer UI موفق | `secondary:deepseek-v4-flash` (یا model_source معادل DeepSeek) |
| footer UI شکست | هرگز `local:qwen2.5*` برای collab_chat |

فایل‌های کانونی:

```
_ops/telegram_center/miniapp_gateway.py
_ops/telegram_center/miniapp/app.js
_ops/owner_console/conversation.py
_ops/owner_console/collaborator.py
_ops/owner_console/collab_model_adapter.py
_ops/owner_console/status.py
_ops/cortex/model_router.py
_ops/tool_request.py
_ops/OCTOPUS-flags.cmd
_ops/tests/test_miniapp_gateway.py
_ops/owner_console/tests/test_conversation.py
_ops/tests/test_collab_components.py
_ops/RESTART-PROCESS.ps1
```

---

## 2. کاتالوگ باگ‌های واقعی این جلسه (باید همه‌شان regression داشته باشند)

### B1 — Auth 403 روی POST `/api/collab`
- **نشانه:** GETها `authed=True`، POST `owner_auth_required`.
- **علل واقعی:** (الف) `AUTH_MAX_AGE_S=300` منقضی؛ (ب) injectی که `window.fetch` را
  بازنویسی می‌کرد و header `X-Tg-Init-Data` را روی POST می‌کشت؛ (ج) تفاوت
  `_read_api_authorized` (گاهی gate خاموش = True) vs POST که همیشه HMAC می‌خواهد.
- **ثابت شده:** TTL پیش‌فرض 3600؛ inject فقط config؛ `_get_header` case-insensitive.
- **Regression لازم:** POST با init-data معتبر → 200؛ بدون header → 403؛
  stale auth_date → 403؛ inject فاقد `fetch=` / `window.fetch`.

### B2 — Stub «موانع چیست» را نمی‌فهمید
- **نشانه:** clarify پیشنهاد می‌داد «موانع چیست؟» بعد همان را clarify می‌کرد.
- **علت:** `_BLOCK` فقط `چه.*مانع`؛ «موانع چیست» و حتی `handle("موانع")` از callback جا می‌افتاد.
- **ثابت شده:** `_BLOCK` شامل `مانع|موانع`؛ `_META_MISS` برای «چرا نمیفهمی»؛ `_GREET` برای سلام/سلان.
- **Regression:** `موانع چیست` / `موانع` / `سلام` / `سلان` / `چرا نمیفهمی` → kinds درست.

### B3 — Ask روی «در حال فکر کردن» می‌ماند
- **نشانه:** حالت Ask + ollama hang؛ UI بدون `.catch`/abort کافی.
- **ثابت شده:** AbortController؛ ask brain timeout کوتاه؛ collab-fallback؛ پیام خطای واضح.
- **Regression:** apiPost abort → `client_timeout`؛ UI pending را پاک کند.

### B4 — `CORTEX_LOCAL_FIRST` دزدی DeepSeek (بحرانی)
- **نشانه:** footer `local:qwen2.5:latest`؛ جواب بی‌ربط دربارهٔ لید نقاشی/پول.
- **علت:** `collab_chat=secondary` + LOCAL_FIRST=1 → qwen quality-gate پاس → هرگز DeepSeek.
- **ثابت شده:** skip LOCAL_FIRST برای `task=="collab_chat"`؛ ممنوع بودن fallback نهایی به local برای collab_chat.
- **Regression اجباری:** با `CORTEX_LOCAL_FIRST=1` و mock local که متن بلند برمی‌گرداند،
  `ask("collab_chat", ...)` **نباید** `tier=local` / `local_first=True` برگرداند وقتی
  DeepSeek/paid در دسترس است؛ و اگر paid fail شد → `ok=False` نه qwen.

### B5 — `client_timeout` / `bad_json · HTTP 504`
- **نشانه:** DeepSeek ۲۰–۳۰ث؛ کلاینت ۱۵ث abort؛ یا 504 با بدنهٔ غیرقابل parse.
- **ثابت شده:** کلاینت ۶۰ث؛ سرور ۵۵ث؛ timeout → reply.v1 با kind=timeout و HTTP 200.
- **Regression:** مسیر timeout در gateway schema رسمی برمی‌گرداند؛ تست parse در JS یا قرارداد.

### B6 — import اشتباه adapter
- **نشانه:** `ModuleNotFoundError` از `from cortex.model_router import ask`.
- **ثابت شده:** `import model_router` با path تخت (`cortex/` روی sys.path).
- **Regression:** `_default_ask` در تست واقعی/integration بدون package `cortex`.

### B7 — حلقهٔ tool_request روی «نمی‌دانم»
- **نشانه:** کارت رد می‌شد چون cost < 12 حرف / «نمی‌دانم».
- **ثابت شده:** `_normalize_cost`؛ پرامپت دیگر «بگو نمی‌دانم» را تشویق نمی‌کند.
- **Regression:** `t_unknown_cost_is_normalized_not_looped`.

### B8 — clarify/status سنگین → حس «کار نمی‌کند»
- **علت:** `catalog.discover()` اول هر handle؛ `unified` دوبار در clarify.
- **ثابت شده:** intent سریع قبل از catalog؛ cache ۸ث `_unified`؛ `_self_context` سبک.
- **Regression/perf smoke:** `سلام` < 0.5s بدون مدل؛ blockers با cache گرم سریع.

### B9 — عکس بدون کپشن در DM بن‌بست
- **ثابت شده:** پیام vision + یک خط از blockers.
- **Regression اختیاری:** unit روی متن capture path.

---

## 3. ماموریت اجرایی (به ترتیب — بدون پرش)

### فاز A — Deep-scan فقط‌خواندنی (گزارش اول، قبل از ادیت)

1. بخوان و جدول کن: flags-loaded برای `miniapp-gateway` / `center` / `cortex`
   (`OCTOPUS_COLLAB_USE_MODEL`, `CORTEX_LOCAL_FIRST`, `AUTH_MAX_AGE`, `WIRE_COLLAB`).
2. `rg` برای: `window.fetch` در inject؛ `collab_chat`؛ `LOCAL_FIRST`؛
   `from cortex.model_router`؛ `AUTH_MAX_AGE`؛ `client_timeout`؛ `_normalize_cost`.
3. آخرین ۲۰ خط `state/paid-calls.jsonl` برای `task=collab_chat` — ok/model/tier.
4. لیست شکاف‌ها نسبت به جدول Ground Truth §1.

خروجی فاز A: `FINDINGS.md` زیر
`_ops/state/adr-033/reports/DEEP-SCAN-COLLAB-2026-08-12/` با ستون
`bug_id | status(fixed/open/regress-missing) | evidence`.

### فاز B — بستن شکاف‌ها (کد + تست)

برای هر `open` یا `regress-missing`:

1. فیکس minimal (Improve, don't rewrite).
2. تست regression هم‌نام با bug_id در همان PR منطقی.
3. اجرای هدفمند:
   - `owner_console/tests/test_conversation.py`
   - `tests/test_miniapp_gateway.py`
   - `tests/test_collab_components.py`
   - `tests/test_tool_request.py` (اگر ابزار لمس شد)
4. اگر تستی LOCAL_FIRST+collab ندارد → **حتماً اضافه کن** (B4).

### فاز C — Verify زنده (اجباری)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File F:\backup\_ops\RESTART-PROCESS.ps1 gateway
powershell -NoProfile -ExecutionPolicy Bypass -File F:\backup\_ops\RESTART-PROCESS.ps1 status
```

سپس پروب پایتون (بدون چاپ secret):

```text
collaborator.handle("راجب اختاپوس چی میدونی")
→ model_source شامل deepseek (نه local:qwen)
→ متن به قلب/قشر/پا/گیت اشاره کند یا از CURRENT-TRUTH/blockers بیاید
→ elapsed گزارش شود (انتظار تقریبی ۱۰–۴۰s)
```

پروب منفی:

```text
با CORTEX_LOCAL_FIRST=1 و mock local «پاس‌کیفیت»، collab_chat نباید local برگردد
اگر DeepSeek عمداً fail شود → ok=False یا stub deterministic، نه qwen hallucinate
```

### فاز D — ضدباگ UI قرارداد

چک کن `app.js`:

- [ ] AbortController روی apiPost
- [ ] collab timeout ≥ 60000
- [ ] پیام خطا برای timeout/504 دیگر کاربر را به «همکار فوری است» گمراه نکند
  (آن جمله وقتی stub بود درست بود؛ الان DeepSeek است — متن را صادق کن)
- [ ] وقتی `kind===timeout` از schema رسمی، متن `r.text` نشان داده شود نه «جواب نگرفتم»
- [ ] cache-bust HTML برای app.js همچنان hash دارد

### فاز E — خودآگاهی / کشف مشترک

`_self_context` باید:

- سبک بماند (< ~۲۰۰ms ideally؛ بدون double snapshot سرد)
- secret نداشته باشد
- برای سؤال‌های «خودت کی‌ای / از چی تشکیل شدی / موانع» کافی باشد
- اگر فایل غایب بود fail-soft

اختیاری اما ارزشمند: یک intent در `conversation.py` برای
`خودآگاه|خودت را بهتر|از چی تشکیل` → پاسخ ساختاری + اجازهٔ enrich مدل.

### فاز F — صداقت دربارهٔ «خودبهبودی خودکار»

اگر مالک پرسید «دو ساعت اخیر خودش بهتر شده؟»:

- فقط از شواهد: `paid-calls.jsonl` · `self-loop-ingest.jsonl` · improve apply receipts ·
  code apply commits · flags-loaded boot times
- **ادعا نکن** beat++ = هوش بیشتر
- اگر paid deep اغلب `ok=False` است، صریح بگو مغز پولی برای deep خراب/بسته‌است
  ولی collab_chat جداست

---

## 4. معیار پذیرش نهایی (Definition of Done)

همهٔ این‌ها باید هم‌زمان سبز باشند:

1. تست‌های هدفمند بالا سبز.
2. Regression B4 موجود و سبز.
3. پروب زنده collab → `deepseek` در model_source.
4. inject فاقد fetch wrapper.
5. AUTH TTL ≥ 3600 در flags-loaded gateway.
6. timeout مسیر collab → UI-readable reply.v1 (نه bad_json).
7. `موانع چیست` → blockers؛ `سلام` → intro؛ نه clarify غلط.
8. HANDOFF یک بولت wikilink/خلاصه + مسیر evidence.
9. گزارش پایانی شامل: Fixed / Remaining / Verify commands / «مالک مینی‌اپ را ببند/باز کن».

---

## 5. محدودهٔ منفی (وارد نشو مگر مالک بگوید)

- روشن کردن OTLP remote · برداشتن kill-switch · money auto-send
- بازنویسی کامل MiniApp یا جایگزینی Telegram
- Arm کردن مدل‌های دیگر به‌جای DeepSeek بدون شاهد
- Commit کلید / `.env`
- «نصب پکیج DeepSeek» — لازم نیست؛ API از قبل در `debate/client.py` + budgets است

---

## 6. قالب گزارش پایانی به مالک (فارسی، کوتاه)

```text
## Verdict
(یک خط: مسیر حرف زدن سالم است / نیست)

## Bugs closed
- B# …

## Still open
- … یا هیچ

## Live proof
- model_source=…
- elapsed=…
- gateway pid=…

## Owner action
مینی‌اپ را ببند و باز کن → همکار → سؤال تست
```

---

## 7. پرامپت یک‌خطی برای شروع ایجنت

```text
این فایل را قانون کار خودت بدان:
00 - Inbox/2026-08-12 MEGAPROMPT — Senior Deep-Scan MiniApp Collab DeepSeek.md

فاز A→F را کامل اجرا کن. اول FINDINGS، بعد فیکس+regression، بعد RESTART gateway،
بعد پروب زنده. هدف: collab فقط DeepSeek، صفر qwen-dزدی، صفر 403/504/bad_json/clarify-غلط
روی مسیرهای شناخته‌شدهٔ جلسهٔ ۲۰۲۶-۰۸-۱۲. Improve don't rewrite. Secret commit نکن.
```

---

## 8. زمینهٔ مالک (انگیزه)

مالک می‌خواهد با اختاپوس **حرف بزند**، حرفش را بفهمد، و با هم کشف کنند اختاپوس
از چه تشکیل شده. پکیج دانلودی نمی‌خواهد — DeepSeek API از قبل هست.
هر جوابی با `local:qwen` یا clarify الکی یا timeout خام = شکست ماموریت.
