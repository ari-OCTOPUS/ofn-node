---
tags: [ofn, handoff, status]
aliases: [وضعیت زنده, Handoff]
updated: 2026-08-10
---

# HANDOFF — برای جلسهٔ بعدی

**پیوندها:** [[INDEX]] · [[CLAUDE]] · [[DECISIONS]] · [[LESSONS-ZIMAN]] · [[LESSONS-STUDIO]]

```
pytest      عدد زنده را با python3 tools/repo_baseline.py --tests بگیر
            (آخرین اندازه‌گیری ۲۰۲۶-۰۸-۱۰: ~۱۷۲۷ pass / ۵ skip)
preflight   عدد را از python3 -m ofn.preflight بگیر
boot        OK — ۳۰/۳۰ (NORMAL) · memory.sqlite هم در quick_check
گیت‌ها       secret_rotation 🔒 · partner_precondition 🔒 · miner_isolation 🔒
WIRE        outbound خاموش · email/publish در env روشن ولی کد Python نمی‌خواندشان
            (امنیت از outbox + store-layer status تأمین می‌شود، نه از این پرچم‌ها)
بات‌ها       ziman ✅ · lead ✅ · studio/studio_partner ✅ · owner ✅ · hypno ✅
            Bluetooth هم اکنون کار می‌کند (ap6256-bt.service, hci0 UP, BT 5.0)
allowlist   owner=۱ · lead=۱ · studio=۲ · ziman=۱
سرویس‌ها     ofn · hypno-fugu-mini · cloudflared · dropbear  →  هر چهار active
            ofn-alert.service نصب شد (OnFailure=ofn-alert روی ofn.service)
دامنه‌ها     panel/ziman/lead/studio/app/hypno → همه ۲۰۰
UNIFY       fugu_core (auth/scrub/brain/memory) + memory.sqlite سه‌لایه
            مغز مشترک Sakana (fugu) برای OFN + hypno · pack hypno (tenant ۴)
            quota ۳۵/۳۵/۲۰/۱۰ = ۱.۰۰ · ۱۳۲ chunk shared knowledge
جدید        kill switch ✅ · metrics زنده ✅ · alert (log+Telegram opt-in) ✅
            P0+P1 بسته (webhook harden · gates · inbox machine · backup verify)
```

---

## 📝 جلسهٔ ۲۰۲۶-۰۸-۱۰ — اجرای کامل COMPLETE-FINISH (فاز H تا M)

شش commit (`1a7010a` → `ac4af7b`) که مگاپرامت کامل‌کننده را بست — همهٔ
کارهای باز پروژه.

### فاز H — معماری تدریجی (1a7010a)
- http_api: `_OWNER_GET_TABLE` fast path (fallback کامل به if-chain)
- `Node.owner` facade (`owner_reads.py`) — seam برای extract آینده
- `tests/fixtures/renditions.py` — fixture مشترک (cross-test import حذف)
- studio.yaml: gate `capacity` اضافه شد (parity با ziman/lead)

### فاز I — یافته‌های باز P2 (0120735)
- ۱۷: shell/boot throttle (۱۰/۶۰ ثانیه + coalesce) ✅
- ۱۹: LIKE ESCAPE سمت سرور ✅ · ۳۶: `.part` sweeper ✅
- ۶۵: ARIA tabs ✅ · ۶۶: lead poll ۶۰s + visibility stop ✅
- ۶۸: dedup recent leads ✅ · ۸۶: service_area comment صادق ✅
- ۸۷: پیام کارمزد کانال کامل‌تر ✅

### فاز J — یافته‌های P3 (5ff297c)
- ۲۰: kill switch RAM — DecisionRecord + یادداشت panel
- ۳۳: journal_size_limit اندازه‌گیری شد (پایدار ~۱.۲MB)
- ۳۴: power-cut simulation سبز — boot checkpoint امن
- ۳۵: RETENTION.md runbook · ۳۸: brain queue RAM — DecisionRecord

### فاز K — یافته‌های P4 (e8ab725)
- ۱۳: تست معماری mutation↔ledger — **۷ شکاف واقعی پیدا و بسته شد**
  (send_to_outbox، attach_media، file_media، set_draft_labels،
  set_media_labels، record_felt، update_studio_assistant)
- ۱۸: session sig ۱۲۸-bit — DecisionRecord + تست pin
- ۶۷: LEAD.offset حذف · ۷۵: تست Persian dynamic labels
- ۹۰: product_photos DecisionRecord · ۹۴: megaprompt test inventory align
- ۹۸: API namespace glossary

### فاز L — UNIFY: hypno edge داخل OFN (818b426)
- `ofn/kernel/edge.py` + `safety.py` (کپی از hypno، provenance مستند)
- متدهای Node: hypno_edge_decision/daily/history
- مسیرها: POST/GET `/api/v1/hypno/edge/*` (auth دار)
- **hypno همچنان روی ۸۸۹۵ فعال است** (۹۰ تست سبز) — غیرفعال‌کردن
  سرویس قدم دوم با حکم آری (systemd change)

### فاز M — vendor مارکتینگ (ac4af7b)
- `VENDOR-EVALUATION.md`: ۴ کاندید سنجیده شد — پیشنهاد: Telegram اول،
  Bluesky pilot، Instagram با نیاز واقعی، Mailchimp رد
- `platforms/telegram_readonly.py`: skeleton read-only (publish غایب)
- **منتظر حکم آری** — هیچ vendor واقعی وصل نشده

### صحت نهایی
```
pytest      1767 passed · 5 skipped (تأیید: tools/repo_baseline.py --tests)
boot        OK — 31 checks · state_dir 0700
سرویس‌ها     ofn + hypno + cloudflared active · هر ۵ پورت 200
WIRE/gates  خاموش/بسته · sender ساخته نشد · UI حذف نشد
CRIT-1      8090 بدون listener
```

### مانده برای حکم آری
- **غیرفعال‌کردن hypno-fugu-mini.service** (قدم دوم UNIFY)
- **vendor رسمی** (از VENDOR-EVALUATION)
- kill switch بادوام · retention با پاک‌کردن · حذف product_photos
- Telegram alert · systemd unit changes

---

## 📝 جلسهٔ ۲۰۲۶-۰۸-۱۰ — اجرای کامل P1→P4 (فاز A تا G)

هفت commit (`fd4aa03` → `8707f8f`) که فازهای A–G مگاپرامپت P1-TO-P4 را بست.

### فاز A — امنیت connector (fd4aa03)
- ReplayGuard: digest کل initData، نه suffix ۶۴
- platforms: `broken_platforms()` جدا از available
- وب‌هوک: tenant از path + cross-check با Host (mismatch → 403)
- owner_observability docstring صادقانه
- OFN_WIRE_OUTBOUND: intent-only تا sender
- `require_release_context()` — گارد ساختاری sender آینده
- چت استودیو: scrub قبل از persist (PII)

### فاز B — inbox state machine (7783589)
- `claim_next()` اتمیک: pending → processing (BEGIN IMMEDIATE)
- mark_processed/mark_failed با guard وضعیت (bool برمی‌گردانند)
- `recover_stale()`: processing قدیمی → held (ستون claimed_at + migration)
- `inbox_processor.py`: dry-run (فقط shape؛ هیچ outbound)
- `inbox_ledger_gaps` شمارندهٔ reconciliation در observability

### فاز C — ConnectorMetrics (3cc76ca)
- instance در build_node · record در handle_webhook (inbound/processed/rejected/failed)
- snapshot در observability
- panel drawInbox: counts همیشه؛ vendor chip جدا

### فاز D — backup/media (9eb699a)
- verify_backup: media count + bytes در برابر manifest
- backup(): required DB غایب → fail
- memory.sqlite در backup (حکم آری) + quick_check در boot
- attach_media rollback · delete_media tombstone
- `restore_media()` sandbox-tested

### فاز E — اسناد (efb45a1)
- HANDOFF header: اعداد ثابت → ارجاع به command
- IMPLEMENTATION-GAP-MATRIX: بخش connector/observability
- test_shell_contract: ۴ pin جدید
- `repo_baseline.py --verify`

### فاز F — چهار پنل (c5cc82b)
- panel: SDK defer + tg() تابعی · cursor خنثی · بدون raw JSON · KIND_FA
- lead: sheet a11y (dialog/Escape) · inline error به‌جای alert
- studio: STYLE_FA + ruleFa (بدون کلمه فنی، D-22)
- lead.yaml: وعدهٔ service_radius صادق شد

### فاز G — runbooks (7a1cf8a)
- docs/runbooks/: ۸ فایل (NTP/TUNNEL/RESTORE/INBOX-HELD/OUTBOX-HELD/
  WEBHOOK-SIGNATURE/RATE-SPIKE/SCHEMA-DRIFT) + test_runbook_coverage
- `inbox_backlog` flag در observability (depth ≥ ۱۰)
- ss 8090: بدون listener (CRIT-1 تمیز)

### فاز Z — بستن
- boot: memory.sqlite read-only check (8707f8f) — boot OK ۳۱/۳۱
- pytest ۱۷۳۳ pass · ۵ skip · هر ۵ پورت ۲۰۰

### صحت نهایی
```
pytest      1733 passed · 5 skipped (تأیید: tools/repo_baseline.py --tests)
boot        OK — 31 checks · state_dir 0700 (chmod با حکم آری)
سرویس‌ها     ofn active · هر ۵ پورت ۲۰۰
WIRE/gates  خاموش/بسته · sender ساخته نشد · UI حذف نشد
memory      در backup scope (حکم آری) + read-only boot check
```

### آنچه عمداً نشد / منتظر حکم
- HMAC واقعی vendor (noop_until_vendor — runbook WEBHOOK-SIGNATURE)
- restore زندهٔ رسانه (کد + sandbox آماده؛ اجرا فقط با حکم)
- Telegram alert · systemd unit changes · kill switch بادوام
- فاز H (معماری تدریجی) — برای جلسهٔ بعد اگر A–G سبز ماند

---

## 📝 جلسهٔ ۲۰۲۶-۰۸-۱۰ — مگاپرامپت ایجنت بعدی (DeepSeek V4 Fast)

دو سند ذخیره شد برای ادامهٔ کامل P1→P4 بعد از P0:

| سند | نقش |
|---|---|
| [[MEGAPROMPT-P1-TO-P4-COMPLETE]] | نقشهٔ کامل فازها، یافته‌ها، حکم‌ها، معیار پذیرش |
| [[AGENT-NEXT-DEEPSEEK-V4-FAST]] | اسکریپت بایت‌به‌بایت بلوک ۰…۱۶ برای DeepSeek V4 Fast |

Canvas مرجع: `~/.cursor/projects/home-ari/canvases/ofn-100-findings.canvas.tsx`  
INDEX به‌روز شد. **کار بعدی ایجنت:** اجرای `AGENT-NEXT-DEEPSEEK-V4-FAST` از بلوک ۱.

قلم باز نیازمند حکم آری: `chmod 0700 /home/ari/.local/share/ofn` (فعلاً `0755` + preflight warn).

---

## 📝 جلسهٔ ۲۰۲۶-۰۸-۱۰ — رفع P0 از ممیزی صد یافته

چهار commit (`51a27ad` → `898fa6d` → `08711d0`) که ۱۵ یافتهٔ P0 را بست.

### C۱ — ایمن‌سازی مسیر وب‌هوک (یافته‌های ۱، ۴، ۵، ۱۰، ۱۵، ۲۹، ۲۷)

- **raw body ذخیره نمی‌شود.** ستون `raw_body` با `body_sha256` + `body_size`
  جایگزین شد. فقط هش و اندازه نگه داشته می‌شود — نه متن خام، نه PII.
- **bare except تخصصی شد.** فقط `sqlite3.IntegrityError` (duplicate) False
  برمی‌گرداند؛ خطاهای واقعی DB (disk full، corrupt) propagate می‌شوند.
- **rate limiter وصل شد.** یک instance process-scoped در handle_webhook.
  ۴۲۹ + Retry-After بعد از limit. Bucket cap (۱۰۲۴) با FIFO eviction.
- **ترتیب inbox → ledger.** اگر inbox.store شکست بخورد، ledger نوشته نمی‌شود.

### C۲ — اعمال گیت و kill switch (یافته‌های ۲، ۳، ۶، ۱۴)

- **_gate_enqueue helper.** هر چهار مسیر مستقیم enqueue (publish_draft،
  send_to_outbox، send_lead_reply، send_lead_quote) حالا از یک helper مشترک
  عبور می‌کنند که kill switch را اول چک می‌کند.
- **kill switch در owner_decide.** اگر kill روشن باشد، approve رد می‌شود
  (reject همچنان کار می‌کند — چیزی نمی‌فرستد).
- **partner_precondition در default closed gates.** اضافه شد به config.load().
- **stub fail-closed.** owner_decide و submit_answer وقتی وصل نیستند ok=False
  برمی‌گردانند، نه ok=True.

### C۳ — boot زیمان، store close، healthz، outbox guard (یافته‌های ۲۴، ۲۶، ۴۳، ۷۶–۸۰)

- **return زودهنگام ziman حذف شد.** خط `return;` بعد از `await load()` که
  setDots/safe_mode/draw را غیرقابل‌دسترس می‌کرد. تست رگرسیون اضافه شد.
- **close() همهٔ storeها.** اکنون products/studio/consent/audience/marketing/
  assistant هم بسته می‌شوند، نه فقط چهارتای اصلی. خطاها log می‌شوند.
- **healthz صادقانه.** docstring می‌گوید liveness-only است. readiness واقعی
  در /api/v1/owner/observability.
- **outbox state guard.** mark_sent فقط از in_flight → sent. mark_failed از
  pending/held/in_flight. mark_sent روی pending بی‌اثر است (صفر ردیف).

### C۴ — state_dir mode (یافته‌های ۱۶، ۲۵، ۵۲)

- **makedirs mode=0o700.** دایرکتوری state هنگام ساخت 0700 می‌شود.
- **preflight check.** اگر mode ≠ 0700 باشد، هشدار می‌دهد. auto-chmod نمی‌کند.
- **نکته:** دایرکتوری live فعلی 0755 است (از نصاب قدیمی). هشدار پیداست؛
  اصلاح با حکم آری (`chmod 0700 /home/ari/.local/share/ofn`).

### صحت
```
pytest      1688 passed · 5 skipped (تأیید: tools/repo_baseline.py --tests)
boot        OK — 30 checks passed (مهاجرت inbox در اولین restart اجرا شد، دومی سبز)
سرویس‌ها     ofn active · هر پنج مسیر ۲۰۰ · sabaapp ۲۰۰
curl        ziman: return حذف شد · setDots/draw حالا سرو می‌شوند
state_dir   0755 (هشدار پیداست؛ اصلاح با حکم آری)
outbox      تغییر نکرد
WIRE/gates  خاموش/بسته · partner_precondition اضافه شد
```

### آنچه عمداً نشد
- HMAC واقعی فعال نشد (هنوز vendor نیست؛ noop ایمن‌سازی شده باقی است)
- بازطراحی inbox/ledger atomicity (P1)
- تغییر systemd/backup/alert (نیازمند حکم)
- kill switch بادوام (P3، intentional)

---

## 📝 جلسهٔ ۲۰۲۶-۰۸-۱۰ — ارتقای چهار کنترل‌پنل (فاز ۲–۸)

### آنچه عوض شد

**بک‌اند جدید:**
- `GET /api/v1/owner/observability` — صندوق ورودی و وضعیت کانال‌ها
  (`node.owner_observability` + مسیر در `http_api` + wiring در `run.py`).
  owner-only، no-store، بدون راز یا متن خام وب‌هوک. ۱۰ تست جدید.

**panel.html (مالک):**
- کارت تازهٔ «صندوق ورودی — کانال‌ها» بعد از درِ خروج. تعداد پیام‌های رسیده
  per-tenant، حالت صادقانهٔ «هنوز فروشنده‌ای وصل نیست». از `refresh()` تغذیه
  می‌شود با `.catch` مستقل.

**lead.html (عباس):**
- برچسب اولویت از `score_detail.recommendation` (اولویت بالا / پیگیری کن /
  بعداً) به‌جای فقط عدد خام. توضیح مدل فارسی زیر هر کارت.
- empty-state گرم: جداسازی «فیلتر چیزی پیدا نکرد» از «هنوز لیدی نرسیده».

**studio.html (سبا):**
- `tg().setHeaderColor('#131114')` + `setBackgroundColor` در `shell()` —
  هدر تلگرام با پالت پوسته یکی شد.

**ziman.html (ملیحه):**
- empty-state قفسه خالی گرم‌تر شد با راهنمایی روی همان صفحه.

### آنچه عمداً دست‌نخورده ماند
- همهٔ بخش‌های panel.html (kill، صف تصمیم، میز نقاشی، metrics، outbox، لجر، سطوح)
- CRM، جستجو/فیلتر، جواب/قیمت، ثبت لید در lead.html
- آرشیو، گالری، چت، آپلود، مارکتینگ در studio.html
- فرم قطعه، قفسه، سؤال‌ها، عکس، toLatinDigits در ziman.html
- گیت‌ها، WIRE، outbox، رازها — هیچ‌کدام تغییر نکرد

### صحت
```
pytest        1662 passed · 5 skipped (تأیید: tools/repo_baseline.py --tests)
boot          OK — 29 checks (قبلاً ۲۸ بود، inbox اضافه شد)
سرویس‌ها       ofn active · هر پنج مسیر ۲۰۰ · sabaapp ۲۰۰
curl verify   صندوق ورودی در panel · score_detail در lead ·
              setHeaderColor در studio · empty warm در ziman — همه سرو می‌شوند
outbox        تغییر نکرد
journal       بدون SAFE MODE · بدون traceback · بدون فعالیت خروجی
```

---

## 📝 جلسهٔ ۲۰۲۶-۰۸-۱۰ — مگاپرامپت مارکتینگ + اسکن پنل‌ها + دستور ارتقای UI

### بک‌اند connector (انجام‌شده در کد)

کامیت `d140756`: inbox · correlation · inbound rate · HMAC verify ·
connector metrics · `POST /api/v1/webhooks/…` — بدون vendor واقعی و بدون
sender. خط پایهٔ تست را با `tools/repo_baseline.py --tests` بگیر
(snapshot حدود ۱۶۵۷ collected).

### اسناد

- [[MEGAPROMPT-MARKETING-PLATFORM-INTEGRATION]] — نقشهٔ مفهومی + فازها
- [[AGENT-NEXT-PANEL-UPGRADE]] — **دستورکار ایجنت بعدی برای چهار کنترل‌پنل**
- [[docs/handoffs/panel-scans-2026-08-10/INVENTORY]] — اسکن پایه

### چهار کنترل‌پنل — وضعیت UI

| پنل | فایل | نکته |
|---|---|---|
| مالک | `web/panel.html` | قوی است؛ inbox/observability هنوز در UI نیست |
| لید | `web/lead.html` | CRM روی boot؛ اولویت انسانی روی کارت ناقص/قابل‌بهبود |
| استودیو | `web/studio.html` | آرشیو/چت زنده؛ هدر تلگرام/خلاصهٔ انتشار قابل‌ادغام |
| زیمان | `web/ziman.html` | فرم قطعه سالم؛ اسم/empty-state را در ارتقا ادغام کن |

**قاعده برای ایجنت بعدی:** حذف ممنوع — فقط ادغام یا اضافه. اول اسکن زنده،
بعد panel → lead → studio → ziman.

### زیرساخت

NTP sync · cloudflared active · HTTPS ۲۰۰ در آخرین سنجش. دو `.bak-*`
untracked بماند.

---

## ✅ بستن جلسهٔ ۲۰۲۶-۰۸-۰۹ — سخت‌سازی دسترسی پشتیبان

### آنچه عوض شد — یک مجوز، روی یک دایرکتوری

یک دایرکتوری پشتیبانِ یک‌بارمصرف از `0755` به `0700` رفت. پیش و پس از تغییر،
metadata سنجیده شد: دایرکتوری واقعی بود، مالکش کاربر مالک، symlink نبود، و
بیرون از هر درخت گیتی قرار داشت.

**هیچ چیز دیگری لمس نشد:** نه هیچ artifact پشتیبانی، نه مالکیت، نه گروه، نه
ACL، نه سرویس، نه timer، نه job پشتیبان، نه مسیر restore، نه هیچ فایل
گیت‌خورده. mode فایل‌های داخل دایرکتوری هم عوض نشد — پیش و پس از تغییر
مقایسه شد و یکسان ماند. هیچ آرشیوی باز، استخراج، کپی یا خوانده نشد.

### دو چیزی که تأیید **نشدند** — و ادعا هم نمی‌شوند

**۱. بررسی از حساب غیرمالک انجام نشد.** انتظار می‌رود `0700` دسترسی غیرمالک
را ببندد، ولی این **استنتاج از بیت‌هاست، نه مشاهده**. به‌عنوان یک چک
انجام‌نشده ثبت می‌شود، نه یک چک سبز.

**۲. انتساب دسترسی به فایل: `not observable with currently enabled logs`.**
روی این برد لاگ file-access قابل‌انتساب فعال نیست. یعنی **نمی‌توان گفت
دسترسی‌ای رخ نداده** — فقط می‌توان گفت چیزی برای دیدنش وجود ندارد. هیچ
logging، audit یا ردیاب جدیدی هم برای این کار فعال نشد.

در بازهٔ جلسه، لاگ سرویس پشتیبان و OFN از نظر خطای مجوز، شکست پشتیبان و
فراخوانی restore بررسی شد: هیچ‌کدام دیده نشد و هیچ هشداری شلیک نکرد.

### وضعیت پس از تغییر

```
سرویس‌ها     هر سه فعال · هیچ ری‌استارتی انجام نشد
سلامت        هر چهار مسیر داخلی و هر چهار مسیر بیرونی سالم
tmpfs        تقریباً خالی · هیچ پوشهٔ موقت رهاشده‌ای نیست
outbox       خالی — مثل وضعیت تأییدشدهٔ قبلی
پرچم‌های خروجی بدون تغییر نسبت به وضعیت تأییدشدهٔ قبلی
suite        سبز · شمارش را با tools/repo_baseline.py --tests بگیر
journal      بدون SAFE MODE · بدون drift · بدون traceback · بدون فعالیت خروجی
```

### وضعیت تحقیق — دقیق

```
ziman / GiftMesh   corpus محلی وجود ندارد  →  ingestion مسدود
                   «۱۵۰۰+ منبع» unverified · نه مبنای طراحی، نه زمان‌بندی
lead               رجیستری‌اش metadata کانال است، نه corpus تحقیقاتی
                   (فیلد نشانی روی همهٔ رکوردها هست و روی همه خالی است)
hypno              فقط fixture فنیِ provenance-ضعیف · قابل استناد نیست
studio             corpus تحقیقاتی ندارد
```

هیچ ادعا، شاهد یا نتیجه‌ای بین tenantها منتقل نمی‌شود. مرجع نام‌گذاری و
مرزها: D-25 در [[DECISIONS]] و `docs/architecture/PORTFOLIO-TENANT-MAP.md`.

### ریسک باز

دایرکتوری مقصد job پشتیبان **در دامنهٔ این تغییر نبود و همچنان owner-private
نیست.** آنجا جایی است که نسخه‌های شبانهٔ دیتابیس‌ها می‌نشینند. تصمیمش با توست؛
من دست نزدم.

---

## ✅ جلسهٔ ۲۰۲۶-۰۸-۰۹ — واژگان پرتفوی، دید مالک، بهداشت تست

سه دستهٔ مستقل، سه کامیت جدا. `HEAD` این شاخه: `df927e7`.

### ۱) واژگان پرتفوی — D-25

یک پیش‌نویس مگاپلن با نام‌هایی رسید که با `packs/` نمی‌خواندند. حکم مالک ثبت
شد؛ جزئیاتش در [[DECISIONS]] است، اینجا فقط چیزی که برای کار روزمره لازم است:

```
GiftMesh Sydney   برند/خط عرضهٔ تنانت `ziman` — تنانت جدید نیست
lead              نقاشی ساختمان
studio            تنانت محتوای محدود
OFN               نام پلتفرم است، نه نام هیچ بیزنسی
hypno             تنانت واقعی · خارج از scope پرتفوی تا charter مالک
```

مرجع نام‌گذاری: `docs/architecture/PORTFOLIO-TENANT-MAP.md`. **قبل از افزودن یا
نام‌گذاری هر تنانت، بیزنس یا برند، اول D-25 و این نقشه را بخوان.**

### ۲) پنل مالک — مستقر شد

پنل حالا دید عملیاتی **فقط-خواندنی** دارد روی: وضعیت outbox · خلاصهٔ زنجیرهٔ
لجر · پیکربندی سطوح سرو‌شده · خط وضعیت مغز · حالت «اندازه‌گیری نمی‌شود» ·
و `hypno` که حالا برچسب دارد.

- **هیچ کنترل نوشتن/ارسال/انتشار/تأیید اضافه نشد.**
- **تبصره:** میز نقاشی (painting desk) فرم‌های POST دارد (leads, channels, modules, interactions, campaigns, accounts, tenders, vendors) — این عمدی و قدیمی است. «فقط‌خواندنی» در مگاپرامپت ناظر endpointهای جلسهٔ ۰۸-۰۹ (outbox/ledger/levels/brain) بود، نه کل POSTهای نقاشی.
- endpointهای خواندنی مالک همچنان احراز هویت می‌خواهند؛ بدون آن ۴۰۱ می‌دهند.
- HTML پنل موقع بوت خوانده می‌شود، پس ری‌استارت کنترل‌شدهٔ OFN لازم بود و
  با موفقیت انجام شد.

### ۳) بهداشت تست و صحت هشدار

- نشتی پوشهٔ موقت تست بسته شد؛ حالا هر پوشه صاحب دارد و قطعی پاک می‌شود.
- سه اجرای متوالی سبز، **بدون هیچ رشدی در `/tmp`**.
- تست هشدار دیگر رکورد crash ساختگی در لاگ هشدار زندهٔ اپراتور نمی‌نویسد و
  در زمان اجرای تست اصلاً نمی‌تواند به بیرون اطلاع بدهد.
- خط‌های ساختگی گذشته **پاک نشدند** — نگه داشته و یادداشت‌گذاری شدند. آن‌ها
  نه crash واقعی‌اند و نه هشدار خروجی؛ این‌طور تفسیرشان نکن.

### ۴) وضعیت زنده پس از ری‌استارت کنترل‌شده

```
HEAD              df927e7
pytest            ۱۵۹۵ سبز · ۵ skip (总数: ۱۶۰۰; تأیید: tools/repo_baseline.py --tests)
سرویس‌ها           ofn · ofn-boot · cloudflared  →  هر سه active
سلامت             loopback و HTTPS برای ziman · lead · studio · panel  همه سبز
SAFE MODE         نه · schema drift نه · traceback نه · فعالیت خروجی نه
outbox            پیش و پس از ری‌استارت خالی
پشتیبان           پیش از ری‌استارت گرفته و با manifest تأیید شد
```

### ۵) قواعد اپراتور — از این جلسه به بعد

```
شمارش تست/موجودی   python3 tools/repo_baseline.py --tests
                   در CLAUDE.md عدد ثابت ننویس
حافظهٔ موقت تست     tests.tmpdir.temp_dir(self) یا TemporaryDirectory صاحب‌دار
                   mkdtemp() بدون مدیریت، بیرون از helper ممنوع
```

**ری‌استارت OFN بعد از تغییر HTML**، به همین ترتیب: کل suite → بررسی نحوی
اسکریپت با node → preflight/health → پشتیبان → ری‌استارت با مهلت کران‌دار →
سلامت داخلی و خارجی → بررسی احراز هویت endpointها → مقایسهٔ outbox → journal.

### ۶) صف کار بعدی

- کار عملیاتی بعدی همچنان **راستی‌آزمایی موجودی تحقیق** و یک pilot ingestion
  کران‌دار برای `ziman`/GiftMesh است. هیچ corpus خامی به Fugu نمی‌رود و
  Architecture Lab هنوز فعال نمی‌شود.
- قلم باز: **`OCTOPUS_WIRE_*` به‌عنوان نام سندی در برابر enforcement واقعیِ
  قابل‌راستی‌آزمایی در مخزن.** تا وقتی تصمیم جداگانه‌ای بازبینی نشده،
  ممنوعیت‌های فعلی را تضعیف نکن.

---

## ✅ جلسهٔ ۲۰۲۶-۰۸-۰۸ (OPERATOR SAFETY) — دکمه اضطراری، مانیتورینگ، هشدار

سه قابلیت ایمنی مالک اضافه شد. همه زیر قواعد CLAUDE.md، بدون لمس راز،
بدون خروجی واقعی، با تست.

### ۱) کلید خاموشی (Kill Switch) — وصل شد

کلید خاموشی در معماری موجود بود ولی هیچ دکمه/endpoint/کدی برای روشن کردنش
وجود نداشت. حالا کامل شد:

- **engage سریع** (panic button، یک ضربه): `POST /api/v1/owner/kill`
- **release محتاطانه** (تأیید دو مرحله‌ای): `POST /api/v1/owner/kill/release`
- state در حافظه (fail-safe: restart = disengage)، audit در `release_switch_events`
- به ledger همه tenantها نوشته می‌شه (`KILL_SWITCH`)
- دکمه در هدر panel.html با بنر قرمز
- **۲۳ تست** در `tests/test_kill_switch.py` (kernel + node + HTTP + audit + idempotency)

فایل‌های تغییر: `ofn/node.py` (engage_kill, release_kill, _record_release_event),
`ofn/adapters/http_api.py` (۲ endpoint + session_id در Principal),
`ofn/adapters/marketing_store.py` (record_release_event),
`ofn/run.py` (wiring), `web/panel.html` (دکمه + بنر), `tests/test_kill_switch.py`.

### ۲) داشبورد سلامت برد (Metrics) — زنده

- ماژول `ofn/adapters/sysmetrics.py`: دما (۵ زون)، RAM، load، uptime، دیسک
- endpoint `GET /api/v1/owner/metrics` (owner-only)
- داشبورد در panel.html، هر ۳۰s با poll موجود به‌روز می‌شه
- رنگ دما: سبز < ۷۰°، زرد ۷۰-۸۰°، قرمز ≥ ۸۰° (throttle)
- هیچ cache‌ای نیست — metrics همیشه fresh خونده می‌شه

فایل‌های تغییر: `ofn/adapters/sysmetrics.py` (جدید), `ofn/node.py` (owner_metrics),
`ofn/adapters/http_api.py` (endpoint), `ofn/run.py` (wiring + state_dir),
`web/panel.html` (داشبورد).

### ۳) هشدار خرابی سرویس (Alert) — لایه‌ای

- `ofn-alert.service`: `OnFailure=` روی `ofn.service` (وقتی start limit پر شد)
- لایه ۱: لاگ محلی همیشه (`service-alerts.log`)
- لایه ۲: Telegram فقط وقتی `OFN_ALERT_TELEGRAM=1` (default خاموش)
- **۹ تست** در `tests/test_alert.py` (flag gate، misconfiguration، no-crash)
- تست شلیک واقعی systemd انجام شد و سبز شد
- توکن/چت‌آیدی از secrets.env خونده می‌شه، هرگز در کد نیست

فایل‌های تغییر: `ofn/adapters/alert.py` (جدید), `tests/test_alert.py` (جدید),
`deploy/systemd/ofn-alert.service` (جدید), `deploy/systemd/ofn.service` (OnFailure),
`deploy/install.sh` (نصب unit جدید).

### نکات

- **Bluetooth هم راه افتاد** در همین جلسه: `hciattach` روی UART9، سرویس
  `ap6256-bt.service`، hci0 UP با BT 5.0. مستقل از سه قابلیت بالا.
- **NPU librknnrt.so v2.3.2** نصب شد + راهنمای کامل `NPU-GUIDE.md`.
- کل suite: **تعداد تست: عدد را از `tools/repo_baseline.py --tests` بگیرید، صفر fail** — هیچ regression.
- هیچ رازی خوانده/چاپ/نوشته نشد. هیچ WIRE_* روشن نشد. هیچ چیزی به بیرون نرفت.

---

## ✅ جلسهٔ ۲۰۲۶-۰۸-۰۷ (UNIFY FINALIZE) — چهار نقطهٔ کور بسته شد

چهار نقطهٔ کور بازمانده از MEGAPROMPT-UNIFY بسته شد:

- **B-۲ panel_note:** brain call پنهان از write path‌های hypno حذف شد. حالا
  فقط log می‌نویسد، نه مغز.
- **B-۳ consent rename:** `sessions.consent` → `safety_acknowledged` با
  migration داده (دو ردیف حفظ شد). کد هر دو نام را می‌پذیرد.
- **B-۸ thread safety:** `fugu_core.memory` با RLock thread-safe شد (تست ۸
  thread همزمان سبز).
- **فاز ۴ اتصال inline:** `StudioAssistantStore` از shared corpus fallback
  می‌خواند؛ memory_path در config؛ run.py ایمن.

فایل‌های تغییر:
- `hypno/run.py` — panel_note + consent rename
- `hypno/adapters/store.py` — schema + `_migrate_consent_rename`
- `web/index.html` — payload `safety_acknowledged`
- `~/shared/fugu_core/src/fugu_core/memory.py` — RLock
- `ofn/config.py` — `memory_path`
- `ofn/run.py` — `_shared_memory` helper
- `ofn/adapters/studio_assistant.py` — `shared_memory` param + fallback
- تست‌های جدید: panel_note, thread safety, shared memory fallback

---

## ✅ جلسهٔ ۲۰۲۶-۰۸-۰۷ (UNIFY) — مغز و حافظهٔ مشترک OFN + hypno

UNIFY فاز ۰ تا ۴ انجام شد. دو پروژه حالا یک مغز (Sakana fugu) و یک
حافظهٔ سه‌لایه (memory.sqlite) مشترک دارند، بدون اینکه کد زنده تغییر کند.

- **`~/shared/fugu_core/`** — پکیج مشترک (auth/scrub/brain/memory)، خالص
  stdlib، نصب با `.pth` (pip روی DietPi نیست). ۲۵ تست.
- **`memory.sqlite` سه‌لایه** در `~/.local/share/fugu_core/`: turns/facts/
  corpus+FTS5. قانون جداسازی tenant فقط در corpus می‌تواند `shared` باشد.
- **`packs/hypno.yaml`** — tenant چهارم. quota: ۳۵/۳۵/۲۰/۱۰ = ۱.۰۰.
- **مغز ریموت Sakana** برای hypno فعال شد (`HFM_REMOTE_API_KEY` از OFN).
  تأیید زنده: `source: remote:fugu`.
- **۱۳۲ chunk** از hypno research_docs به shared corpus منتقل شد.

**آنچه دست‌نخورده ماند:** کد OFN و hypno تغییر نکرد؛ فقط pack‌ها و env.
`assistant.sqlite` و `hypno.sqlite` بازنویسی نشدند. MEGAPROMPT-UNIFY.md
باز است (نقاط کور B-2 panel_note، B-3 consent، B-8 worker async).

---

## ✅ جلسهٔ ۲۰۲۶-۰۸-۰۷ — جریان خروجی لید نقاشی + سینک تلگرام

**۱) سینک کامل اورنج‌پای و بات‌های تلگرام.** تضاد توکن hypno/lead رفع شد:
`@ssaabbaabot2725bot` فقط نقاشی/لید است؛ `@Sabaminiappbot` (دو p) شد
«آرام‌جا» و فقط به hypno وصل. پنج بات OFN دکمهٔ «Open App» گرفتند. دامنهٔ
`app` از تونل اشتباه (`f62ab442`) به تونل ما (`968b3e96`) وصل شد.

**۲) شکاف خروجی لید نقاشی پر شد.** تا دیروز لید فقط ورودی داشت. حالا
پارتنر می‌تواند جواب/قیمت بنویسد و لیدها را جستجو/فیلتر/تغییر وضعیت کند.
الگوی `publish_draft` استودیو کپی شد: یادداشت سبز (بدون outbox)، SMS/ایمیل/
قیمت RED (وارد outbox → owner_queue → double-confirm آری).

فایل‌های تغییر:
- `ofn/node.py` — `send_lead_reply` + `send_lead_quote` + `import hashlib`.
- `ofn/adapters/http_api.py` — ۳ endpoint partner + `query` در signature.
- `ofn/run.py` — تزریق دو callback جدید.
- `web/lead.html` — نوار جستجو/فیلتر + کارت لید + sheet جواب/قیمت.
- `tests/test_painting_outbox.py` — ۱۲ تست جدید (Node واقعی، نه lambda).
- `tests/test_handler_failure.py` — signature `handle` به‌روز شد.

---

## ✅ جلسهٔ ۲۰۲۶-۰۸-۰۶ — شکاف #۱ لید بسته شد + پرچم بوت رفع شد

امتیاز لید اشتباه وصل بود (شکاف #۱ همین فایل): `kernel/painting_math.py:
lead_priority()` ساخته و تست شده بود ولی هیچ‌وقت صدا زده نمی‌شد؛ به‌جایش
`lead_store.py:_score()` (یک heuristic کلمه‌کلیدی) اجرا می‌شد. B2B/مناقصه/
منبع از مدل واقعی استفاده می‌کردند و `score_json` ذخیره می‌کردند، ولی لیدها
نه.

**چه changed:**
- `lead_store.py`: ستون `score_json` به `painting_leads` اضافه شد + مهاجرت
  (`_add_score_json` با `add_column_if_absent`). `_score()` حذف شد؛ به‌جایش
  `lead_priority()` از یک پل مستند (`_lead_components`) تغذیه می‌شود که هفت
  محور V/I/G/T/Q/R/C را از فیلدهای پراکندهٔ لید می‌سازد. هر محور بی‌داده
  `None` می‌ماند تا مدل `incomplete` را علامت بزند (هرگز سکوت نکند). خروجی
  همان شکل `score_json` است که B2B/مناقصه دارند. `update_lead` با تغییر
  message/distance/... امتیاز را بازمحاسبه می‌کند؛ `score` دستیِ مالک اولویت
  دارد. مسیر خواندن `score_json` ذخیره‌شده را ترجیح می‌دهد و برای ردیف‌های
  قدیمی به `_lead_score_detail` برمی‌گردد.
- `boot.py`: `painting` به `MIGRATIONS` اضافه شد. این مهم بود — سرپرست بوت
  مهاجرت `lead_store` را نمی‌شناخت و `schema:painting(critical)` را بالا
  می‌آورد و گره را در SAFE MODE نگه می‌داشت. حالا بوت `boot OK — ۲۷/۲۷`
  و حالت NORMAL است.

**امنیت:** هیچ خروجی بیرونی، هیچ outbox، هیچ کانال. `OFN_WIRE_OUTBOUND=0`.
امتیاز صرفاً پیشنهاد/اولویت‌بندی است؛ اجازهٔ اقدام نمی‌دهد.

**تست:** ۴ تست جدید در `test_painting_store.py` (مدل lead_priority، ماندگاری
score_json، بازمحاسبهٔ update، مهاجرت فایل قدیمی). کل: ۱۵۹۵ سبز + ۵ skip (تأیید: tools/repo_baseline.py --tests).
`schema:painting` در `test_schema_drift.py` هم سبز.

**هشدار — وزن‌ها هنوز کالیبره نیستند.** `_lead_components` الفبای اولیه است،
نه حقیقت بیزنسی. وقتی دادهٔ واقعی intake آرمین собр شد، وزن‌ها و این قرائت‌ها
باید با آن تنظیم شوند. تا آن زمان امتیاز فقط یک پروکسی قابل‌اتکاتر از قبل است.

**🟢 توکن‌های ورود گذاشته شد (همان جلسه).** آرمین `OFN_BOT_TOKEN_LEAD` و
`OFN_BOT_TOKEN_OWNER` را از BotFather گرفت و در `~/.config/ofn/secrets.env`
گذاشت. هر دو بات با `getMe` تلگرام تأیید شد (`ok=true`؛ usernameها بدون مقدار:
lead=`ssaabbaabot2725bot`، owner=`Robo2725_bot`). سرویس ری‌استارت شد،
`boot OK — 27/27`، allowlistها سر جاشان (owner=۱، lead=۱).

**قدم بعدی (آزمایشگاهی، نه روی سیم):** تست ورود واقعی از گوشی آرمین هنوز
انجام نشده — این تنها کسی است که می‌تواند آن را کند (نیاز به لانچ واقعی
تلگرام از دستگاه خودش). ایجنت بعدی: منتظر نتیجهٔ تست گوشی بمان، یا اگر آرمین
گفت «وارد شدم»، برو سراغ ساخت لید تستی و جریان intake.

**drift بی‌ضرر (هنوز باز):** `OFN_WIRE_EMAIL`/`OFN_WIRE_PUBLISH` در `node.env`
روشن‌اند ولی کد Python نمی‌خواندشان — امنیت از outbox + store-layer status
تأمین می‌شود. بهتر است در `node.env` خاموش شوند تا با واقعیت یکی باشند.

---

## ✅ جلسهٔ ۲۰۲۶-۰۸-۰۶ — جراحی پنل سبا (دو مرحله)

دو جراحی کوچک روی `web/studio.html` انجام شد؛ بک‌اند منطقی دست نخورد.

**مرحلهٔ ۱ — چیدمان و متن:**
- چت‌باکس وسط و بالاتر آمد (`max-width:720px; margin:auto`).
- پنل خالی تیرهٔ بالای چت‌باکس حذف شد (دو لایهٔ تزئینی `.sheet.back` با
  `min-height:352px` یک نوار خاکستری بلند می‌ساختند). حالا وقتی کارت تصمیم
  نیست، فضا اشغال نمی‌شود.
- دکمه‌های زیر چت‌باکس مرتب شدند (`justify-content:center; flex-wrap:wrap`).
- نشت کلمهٔ فنی «RAG» در کپشن پیشنهاد حذف شد.
- متن‌ها گرم، ساده، دخترانه و غیرفنی شدند: «چت باکس»→«بزن بریم برای امروز»،
  «بپرس»→«بفرست»، «هلپ ساده»→«مشاوره»، placeholder، کپشن، و لیست پیشنهادها
  در `studio_assistant.py` کاملاً بازنویسی شد.
- گالری: بنر «خوش اومدی سبا جان…» بالای صفحه (اسم از session، نه static —
  قانون نشت اسم قبل از احراز هویت) و empty-state گرم.

**مرحلهٔ ۲ — آپلود و حذف:**
- آپلود چندتایی مقاوم‌تر شد: یک عکس بد، batch را متوقف نمی‌کند (حذف `break`)،
  شمارش واقعی خطاها، و آزادسازی بهتر حافظه (`bmp.close()` در `finally`،
  renditions+original موازی). کیفیت حفظ شد (۱۶۰۰px + اصل فایل).
- یک «×» کوچک بالای هر عکس (سمت چپ داخل عکس) با تأیید «مطمئنی؟» → فقط همان
  عکس حذف می‌شود. `stopPropagation` روی pointer/touch/click جلوی long-press و
  انتخاب را می‌گیرد.

تست‌های جدید: ۲۱ تست (قراردادهای UI، متن گرم، نبود کلمات فنی، edge caseهای
حذف آلبوم/عکس/توضیح/برچسب، ضربدر روی عکس، آپلود بدون break).

**نکتهٔ مهم:** خیلی از چیزهایی که «خراب» به‌نظر می‌رسیدند از قبل سالم بودند:
حذف آلبوم (عکس‌ها را فقط از آلبوم خارج می‌کند)، حذف عکس، پاک‌کردن توضیح/
برچسب، یکی‌شدن آلبوم/دسته، long-press، random بودن پیشنهادها. جراحی فقط روی
آنچه واقعاً ناقص بود متمرکز شد.

---

## ✅ جلسهٔ ۲۰۲۶-۰۸-۰۶ — پرورش عمیق مدل لبهٔ سیستم در hypno

مدل «لبهٔ سیستم» (تفکیک بدن/خود/ابرموجود) که در جلسهٔ قبل فقط کد+RAG بود،
حالا **کامل به مغز و endpoint و حافظهٔ روزانه وصل شد.** سه شکاف بسته شد:

```
کار ۱ · مغز     brain.py: _extract_scores (نمره از متن فارسی) +
                _edge_reply_from_scores + EDGE_SYSTEM_PROMPT.
                وقتی کاربر در chat نمره می‌دهد، مغز مدل را محاسبه و به
                فارسی ساده جواب می‌دهد (source: «rules+مدل» / edge: True).
کار ۲ · endpoint POST /api/edge/decision (۱۲ متغیر → تجزیهٔ تصمیم)؛
                POST /api/edge/daily (B/C/X → حکم + streak + red_flag)؛
                GET  /api/edge/history (آخرین N روز).
کار ۳ · حافظه    store.py: جدول edge_daily (upsert یک‌ردیف‌درروز) +
                log_edge_daily + edge_history. قانون سه‌روزه از روی آن می‌خواند.
کار ۴ · پرامپت   EDGE_SYSTEM_PROMPT ساخته شد؛ مغز ریموت وقتی موضوع لبه است از
                آن استفاده می‌کند (سه قطب، بدون کلمهٔ فنی، ارجاع به تجزیه).
```

تست‌های جدید: ۱۹ تست (نمره‌گیری، تجزیه، endpointها، upsert، chat wiring،
بحران-قبل-از-مغز، idempotency اسکیما).

**۶۲ تست سبز (تاریخی)** (۴۳ + ۱۹). `hypno-fugu-mini.service` active. هیچ دیتای قدیمی
دست‌نخورد (۱۳۲ پژوهش، پیام‌ها دست‌نخورده). جدول `edge_daily` با
`CREATE TABLE IF NOT EXISTS` اضافه شد.

نمونهٔ زنده: «کدنویسی تا ۳ صبح بعد از ترند» → سهم ابرموجود ۴۰٪ > خود ۲۶٪،
حکم «ترکیبی». «نقاشی برای runway» → سهم خود ۵۸٪، حکم «بیشتر از خودت». روز سخت
(B=۳,C=۲,X=۸) → زرد + «فردا گسترش ممنوع؛ فقط تثبیت.»

بک‌آپ‌ها: `*.bak-deep-20260806-225712`. مگاپرامپت: [[MEGAPROMPT-EDGE-DEEP]].

---

## لید نقاشی — شکاف‌ها

کاوش کامل کد لید نقاشی (تنانت `lead`، پورت ۸۷۹۲) نشان داد بیشتر از حد تصور
ساخته شده، ولی چند جا وصل نیست. ترتیب اولویت:

1. **✅ رفع شد (۲۰۲۶-۰۸-۱۰).** `kernel/painting_math.py:lead_priority()`
   در `create_lead`/`update_lead` وصل شد (از طریق `_score_payload()`).
   `_score()` قدیمی حذف شد. `score_json` در schema و ذخیره‌سازی فعال است.
   ۱۲ تست سبز. (D-23 بسته)
2. **✅ رفع شد (۲۰۲۶-۰۸-۰۷).** جریان خروجی ساخته شد: `send_lead_reply`
   (یادداشت/SMS/ایمیل) و `send_lead_quote` در `node.py`. یادداشت سبز (interaction
   + ledger، بدون outbox)؛ SMS/ایمیل/قیمت RED (وارد outbox → owner_queue →
   double-confirm). وضعیت لید خودکار حرکت می‌کند (`new→contacted→quoted`).
3. **✅ رفع شد (۲۰۲۶-۰۸-۰۷).** UI پارتنر کامل شد: نوار جستجو + فیلتر وضعیت
   + dropdown تغییر وضعیت + sheet جواب/قیمت. سبک گرم/غیرفنی (D-22).
4. **✅ رفع شد (۲۰۲۶-۰۸-۰۷).** `GET /api/v1/painting/leads` partner اضافه شد
   با q/status. `ApiApp.handle` حالا query می‌گیرد (backward-compatible).
5. **✅ رفع شد (۲۰۲۶-۰۸-۱۰).** سورس‌رجیستری دیگر ساکت شکست نمی‌خورد.
   `node.py` بارگذاری `data/painting_source_registry.json` را در `except Exception: pass`
   پیچیده بود؛ اگر فایل غایب/خراب بود، جدول منابع خالی می‌ماند بدون هیچ لاگی.
   except clause حالا یک هشدار به stderr می‌نویسد.
6. **✅ رفع شد (۲۰۲۶-۰۸-۰۷).** `test_painting_outbox.py` ۱۲ تست با Node و
   Outbox و Ledger واقعی اضافه شد: note بدون outbox، SMS/quote در RED،
   idempotency، تغییر وضعیت خودکار، owner_queue.

---

## ✅ جلسهٔ قبلی — حلقهٔ آرشیو ساخته شد

عکس‌ها اضافه می‌شدند ولی هیچ کاری نمی‌شد با آن‌ها کرد: کارت جلو می‌گفت
«چیزی برای تصمیم نیست» چون اپ فقط دربارهٔ **انتشار** فکر می‌کرد، و کارِ
امشب **بایگانی** بود.

دو چیز اصلاً وجود نداشتند و بدون آن‌ها آرشیو ممکن نبود:

```
ساخت آلبوم از گوشی      نبود  → POST /api/v1/studio/albums
انتقال عکس به آلبوم     نبود  → POST /api/v1/studio/media/<id>/album
                              (فقط موقع آپلود می‌شد، یعنی باید از قبل
                               می‌دانست عکس کجا می‌رود)
```

و حالت آرشیو (D-20): یک عکس در هر لحظه · «۳ از ۱۲» · چیپ آلبوم‌ها +
«آلبوم تازه» همان‌جا · برچسب‌های جفتی · «ثبت و بعدی» / «فعلاً رد کن» ·
هر عکس همان لحظه ثبت می‌شود، هیچ batch ای نیست.

انتخاب چندتایی هم اضافه شد (`multiple`) — پنجاه عکس یک‌جا انتخاب، ولی
**پشت سر هم** فرستاده می‌شوند، نه هم‌زمان.

⚠️ حین همین کار یک نشتی تنانت پیدا شد و بسته شد (D-21): شناسهٔ آلبوم بدون
بررسی تنانت نگاه می‌شد.

---

## ✅ همین جلسه — مینی‌اپ سبا: چرا «هیچی نداشت»

سبا و آری با هم بازش کردند: صفحه می‌آمد، ولی خالی بود. ژورنال گفت
`GET /sabaapp -> 200` سه بار، و **هیچ درخواست دیگری** — یعنی صفحه هیچ‌وقت
به نود نرسید.

دو باگ، مستقل از هم:

```
۱. نگهبان ساکت    start() یک try/catch هم‌زمان دور یک تابع async داشت.
                  هیچ‌وقت چیزی نمی‌گرفت. هر خطای boot = صفحهٔ ساکن،
                  که شبیه «اپ سالم و خالی» است، نه شبیه خطا.
                  → boot().catch(...) + onerror + unhandledrejection
                  → همان قاعده تعمیم داده شد و ۴ مورد دیگر پیدا کرد:
                    loadGallery · loadBusiness · addPhoto · publishCurrent
                    (هر چهارتا از داخل event handler → reject به هیچ‌کس)

۲. بن‌بست خالی    گالری می‌گفت «از تب امروز اضافه کن»، تب امروز می‌گفت
                  «منتظر بمان». حلقهٔ بسته.
                  → کارت اول روی حساب خالی: «بیایید اولین عکس را بگذاریم»
                  → دکمهٔ «عکس تازه» داخل خود گالری
```

و برای اینکه دفعهٔ بعد حدس نزنیم: `POST /api/v1/shell/boot` (D-18). پوسته
حالا خودش می‌گوید چطور بالا آمد یا نیامد، و در ژورنال می‌نشیند.

### ✅ علت پیدا شد — و اندازه‌گیری لازم نبود

`no-shell` باگ نبود، **گزارشِ درستِ یک باگ دیگر** بود. در `studio.html`:

```js
const tg = window.Telegram && window.Telegram.WebApp;   // در اسکریپت inline
<script defer src=".../telegram-web-app.js">            // در <head>
```

اسکریپت inline موقع **پارس** اجرا می‌شود؛ اسکریپت `defer` **بعد** از پارس.
پس `tg` همیشه `undefined` بست — یک بار، برای همیشه، روی هر پلتفرمی. یعنی
گوشی هم `no-shell` می‌داد. تست گوشی جواب نمی‌داد.

⚠️ چیزی که باعث شد از بازبینی رد شود: صدا زدنِ `boot()` **دقیقاً به همین
دلیل** به `DOMContentLoaded` موکول شده بود، با کامنتی که خطر را توضیح می‌داد.
ولی چیزی که موکول شده بود *فراخوان* بود نه *خواندن* — و مقدار هزار خط
بالاتر یخ زده بود. فایل طوری خوانده می‌شد که انگار ترتیب حل شده.

سه شکل دیگر هم داشت: `shell()` هیچ‌وقت `tg.ready()` صدا نزد و `tap()` هرگز
هپتیک نداد.

**اصلاح:** خواندن با تابع (`const tg = () => ...`)، نه با متغیر. `defer`
سر جایش ماند — عمدی بود و دلیل داشت (اسکریپت شخص ثالث نباید first paint را
ببندد؛ همان اشتباه فونت در zim). هر دو قاعده درست‌اند.

### برچسب شکسته شد (خواستهٔ آری)

```
no-sdk        اسکریپت SDK اصلاً اجرا نشد → خطای بارگذاری. reload کمک می‌کند.
no-initdata   SDK هست، امضا نیست → از مسیر اشتباه باز شده. reload بی‌فایده.
```

پیام هرکدام فرق دارد، و دکمهٔ «دوباره تلاش کن» فقط روی `no-sdk` می‌آید.
`platform`/`version` هم کنار گزارش می‌رود (هیچ‌کدام PII نیست) — پس مرورگر
(`unknown`) از کلاینت (`tdesktop`/`ios`/`android`) در یک نگاه جدا می‌شود.

`no-shell` در کرنل پذیرفته می‌ماند: سه پوستهٔ دیگر هنوز می‌فرستندش و تاریخچهٔ
ژورنال هم دارد.

✅ ریستارت شد ۰۴:۴۰ (PID 24849) و **روی سیم بررسی شد** — نه فقط روی دیسک:

```bash
curl -s -H "Host: studio.master-painting.com" http://127.0.0.1:8793/sabaapp \
  | grep -n "const tg"
# 609:  const tg = () => window.Telegram && window.Telegram.WebApp;
```

هر چهار leg بعدش ۲۰۰. `Cache-Control: no-store` هم زنده است، پس کش کلاینت
این بار مانع نیست.

```bash
sudo journalctl -u ofn --since "-10 min" | grep "shell/boot"
```

### ✅ چیدمان «امروز» — دکمه‌ها روی هم افتاده بودند

بعد از زنده شدن، سبا گزارش داد «بعداً» و «عکس تازه» کاملاً روی هم‌اند. علت
سه قاعده با هم بود:

```
.stack        position:relative · height:352px    ثابت
.sheet        position:absolute · top:0           هر سه بیرون از جریان
.sheet.front  height:320px                        ثابت
```

کارت جلو دو چیز متفاوت را نگه می‌دارد: یک **تصمیم** (عنوان + توضیح + strip،
که در ۳۲۰ جا می‌شود — عدد از همین‌جا آمده) و یک **سؤال کرنل** (عنوان +
توضیح + textarea + خط خطا + دو سه دکمهٔ ۵۲px، که جا نمی‌شود). چون کارت
`absolute` بود، سرریز بیرون از stack نقاشی می‌شد و می‌افتاد روی `.act` ثابتِ
زیرش.

اصلاح: تنها لایه‌ای که محتوا دارد در جریان می‌ماند، پس deck با آن اندازه
می‌شود نه با حدس. `height` → `min-height`.

⚠️ این هم مثل inset بالا، **تا امروز دیده نشدنی بود**: `askCard()` فقط وقتی
اجرا می‌شود که نود سؤال بدهد، و پوسته هرگز آن‌قدر جلو نمی‌رفت. یک باگ
راه‌اندازی، سه باگ چیدمان را پشت خودش پنهان کرده بود.

### ⬜ مانده در پوستهٔ استودیو

```
[ ] tg.setHeaderColor / setBackgroundColor — هدر تلگرام با پالت پوسته یکی
    نمی‌شود. پیدا شد، اصلاح نشد. (سبا گفت مشکل اصلی رنگ نیست)
```

### ⚠️ درس عملیاتی — «اصلاح شد» با «سرو می‌شود» یکی نیست

یک دور کامل تلف شد چون گزارش دادم اصلاح انجام شده و ریستارت را به بعد
سپردم. آری دید که هیچ چیز عوض نشده — درست هم بود: نود هنوز PID قبلی بود و
`const tg = window.Telegram && ...` را سرو می‌کرد، در حالی که گیت اصلاح را
داشت.

ادعا («فایل را عوض کردم») و ثبت مستقل («نود چه می‌دهد») از هم جدا نشده
بودند. §۸-ب دقیقاً همین است، و `curl` بالا ثبت دوم است.

**قاعده:** بعد از هر ویرایش `web/`، ریستارت + یک `curl` که بایتِ عوض‌شده را
نشان دهد. دیسک شاهد نیست.

### ⚠️ تلهٔ خودِ همین کار — ثبت شد چون دوباره پیش می‌آید

اولین تستی که نوشته شد `defer` را ممنوع می‌کرد. سبز شد، و **یک تست موجود را
قرمز کرد** که `defer` را *واجب* می‌دانست (سفیدی صفحه روی شبکهٔ کند). دو
قاعدهٔ درست، رو در رو — چون تست **مکانیزم** را سنجیده بود نه **خاصیت** را.

خاصیت این است: «مقدار قبل از اجرای SDK در یک نام بسته نشود.» با `defer` هم
برقرار می‌ماند. عمق brace هم جواب نمی‌داد: بایندِ باگ‌دار داخل یک IIFE بود،
یعنی «داخل تابع» و «دیرتر اجرا می‌شود» دو ادعای متفاوت‌اند.

دقیقاً همان §۸-الف. اینجا خودِ تست گیرش انداخت، نه بازبینی.

⚠️ **عملیاتی:** نود کل `web/` را موقع استارت در حافظه می‌خواند. هر ویرایش
پوسته تا `sudo systemctl restart ofn` سرو نمی‌شود.

---

## 🔴 قلم‌های باز — به ترتیب فوریت

### ۱. شناسهٔ اپراتور در allowlist استودیو

اگر برای تست اضافه شد، **باید برداشته شود**.

> ⚠️ (۲۰۲۶-۰۸-۱۰) `OFN_PARTNER_USER_IDS_STUDIO` در هیچ‌جای مخزن یافت نشد —
> یا قبلاً حذف شده یا هرگز با این نام وجود نداشت. صاحب تأیید کند.

```
[ ] بعد از بردار طلایی: شناسهٔ اپراتور از OFN_PARTNER_USER_IDS_STUDIO حذف
    → sudo systemctl restart ofn
    → تأیید: «allowlist studio: 1 account(s)»
```

`allowlist` تنها چیزی است که دادهٔ سه شریک را از هم جدا نگه می‌دارد.
شناسهٔ اپراتور که در فهرست یک شریک جا بماند، همان چیزی است که کسی شش ماه
بعد پیدا می‌کند و نمی‌داند عمدی بوده یا نه.

⚠️ و **به سبا گفته شود** که یک بار برای تست وارد پوستهٔ او می‌شویم.

### ۲. دو بردار طلایی — هیچ‌کدام بدون یک آدم ساخته نمی‌شوند

```
[ ] tests/fixtures/canvas-{1600,320}.txt   خروجی واقعی canvas.toDataURL()
    از یک عکس عمودیِ گرفته‌شده با دوربین گوشی. اسکرین‌شات EXIF ندارد و
    تست را بی‌معنا سبز می‌کند.
    ترتیب: اول tools/check_rotation.py، بعد tools/capture_golden.py
    عکس کج → بردار نگیر. بردار طلایی از عکس کج، باگ را برای همیشه تثبیت
    می‌کند و هر تست آینده با آن موافق می‌شود.

[ ] بردار طلایی initData از یک لانچ واقعی تلگرام
    تا رسیدنش hmac_variants() قابل حذف نیست — و آن تابع پیاده‌سازی‌های
    *غلط* را زنده نگه می‌دارد.
```

### ۳. فایروال — از دو شب پیش منتظر است

نوشته شده، اعمال نشده. `deploy/firewall/APPLY.md` با dead-man switch.
**آری خودش اعمال می‌کند** — یک قاعدهٔ بد روی ۲۲ یعنی قفل شدن تنها راه
ورود به برد. مؤثرتر از هر رمزنگاری‌ای که روی این برد ممکن است.

---

## وضعیت هر leg

```
ziman    ✅ زنده · یک کاربر واقعی · قطعهٔ تست حذف شد · قفسه خالی
lead     ⬜ فقط پوسته — عمدی. نقاشی ساختمان «قطعه» ندارد؛ فرم قطعه دادن
             به عباس یعنی ابزاری که برای کار او ساخته نشده
studio   🟡 مینی‌اپ باز می‌شود · فرم عکس هست · انتشار به outbox می‌رود
             منتظر: رضایت‌نامهٔ امضاشده، وگرنه انتشار قفل می‌ماند (درست است)
mining   ⬜ کرنل آماده · اجرا متوقف تا [[DECISIONS|D-8]]
```

---

## بار روی برد — اندازه‌گیری ۲۰۲۶-۰۸-۰۵

```
load average   0.47 / 0.68 / 0.62
رم             1703 / 3910 MB  ·  2207 MB آزاد
دما            24°C
ofn            یک پروسه · 28 MB RSS
```

**چهار leg روی این برد مسئله نیست؛ مدل محلی است.** ofn تمام‌شده ۲۸ مگابایت
می‌گیرد. قید §۵ دربارهٔ ~۱۸۰۰ مگابایتِ یک مدل محلی است که هنوز نصب نشده و
معماری فعلی لازمش ندارد — مغز میزبان است. تا وقتی هیچ مدلی روی برد بار
نشود، سقف رم مسئلهٔ امروز نیست.

---

## استودیو — چه چیزی هست و چه چیزی نیست

```
✅ ST-1 رضایت        subjects · releases · draft_subjects · posts
✅ ST-2 رسانه        photos.py (۳۵ تست بیرونی) · media.py · ۷۰۰/۶۰۰
✅ ST-3 پوسته        بودجه‌های DESIGN-DIRECTIVE به‌شکل تست
✅ مدل داده          collection → draft → media · sensitivity قفل‌شده
✅ مخاطب             subscribers · revenue_events · audience_snapshot
✅ ST-4 مشاور        ردهٔ ۰ · Evidence فقط عدد · شجره‌نامه اجباری · جغجغه
✅ مغز               الف پنل · ب لایهٔ استخراج · ج استودیو از راه گارد
✅ پیش‌نویس پیام      متن آماده، ارسال با دست، هیچ‌جا ذخیره نمی‌شود
⬜ scout ترند        الگو در kernel/scout.py هست، وصل نشده
❌ خودکارسازی پیام   [[DECISIONS|D-13]] — حذف شد، نه معلق
```

### مغز — هر سه مرحله بسته شد

```
الف  پنل آری · probe با جواب معلوم · سقف تماس به تفکیک پله
ب    لایهٔ استخراج — Evidence فقط عدد نگه می‌دارد، جایی برای پیکسل نیست
ج    استودیو، ولی فقط از راه advisor.prepare قبل از router.ask
```

⬜ **هنوز هیچ تماس واقعی گرفته نشده.** اولین `probe` است که
[[DECISIONS|D-16]] را جواب می‌دهد: لجر یا موافقت مدل را ثبت می‌کند یا
اختلاف. تا آن لحظه اینکه مغز روی چه چیزی است، حدس است.
`OFN_OWNER_USER_IDS` خالی است، پس هیچ نشست مالکی صادر نمی‌شود.

---

## زیمان — هر چهار قلم بسته شد

```
✅ بایگانی        محور جدا از state · کد آزاد نمی‌شود · برگشت‌پذیر
✅ عکس            piece_slug چون SKU حروف بزرگ دارد و مسیرساز ردش می‌کند
✅ CSV            BOM · ارقام لاتین · بدون ستون مالیاتی و بدون حاشیه
✅ gst فصلی       قاعده در کرنل، ساعت در نود — plan اصلاً عوض نشد
✅ فونت           هر چهار پوسته از /font/vazirmatn.woff2 خود نود
```

---

## آدرس‌ها

```
ziman.master-painting.com    → 8791
lead.master-painting.com     → 8792
studio.master-painting.com   → 8793   و /sabaapp
app.master-painting.com      → 8793   ⬜ ingress هست، رکورد DNS نه
panel.master-painting.com    → 8794
```

`app.*` عمداً ناتمام ماند: یک نام قشنگ‌تر است، نه یک بازکننده. وقتی سبا
دارد استفاده می‌کند و آدرس اذیتش کرد، یک `CNAME` به
`<tunnel-id>.cfargotunnel.com` کافی است.

---

## آیین پایان جلسه (طبق [[CLAUDE|§۹]])

1. این فایل را تازه کن.
2. اگر بیش از ~۵ فایل عوض شد، `agent-checkpoint:`.
3. هیچ راز، هیچ PII، هیچ خروجی مدل خام اینجا ننویس.
4. اگر تستی قرمز ماند، بنویس **کدام** و **چرا**.
