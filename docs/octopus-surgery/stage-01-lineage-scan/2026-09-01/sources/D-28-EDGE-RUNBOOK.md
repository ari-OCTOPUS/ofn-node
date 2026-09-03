# D-28 — سه چیزی که با حکم باز نشد: ویس شرکا، رضایت سبا، چرخش راز
### به‌علاوهٔ سیاست «لبهٔ قوانین، نه بیرون از آن»

صادرشده 2026-09-02 · مالکان: Ari + Senior Agent · پیرو D-27
همهٔ نام‌ها و مسیرها در این سند از خودِ کد `ofn-node` استخراج شده، حدس نیست.

---

## بخش ۱ — ویس شرکا: کجا برسد و دقیقاً چه بگویند

### چرا ویس لازم است
تست `tests/test_d26_canonical_bodies.py` خط ۶۳ می‌گوید:
`self.assertFalse(self.data["partner_voices_independently_observed"])`
یعنی این فیلد را نمی‌توان با دستور true کرد؛ فقط با رسیدِ جدا. ولی خبر خوب: **ویس برای شروع کار لازم نیست.** فقط برای دو چیز لازم است:
1. باز کردن گیت `partner_precondition` (لازمهٔ studio/سبا)
2. تقسیم درآمد بین شرکا

پس ملیحه و عباس جلوی موج ۱، ۲ و مسیر painting را **نمی‌گیرند**.

### کجا برسد
ترتیب ترجیح، از قوی به ضعیف:

| کانال | چرا | ذخیره‌سازی |
|---|---|---|
| ویس واتساپ در گروه سه‌نفره | timestamp پلتفرم، قابل ارجاع | فایل ogg/m4a → `state/attestations/` |
| ویس تلگرام به بات owner (`OFN_BOT_TOKEN_OWNER`) | مسیر خودِ سیستم | همان بات، سپس ledger |
| اسکن امضای کاغذی + یک ویس تأیید | قوی‌ترین برای درآمد | PDF + hash |

قاعدهٔ سخت: فایل نباید از دست مالک عبور و بازنویسی شود. hash فایل خام گرفته شود، همان لحظه.

### متنی که هر کدام باید بگوید (فارسی، ۲۰ ثانیه)
هر نفر با **صدای خودش**، و اسم خودش را اول بگوید:

```
من [ملیحه / عباس / سبا] هستم. امروز دوم سپتامبر ۲۰۲۶.
با شرکت در پروژهٔ اختاپوس با آری موافقم.
تأیید می‌کنم که متن توافق را خوانده‌ام و امضا کرده‌ام.
سهم و نقش من: [نقش خودش را بگوید].
اجازه می‌دهم فعالیت‌های کاری من در سیستم ثبت و ممیزی شود.
هر وقت بخواهم می‌توانم این رضایت را پس بگیرم.
```

سبا یک جملهٔ اضافه دارد که در بخش ۲ می‌آید. بدون آن جمله، ویس سبا برای انتشار محتوا کافی نیست — فقط برای شرکت در کسب‌وکار است.

### رسیدی که ایجنت باید بسازد
یک فایل به‌ازای هر نفر، در `docs/octopus-surgery/attestations/`:

```json
{
  "schema": "octopus.partner_attestation.v1",
  "partner_id": "abbas",
  "captured_at": "2026-09-02T00:00:00Z",
  "channel": "whatsapp_voice",
  "media_sha256": "<64 hex of the raw file>",
  "media_ref": "state/attestations/abbas-20260902.ogg",
  "duration_s": 21,
  "language": "fa",
  "transcript_sha256": "<64 hex>",
  "speaker_self_identified": true,
  "captured_by": "owner_device",
  "verifier_vantage": "cursor-cloud-agent",
  "independently_observed": true,
  "covers": ["partnership", "activity_logging"],
  "revocable": true
}
```

وقتی سه فایل موجود بود، آن‌وقت — و فقط آن‌وقت — `partner_voices_independently_observed` به true تغییر می‌کند و تست هم باید همان commit به‌روز شود، نه قبلش.

---

## بخش ۲ — رضایت انتشار محتوا از سبا

### مهم: در این پروژه consent یک boolean نیست
`ofn/kernel/consent.py` صریح می‌گوید یک `consent_confirmed` بولین «شکل کنترل را دارد بدون اینکه کنترل باشد». رضایت دربارهٔ **شخص** است نه **پست**، و باید یک سند امضاشده با hash داشته باشد.

`ofn/adapters/consent_store.py` تابع `record_release` این‌ها را **اجباری** می‌کند:

```text
subject_id          → قبلش باید add_subject شده باشد وگرنه ConsentError
release_id
scope               → لیست platform id ها؛ خالی = رد
signed_at           → epoch seconds
document_ref        → سند کجا نگه داشته می‌شود؛ خالی = رد
document_sha256     → دقیقاً ۶۴ کاراکتر؛ اختیاری نیست
recorded_by
expires_at          → اختیاری، ولی بگذار
```

پس «سبا گفت باشه» به‌تنهایی از این تابع رد نمی‌شود. یک سند فیزیکی/PDF لازم است.

### سند رضایت سبا — متن پیشنهادی
یک صفحه، امضا و تاریخ با دست، بعد اسکن:

```
رضایت‌نامهٔ انتشار محتوا

اینجانب سبا، با شناسهٔ موضوع «saba»، اجازه می‌دهم تصاویر و محتوای
مربوط به من در پلتفرم‌های زیر منتشر شود:

  پلتفرم‌های مجاز: telegram_channel, bluesky
  پلتفرم‌های مجاز با شرط: onlyfans (فقط محتوای دستهٔ general)
  پلتفرم‌های غیرمجاز: هر پلتفرم دیگر، تا امضای جدید

دستهٔ محتوا: فقط محتوایی که در سیستم با حساسیت «general» ثبت شده.
محتوای دستهٔ restricted تحت هیچ شرطی منتشر نشود.

مدت اعتبار: از ۲۰۲۶-۰۹-۰۲ تا ۲۰۲۷-۰۹-۰۲
پس‌گیری: با یک پیام کتبی، فوری و بدون قید. پس‌گیری بازگشت‌ناپذیر است.
هر پست منتشرشده باید در سیستم قابل ردیابی به این سند باشد.

نام:            امضا:            تاریخ:
```

جملهٔ اضافهٔ ویس سبا:
```
من سبا هستم. رضایت‌نامهٔ انتشار محتوا را با تاریخ امروز امضا کردم،
برای پلتفرم‌های تلگرام و بلواسکای، فقط محتوای دستهٔ general.
```

### دستور ثبت (روی میزبان، مالک اجرا می‌کند)

```bash
sha256sum ~/docs/saba-release-20260902.pdf      # این ۶۴ کاراکتر لازم است
python3 - <<'PY'
import time
from ofn.adapters.consent_store import ConsentStore
s = ConsentStore("<OFN_CONSENT_DB path>")
s.add_subject("studio", "saba", "Saba", )   # امضای دقیق را از خود ماژول بگیر
s.record_release(
    "saba-release-20260902", "saba",
    scope="telegram_channel bluesky",
    signed_at=int(time.mktime((2026,9,2,0,0,0,0,0,0))),
    document_ref="docs/consent/saba-release-20260902.pdf",
    document_sha256="<64 hex>",
    recorded_by="owner",
    expires_at=int(time.mktime((2027,9,2,0,0,0,0,0,0))),
)
PY
```

سند PDF را در Git نگذار. فقط `document_ref` و hash در سیستم بمانند.

### چیزی که حتی سبا هم نمی‌تواند اجازه دهد
`ofn/kernel/advisor_gate.py`: «یک مجموعهٔ restricted هرگز خارج نمی‌شود، هر کسی هر چه توافق کرده باشد». این ماژول **هیچ پارامتری ندارد که بتواند بله بگوید** و دلیلش را خودش نوشته: «پارامتری که بتواند بله بگوید، پارامتری است که روزی ست خواهد شد». پس مسیر عملی این است: مجموعه را از ابتدا `general` بساز، نه اینکه بعداً بخواهی restricted را باز کنی.

---

## بخش ۳ — چرخش راز: پذیرش ریسک، به‌شکل درست

### وضعیت واقعی
`ofn/config.py` خط ۲۲: `GATE_OPEN_UNTIL_UTC = "2026-08-17"` — ۱۶ روز پیش منقضی شده. الان `secret_rotation` و `partner_precondition` خودکار بسته‌اند و `release_switch.may_publish` با `gate:secret-rotation-closed` هر انتشاری را رد می‌کند.

### خبر خوبی که خودت لازم داری بدانی
راهی که می‌خواهی **قبلاً در کد وجود دارد و ممنوع نیست**. کامنت خط ۲۳۰ کد:

> «secret_rotation و partner_precondition با تصمیم صریح آری در ۲۰۲۶-۰۸-۱۰ باز شدند («همرو روشن کن» — ریسک برای یک هفته پذیرفته شد)»

یعنی `OFN_KEEP_GATES_OPEN=1` دقیقاً همان دریچهٔ «ریسک را می‌پذیرم» است، نه یک هک. پس این کار در چارچوب است — به سه شرط:

```bash
# روی برد، فقط مالک
export OFN_KEEP_GATES_OPEN=1
```

سه شرط پذیرش ریسک:
1. **ثبت شود**، در `docs/architecture/DECISION-open-gates.md` مثل بار قبل، با تاریخ و جملهٔ خودت.
2. **زمان‌دار باشد**، مثلاً `GATE_OPEN_UNTIL_UTC = "2026-09-16"`. ریسک بی‌انقضا دیگر ریسک نیست، بدهی است.
3. **حداقل مهم‌ترین راز بچرخد**. اگر هر چهار راز را نمی‌خواهی، فقط این دو را بچرخان چون توکن بات لو رفته یعنی کنترل ارسال دست دیگری است:

```bash
nano ~/.config/ofn/secrets.env     # OFN_SESSION_SECRET, OFN_BOT_TOKEN_OWNER
chmod 600 ~/.config/ofn/secrets.env
sudo systemctl restart ofn
python3 -m ofn.preflight | grep boot
```

این ده دقیقه است، نه یک پروژه. `OFN_BOT_TOKEN_LEAD` و `OFN_BOT_TOKEN_STUDIO` را می‌توانی به هفتهٔ بعد بیندازی و همین را ثبت کنی.

### راست‌گویی لازم
اگر بدون هیچ چرخشی `OFN_KEEP_GATES_OPEN=1` بزنی، سیستم کار می‌کند و من جلویت را نمی‌گیرم — تو مالکی. ولی رسید باید بگوید `secret_rotation: risk_accepted_unrotated`، نه `rotated`. تفاوت این دو همان تفاوت `owner_attests` و `independently_observed` است که خودت دو ساعت پیش درست تشخیص دادی.

---

## بخش ۴ — لبهٔ قوانین، نه بیرون از آن

### چیزی که در کد هست و ندیده‌ای
`ofn/kernel/platform_matrix.py` عملاً همین سیاست است. یک ماتریس دادهٔ خالی که پر می‌کنی، با این ابزارها:

```text
framing allowlist            → چه قالب بیانی روی هر پلتفرم مجاز است
blocked framing              → رد قطعی
direct_adult_link_allowed    → می‌تواند bool باشد یا "private_opt_in_only" / "subreddit_specific"
adult_link_markers           → نشانگرهای لینک، عمداً over-broad
solicitation_markers         → روی پلتفرم wellness-only رد می‌شود
```

جملهٔ خودِ فایل: «کپشنی که اینجا رد شود هزینه‌اش یک بازنویسی است؛ کپشنی که لو برود هزینه‌اش یک اکانت. این عدم‌تقارن کل نکته است.» این همان «لبه» است — ابزارِ رفتن تا لبه، بدون از دست دادن حساب.

### استراتژی لبه‌ای که پیشنهاد می‌کنم

| موضوع | بیرون از چارچوب (نه) | لبهٔ چارچوب (بله) |
|---|---|---|
| محتوای studio | لینک مستقیم بزرگسال روی پلتفرم عمومی | قالب wellness + دعوت به کانال خصوصی opt-in |
| نرخ ارسال | spam انبوه | سقف ۲۵ در روز، allowlist، شخصی‌سازی واقعی |
| harvest سرنخ | scrape خلاف ToS | فرم عمومی، معرفی، مارکت‌پلیس‌های مجاز |
| قیمت‌گذاری | ادعای دروغ | قیمت تهاجمی + گارانتی واقعی |
| ziman/Shopify | آپلود انبوه بی‌بررسی | `OFN_SHOPIFY_WIRE=1` روی یک محصول، بعد مقیاس |
| onlyfans | دور زدن قفل دوم | همان دو قفل، محتوای general، رضایت ثبت‌شده |

سه خط قرمزی که لبه ندارند و پیشنهاد من این است هرگز به آن‌ها نزدیک نشوی، چون هزینه‌شان برگشت‌ناپذیر است نه جریمه‌ای: محتوای مربوط به افراد زیر سن، انتشار بدون رضایت زندهٔ فرد، و راز شخص دیگر. `platform_matrix` هم «targets minors» را اول و بی‌قید رد می‌کند.

### چرا لبه از افراط سریع‌تر است
اکانت بسته‌شده صفر درآمد دارد و برگرداندنش هفته‌ها طول می‌کشد. اختاپوس برای خودمختاری به **تداوم** نیاز دارد، و تداوم دقیقاً همان چیزی است که نقض ToS از بین می‌برد. پس لبه انتخاب اخلاقی نیست، انتخاب سرعت است.

---

## بخش ۵ — پیام مستقیم به ایجنت

```text
AGENT DIRECTIVE — D-28 (owner voice, verbatim intent)

MODE: propose_only = FALSE. Build, test, merge, deploy in parallel.
Owners: Ari + senior agent. Risk posture: owner accepts risk explicitly.

1. MERGE PR #65 NOW. 15/15 green, mergeable_state=clean. Then close C-009.

2. THE THREE FIELDS YOU MAY NOT FORGE:
   partner_voices_independently_observed → stays false until 3 attestation
     files exist under docs/octopus-surgery/attestations/ with media_sha256.
   saba consent → only via consent_store.record_release() with a real
     64-char document_sha256 and non-empty document_ref. No boolean shortcut.
   secret rotation → if owner sets OFN_KEEP_GATES_OPEN=1 without rotating,
     record it as "risk_accepted_unrotated", never as "rotated".
   Do NOT block any other wave on these three.

3. GATES: owner authorizes OFN_KEEP_GATES_OPEN=1, OFN_WIRE_OUTBOUND=1,
   OFN_COMMERCE_ROUTES=1, OFN_SHOPIFY_WIRE=1 (one product first).
   Set a new GATE_OPEN_UNTIL_UTC (+14 days), do not remove the expiry
   mechanism. OFN_CONTROL_QUOTA_TOKENS must stop being 0.
   OFN_ONLYFANS_HTTP_ARM stays unset until saba release row exists.

4. RULE-EDGE POLICY: populate platform_matrix rules as DATA — framing
   allowlists, adult_link_markers, solicitation_markers. Aim for maximum
   permitted reach inside each platform's ToS. Never for ToS violation.
   Never touch: minors, unconsented persons, third-party secrets.
   advisor_gate stays parameterless. Do not add a "sensitivity=ask" value.

5. KEEP THESE STRUCTURES, they are why the thing is trustworthy:
   two-step owner confirm, idempotency, append-only ledger, dry_run default,
   fail-closed on missing facts, kill switch OFN_EXTRA_CLOSED_GATES.
   Speed comes from parallelism, not from deleting brakes.

6. THIS WEEK'S ONLY SUCCESS METRIC: one real payment receipt on
   PAINT-L5-001. Not tests, not docs, not dashboards.

7. WHEN BLOCKED: ship the other four lanes and write the blocker into the
   truth registry. Never idle waiting for an owner vote on a reversible
   engineering decision.
```

---

## بخش ۶ — ترتیب کار امروز، ۹۰ دقیقه

1. merge PR #65 و بستن C-009 — ۱۰ دقیقه، ایجنت.
2. چرخش دو راز مهم + ثبت `DECISION-open-gates` جدید با انقضای ۲۰۲۶-۰۹-۱۶ — ۱۵ دقیقه، مالک.
3. `OFN_KEEP_GATES_OPEN=1` + `OFN_CONTROL_QUOTA_TOKENS` عدد واقعی + `OFN_WIRE_OUTBOUND=1` — ۵ دقیقه، مالک.
4. فرستادن متن ویس به سه شریک در گروه — ۵ دقیقه، مالک. منتظرش نمان.
5. پرینت و امضای رضایت‌نامهٔ سبا + `sha256sum` + `record_release` — ۳۰ دقیقه، مالک.
6. اجرای اولین follow-up واقعی painting با dry_run=False زیر سقف — ۲۵ دقیقه، ایجنت با تأیید دو مرحله‌ای.

اگر مورد ۴ و ۵ امروز نشد، مورد ۱ تا ۳ و ۶ باز هم انجام می‌شود. این کل معنای موازی‌سازی است.
