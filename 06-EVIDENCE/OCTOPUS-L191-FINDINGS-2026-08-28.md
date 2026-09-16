---
type: report
project: "[[04 - Architect System/architect/PROJECT]]"
status: ready
tags: [octopus, mesh, ofn, t0, github]
created: 2026-08-28
updated: 2026-08-28
created_by: agent
language: fa
sources:
  - "[[08-PLANS/OCTOPUS-API-BRAIN-RESEARCH-TO-LAPTOP-AGENT-MEGAPROMPT-2026-08-28]]"
  - "[[08-PLANS/OCTOPUS-ROADMAP-API-2026-08-28]]"
  - "[[04 - Architect System/architect/PROJECT]]"
---

# یافته‌های لپ‌تاپ ۱۹۱ — ۲۸ اوت ۲۰۲۶

حکم جلسه: **BLOCKED_WITH_EVIDENCE**. بردها از لپ‌تاپ با SSH در دسترس‌اند. مسیر مالک از وب‌اپ OFN بدون تونل روی ۱۹۱ قابل استفاده نیست. تخلیهٔ `proposal.v1` از ۱۸۰ به ۱۳۸ زنده نیست. هیچ runtime عوض نشد، هیچ push انجام نشد، `money_flag=OFF`، `HOLD_EXTERNAL` حفظ شد.

ناظر: `node_id=191` · `asserted_ip=192.168.0.191` · hostname `DESKTOP-KA9RFN5` · `vantage=this_host` · `scope=this_host_only` · `claim_type=observation`. تناقض هویت claimed-vs-live در این پروب دیده نشد.

بستهٔ شواهد: `C:\Users\Armin\.zcode\tmp\OCTOPUS-EXECUTION-v2\`  
سرشماری Git: `C:\Users\Armin\.zcode\tmp\OCTOPUS-SYNC-CENSUS-v7-20260828\`  
نقشهٔ بصری (نه منبع حقیقت): Canvas کنار چت.

## ۱. این جلسه چه خواست و چه تحویل داد

| خواسته | نتیجه |
|---|---|
| مگاپرامپت پژوهشی + اجرایی v2 روی لپ‌تاپ | فاز A شروع شد؛ در A-30 به‌خاطر نبود تونل اجباری و قفل ناقص T0 ایستاد |
| داشبورد KV cache llama.cpp + شبیه‌ساز prefix cache | دو Canvas تحلیلی؛ عدد runtime نیستند |
| آیا بردها به هم و به لپ‌تاپ وصل‌اند؟ چه کاری در جریان است؟ | SSH LAN ثابت؛ تونل `8791–8796` روی ۱۹۱ نیست؛ drain پیشنهاد زنده نیست |
| پنل‌های وب را بخوان؛ ادغام با ۱۳۸ بدون بازنویسی تم | موجودی ثبت شد؛ اتصال از آداپتور/تونل است نه فرانت جدید |
| همگام‌سازی دایرکتوری ↔ GitHub (دستور v7) | سرشماری کامل؛ **push نشد**؛ lineage نامرتبط germline↔ofn-node |

دو حکم جدا را قاطی نکنید:

1. **OCTOPUS-L191-EXEC-v2** (~10:22–10:33Z): قانون تونل‌اول. Adapter census اجرا نشد. `t0_lock=FAIL`.
2. **OCTOPUS-L191-PARALLEL-v3** + پروب مش (~10:46–11:59Z): بعد از سؤال مالک دربارهٔ اتصال بردها، SSH فقط‌خواندنی به ۱۳۸/۱۸۰/۱۸۲ مجاز شد. T0 به‌عنوان فرآیند زنده **READY** ثبت شد؛ Flash Attention همچنان صریح نیست. زنجیرهٔ runtime تا EDGE-6 تشخیص داده شد.

هیچ‌کدام runtime را عوض نکردند.

## ۲. توپولوژی ثابت‌شده

| گره | هویت زنده | نقش |
|---|---|---|
| ۱۹۱ | `DESKTOP-KA9RFN5`، Wi-Fi `192.168.0.191` | لپ‌تاپ / germ / MiniApp / organism |
| ۱۳۸ | `DietPi`، eth0 `192.168.0.138` | spine کسب‌وکار / `ofn.run` / mint |
| ۱۸۰ | `octopus-continuity-180`، eth0 `192.168.0.180` | cognition + T0 llama.cpp |
| ۱۸۲ | `sensorium-opi5pro`، eth0 `192.168.0.182` | witness |

کرنل هر سه برد: `Linux 6.1.115-vendor-rk35xx` aarch64. برچسب رجیستری «x86 برای ۱۸۰» با کرنل زنده تناقض دارد؛ حقیقت زنده برنده است (CTR، فقط سند).

قرارداد تونل تا مش کامل: local-forward از ۱۳۸ به `127.0.0.1:8791–8794` و `8796` روی ۱۹۱. **نبود پورت روی LAN ≠ نبود API روی loopback برد.**

## ۳. آیا مش الان کار می‌کند؟

پنجره: `2026-08-28T11:48:51Z` تا `11:59:48Z`.  
مدرک: `evidence/live-mesh-status-191-20260828T1155Z.json` و `live-*.txt` / `followup-*.txt` / `outbox-ls-*.txt`.

### ۳.۱ تونل و سرویس‌های لپ‌تاپ

| پورت روی ۱۹۱ | وضعیت |
|---|---|
| 8791–8794، 8796 | **LISTEN نیست** → `REQUIRED_SSH_TUNNEL_NOT_OBSERVED` |
| 8801 board-cp | نیست |
| 8771 organism / 8772 cortex / 8773 live / 8774 MiniApp / 8776 Center | زنده، bind روی `127.0.0.1` (از سرشماری همین روز، نه این پروب SSH) |
| 11434 | Ollama محلی |

روی خود ۱۳۸، `127.0.0.1:8791–8794` = `ofn.run` (pid `1351408`) و `:8796` = `octopus_bridge` (pid `589802`) گوش می‌دهند. از LAN ۱۹۱ به `:8791` اتصال رد می‌شود؛ این پورت‌ها فقط loopbackاند.

SSH مستقیم به هر سه برد **موفق** بود. این جایگزین تونل نیست.

### ۳.۲ گراف اتصال (همین پنجره)

| یال | وضعیت |
|---|---|
| ۱۹۱ → ۱۳۸/۱۸۰/۱۸۲ ICMP+SSH | PROVEN |
| ۱۹۱ → ۱۸۰:۸۰۸۱ | PROVEN (سلامت HTTP 200 در قفل صبح) |
| ۱۹۱ `127.0.0.1:8791–8796` ← forward از ۱۳۸ | **NOT_OBSERVED** |
| TCP زنده ۱۳۸↔۱۸۰ یا ۱۳۸↔۱۸۲ در دو snapshot | **دیده نشد** (`NONE_TO_138`، `NONE_TO_180_OR_182`) |
| SMB ۴۴۵ از ۱۳۸ و ۱۸۲ به ۱۹۱ | ESTAB دیده شد |

### ۳.۳ کار زنده روی هر گره

**۱۹۱.** organism، cortex، live UI، MiniApp gateway، telegram Center، cloudflared به `127.0.0.1:8774`، Ollama. این‌ها ارگانیسم لپ‌تاپ‌اند نه OFN روی ۱۳۸.

**۱۳۸.** از ۲۷ اوت:

- `ofn.service` active — `python3 -m ofn.run` از `2026-08-27 11:33:39 AEST`
- `ofn-heartbeat.service` + timerهای watchdog/sync/budget/scheduler
- `octopus-bridge.service` active
- `octomesh_receive.py 138` زنده
- مسیر مش: `/home/ari/octopus-mesh` (نه `/root/octopus-mesh`، نه `/opt/octopus`)
- inbox مش: **۶ فایل**؛ تازه‌ترین محتوای فهرست‌شده ۲۷ اوت
- outbox مش: **۱۱ فایل**؛ یک ردیف ۲۸ اوت ~16:03 AEST هست — این mint پیشنهاد ۱۸۰ نیست
- در لحظهٔ پروب، یک `git push --force` از heartbeat به germline روی شاخهٔ `ofn/heartbeat` در حال اجرا بود. این جهش این جلسه نیست؛ drift همزمان روی GitHub را توضیح می‌دهد

**۱۸۰.**

- T0 llama-server pid **170941** از `2026-08-27 05:02:12 UTC` — همان فرآیند صبح
- organism روی `127.0.0.1:8090` و `192.168.0.180:8090`
- uvicorn روی `0.0.0.0:8780`
- `octopus-cognitive-worker.timer` حدود هر ۴۵–۶۰ ثانیه oneshot
- inbox مش: **۲۳۲۱ فایل**، تازه‌ترین هر دقیقه
- outbox مش: **۲۵ فایل**؛ تازه‌ترین `2026-08-27T23:14:01Z` (~۱۲٫۷ ساعت قبل از پروب)
- آخرین journal worker: `model_runtime=MODEL_RUNTIME_BLOCKED` با `model_called=true` — **llama down نیست**؛ مسیر worker به runtime مدل مسدود است
- TCP به ۱۳۸ در همان دقیقه: هیچ

**۱۸۲.**

- witness timer هر ~۳ دقیقه؛ service بین تیک‌ها dead (oneshot)
- NATS روی `127.0.0.1:8222` و `192.168.0.182:4222`؛ MQTT `127.0.0.1:1883`؛ متریک `0.0.0.0:9101`
- inbox **۳۵۰۷** / outbox **۸۳۱** — نوشتن `witness_response_*.json` **اثبات mint ۱۳۸ نیست**

**حکم مش.** بردها از لپ‌تاپ SSH می‌شوند. Owner UI کسب‌وکار روی ۱۹۱ بدون تونل به ۱۳۸ نمی‌رسد. تخلیهٔ proposal از ۱۸۰ به ۱۳۸ زنده نیست. اقدام امن بعدی: wait برای local-forward از ۱۳۸. سرویسی روشن نشود، `0.0.0.0` bind نشود، پیام مشتری ارسال نشود.

## ۴. قفل T0 (llama.cpp روی ۱۸۰:۸۰۸۱)

وزن ≠ KV cache.

| مورد | مقدار زنده |
|---|---|
| فایل | `/opt/octopus/models/qwen3-0.6b-q4_0.gguf` |
| اندازه | `428970080` |
| SHA-256 | `da2572f16c06133561ce56accaa822216f2391ef4d37fba427801cd6736417d4` |
| provenance | VERIFIED_BYTE_IDENTICAL با Hugging Face LFS (تأیید سوم مستقل) |
| هندسه GGUF (صبح) | ۲۸ لایه، ۸ KV head، head dim ۱۲۸، `context_length=40960` |
| باینری | `/opt/octopus/runtime/llama.cpp-f280b26/bin/llama-server.f280b26` |
| فلگ‌های cmdline | `--host 0.0.0.0 --port 8081 --ctx-size 2048 --threads 4 --cache-type-k q8_0 --cache-type-v q8_0 --offline` |
| `--flash-attn` | **در cmdline نیست**؛ پیش‌فرض باینری `auto` |
| unit | `octopus-llama-lab.service`؛ `ExecStartPre` چک SHA مدل — تعویض وزن بدون به‌روز کردن `model.sha256` fail-closed است |
| ollama روی ۱۸۰ | ۰ |
| listener 8081 | ۱ |

منابع ۱۸۰ در قفل ~10:46Z:

- RAM کل ~۳۹۱۰ MB؛ free ۲۰۴ MB؛ available ۱۱۳۴ MB
- cgroup: `MemoryCurrent` ~۱٫۸۷ GB > `MemoryHigh` ~۱٫۸۰ GB → **throttle زنده**
- دیسک root ۹۰٪ (۵٫۸G آزاد)؛ inode ۴٪
- dmesg OOM/ENOSPC خالی → فرض OOM ضعیف شد؛ فشار محتمل = cgroup + دیسک

سیاست KV (شورا + اندازهٔ محلی، نه بنچمارک تازه روی این برد):

- T0 کوچک (`ctx=2048`، مدل 0.6B): **q8_0/q8_0 انتخاب درست است**؛ q4_0 روی K بدون بنچمارک اختصاصی ممنوع
- V کوانتیزه از نظر معماری به Flash Attention وابسته است؛ fallback رسمی: `K=q8_0, V=f16`
- اعداد KLD شورا روی Qwen2.5-7B است نه این T0؛ perplexity ≠ KLD
- فرض «q4 همیشه کمتر از f16 حافظه می‌گیرد» را به همهٔ سخت‌افزارها تعمیم ندهید
- 64K/128K برای این مدل **برون‌یابی** است (`context_length=40960`)

تعارض دو قانون:

- مگاپرامپت v2: نبود `--flash-attn on` صریح + bind `0.0.0.0` = `LIVE_FLAGS_CONTRADICT_LOCK` → توقف اجرایی
- موج موازی v3: همهٔ فلگ‌های صریح PROVEN؛ FA=`auto` ثبت شد، stop-code نشد؛ lane L3 = READY

هر دو صادق‌اند. قفل «کامل پیشنهادی v2» پاس نشد. فرآیند T0 زنده و سالم است. این جلسه bind را عوض نکرد و FA را force-on نکرد.

اشکال شمارش فرآیند: `pgrep -af llama-server` خود شل پروب را هم می‌گیرد؛ شمارش معتبر از procfs pid است.

## ۵. زنجیرهٔ باز کسب‌وکار (EDGE-1 تا EDGE-14)

شناسهٔ شناخته‌شده از قبل: `run-spine-138-snap-20260828T005835Z`، canonical `950f8d0e…`. در EXEC-v2 تشخیص کامل زنجیره به‌خاطر stop در A-30 اجرا نشد (`open_chain_failed_stage=NOT_DIAGNOSED`). در PARALLEL-v3 مسیر runtime نوشته شد.

| یال | نام | وضعیت |
|---|---|---|
| EDGE-1 | export snapshot ۱۳۸→inbox ۱۸۰ | PROVEN (receipt byte-identical) |
| EDGE-2 | wake binding | PROVEN (ACK) |
| EDGE-3 | inbox claim روی ۱۸۰ | PROVEN |
| EDGE-4 | cognition predict | PROVEN (فایل منجمد + sha) |
| EDGE-5 | ساخت `proposal.v1` | PROVEN (`proposal-950f8d0e.json` + registry) |
| **EDGE-6** | **ارسال outbox ۱۸۰→۱۳۸** | **PROVEN_BROKEN** |
| EDGE-7 | mint روی ۱۳۸ | MISSING_FOR_RUN (ماشین‌آلات تست‌شده) |
| EDGE-8 | witness ۱۸۲ برای این run | MISSING_FOR_RUN |
| EDGE-9 | owner receipt | ARMED روی PC، مصرف‌نشده در این drain |
| EDGE-10..14 | executor / مشتری / تسویه / حافظه | GATED با HOLD_EXTERNAL |

ریشهٔ EDGE-6 (FACT، نه فرض):

- handler شاخهٔ spine بعد از نوشتن registry همان‌جا `return` می‌کند؛ `outbox.persist_pending` و `outbox.transmit_pending` **فراخوانی نمی‌شوند**
- مسیرهای هم‌نیا در همان فایل هر دو را صدا می‌زنند
- journal از ۲۷ اوت: صفر تلاش send/drain
- ۲۵ فایل outbox؛ هیچ‌کدام `proposal-950f8d0e` نیست — هرگز enqueue نشده
- محیط رد شد: TCP ۱۸۰→۱۳۸:۲۲ reachable؛ پرمیشن outbox root:root 700؛ inode کافی؛ OOM در dmesg نیست؛ timer ارسال جدا وجود ندارد (retry دستی با `octomesh_process.py`)

تعمیر پیشنهادی (اعمال‌نشده): بعد از موفقیت registry، همان الگوی ~۳ خط مسیر mirror. نیاز به GO مشخص روی ۱۸۰. rollback = برگرداندن یک فایل از `.bak`.

worker هر دقیقه inbox تازه می‌خورد و `MODEL_RUNTIME_BLOCKED` می‌نویسد؛ این با EDGE-6 یکی نیست ولی نشان می‌دهد cognition محلی هم به T0 وصل نیست حتی وقتی llama-server بالاست.

## ۶. پنل‌های وب (بازنویسی تم ممنوع)

موجودی دیسک روی `F:\backup`. Runtime کسب‌وکار روی ۱۳۸ جدا است و در پروب مش با `ofn.run` ثابت شد.

### سطح اجازهٔ کسب‌وکار (شیشه / کرم / دارکروم)

مسیر: `F:\backup\03 - Projects\OFN-Board\`

شل‌ها: `web/panel.html`, `lead.html`, `ziman.html`, `studio.html`, `saba-darkroom.html`, `saba-stack.html`

پورت‌های کد: ziman 8791، lead 8792، studio 8793، owner 8794 — bind **127.0.0.1**

صف تصمیم از قبل طراحی شده: `POST /api/v1/decide` با `{id, approve, confirmed_twice}`؛ outbox: `pending` → `approved_manual`. تأیید ≠ ارسال.

اسکیمای نام‌خوردهٔ `owner_decision.v1` / `owner_receipt.v1` روی دیسک پیدا نشد. نزدیک‌ترین قرارداد: همان decide + `octopus-control.v2` + `action-receipt.v1`. آداپتور `ofn/adapters/owner_decision.py` در درخت ofn-node روی شاخهٔ ۱۳۸ هست (۱۲ فیلد).

### سطح اجازهٔ ارگانیسم (فولاد تیره)

`_ops\telegram_center\miniap\` — gateway `127.0.0.1:8774`  
تب تأییدها: `GET /api/approvals` و ✓/✕  
GET `/` ممکن است timeout بدهد (قفل سوکت)؛ این به معنی مرده بودن gateway نیست.

### لولهٔ فرمان

`_ops\board_cp\` — پورت 8801؛ پیش‌فرض کد **`0.0.0.0`** (ریسک قانون جلسه). روی ۱۹۱ در پروب گوش نمی‌دهد.

### برخورد نام میزبان

`app.master-painting.com` هم به استودیو `/sabaapp` و هم به MiniApp نسبت داده شده. قبل از هر «انتقال MiniApp به ۱۳۸» باید DNS/path جدا شود.

### نقشهٔ ادغام بدون از دست دادن تم

1. ۱۳۸ = mint/spine؛ بایت‌های `web/*.html` سفارشی عوض نشوند
2. GO کسب‌وکار فقط از `decide` پنل OFN
3. MiniApp فقط کارت ارگانیسم؛ دکمهٔ approve دوم روی همان آیتم ساخته نشود
4. board-cp موجود به‌عنوان لوله ۱۹۱↔۱۳۸ فقط با bind لوپ‌بک + SSH
5. پنل‌های اضافه (8770، 8773، 8788، 8790، گالری سه‌بعدی) demote شوند نه حذف

## ۷. همگام‌سازی GitHub ↔ محلی (دستور v7)

مشاهده ~`2026-08-28T12:15:00Z`. جهش صفر. `F_backup_git_ops=0`.

**GitHub `ari322/ofn-node`:** ۱۳ شاخه. `main = 388594e048cc7d0d2829f4aa067e525e4c3be7e8`. هیچ `exec-v3/*` نیست. این بخش ادعای مالک تأیید شد.

استثنا از baseline زنده: `ofn/heartbeat` روی GitHub از `7909cb16` به `f14c4776` drift کرده (همزمان با force-push مشاهده‌شده روی ۱۳۸). این census آن را عوض نکرد.

فرض «تم آخرین نسخه فقط روی لپ‌تاپ است» برای OFN **رد شد**.

| مقایسه | نتیجه |
|---|---|
| CSS/فونت `web/cockpit-v2` vs GitHub `integration/138-business-spine-20260828` (`68813370`) | **یکسان** |
| دکمه‌های `panel.html` vs همان شاخه | **یکسان** (۱۳ دکمه) |
| ولت `panel.html` (`b2e05bb5…`) vs GitHub/ofn-spine (`aec7e559…`) | ولت **عقب‌تر** است (ویجت متریک octopus-sync را ندارد) |

**هرگز** کپی ولت را روی GitHub ننویسید.

`cockpit-v2` روی `main` نیست؛ روی `ofn/cockpit-v2-20260827` و `integration/138-business-spine-20260828` هست. روی main فقط htmlهای قدیمی lead/panel/studio/ziman است.

**Lineage:** `E:\germline\octopus.git` نوک `exec-v3/integration` = `7125b314` با GitHub ofn-node **merge-base ندارد** (`UNRELATED`). درخت آن حدود ۱۲۸۵۹ مسیر است؛ **صفر** `ofn/` یا `web/`. کار امروز Census/Router/Painting در آن درخت ولت است. از germline به ofn-node نباید push شود — همان تلهٔ Obsidian.

`langar` @ `4ff00f31` و `Armin` @ `fcaca746` با `origin/main` هم‌خوان (ahead/behind = 0).

درخت بدون git `ofn-spine`: ۴۵۶ فایل با `68813370` یکسان؛ GitHub ۱۳۸ حدود ۱۷۸۵ فایل اضافه‌تر دارد که تقریباً همه `.tmp-test*` تولیدشده‌اند — منبع نیستند.

بیمه (بدون جهش): آرشیو + ۳ git bundle زیر مسیر census. Secret gate: PASS. `.bak-*` دست‌نخورده.

```
VERDICT=BLOCKED_WITH_EVIDENCE
blocker_codes=GIT_WRONG_LINEAGE,OWNER_GO_REQUIRED,HOLD_EXTERNAL
evidence_bundle_sha256=9cab2f48e5921072ffdbfb050d3d8503dd92c0ae346e860eaa34365576cf1760
commits_created=0
branches_pushed=0
remote_branch_count=13 (قبل و بعد)
```

برای گذاشتن cockpit روی `main`: merge **داخل خانوادهٔ ofn-node** (`integration/138` یا `ofn/cockpit-v2`)، نه germline. سکوت مالک = HOLD.

## ۸. گارد ایمنی و هزینه (فقط خواندن درخت ofn-node @68813370)

| گارد | در ofn-node |
|---|---|
| money_flag | MISSING (روی router لپ‌تاپ / mesh) |
| HOLD_EXTERNAL | MISSING به‌عنوان نماد (در payload مش ۱۸۰ هست) |
| egress_policy | PROVEN_ADAPTIVE در `brainport.py` — allowlist کسب‌وکار است نه مقصد |
| rate_limit | PROVEN_FILE |
| ledger/quota | PROVEN_DESIGN — تبدیل USD در-ریپو نیست |
| idempotency | PROVEN_MULTIPLE |
| retry | PROVEN_BOUNDED (MAX_ATTEMPTS=3) |
| provider_registry | MISSING — `BRAIN_PROVIDER` env |
| sandbox شبکه | MISSING |
| owner_gate | PROVEN_CONTRACT در آداپتور |

قانون هویت فروشنده: `vendor_id` هرگز از URL/dialect حدس زده نشود. DeepSeek روی endpoint سازگار Anthropic باید `vendor_id=deepseek` بماند. این هنوز در `brainport.py` مدل نشده.

آزمایشگاه prefix-cache (شبیه‌ساز آفلاین روی ۱۹۱، صفر API خارجی): PARTIAL · `COMMON_PREFIX_NOT_A_COMPLETE_UNIT` ۴۴/۴۸. hit واقعی فقط از `prompt_cache_hit_tokens` ارائه‌دهنده. Canvas شبیه‌ساز حقیقت اجرا نیست.

## ۹. رأی‌های خودمختاری مالک (اعمال‌نشده در این جلسه)

در `artifacts/13-AUTONOMY-DECISIONS.yaml` ده ردیف با رأی صریح مالک ثبت شده (از جمله پاکسازی ۱۸۰، poller فقط APPROVED، timer پنج‌دقیقه‌ای drain، chrony+RELP، router با سقف، درس بعد از هر receipt، watchdog). این جلسه آن‌ها را **اجرا نکرد**.

ترتیب اعلام‌شده: اول ردیف ۳ (پاکسازی ۱۸۰) وگرنه بقیه امن نیستند. پیش‌نیاز EDGE-6 هم GO نوشتن روی ۱۸۰ است.

تأیید کلید در همان فایل (بدون افشای مقدار): یک مسیر OpenAI پاسخ داد؛ Anthropic 400؛ دسترسی خواندن خصوصی GitHub از یک توکن تأیید شد؛ توکن نوشتن PC رد شد. T2 زنده نشد. `paid_api_calls` این مأموریت اجرایی = 0.

## ۱۰. Canvasهای تحلیلی (نه حقیقت runtime)

- KV cache: تخمین f16/q8_0/q4_0؛ دروازهٔ `--flash-attn on` برای V کوانتیزه؛ KLD به‌عنوان reported evidence نه perplexity
- DeepSeek prefix: مرز درخواست، common-prefix از توکن صفر، SHA-256، BLOCKED/PARTIAL؛ hit واقعی فقط از usage receipt

۶۴K/۱۲۸K برای T0 برون‌یابی است.

## ۱۱. تصمیم‌های باز مالک (سکوت = HOLD)

| شناسه | سؤال |
|---|---|
| OD-001 | local-forward روی ۱۹۱ به `127.0.0.1:8791–8794,8796` |
| OD-002 | bind T0: آدرس LAN مشخص یا loopback/تونل — نه تأیید `0.0.0.0` |
| OD-003 | restart برنامه‌ریزی‌شده برای `--flash-attn on`، یا روش اثبات effective auto بدون جهش |
| OD-004 | GO تعمیر سه‌خطی EDGE-6 روی ۱۸۰ (بعد از پاکسازی ردیف ۳ اگر هنوز معتبر است) |
| OD-SYNC-01 | ~۱۷۸۲ فایل `.tmp-test*` روی GitHub: بماند، gitignore از حالا، یا purge با commit جدید (بدون history rewrite) |
| OD-SYNC-02 | germline exec-v3 را با ofn-node قاطی نکن؛ اگر آرتیفکت امروز باید روی GitHub باشد، کپی به کلون خانوادهٔ ofn-node |
| OD-SYNC-03 | promote شاخهٔ ۱۳۸/cockpit-v2 به `main`؟ فقط merge داخل GitHub |
| OD-SYNC-04 | ولت `panel.html` را از GitHub به‌روز کن، نه برعکس |
| DNS | جدا کردن `app.master-painting.com` قبل از host مشترک MiniApp/استودیو |

## ۱۲. حکم نهایی ماشین‌خوان

```
mission_id=OCTOPUS-L191-EXEC-v2 + PARALLEL-v3 + DIR-GITHUB-SYNC-v7
observer=191/192.168.0.191/DESKTOP-KA9RFN5
status=BLOCKED
t0_process=LIVE pid 170941
t0_lock_v2=FAIL (flash_attn صریح غایب + wildcard bind)
t0_lock_v3=READY flags_verified=partial
tunnel_8791_8796_on_191=ABSENT
ofn_on_138_loopback=LIVE
proposal_drain_180_to_138=PROVEN_BROKEN (EDGE-6)
open_run_id=run-spine-138-snap-20260828T005835Z
github_ofn-node_main=388594e0
github_exec-v3=ABSENT
local_7125b314_vs_ofn-node=UNRELATED
theme_vault_ahead_of_github=FALSE
vault_panel_html=BEHIND
runtime_changes=0
paid_api_calls=0
external_effects=0
commits_created=0
branches_pushed=0
next_resumable_step_id=A-20 (تونل) سپس OD-004 (EDGE-6)
resume_is_safe=true
VERDICT=BLOCKED_WITH_EVIDENCE
```

پاکت داور برای کل گزارش: `node_id=191` · `asserted_ip=192.168.0.191` · `vantage=this_host` · `scope=this_host_only` · `claim_type=observation` مگر جایی صریحاً `inference` آمده باشد (مثلاً علت `MODEL_RUNTIME_BLOCKED` با وجود llama زنده).
