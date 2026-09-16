---
type: knowledge
status: active
tags: [signed-probe, single-call, pattern, ed25519, nonce, idempotency, yaml-config]
created: 2026-08-20
updated: 2026-08-20
created_by: agent B (ZCode) — درخواست پژوهشی مالک 2026-08-20
reference_impl: research/event_time_probe/{run_probe_v2,pipeline}.py
---

# سند ۲ — پروب تک‌فراخوانی امضاشده (Signed Single-Call Probe): مفاهیم، الگو، و schema پیکربندی

## ۱. خاستگاه‌های علمی و صنعتی

الگو از چهار سنت مستقل تغذیه می‌شود که هم‌گرایش‌اند: **قفل‌کردن آزادیِ
اجراکننده قبل از مشاهدهٔ نتیجه، و بستنِ اثبات به همان اجرا.**

1. **پیش‌ثبت آزمایش بالینی (Trial Pre-registration).** در روش‌شناسی پزشکی،
   پروتکل (فرضیه/معیار/حجم نمونه) قبل از دیدن داده قفل می‌شود تا «researcher
   degrees of freedom» و p-hacking بسته شود. آنالوگ ما: payload امضاشده قبل
   از فراخوان؛ هر انحراف = GOVERNANCE_DEVIATION ثبت‌شده (مصداق واقعی: K9
   که با رأی چت اجرا شد و انحراف خورد).
2. **کلیدهای idempotency پرداخت.** در سیستم‌های تراکنشی (الگوی شناخته‌شدهٔ
   Stripe Idempotency-Key)، هر عملیات پولی یک کلید یکتا می‌گیرد و تکرارِ
   همان کلید همان اثر را برمی‌گرداند، نه اثر دوباره. آنالوگ: ‏`task_id/run_id`
   یکتا + شمارندهٔ فراخوان که باید دقیقاً ۱ شود؛ retry صفر حتی بعد از شکست.
3. **Nonce و اتصال چالش-پاسخ.** در پروتکل‌های احراز (OAuth nonce، ‏TLS
   handshake، challenge-response)، nonce یک‌بارمصرف پاسخ را به همین درخواست
   مقید می‌کند و replay را بی‌معنا می‌کند. آنالوگ: پرامپتِ
   `EVENT-TIME-PROBE-<run_id>` که sha آن **قبل از** فراخوان در رسید ثبت
   می‌شود — پاسخِ حامل nonce، متعلق به همین probe است نه یک پاسخ ذخیره‌شده.
4. **سنجش و گواهی تک‌گلوله‌ای.** در امنیت سخت‌افزار (TPM Quote، ‏secure-boot
   measurement) یک «quote» امضاشده وضعیت لحظه‌ای را با کلید غیرقابل‌جعل
   گواهی می‌کند؛ و Certificate Transparency نشان داد «شاهدِ append-only»
   (زنجیرهٔ هش) چطور تاریخ را غیرقابل بازنویسی می‌کند. آنالوگ: رویداد
   `provider_server_created` روی spine append-only + لجر ژنوم؛ و امضای
   Ed25519 (RFC 8032) روی payload با لنگر انگشت‌نگارتی.

## ۲. الگوی پیاده‌سازی امن (۹ مؤلفه)

مرجع: `research/event_time_probe/run_probe_v2.py` + `pipeline.py`.

```text
┌─ 1. پیش‌ثبت امضاشده ──────────────────────────────┐
│ payload JSON + sha256 پین‌شده + امضای Ed25519      │
│ + لنگر اعتماد (fingerprint) fail-closed            │
├─ 2. گیت مجوز idempotent ──────────────────────────┤
│ امضا معتبر ⇐ capability «دقیقاً ۱ فراخوان»         │
│ (نه بیشتر؛ نه کمتر — شمارنده باید ۱ شود)          │
├─ 3. پیش‌پرواز ۱۰بندی ─────────────────────────────┤
│ lease تک‌نویسنده · anchor · payload-hash · امضا    │
│ · pin تازه · یکتایی task/run · رزرو بودجه ≤ سقف    │
│ · صفر آزمایش هم‌زمان · executable=false · counter=0 │
│ هر شکست: PROBE_NOT_STARTED · calls=0 · AUD=0      │
├─ 4. درخواست nonce-بند ────────────────────────────┤
│ nonce = f(run_id)؛ sha پیش‌ثبت؛ stream/tools/       │
│ temperature/model عیناً از منبع امضاشده            │
├─ 5. تله‌متری پنج‌نقطه‌ای ──────────────────────────┤
│ t_start · t_body_sent · server_created ·           │
│ t_headers · t_body_complete                        │
│ (تفکیک ارسال/دریافت بدون گمان)                    │
├─ 6. اعتبارسنجی پاسخ ─────────────────────────────┤
│ HTTP·schema·created∈int·nonce exact·choices=1·     │
│ usage·finish·بدون secret                           │
├─ 7. حکم‌های بسته و بی‌ابهام ──────────────────────┤
│ PASS · RESPONSE_INVALID · HTTP_FAILED ·            │
│ BLOCKED_{FX_STALE|SOURCE_CONFLICT|SIGNATURE|LEASE} │
│ «خرج‌شده ولی نامعتبر» = calls=1 + verdict شکست     │
│ (هیچ PARTIAL_SUCCESS مبهمی وجود ندارد)             │
├─ 8. شاهد append-only ─────────────────────────────┤
│ رسید pin (JSONL، هرگز overwrite) + ردیف هزینهٔ     │
│ منتسب (task/run) + رویداد spine با occurred_at     │
│ از ساعتِ مستقل سرور                               │
└─ 9. پس‌شرط‌ها ────────────────────────────────────┘
  counter==1 · retry==0 · lease آزاد · raw فقط پس از
  redaction · executable==false
```

### خواص امنیتی حاصل

| خاصیت | سازوکار |
|---|---|
| جلوگیری از replay | nonce مقید به run_id + idempotency-key |
| عدم‌انکار (non-repudiation) | امضای Ed25519 روی payload + رسید cost منتسب |
| مهار بودجه | رزرو پیشینی + سقف در payload + HARD_STOP |
| حداقل TOCTOU | هش payload قبل از امضا؛ anchor قبل از verify؛ lease قبل از نوشتن |
| قابلیت ممیزی | زنجیرهٔ append-only: receipt→probe→spine با هش‌های متقابل |
| سلبِ اختیار بعد از امضا | مدل/پارامترها از payload؛ انحرافِ عامل = verdict شکست |

### درس‌های میدانی از پیاده‌سازی امروز (همه واقعی)

1. payload باید **مدل/endpoint را pin کند** — استثنای «منبع تصمیم مسیریابی»
   در رسید قابل دفاع است ولی ایده‌آل نیست.
2. حکم BLOCKED_LEASE در اولین اجرا آمد چون خود سازنده lease نگه داشته بود —
   fail-closed درست کار می‌کند؛ نگهبان باید lease جلسهٔ خودش را آزاد کند.
3. تفکیک پنج timestamp با `http.client` ممکن شد ولی `urllib` آن را نمی‌دهد —
   انتخاب ابزار HTTP بخشی از طراحی امن است، نه جزئیات.
4. معنای فیلد سرور (`created`) بدون سند، `UNKNOWN` ثبت شد — برچسب صادقانه
   بهتر از تفسیر درست‌نماست.

## ۳. ساختار پیکربندی YAML برای سیستم امضامحور (مرجع)

```yaml
# signed-probe.system.yaml — الگوی عمومی
schema: signed-probe.config/1

trust:
  algorithm: Ed25519            # RFC 8032؛ فقط این مجاز
  public_key_path: _ops/owner-signing/octopus-owner-ed25519-public.pem
  anchor_fingerprint_sha256: 2413e974…ab6b2   # پین‌شده؛ mismatch ⇒ fail-closed
  verify_before: [sign, paid_call, restart]   # نقاط اجباری verify

authorization:
  payloads_dir: 02-DECISIONS
  payload_sha256_pin: true       # هش در پیکربندی = payload تغییر کرده ⇒ BLOCK
  capability: {max_calls: 1, retries: 0, concurrency: 1}

preflight:                       # هر مورد false ⇒ PROBE_NOT_STARTED
  writer_lease: required
  fx_pin: {fresh_max_age_hours: 24, source: RBA_F11_CSV,
           conflict_policy: BLOCK, quote_convention: USD_per_AUD}
  budget: {reserve_before_call: true, hard_stop_aud: 0.01}
  uniqueness: [task_id, run_id]
  executable_must_be: false

request:
  params_from: signed_payload    # عیناً؛ عامل حق تغییر ندارد
  nonce: {template: "EVENT-TIME-PROBE-{run_id}",
          register_sha256_before_call: true}
  sampling: {stream: false, tools: [], temperature: 0, max_output_tokens: 32}

receipts:
  pin:  {path: _ops/state/cortex/fx-pin-receipts.jsonl, mode: append_only}
  probe:{path: 06-EVIDENCE/EVENT-TIME-PROBE-*.json, schema: event-time-probe.v1}
  cost: {path: _ops/state/cortex/cost-receipts.jsonl,
         attribution_fields: [task_id, run_id, attribution]}

verdicts: [PROBE_PASS, PROBE_RESPONSE_INVALID, PROBE_HTTP_FAILED,
           PROBE_BLOCKED_FX_STALE, PROBE_BLOCKED_SOURCE_CONFLICT,
           PROBE_BLOCKED_SIGNATURE, PROBE_BLOCKED_LEASE]   # بسته؛ بدون PARTIAL
```

### جدول تحلیل فیلدها

| فیلد | چرا امضامحور است | رفتار نقض |
|---|---|---|
| `trust.anchor_fingerprint_sha256` | کلید عمومی داخل repo قابل تعویض است؛ لنگر آن را قفل می‌کند | mismatch ⇒ هیچ امضایی معتبر نیست |
| `authorization.payload_sha256_pin` | امضا روی هش؛ تغییر payload بعد از امضا | BLOCK قبل از capability |
| `capability.max_calls: 1` | جوهرِ «تک‌فراخوانی» | شمارنده > 1 = STOP |
| `capability.retries: 0` | شکست هم خرج است؛ تکرار = دو داده | حتی timeout ≠ retry |
| `preflight.writer_lease` | دو نویسنده = رسید رقابتی | HOLD ⇒ PROBE_BLOCKED_LEASE |
| `preflight.fx_pin.conflict_policy` | منبع دوتایی = ابهام | BLOCK، نه انتخاب مطلوب |
| `request.nonce.register_sha256_before_call` | اثبات تعلق پاسخ | نبودش ⇒ nonce تزئینی |
| `receipts.pin.mode: append_only` | شاهد overwriteناپذیر | هر overwrite = تخلف |
| `verdicts` (بسته) | حکم‌سازی آزاد = PARTIAL مبهم | مقدار خارج فهرست = خطای پیکربندی |

### پیت‌فال‌های YAML مخصوص این سیستم

- `retries: 0` و `retries: "0"` یکسان رفتار نمی‌کنند در برخی ولیدیتورها —
  نوع را صریح int نگه دار.
- `algorithm: Ed25519` را enum بسته کنید؛ `ed25519/ED25519` مترادف شمرده نشود.
- `verify_before` لیست است؛ مقدار اسکالر = فقط یک نقطهٔ verify می‌ماند و سکوت.
- fingerprint را نقل‌قول نکنید اگر با `0x` شروع می‌شود (YAML آن را hex-int
  می‌کند) — sha256 هگز خالص این خطر را ندارد ولی قاعده را عمومی نگه دارید.

## ۴. منابع

- RFC 8032 (EdDSA/Ed25519) · RFC 6962 (Certificate Transparency؛ شاهد append-only)
- الگوی Idempotency-Key در APIهای پرداخت (مستندات Stripe)
- پیش‌ثبت آزمایش‌های بالینی (clinicaltrials.gov؛ CONSORT)
- پیاده‌سازی مرجع این الگو در OCTOPUS: ‏`research/event_time_probe/` +
  رسیدهای امروز + `06-EVIDENCE/DIRECTIVE-12-REPORT-AGENT-B-2026-08-20.md`
