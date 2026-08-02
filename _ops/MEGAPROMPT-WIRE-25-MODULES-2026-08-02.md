---
type: megaprompt
project: "[[04 - Architect System/architect/PROJECT]]"
status: active
tags: [octopus, wiring, blackbox, fix, phased]
created: 2026-08-02
updated: 2026-08-02
---

# مگاپرامپت — وصلِ ۲۵ ماژولِ نیمه‌ساخته به ارگانیسمِ زنده

> این سند برای **ایجنتِ سازنده** نوشته شده. ۲۵ ماژولِ `_ops/` ساخته شده‌اند،
> تستِ سبز دارند، ولی در هیچ مسیرِ productionای صدا زده نمی‌شوند (دستهٔ C در
> [[_ops/MEGAPROMPT-BLACKBOX-SCAN-2026-08-02|اسکنِ جعبهٔ سیاه]]). این مگاپرامپت
> آن‌ها را در ۵ فازِ وابسته می‌چیند و برای هر کدام **یک خطِ وصل‌کردن** می‌دهد.

---

## ۰ · این ماشین هنگ می‌کند (این را نخوان)

دو آنتی‌ویروس روی `F:\backup` فعال‌اند. هر فایل ۳-۶ms. یک workflow با ۱۱ ایجنت
لپ‌تاپ را خواباند. **قواعد:**
1. از `_ops/` شروع کن، نه از ریشه. هرگز `find`/`du`/`rglob` از `F:\backup`.
2. از `Grep`/`Glob` استفاده کن. هر فرمان زیر ۶۰ ثانیه.
3. حداکثر ۴ ایجنتِ همزمان.
4. **هرگز فلگ را عوض نکن، پروسه را ری‌استارت نکن، git commit نکن** (مگر با
   `OWNER_AUTH`). تو فقط می‌سازی و تست می‌کنی؛ مسلح‌سازی و ری‌استارت کارِ مالک است.

---

## ۱ · ریشهٔ الگو — چرا ۲۵ تا وصل نیستند

ساخت و وصل دو کارِ مجزای روی دو فایلِ متفاوت‌اند. ماژول را در `_ops/legs/`
می‌سازی، ولی وصل‌کردنش یعنی ویرایشِ `center.py` یا `wiring.py` یا `organism.py` —
که در این هفته همیشه دستِ یک سشنِ موازی بود. پس ایجنت ماژول را می‌سازد، تستش
سبز می‌شود، ولی وصل به «بعد» می‌رود و بعد هیچ‌وقت نمی‌رسد.

**قاعدهٔ این مگاپرامپت:** هر ماژول تا وقتی وصل‌نشده‌است «تحویل‌نشده» است. سبزیِ
تست به‌تنهایی کافی نیست — باید **اثرِ observable** در ORGANISM-STATE یا کارتِ
تلگرام نشان دهی.

---

## ۲ · پنج فاز (به ترتیبِ وابستگی — فازها را قاطی نکن)

### فاز ۱ — مسیرِ لید (۱۲ ماژول، خطرناک‌ترین — چون transport مسلح است)

> ⚠️ `OCTOPUS_WIRE_LEAD_OUTBOUND=1` و `OCTOPUS_SMTP_USE_GMAIL=1` در هر ۴ پروسه
> روشن‌اند. هر اشتباه در این فاز می‌تواند ایمیلِ واقعی بفرستد. **اول قفلِ
> قانونی، بعد بقیه.**

| # | ماژول | یک خطِ وصل | اولویت |
|---|---|---|---|
| ۱ | `legs/lead_suppression.py` | ✅ وصل شد (cd6eebf) | انجام‌شده |
| ۲ | `legs/lead_effect_gate.py` (`authorize`) | `center.py` دکمهٔ ✅ را به `authorize(eid,lid,token)` سیم کند | 🔴 اول |
| ۳ | `legs/lead_card.py` | `center.py` کارتِ لید را از `lead_card.render` بیاورد (پشتِ `OCTOPUS_WIRE_LEAD_CARD_CONTACT`) | بالا |
| ۴ | `legs/lead_first_reply.py` | پيش‌نویس روی کارت نشان داده شود (الان بی‌خواننده) | بالا |
| ۵ | `legs/lead_leg_inbox.py` | persistence path به lead_discovery وصل شود | متوسط |
| ۶ | `legs/consent_gate.py` | predicateها به lead_email_intake وصل شوند | متوسط |
| ۷ | `legs/speed_to_lead.py` | first-response timer به lead pipeline وصل شود | متوسط |
| ۸ | `legs/claims_backfill.py` | به accounting/attribution وصل شود | پایین |
| ۹ | `legs/deposits_export.py` | به قلبِ پول وصل شود | پایین |
| ۱۰ | `legs/ingest_adapter.py` | به تماس‌های بیرونی وصل شود | پایین |
| ۱۱ | `legs/raw_store.py` | به مسیرِ نقد وصل شود | پایین |
| ۱۲ | `legs/recon.py` | به accounting reconciliation وصل شود | پایین |

**قانونِ فاز ۱:** تا `authorize` وصل نشده، هیچ وصلِ دیگری ایمیل نمی‌فرستد —
و این درست است. ولی لحظهٔ وصل، هر چیزِ دیگر هم زنده می‌شود. پس قبل از وصلِ
`authorize`، مطمئن شو suppression (۱) کار می‌کند.

### فاز ۲ — مسیرِ mining (۴ ماژول — ✅ نیمه‌انجام‌شده)

| # | ماژول | یک خطِ وصل | وضعیت |
|---|---|---|---|
| ۱۳ | `legs/mining_card.py` | ✅ وصل شد به `render.py` (a7a8504) | انجام‌شده |
| ۱۴ | `legs/mining_stop_intent.py` | ✅ وصل شد به `tg_mining` (3158ae8) | انجام‌شده |
| ۱۵ | `legs/mining_swap_card.py` | ✅ وصل شد به `tg_mining` (3158ae8) | انجام‌شده |
| ۱۶ | `legs/mining_switch_receipt.py` | wiring آن رویدادِ switch را صدا بزند (هنوز صداکنندهٔ production ندارد) | باز |

### فاز ۳ — کورتکس / خودآگاهی (۵ ماژول)

| # | ماژول | یک خطِ وصل |
|---|---|---|
| ۱۷ | `cortex/depth_guard.py` | در چرخهٔ cortex، ناوردیِ ضدِ جعبه‌سیاه را اجرا کند |
| ۱۸ | `cortex/indicator_scorecard.py` | به داشبوردِ `/x` یا beat اضافه شود |
| ۱۹ | `self_insight.py` | از یافته به فرضیه در چرخهٔ epistemics |
| ۲۰ | `metrics/metric_separation.py` | جایگزینِ متریکِ درهم در heartbeat |
| ۲۱ | `legs/knowledge_leg.py` | از `__import__` به importِ صریح در wiring (marginally-wired → wired) |

### فاز ۴ — گاردِ امنیتی + والکتر (۳ ماژول)

| # | ماژول | یک خطِ وصل |
|---|---|---|
| ۲۲ | `arm_gate.py` | 🔴 `wiring.py` آن را import کند نه فقط فلگش را بخواند — گاردِ defense-in-depth که کور شده |
| ۲۳ | `vault_updater*.py` (۳ فایل) | pipeline را به cortex/apply وصل کند (پشتِ فلگِ APPLY_MERGE که **خاموش** می‌ماند) |

### فاز ۵ — ابزارِ تلگرام + بقیه (۴ ماژول)

| # | ماژول | یک خطِ وصل |
|---|---|---|
| ۲۴ | `tg_send_audit.py` · `tg_trace.py` · `tg_receive_probe.py` | به کارتِ `/x` یا doctor وصل شوند (ابزارِ ممیزی) |
| ۲۵ | `legs/ziman_biology.py` · `legs/books_xero.py` · `legs/agent_gateway_http.py` · `legs/sync_health.py` | skeletonهای first-draft — رأیِ مالک: وصل، آرشیو، یا تعویق |

---

## ۳ · معیارِ «تحویل‌شده» (بدونِ این، کار پذیرفته نیست)

برای هر ماژول، سه شاهد:
1. **اثرِ observable:** تغییر در `ORGANISM-STATE.json` یا کارتِ تلگرام یا خروجیِ
   CLI — نه فقط سبزیِ تست.
2. **جهش‌آزمایی:** فیکس را برگردان → تستِ مربوطه قرمز شود. بین جهش‌ها
   `__pycache__` را پاک کن.
3. **صداقت:** اگر مسیرِ end-to-end اثبات‌نشده (مثلاً نودِ زنده لازم دارد)، صادقانه
   بنویس «اثبات‌نشده».

---

## ۴ · مرزهای سخت

- **D-10/D-11:** هر swap/withdraw = HARD_STOP، فقط انسان. `authorize` فقط
  «تأییدِ مالک ثبت شد» می‌گوید، اجرا نمی‌کند.
- **D-20:** SSH به نودها ممنوع. توقف از مسیرِ ثبتِ نیت.
- **هیچ‌چیز نساز مگر در فازِ مشخص‌شده‌اش.** قاطی نکن.
- **هرگز فلگ را روشن نکن.** تو فقط وصل می‌کنی؛ مسلح‌سازی = `OWNER_AUTH: ARM FLAG`.
- **هرگز ایمیل نفرست.** transport مسلح است.
- **حریمِ خصوصی + راز** (همان منشور).

---

## ۵ · خروجیِ مورد انتظار

برای هر فاز: گزارشِ «فازِ N تمام شد / نیمه / باز» با اثباتِ هر ماژول.
به‌روزرسانیِ حافظه: `Active Context` و `Progress` پروژهٔ مرتبط در پایانِ هر فاز،
و یک ورودی در `01 - Dashboard/HANDOFF.md` (فقط wikilink، زیرِ ۲۰۰ خط).
