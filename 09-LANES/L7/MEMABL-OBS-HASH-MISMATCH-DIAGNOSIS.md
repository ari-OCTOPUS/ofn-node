# تشخیص ابطال MEMABL-OBS — mismatch متن‌هش در برابر بایت‌هش

GOV_VERSION=V8 · LADDER=L2 · VERIFIED_CASH=0  
scope: this_host_only · claim_type: filesystem + receipt · PROMPT 2 اجرا نشد.

## حکم

MEMABL-OBS در اجرای N3-B (۲۰۲۶-۰۹-۰۵) **قبل از هر نتیجهٔ علمی** باطل شد. علت:
پیش‌ثبت، هش **بایت خام** را قفل کرد؛ رانر همان فایل‌ها را با **حالت متن**
(`Path.read_text` → ترجمهٔ CRLF به LF → `encode("utf-8")`) دوباره هش کرد.
سه ماژول فیکسچر روی دیسک فقط CRLF داشتند؛ دو هش یکی نشدند؛ رانر با
`frozen source module hash mismatch` خروج ۱ داد. هیچ امتیاز Brier نوشته نشد.

این با `H1_STRONG_FAIL` بعدی N3V2 یکی نیست (اجرای جدا پس از تعویض به بایت‌هش).

## کجا mismatch شد (فایل:خط)

| نقش | مسیر | خط | روش |
|---|---|---|---|
| مقایسهٔ شکست‌خورده (preflight داخل رانر) | `F:\octo-exec\N3-REPRO-20260905\n3b_memabl_obs.py` | **91–96** | `sha256_text(Path.read_text(encoding="utf-8"))` در برابر `config["source_file_sha256"]` |
| تعریف text-hash | همان فایل | **24–25** | `hashlib.sha256(value.encode("utf-8")).hexdigest()` |
| هش prereg روی دیسک | همان فایل | **156** | `sha256_text(args.config.read_text(...))` — در این اجرا به آن نرسید |
| قفل بایت‌هش در پیش‌ثبت | `F:\octo-exec\N3-REPRO-20260905\receipts\N3B-PREREGISTRATION.json` | **18–22** | مقادیر `source_file_sha256` |
| تولید همان مقادیر | COMMAND-CHAIN sequence **107** `n3b-harness-static-validation` | argv در jsonl | `h=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()` |
| preflight نام‌دار که **گذراند** | COMMAND-CHAIN sequence **108** `n3b-preregistration-preflight` | argv در jsonl | فقط `read_bytes()` == prereg → `preflight: OK` |
| اجرا | COMMAND-CHAIN sequence **109** | return_code **1** | stderr: `frozen source module hash mismatch` |

`ofn/preflight.py` در کلون N3 مربوط به mode بوت است و این mismatch را مقایسه نکرد.

## مقادیر هش (منبع اجباری)

Prereg `source_file_sha256` = byte-hash (منبع: `N3B-PREREGISTRATION.json` خطوط 18–22 و stdout فرمان 107).

Text-hash در رسید 109 **چاپ نشد** (stdout خالی؛ sha256 فایل stdout = `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` = SHA-256 تهی). مقادیر متن زیر **بازسازی** شدند در 2026-09-08 با همان متد رانر روی فایل‌هایی که هنوز byte-hash آن‌ها با prereg یکی است (`unverified` به‌عنوان مقدار ثبت‌شده در 2026-09-05؛ reconstruction این جلسه):

| فایل | CRLF count (این جلسه) | byte-hash = prereg | text-mode hash (بازسازی) |
|---|---:|---|---|
| `octopus_observation/obs_fixture.py` | 123 | `7f4e181f51915df26b18f80e84391965a382fd1b45d2777ac4850e176df18c75` | `bdc6a07a6f53876f653a0ae5a64042477a61eea7013ed9a07b7bfb6bc3801be1` |
| `octopus_observation/producer_strategy.py` | 30 | `e84a9dde5e147df88f69e5a961fe07407be228fbc83be58a53190a14767d0e58` | `5b17ea47a2e1a9a279a345badfb0c01099b9e268e263ee232adc98c2f54ab8c3` |
| `octopus_observation/producer_persistence.py` | 24 | `830f823b93d42cd56adf05166ab5e5f9f3f4ff54a899d3525c154b8499b516d2` | `40490279a5ca1c2adb4ca87d9dbea1752bfe4527c2050c05b21e372c6d1e5c06` |

Prereg file byte-hash: `d0566b598588e58b46777cd5e6add7e6b5055526d76e2b69154791d31614aa33` (منبع: `N3-FINAL-REPORT.md` `N3B_PREREG_HASH` و stdout فرمان 108).

رسید 109: `entry_hash=2453a22dabe9ecb3c63ddeef6cf2bc5a2d0f2bea5659c581d6a3b839131ea223` · `stderr_sha256=0367c422b60cc1c955747eef7d432edc80cdab05a8b717ecac2bdf865f8ef180` · `return_code=1`.

## تناقض‌ها — status: open (حل‌نشده)

| claim | value_a | source_a | value_b | source_b | resolution | status |
|---|---|---|---|---|---|---|
| علت ابطال | «Unicode-normalized text hashes» | `N3-FINAL-REPORT.md` بخش N3-B | کد NFC/NFD ندارد؛ `read_text` ترجمهٔ newline است | `n3b_memabl_obs.py:91-96` | null | open |
| حکم MEMABL-OBS | `N3B_VERDICT=INVALID` | `N3-FINAL-REPORT.md` | `H1_STRONG_FAIL` هر دو seed | N3V2 `receipts/MEMABL-*-obs.json` | دو اجرای جدا | open |
| GATE-6 | MEMABL-OBS invalid | `07-HANDOFF/STATE-20260906.md` خط 17 | N3V2 Gate B بسته به‌خاطر fail علمی | `RUN-STATE.json` `memory_gate_b=CLOSED` | null | open |
| تست قبلی L7 | `tests/contract/test_l7_json_fields.py` ۲ پاس | `09-LANES/L7/LANE-REPORT.md` قبلی | فایل روی دیسک نیست | Test-Path این جلسه | null | open |

## اصلاح بعدی (خارج از این پاس — فقط زمینه)

N3V2 `harness/n3b_memabl_obs.py` خطوط 91–96 به `read_bytes()` عوض شد؛ `science.py` خط ۱ و ۱۲ همان را «corrected pre-freeze byte-hash plumbing» می‌نامد. آزمایش علمی دوباره در این پاس اجرا نشد.
