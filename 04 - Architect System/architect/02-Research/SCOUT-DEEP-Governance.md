---
type: research
project: "[[04 - Architect System/architect/PROJECT]]"
tags: [scout, deep-dive, governance, implementation, track-a]
status: done
created: 2026-07-03
sources: ["[[04 - Architect System/architect/02-Research/SCOUT-SUMMARY]]", "[[04 - Architect System/architect/02-Research/SCOUT-A]]", "[[04 - Architect System/architect/02-Research/SCOUT-C]]"]
updated: 2026-07-04
---

# SCOUT-DEEP — خوشه حاکمیت (کاندیدهای ② ③ ⑤ ⑥)

> **Run دوم Architecture Scout** — عمیق‌سازی TOP-7 تا سطح دستورالعمل پیاده‌سازی. این فایل چهار کاندید حاکمیتیِ [[04 - Architect System/architect/02-Research/SCOUT-SUMMARY|SCOUT-SUMMARY]] را پوشش می‌دهد؛ خوشه ماین (①④⑦) در `SCOUT-DEEP-Mining.md`.
> روش: ۴ ایجنت موازی + یک دور دوم ۳-ایجنتی برای بستن سوالات باز؛ فقط منابع اولیه (docs/repo/man pages/kernel patchwork) fetch شد. تگ‌ها مثل قبل: [Verified] / [Unverified] / [Inferred].
> **قید:** تا بسته‌شدن rotation (§Security Gate)، همه‌چیز فقط طراحی/نوت است — هیچ deploy.

---

## خلاصه اجرایی (۳۰ ثانیه)

چهار الگو، چهار **مرزِ** مکملِ حاکمیت که هیچ‌کدام دیگری را پوشش نمی‌دهد:

| مرز | الگو | جملهٔ هسته | هزینه | آماده؟ |
|---|---|---|---|---|
| **خرج/مدل** | ② LiteLLM | هیچ tool-call یا دلاری بدون عبور از پراکسی | S–M | بله (Postgres + بنچ RAM) |
| **تاریخ** | ③ anchoring | هیچ بازنویسیِ لاگ بدون رسوایی | S | بله (کاملاً verified) |
| **verdict** | ⑥ FIDO2 | هیچ تاییدی بدون لمس فیزیکی | S | بله (مسیر تلفن بسته → دو-tier) |
| **اجرا** | ⑤ lease/watchdog | هیچ گامی بدون مجوز زنده؛ غیاب سیگنال = توقف | S–M | تقریباً (تست /dev/watchdog روی برد) |

**ترتیب اجرا پیشنهادی:** ③ → ② → ⑥ → ⑤ (پایین، جدول کامل). همه پس از rotation.

**وضعیت سوالات باز run قبل — همه بسته شد:**

| سوال | نتیجه |
|---|---|
| status code بلاکِ tool_permission | **HTTP 400** هر دو مسیر (نه 403) [Verified: source] |
| پوشش streaming در guardrail | **بله، پوشش دارد** (buffer کامل → recheck) [Verified] |
| Key Rotation، Free یا Enterprise | on-demand = Enterprise؛ scheduled احتمالاً Enterprise → **مسیر Free بگیر** [Verified/Inferred] |
| sk در ssh داخلیِ ویندوز | **نه در build داخلی مستند** → MSI (libfido2 1.16.0) یا WSL2 [Verified] |
| ToS خودکارسازی DigiCert TSA | **مسکوت** (نه اجازه نه منع) → **freetsa را ترجیح بده** [Verified] |
| `/dev/watchdog0` روی Orange Pi | **بستگی به کرنل**: mainline/Armbian-edge بله؛ **BSP رسمی Orange Pi = نه، overlay لازم** [Verified] |

---

## ② LiteLLM به‌عنوان choke-point واحد

### وضعیت verified (July 2026)
- نسخه: **v1.86.2** (2026-05-27)، ریلیز تقریباً روزانه، imageها cosign-signed از v1.83.0 [Verified: github.com/BerriAI/litellm/releases]
- لایسنس: **MIT** به‌جز شاخه `enterprise/` [Verified: LICENSE]
- **همه اجزای موردنیاز ما Free/OSS هستند:** virtual keys، budgets (کلید/تیم/کاربر/global، چندپنجره‌ای)، `fail_closed_budget_enforcement`، **`tool_permission` guardrail** (کد در `litellm/proxy/guardrails/guardrail_hooks/tool_permission.py` — داخل شاخه MIT، نه enterprise) [Verified: docs.litellm.ai/docs/proxy/guardrails/tool_permission + GitHub contents API]
- Enterprise-only (لازم نداریم): `/key/regenerate`، audit logs داخلی، model-specific key budgets [Verified]

### شرط‌های سخت
1. **Postgres اجباری است** برای virtual keys — مسیر SQLite/سبک‌تر در ۲۰۲۶ وجود ندارد [Verified: docs/proxy/virtual_keys]
2. **بودجه‌ها به USD هستند** — سقف D-25 (AU$30) ≈ **US$19** [Inferred: نرخ ~۰٫۶۵ — هنگام set چک شود]
3. باگ باز: image `linux/arm64` بعضی tagها باینری amd64 دارد (manifest mislabeled) → روی Orange Pi قبل از اعتماد: `docker manifest inspect` + boot test [Verified: GitHub issue]
4. RAM مستند فقط برای prod بزرگ است (۸GB/۴core)؛ **عدد سبک solo جایی منتشر نشده — باید روی برد اندازه گرفت** [Verified: نبودِ عدد]

### config.yaml — فقط کلیدهای verified
```yaml
model_list:
  - model_name: claude-worker
    litellm_params:
      model: anthropic/claude-sonnet-4-5
      api_key: os.environ/ANTHROPIC_API_KEY

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
  database_url: os.environ/DATABASE_URL          # postgres — اجباری برای virtual keys
  fail_closed_budget_enforcement: true           # spend غیرقابل‌تایید => 503
  alerting: ["webhook"]                          # WEBHOOK_URL => پل تلگرام
  alert_types: ["budget_alerts", "spend_reports", "db_exceptions", "failed_tracking_spend"]

litellm_settings:
  max_budget: 19            # سقف global USD ~= AU$30 (adapted)
  budget_duration: 30d

guardrails:
  - guardrail_name: "tool-permission-guardrail"
    litellm_params:
      guardrail: tool_permission
      mode: "post_call"
      default_on: true      # بدون این، guardrail فقط on-request اجرا می‌شود => fail-open خاموش
      rules:
        - id: "allow_safe_tools"
          tool_name: "^(read_file|search)$"
          decision: "allow"
        - id: "mail-domain"
          tool_name: "^send_email$"
          decision: "allow"
          allowed_param_patterns:
            "to[]": "^.+@yourdomain\\.example$"
      default_action: "deny"
      on_disallowed_action: "block"   # block = درخواست halt؛ rewrite = حذف tool + پیام خطا در پاسخ
```
schema قواعد (verbatim از docs): `id`، `tool_name` (regex)، `tool_type` (regex)، `decision: allow|deny`، `allowed_param_patterns` (regex روی مسیر آرگومان‌ها با نوتیشن نقطه و `[]`) — **enforcement سطح پارامتر واقعاً وجود دارد** [Verified].

**رفتار دقیق (verified از سورس `tool_permission.py`، شاخه main):**
- **block:** مسیر pre-call (چک `tools` درخواست) `raise HTTPException(status_code=400, detail={"error":"Violated guardrail policy","detection_message":msg})`؛ مسیر post-call (چک `tool_calls` پاسخ) `GuardrailRaisedException` با `status_code` پیش‌فرض ۴۰۰ → **هر دو مسیر HTTP 400 (نه 403)** [Verified: raw litellm/proxy/guardrails/guardrail_hooks/tool_permission.py + exceptions.py]
- **rewrite:** بدون exception؛ tool مجازنشده از `data["tools"]`/`functions` حذف و `tool_choice`/`function_call` = `"none"`؛ سمت پاسخ `tool_calls` فیلتر (یا `None`) و رشته `"Permission denied: {message} (Rule: {rule_id})"` به `content` افزوده می‌شود [Verified: source]
- **streaming:** ✅ **پوشش دارد** — `async_post_call_streaming_iterator_hook` همه chunkها را buffer می‌کند، با `stream_chunk_builder` بازسازی، همان چک را می‌زند و via `MockResponseIterator` دوباره emit می‌کند (کل stream قبل از yield buffer می‌شود) [Verified: source]. یعنی سوال باز run قبل بسته شد.

### صدور کلید و بودجه پشته‌ای (الگوی ضد-runaway)
```bash
curl http://0.0.0.0:4000/key/generate -H "Authorization: Bearer <master>" -d '{
  "models": ["claude-worker"],
  "budget_limits": [
    {"budget_duration": "24h", "max_budget": 1},
    {"budget_duration": "30d", "max_budget": 15}
  ],
  "tpm_limit": 20000, "rpm_limit": 10, "soft_budget": 12
}'
```
یک روز runaway نمی‌تواند ماه را بخورد (24h نیمه‌شب UTC ریست، 30d اول ماه) [Verified: docs/proxy/users]. خطای بودجه: کلید → 400 `ExceededTokenBudget`؛ customer → 401؛ spend غیرقابل‌تایید با فلگ fail-closed → **503** [Verified].

### استقرار و ادغام با fusion-mvp
- **جانمایی [Inferred]:** پراکسی + Postgres روی Orange Pi 5 (always-on، کلیدهای provider از PC ایجنت‌ها جدا می‌شوند)؛ ایجنت‌ها فقط virtual key + `base_url` پراکسی.
- **Egress enforcement [Inferred — در docs نیست ولی همان چیزی است که پراکسی را غیرقابل‌دورزدن می‌کند]:** ایجنت‌ها با user اختصاصی `agent`؛ nftables خروجی: `meta skuid agent ip daddr <pi> tcp dport 4000 accept; meta skuid agent counter drop` + بستن/pin کردن DNS برای همان user. هم‌افزا با srt (A12).
- **پل تلگرام:** webhook پراکسی JSON می‌فرستد (`"event": "budget_crossed" | "threshold_crossed"(85%/95%) | "projected_limit_exceeded"`) → یک bridge ~۳۰ خطی FastAPI روی Pi → Bot API [spec Verified؛ bridge Inferred].
- **دکمه panic:** `/key/block` فوری و برگشت‌پذیر و Free — مستقیم از بات تلگرام [Verified].

### گوچاهای fail-open (چک‌لیست ضد-خطا)
1. `default_on: true` یادت نرود — وگرنه guardrail همیشه اجرا نمی‌شود [Verified فلگ؛ پیامد Inferred]
2. `max_budget` پیش‌فرض **null** = بدون سقف [Verified]
3. `allow_requests_on_db_unavailable: True` را **هرگز** set نکن — fail-open مستند [Verified: docs/proxy/prod]
4. rate-limitها روی کلید admin اعمال نمی‌شوند → کلید admin هرگز دست ایجنت [Verified]
5. spend batch هر ۶۰s + چک ریست بودجه هر ~۱۰min → پنجره کوچک overshoot [Verified کلیدها؛ پیامد Inferred]

### Rollback و ریسک
- پراکسی پایین = کل پایپ‌لاین پایین (پذیرفته — این همان choke-point است). mitigation: systemd `Restart=always` + مانیتور `/health/readiness` از بات [Inferred].
- rollback کامل: برگشت کلیدهای provider به ایجنت‌ها (کپی sealed آفلاین نگه دار) [Inferred].
- **هزینه پذیرش: S–M** (~۳–۵ ساعت نصب/میزان‌سازی + اندازه‌گیری RAM روی برد).

### چرخش کلید (سوال باز run قبل — بسته شد)
- **on-demand `/key/{key}/regenerate` = ✨ Enterprise** (docs صریح: "This is an Enterprise feature") [Verified: docs/proxy/virtual_keys].
- **Scheduled rotation** (`LITELLM_KEY_ROTATION_ENABLED=true` + `auto_rotate`/`rotation_interval`) زیر همان بخش Enterprise و بدون مارکر جدا؛ مسیر ایمیل چرخش در کد `litellm_enterprise` را hard-require می‌کند → **به‌احتمال زیاد Enterprise** [Verified مارکر + کد؛ گیت لایسنسِ خودِ worker Unverified].
- **نتیجه عملی:** rotation را با مسیر **Free** بزن — `/key/generate` کلید نو + `/key/block` کهنه (همان دکمه panic). Enterprise لازم نیست.

### سوالات باز باقی‌مانده ②
- RAM واقعی proxy+Postgres روی ARM64 → **بنچ روی برد** (هیچ عدد منتشرشده‌ای نیست؛ تنها سوال واقعاً بازِ این کاندید).
- حداقل نسخهٔ معرفی `fail_closed_budget_enforcement` قابل‌pin نشد (روی main تاریخ ۲۰۲۶-۰۷-۰۳ حاضر و OSS است) [Verified حضور؛ نسخه Unverified] — کم‌اهمیت چون نسخهٔ فعلی داردش.

---

## ③ انکر خارجی سرِ Anchor Ledger (OTS + git + RFC 3161)

### وضعیت verified
- `opentimestamps-client` **v0.7.2** (Dec 2024 — همچنان آخرین)، LGPL-3.0، `pip3 install opentimestamps-client` [Verified: repo]
- کالندرهای پیش‌فرض ۴ تا، قاعده **2-of-4**، رایگان و بدون اکانت؛ هر ۴ تا امروز 200 OK [Verified: uptime.opentimestamps.net]
- freetsa.org زنده (cert جدید Mar 2026، اعتبار تا 2040) · DigiCert TSA رایگان (`http://timestamp.digicert.com`) · DFN فقط غیرتجاری [Verified]
- sigstore/timestamp-authority v2.1.2 فعال است **ولی self-host برای threat model ما بی‌فایده: TSA در همان دامنه اعتماد مالک دیسک** [Verified وجود؛ ارزیابی Inferred] → SKIP.

### ⚠ تصحیح نسبت به SCOUT-SUMMARY
1. **`ots stamp` فلگ digest ندارد — فقط FILE می‌گیرد** (`args.py`: `type=argparse.FileType('rb')`). پس head hash اول در فایل نوشته می‌شود. فلگ `-d DIGEST` فقط روی `verify` است و همان SHA256 فایلِ stamp-شده است [Verified: args.py, cmds.py].
2. **`ots verify` به Bitcoin Core node نیاز دارد (pruned کافی است)** [Verified: README]. بدون node: `--no-bitcoin` → فقط block height + merkleroot چاپ می‌کند و باید دستی با explorer چک کنی (اعتماد به explorer) [Verified: cmds.py]. fallback داخلی به explorer وجود ندارد.
3. اگر <۲ کالندر در ۵s جواب دهند، stamp **کلاً fail می‌شود** (proof pending هم ساخته نمی‌شود) → صف spool-and-retry لازم است [Verified: cmds.py].

### اسکریپت anchor (هر خط تگ‌دار)
```bash
#!/usr/bin/env bash
set -euo pipefail
SEQ="$1"; HEAD_HEX="$2"                    # از پایپ‌لاین پایتون                [design]
A="anchors/${SEQ}"; mkdir -p "$A"
printf '%s' "$HEAD_HEX" > "$A/head.txt"    # ots فایل می‌خواهد                  [Verified]
ots stamp "$A/head.txt"                    # => head.txt.ots ؛ fail اگر <2/4 کالندر [Verified]
git -C anchors-repo add -A && git -C anchors-repo commit -m "anchor seq=${SEQ} head=${HEAD_HEX}" \
  && git -C anchors-repo push origin main  #                                    [Inferred design]
openssl ts -query -digest "$HEAD_HEX" -sha256 -no_nonce -cert -out "$A/head.tsq"
                                           # digest مستقیم؛ فایل لازم نیست       [Verified: openssl-ts man]
curl -sS -H "Content-Type: application/timestamp-query" --data-binary "@$A/head.tsq" \
  https://freetsa.org/tsr > "$A/head.freetsa.tsr"                    # [Verified: رسپی خود freetsa]
curl -sS -H "Content-Type: application/timestamp-query" --data-binary "@$A/head.tsq" \
  http://timestamp.digicert.com > "$A/head.digicert.tsr"             # [URL Verified؛ الگو Inferred]
cp /etc/ssl/anchor-certs/freetsa-{tsa.crt,cacert.pem} "$A/" || true  # آرشیو chain هنگام stamp [Inferred]
```
- **آرشیو cert chain per-anchor حیاتی است** — چرخش واقعاً رخ می‌دهد: freetsa در Mar 2026، DFN در Jun 2026، DigiCert ≤۱۵ ماه [Verified]. verify بعدی با `-CAfile`/`-untrusted` آرشیوی + در صورت انقضا `-attime` [Verified: manpage].
- شب‌ها: `ots upgrade anchors/*/head.txt.ots` تا proofهای pending کامل شوند (چند ساعت تا تایید Bitcoin) [Verified: README].
- آفلاین (سولار/قطع‌ووصل): head به `anchors/spool/` و retry با تایمر [design].

### Runbook حسابرس (۶ ماه بعد)
1. زنجیره hash را محلی بازمحاسبه کن؛ head ادعایی seq N را دربیار.
2. `ots upgrade` سپس `ots verify` با node (pruned) → "Bitcoin block X attests existence as of DATE" [Verified].
3. `openssl ts -reply -in head.tsr -text` برای genTime؛ سپس `-verify` با chain آرشیوی → "Verification: OK" [Verified].
4. clone از remote؛ تطبیق head فایل commit با proofها؛ پیوستگی seq بدون gap [Inferred].

### جدول threat-model (هر انکر چه می‌خرد)
| انکر | اثبات می‌کند | نمی‌کند / ضعف |
|---|---|---|
| OTS | وجود head قبل از بلاک T؛ رایگان؛ فقط digest+nonce خارج می‌شود [Verified: README Privacy] | حذف رکوردهای بعدی؛ نیاز به node برای verify کامل |
| git remote | نسخه off-box در دامنه credential جدا [Inferred] | **GitHub برای مالکِ خودش immutability نیست**: admin bypass، ویرایش/حذف ruleها، force-push؛ protected branch در план Free فقط repo عمومی [Verified: GitHub docs] → نقش = افزونگی، نه شاهد |
| RFC 3161 | امضای authority روی (digest، genTime) — فوری، بدون تاخیر تایید | تمرکز اعتماد در یک TSA؛ وابستگی verify بلندمدت به chain آرشیوی [Verified] |

**پنجره صادقانه: هرچه قبل از اولین انکرِ همان رکورد بازنویسی شود، هیچ‌کدام نمی‌گیرند** → verdictهای HITL را event-driven (لحظه ثبت) انکر کن، بقیه ساعتی [Inferred — پیشنهاد]. هزینه per-event ≈ صفر [Verified: donation-funded].

**TSA کدام؟ (سوال باز run قبل — بسته شد):** ToS خودکارسازیِ پایدار DigiCert **در KB مسکوت است** (نه اجازه نه منع صریح؛ صفحه code-signing-محور، ممکن است هر لحظه rate-limit کند) [Verified: نبودِ بند]. در مقابل **freetsa.org سیاست صریحِ عمومی و بدون سهمیه دارد** ("do not abuse") و خودش را RFC-3161 SaaS عمومی معرفی می‌کند [Verified: freetsa.org] → **freetsa را TSA اصلی بگیر، DigiCert را فقط به‌عنوان دومِ best-effort.** گزینهٔ Sectigo تایید نشد [Unverified].

- **هزینه پذیرش: S** (~۱–۲ ساعت + cron/spool).
- سوالات باز باقی‌مانده: retention شواهد pre-force-push در GitHub Events API [Unverified] · تست کلاینت روی ARM64 [Unverified].

---

## ⑤ Kill-switch به‌مثابه de-energize: lease + watchdog + halted-safe

### شواهد سخت‌افزار (RK3588 / Orange Pi 5)
| ادعا | وضعیت |
|---|---|
| WDT داخلی RK3588 = Synopsys DesignWare (`dw_wdt`) | [Verified: wiki.t-firefly.com Core-3588J usage_watchdog] |
| binding مین‌لاین: `rockchip,rk3588-wdt` + fallback `snps,dw-wdt` | [Verified: torvalds/linux snps,dw-wdt.yaml] |
| timeout کوانتیزه: {1, 2, 5, 11, 22, 44, **89s سقف**} | [Verified: جدول Firefly] |

**`/dev/watchdog0` هست یا نه؟ (سوال باز run قبل — بسته شد): بستگی به کرنلِ image دارد.**

| کرنل image | `/dev/watchdog0` out-of-box؟ | شاهد |
|---|---|---|
| **Mainline** (Linux ≥ 6.4؛ Armbian *edge*) | **بله** — پیش‌فرض enabled | پچ merge‌شده در 6.4 نود `wdt` را **بدون خط status** اضافه می‌کند → default = okay [Verified: patchwork.kernel.org …shreeya.patel…] |
| **Armbian** (OPi5، edge = mainline) | **بله** (edge)؛ شاخهٔ legacy/BSP = تابع BSP | rockchip64 edge مین‌لاین 6.x/7.x است؛ watchdog در پچ‌ست out-of-tree نیست [Verified: armbian.com/orangepi-5 + rcawston patches] |
| **BSP 5.10 رسمی** (image خود Orange Pi، Ubuntu-Rockchip) | **نه — overlay لازم** | BSP `rk3588s.dtsi` نود را `status = "disabled"` می‌گذارد [Verified: Firefly wiki] |

board DTSهای Orange Pi 5 (`rk3588-orangepi-5.dtsi`) هیچ override `&wdt` ندارند [Verified] → نتیجه فقط با status سطح-SoC تعیین می‌شود. **image رسمی Orange Pi = BSP → باید overlay بزنی؛ Armbian edge = آماده.** چک روی برد و overlay در انتهای ⑤.

⚠ دو تصحیح: `KillWatchdogSec=` وجود ندارد (سه‌گانه واقعی: `RuntimeWatchdogSec/RebootWatchdogSec/KExecWatchdogSec`) و «10s» پیشنهادی SCOUT-A عملاً به TOP یازده‌ثانیه‌ای گرد می‌شود [Verified: systemd-system.conf(5) man7.org].

### قطعات systemd (همه دایرکتیوها verified از man pages)
```ini
# /etc/systemd/system.conf.d/60-watchdog.conf
[Manager]
RuntimeWatchdogSec=30        # dw_wdt به TOP مجاز (44s) گرد می‌کند [Inferred]
RebootWatchdogSec=2min
WatchdogDevice=/dev/watchdog0
```
```ini
# fusion-agent.service — هرگز enable نمی‌شود؛ فقط supervisor مسلح start می‌کند
[Unit]
ConditionPathExists=/run/fusion/armed   # /run در بوت پاک می‌شود => پیش‌فرض disarmed
BindsTo=fusion-supervisor.service
After=fusion-supervisor.service
OnFailure=fusion-failsafe.service
[Service]
Type=notify
ExecStart=/usr/bin/python3 /opt/fusion/agent.py
WatchdogSec=90               # > بدترین گام LLM؛ pet از thread جدا نه thread منتظرِ مدل
Restart=no                   # ایجنتِ مرده حق self-resurrect ندارد
TimeoutStopSec=20
# بدون [Install] => در هیچ بوتی pull نمی‌شود
```
```ini
# fusion-failsafe.service (Type=oneshot) — روی هر failure
ExecStart=/bin/rm -f /run/fusion/armed
ExecStart=/usr/bin/systemctl kill --signal=SIGKILL --kill-whom=cgroup 'fusion-agent*.service'
ExecStart=/opt/fusion/bin/telegram-alert "FAILSAFE: halted"
```
- semantics: `WatchdogSec` → نبود `WATCHDOG=1` در بازه = SIGABRT و failed [Verified: systemd.service(5)] · `OnFailure` = فعال‌سازی unit escalation [Verified: systemd.unit(5)] · `ConditionPathExists` شکست = skip بی‌صدا [Verified] · پاک‌شدن /run در بوت = تضمین FHS 3.0 [Verified: refspecs].
- **pet کردن از پایتون:** پیاده‌سازی رسمیِ بدون‌وابستگی داخل خود man page sd_notify(3) (دیتاگرام AF_UNIX به `$NOTIFY_SOCKET`) — همین را بردار؛ پکیج `sdnotify` از 2017 مرده است [Verified: pypi] · بونوس: `WATCHDOG=trigger` برای خود-گزارش‌دهی خطا [Verified: sd_notify(3)].
- caveat مستند: Conditionها برای شرطی‌کردن dependency مناسب نیستند → supervisor خودش هم arming را چک کند [Verified caveat؛ نتیجه Inferred].

### دکترین lease (prior art → نگاشت ما)
- **etcd**: lease با TTL؛ نبود keepAlive = انقضا؛ revoke = حذف کلیدهای متصل [Verified: etcd.io docs]
- **Kubernetes**: `coordination.k8s.io` Lease؛ heartbeat = آپدیت `spec.renewTime` [Verified: kubernetes.io]
- **Consul sessions** (میراث Chubby): invalidation با TTL/destroy؛ توصیه renew-in-advance؛ `lock-delay` ضد-flapping؛ sequencer برای کشف holder کهنه [Verified: developer.hashicorp.com]
- **Kleppmann**: lease تنها کافی نیست — **fencing token** صعودی لازم است و منبعِ محافظت‌شده باید توکن عقب‌رفته را reject کند؛ انقضا با clock مونوتونیک نه wall-clock [Verified: martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html]

**نگاشت به fusion-mvp [Inferred]:** IGK = مرجع lease. lease امضاشده HMAC = `{lease_id, fencing_counter (مونوتونیک، persisted), issued_mono, ttl 10–30s}`. orchestrator در ttl/3 تمدید می‌کند؛ هر گام side-effect دار lease معتبر ارائه می‌دهد؛ گیت‌وی‌های side-effect (file-writer، egress، audit-sink) امضا + تازگی + عدم-پس‌رفت fencing را چک می‌کنند. STOP = revoke + توقف تمدید. مرگ/قطع kernel ⇒ شکست تمدید ⇒ انقضا ⇒ halt. **غیاب مجوز = توقف** (ISO 13850). state فقط زیر /run ⇒ هر reboot = disarmed.

#### پیاده‌سازی مرجع (اسکلت — طراحی، نه کد آماده prod)

دو نکتهٔ صحت که پیاده‌سازی ساده را می‌شکنند: (۱) **fencing token خط اول دفاع است، نه TTL** — کلپمن ثابت می‌کند lease معلق‌شده/resume‌شده می‌تواند بعد از expire هنوز بنویسد؛ تنها ضمانت، رد توکنِ عقب‌رفته توسط خودِ منبع است. (۲) **مونوتونیک فقط hostِ واحد** — `time.monotonic()` بین PC و Orange Pi قابل‌مقایسه نیست؛ verifier تازگی را با ساعت مونوتونیکِ *خودش از لحظهٔ دریافت* می‌سنجد، نه با `issued_mono`ِ صادرکننده.

```python
# igk/lease.py  — سمت kernel (صادرکننده)   [Inferred design روی prior art Verified]
import hmac, hashlib, json, time, threading

class LeaseAuthority:
    def __init__(self, key: bytes, ttl_s: float = 15.0):
        self._key = key                 # همان کلید HMAC ممیزی kernel (R-02)
        self._ttl_ns = int(ttl_s * 1e9)
        self._epoch = 0                 # STOP = افزایش این
        self._fence = _load_persisted_counter()   # صعودی، روی دیسک persist
        self._lock = threading.Lock()

    def issue(self, holder: str) -> dict:
        with self._lock:
            if self._epoch_stopped():   # بعد از STOP هیچ lease جدیدی نه
                raise PermitDenied("kill-switch engaged")
            self._fence += 1; _persist_counter(self._fence)
            body = {"holder": holder, "fence": self._fence,
                    "epoch": self._epoch,
                    "issued_mono_ns": time.monotonic_ns(),  # فقط برای host واحد
                    "ttl_ns": self._ttl_ns}
        raw = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
        sig = hmac.new(self._key, raw, hashlib.sha256).hexdigest()
        return {"body": body, "sig": sig}

    def stop(self):                     # دکمهٔ kill (تلگرام/بات)
        with self._lock: self._epoch += 1; _persist_epoch(self._epoch)
```
```python
# gateway/verify.py  — هر side-effect gateway (file-writer/egress/audit)   [Inferred]
import hmac, hashlib, json, time

_last_fence = -1                        # per-gateway، در حافظه کافی است
_recv_mono  = {}                        # fence -> لحظهٔ دریافت (ساعت خودِ gateway)

def admit(lease: dict, key: bytes, current_epoch: int) -> bool:
    raw = json.dumps(lease["body"], sort_keys=True, separators=(",", ":")).encode()
    if not hmac.compare_digest(                      # ۱) امضا
            hmac.new(key, raw, hashlib.sha256).hexdigest(), lease["sig"]):
        return False
    b = lease["body"]
    if b["epoch"] != current_epoch:                  # ۲) epoch جاری (STOP → رد)
        return False
    global _last_fence
    if b["fence"] < _last_fence:                     # ۳) fencing: هرگز عقب نه (کلپمن)
        return False
    _last_fence = max(_last_fence, b["fence"])
    now = time.monotonic_ns()                        # ۴) تازگی با ساعت خودِ gateway
    first = _recv_mono.setdefault(b["fence"], now)
    return (now - first) <= b["ttl_ns"]              # منقضی از لحظهٔ دریافت، نه صدور
```

مسیر renew: orchestrator هر `ttl/3` (قاعدهٔ renew-in-advance کنسول) یک lease نو می‌گیرد؛ چون هر issue، `fence` را +۱ می‌کند، gatewayها همیشه توکن روبه‌جلو می‌بینند. **STOP** = `authority.stop()` → `epoch` بالا می‌رود → leaseهای موجود در چک ۲ رد می‌شوند و issueِ جدید هم `PermitDenied` می‌دهد. `current_epoch` را gatewayها از kernel می‌خوانند؛ اگر kernel مرده باشد و epoch در دسترس نباشد → **fail-closed** (رد). این با R-05 (timeout روی IPC kernel) یکی می‌شود.

هشدار طراحی [Inferred]: `_recv_mono` نباید بی‌نهایت رشد کند — با یک TTL-sweep یا حلقهٔ ثابت پاک شود؛ و برای egress که روی Orange Pi و ایجنت روی PC است، خودِ LiteLLM proxy نقش gateway تازگی را بازی می‌کند (زمان دریافت خودش).

### نگاشت Cat-0 / Cat-1 و de-energize واقعی
| دسته | مکانیزم | مبنا |
|---|---|---|
| Cat-1 (توقف کنترل‌شده) | `systemctl stop` → SIGTERM → `TimeoutStopSec` → SIGKILL | [Verified: systemd.service(5)] |
| Cat-0 (فوری، سطح process) | `systemctl kill --signal=SIGKILL --kill-whom=cgroup <unit>` | [Verified: systemctl(1)] |
| Cat-0 واقعی (برق) | Shelly Gen2+: JSON-RPC محلی `curl "http://<ip>/rpc/Switch.Set?id=0&on=false"` از **دستگاه دوم** | [Verified: shelly-api-docs RPC؛ «بدون cloud» Inferred] |

### حالت‌های خرابی + طرح تست
- reboot-loop: `StartLimitIntervalSec/Burst` (پیش‌فرض 10s/5) + `MinimumUptimeSec` (systemd 261، پیش‌فرض 15s) [Verified] — و چون بوت disarmed است، loop بی‌ضرر می‌چرخد [Inferred].
- lease با CLOCK_MONOTONIC (نقد gettimeofday کلپمن) [Verified] · lease در tmpfs = پاک‌شدن مطلوب [Verified FHS].
- WDT وسط LLM-call طولانی: pet در thread مستقل + `WatchdogSec` > بدترین stall؛ HW-WDT را PID 1 pet می‌کند و ربطی به app ندارد [Verified].
- خطر فساد eMMC در ریست‌های مکرر → fs ژورنال‌دار + حداقل نوشتن [Inferred]؛ ابزار تشخیصی: `RuntimeWatchdogPreSec/PreGovernor` [Verified].

تست‌ها (همه دستورها verified):
1. `systemctl kill --signal=SIGSTOP fusion-supervisor.service` → ایجنت‌ها ≤ TTL halt؛ سپس مسیر OnFailure → disarm.
2. `systemctl kill --signal=SIGKILL --kill-whom=main igk.service` → orchestrator باید fail-closed شود (جفتِ R-05).
3. `echo c > /proc/sysrq-trigger` (crash کرنل) [Verified: kernel.org sysrq] → WDT reboot → assert: `/run/fusion/armed` غایب، agent unit ها enabled نیستند.
4. باز کردن `/dev/watchdog` و توقف pet → ریست [Verified: Firefly].

#### چک روی برد + overlay (اگر image رسمی Orange Pi/BSP باشد)
```sh
ls -l /dev/watchdog*                                   # هست؟ → mainline/edge، تمام
dmesg | grep -i -e dw_wdt -e watchdog                  # probe درایور
cat /sys/class/watchdog/watchdog0/{identity,state} 2>/dev/null
```
اگر غایب بود (BSP)، overlay مینیمال [Verified: Firefly `&wdt{status="okay"}`]:
```dts
/dts-v1/; /plugin/;
&wdt { status = "okay"; };
```
روی Armbian: `armbian-add-overlay rk3588-wdt.dts` · روی BSP رسمی: همین تغییر در DTS برد + rebuild.

- **هزینه پذیرش: S–M** (~۴–۸ ساعت طراحی+تست؛ روی Armbian-edge صفرِ سخت‌افزاری، روی image رسمی + یک overlay).
- سوالات باز باقی‌مانده: pretimeout governor روی dw_wdt [Unverified] · استقلال lease-issuer از زنجیره watchdog برای پرهیز common-mode [تصمیم طراحی].

---

## ⑥ Verdict غیرقابل‌انکار + ضد-fatigue (FIDO2 + schema ۴حالته + sterile)

### ⚠ یافته تعیین‌کننده — مسیر تلفن بسته است
**WebAuthn داخل Telegram کار نمی‌کند:** Mini Apps webview آن را ساپورت نمی‌کند (feature-request باز #52، بدون تعهد تلگرام) و دسکتاپ هم passkey ندارد (tdesktop #30083) [Verified: هر دو issue]. پس معماری صادقانه دو-tier است:
- **Tier بحرانی (برگشت‌ناپذیر/مالی/config):** لمس کلید سخت‌افزاری روی PC.
- **Tier روتین:** دکمه‌های inline تلگرام + typed challenge (بدون رمزنگاری سخت‌افزاری).

### مسیر اصلی: python-fido2 (پیشنهاد [Inferred])
- **v2.2.0** (Apr 2026، شامل فیکس YSA-2026-01)، BSD-2، Python ≥3.10، تست‌شده Win/macOS/Linux [Verified: repo/releases]
- challenge سفارشی first-class: `authenticate_begin(..., challenge=...)` — bytes ≥16؛ ما `sha256(canonical_verdict_json)` (۳۲ بایت) می‌گذاریم [Verified: server.py]
- headless بدون مرورگر (CTAP2 روی USB HID) [Verified: examples/credential.py]
- **ویندوز بدون admin**: از مسیر `fido.client.WindowsClient` (WebAuthn API نیتیو)؛ دسترسی raw-HID بدون آن admin می‌خواهد [Verified: README verbatim] · لینوکس: udev rule [Verified]
- verify آفلاین ابدی: ذخیره `{credential_id, client_data_json, authenticator_data, signature}` per verdict؛ چک `public_key.verify(auth_data + client_data.hash, signature)` + تطبیق challenge + فلگ‌های UP/UV [Verified: server.py]

### مسیر جایگزین صفر-کد: OpenSSH sk
```
ssh-keygen -t ed25519-sk -O verify-required          # ساخت؛ verify-required = PIN per signature
ssh-keygen -Y sign -f key -n verdict@farm.local file # امضا (namespace اجباری)
ssh-keygen -Y verify -f allowed_signers -I ari -n verdict@farm.local -s file.sig < file
```
[Verified: man.openbsd.org/ssh-keygen، به‌روز Jul 1 2026].

**ویندوز (سوال باز run قبل — بسته شد):** پشتیبانی FIDO **compile-time و وابسته به libfido2** است (README فورک مایکروسافت: "FIDO security token support needs libfido2 … enabled automatically if they are found") [Verified: openssh-portable README]. **build داخلیِ ویندوز** (OpenSSH.Client optional feature) در هیچ صفحهٔ Microsoft Learn به FIDO2/security-key/`ed25519-sk` اشاره نمی‌کند [Verified: هر دو صفحهٔ Learn] → **فرض کن sk ندارد.** مسیر verified: **MSI رسمی Win32-OpenSSH** (بستهٔ libfido2 1.16.0، MSI برای ARM64 هم) یا **WSL2 با USB passthrough** (توصیهٔ خود Yubico) [Verified: releases + developers.yubico.com]. → روی PC ویندوز، مسیر **python-fido2** (که خودش WebAuthn نیتیو ویندوز را می‌زند، بدون admin) از این دردسر آزاد است و ترجیح دارد.

### Schema چهارحالته (verbatim از agent-inbox) و نگاشت تلگرام
```python
class HumanInterruptConfig(TypedDict):
    allow_ignore: bool; allow_respond: bool; allow_edit: bool; allow_accept: bool
class ActionRequest(TypedDict):
    action: str; args: dict
class HumanInterrupt(TypedDict):
    action_request: ActionRequest; config: HumanInterruptConfig; description: Optional[str]
class HumanResponse(TypedDict):
    type: Literal['accept','ignore','response','edit']; args: Union[None, str, ActionRequest]
```
[Verified: github.com/langchain-ai/agent-inbox README]. نگاشت [Inferred]: `description` = بدنه پیام؛ ردیف ۱: ✅ Accept / 🚫 Ignore؛ ردیف ۲: ✏️ Edit / 💬 Respond (با ForceReply)؛ دکمه‌ها = همان چهار boolean؛ `callback_data` حامل nonce هر run (جفتِ R-02).

### شواهد ضد-fatigue و UX
- «کاربران Claude Code ۹۳٪ promptها را approve می‌کنند» + «approval fatigue» + FNR کلاسیفایر ۱۷٪ → گیت بحرانی را کامل به مدل نسپار [Verified: anthropic.com/engineering/claude-code-auto-mode]
- Sterile Flight Deck (ICAO): «بازه‌ای که خدمه نباید مختل شوند مگر امر حیاتی» [Verified: skybrary]
- UX [Inferred]: (۱) گیت سخت‌افزاری فقط برای برگشت‌ناپذیر/مالی/config — بقیه log-and-proceed یا digest روزانه؛ (۲) **retype پارامترِ بار-بردار** (مبلغ/پسوند آدرس/hostname) نه «yes»؛ (۳) sterile mode: صف‌کردن همه پیام‌های غیربحرانی تا صدور verdict + امضا؛ (۴) صدا/هدر اختصاصی فقط برای گیت سخت‌افزاری.

### سخت‌افزار
- **Yubico Security Key C NFC — US$29** [Verified: listing] · ارزان‌تر: Token2 (€7–23؛ از R3.3 پیش‌فرض `always_uv=true` — برای ما مطلوب) [Verified] · **SoloKeys v2 نخر — پروژه عملاً مرده** [Verified: retrospective Feb 2026]
- **دو کلید از روز اول** (backup enroll شود) [Verified توصیه Yubico] · PIN lockout: ۸ تلاش کل → بلاک و فقط factory-reset (پاک‌شدن credentialها)؛ ۳ پیاپی → reinsert [Verified: Yubico docs]

### جریان ادغام با R-02 و ضد-downgrade
kernel صادر می‌کند nonce → بات گیت + فیلد typed-challenge → helper روی PC می‌سازد `verdict={nonce, action_hash, decision, ts}` → challenge=SHA-256 → لمس (+PIN) → assertion داخل رکورد HMAC-audit کرنل → head انکر خارجی (③). replay با nonce مرده؛ box روت‌شده نمی‌تواند جعل کند (کلید خصوصی هرگز خارج نمی‌شود) [Verified اصل؛ جریان Inferred].
**ضد-downgrade:** فلگ خاموش‌کردن FIDO2 خودش یک اکشن FIDO2-گیت‌دار + بیتِ «FIDO2 فعال» داخل header رکوردهای HMAC تا flip خاموش، verify زنجیره را بشکند [Inferred؛ هم‌ارز قاعده «تغییر config مجوزِ خودِ ایجنت = block» در پست auto-mode [Verified]].

- **هزینه پذیرش: S** (~۳–۴ ساعت + US$58 دو کلید).
- سوالات باز باقی‌مانده: مسیر libfido2 همراه MSI بدون admin از Windows Hello می‌گذرد؟ [Unverified — تست elevated/non-elevated] · رفتار python-fido2 روی hidraw برد ARM64 [Unverified]. (سوال «ssh داخلی ویندوز sk دارد؟» بسته شد: نه در مستندات → مسیر python-fido2/MSI/WSL2.)

---

## هم‌بندی چهار الگو + ترتیب اجرا

چهار مرز مکمل: **② مرز مدل/خرج** (هیچ tool-call یا دلاری بدون عبور از پراکسی) · **⑤ مرز اجرا** (هیچ گامی بدون lease زنده) · **⑥ مرز verdict** (هیچ تاییدی بدون لمس فیزیکی) · **③ مرز تاریخ** (هیچ بازنویسی‌ای بی‌رسوایی).

| ترتیب | الگو | چرا این جایگاه | ساعت تخمینی |
|---|---|---|---|
| 1 | ③ anchoring | مستقل از همه؛ از امروز historyِ غیرقابل‌انکار می‌سازد | ۱–۲h |
| 2 | ② LiteLLM | پیش‌نیاز عملی بقیه (spend-breaker + tool-perimeter) | ۳–۵h + بنچ RAM |
| 3 | ⑥ FIDO2 | R-02 را کامل می‌کند؛ منتظر رسیدن کلیدها | ۳–۴h |
| 4 | ⑤ lease/watchdog | عمیق‌ترین تغییر؛ بعد از تست /dev/watchdog0 روی برد | ۴–۸h |

همه پس از بسته‌شدن گیت rotation؛ آیتم‌های لمس‌کننده kernel/HITL/kill/Ledger طبق REFACTOR_PLAN برچسب `HUMAN-APPROVAL-REQUIRED` دارند.

## تصحیح‌های این run نسبت به SCOUT قبلی
1. `ots stamp` digest نمی‌گیرد — فایل لازم است؛ `ots verify` node می‌خواهد (pruned OK) — «~۱۰ خط + cron» قبلی خوش‌بینانه ولی با اسکریپت بالا همچنان S.
2. `KillWatchdogSec` وجود ندارد (سه‌گانه: Runtime/Reboot/**KExec**)؛ WDT RK3588 کوانتیزه با سقف ~89s. **تصحیح دقیق‌تر:** «BSP پیش‌فرض disabled» درست است ولی کل ماجرا نیست — روی **mainline/Armbian-edge پیش‌فرض enabled** است؛ فقط image رسمی Orange Pi (BSP 5.10) overlay می‌خواهد.
3. FIDO2 از داخل تلگرام ممکن نیست → معماری verdict دو-tier شد (این، کارت ⑥ SUMMARY را دقیق‌تر می‌کند، نقض نمی‌کند). **ssh داخلی ویندوز هم sk ندارد** → python-fido2 یا MSI/WSL2.
4. LiteLLM: Postgres اجباری؛ بودجه‌ها USD (نه AUD)؛ باگ manifest ARM64 باز. بلاک = **HTTP 400** (نه 403)، streaming **پوشش دارد**، چرخش کلید on-demand = Enterprise (مسیر Free بگیر).
5. TSA اصلی = **freetsa** (سیاست عمومی صریح)، DigiCert فقط دوم (ToS مسکوت).

## GAPS باقی‌مانده (فقط چیزهایی که بدون سخت‌افزار/تست‌محلی بسته نمی‌شوند)
> ۵ سوال باز run قبل در دور دوم بسته شد (جدول خلاصه اجرایی). این‌ها فقط با دسترسی به خودِ برد/کلید بسته می‌شوند:
1. **RAM واقعی LiteLLM+Postgres روی Orange Pi 5** — تنها عدد گمشدهٔ تصمیم‌سازِ ②؛ هیچ منبعی ندارد، باید اندازه گرفت.
2. **`/dev/watchdog0` روی image عملیاتیِ خودت** — منطقش روشن شد (mainline بله / BSP نه)، ولی باید روی همان image که واقعاً می‌زنی `ls /dev/watchdog*` بزنی.
3. رفتار python-fido2 روی hidraw برد ARM64 + udev rule (تست دستگاه).
4. آیا libfido2 همراه MSI ویندوز بدون admin از Windows Hello عبور می‌کند (تست elevated/non-elevated).
5. pretimeout governor روی dw_wdt در کرنل خودت [Unverified].
