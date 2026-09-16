# Brushline — معماری مادر و طراحی کامل (Master Architecture)

> نسخه: 2026-07-01 · نویسنده: design pass با Sume (Sydney)
> دامنه: دو لایه به‌هم‌پیوسته — (۱) اپلیکیشن **Brushline** (lead-gen/marketing برای Sister Painting)، (۲) لایه‌ی زیرساخت **infra-control** (control plane چندپروژه‌ای روی VPS).
> این سند single source of truth برای «هرچه تا الان طراحی و کد شده» است. در انتها، ۱۰ پرامپت برای تکمیل و بهینه‌سازی.

---

## ۰. خلاصه‌ی سریع — این چیست و چه می‌گیری؟

دو سیستم مستقل ولی هم‌خانواده، که هر دو روی یک ستون فقرات حاکمیتی (governance) مشترک ساخته شده‌اند:

1. **Brushline** — یک سیستم AI برای lead-gen و marketing یک کسب‌وکار نقاشی ساختمان (residential/strata) در Sydney. هدف: ساختِ owned-channel (Google Business Profile، local SEO، suburb pages) + اتوماسیون speed-to-lead، follow-up و review management. هدف هزینه: **AUD $15–40/ماه** برای API.
   - الگوی معماری: **00-Orchestrator** با ۶ Worker (A–F)، یک **Constitution Gate** و یک **Human Approval Queue**.
   - ماژول standalone است؛ کنار LANGAR می‌نشیند ولی **هرگز DB یا process مشترک ندارد**.

2. **infra-control** — یک control plane سبک روی VPS که چند پروژه‌ی AI را به‌صورت container اجرا و مدیریت می‌کند. GitHub منبع حقیقت؛ deploy کاملاً اتوماتیک ولی gated؛ کنترل از طریق یک Telegram control-bot + یک root CLI به نام `stackctl`.

**اصل پیونددهنده:** هر دو لایه از سه invariant غیرقابل‌حذف و یک audit log هش‌زنجیره‌ای (hash-chained) پیروی می‌کنند. منطق یکسان است در دو مقیاس: «هیچ‌چیز بدون gate و بدون رد انسانی/health-check اجرا نمی‌شود».

---

## ۱. سه Invariant غیرقابل‌حذف (هسته‌ی حاکمیتی)

این سه قید در همه‌ی لایه‌ها حاکم‌اند و **هرگز حذف نمی‌شوند**:

| کد | قید | پیاده‌سازی فعلی |
|---|---|---|
| **INV-1** | هیچ publish/spend/send بدون تأیید انسانی. مسیر همیشه: `draft -> human approve -> publish`. | `ApprovalQueue` (KB-05)، هیچ auto-approve حتی روی انقضای SLA. در infra: CI test gate + health-check قبل از live. |
| **INV-2** | PII و داده‌ی مالی مشتری هرگز وارد LANGAR یا حافظه‌ی AI نمی‌شود — فقط hash-ref. | `audit._sanitise_payload()` فیلدهای PII را به `sha256:...` تبدیل می‌کند؛ `MEMORY_PII_ALLOWED=False`؛ `PII_STORAGE="hash_ref"`. |
| **INV-3** | هر auto-execution یک kill switch + سقف خرج per-action/per-day + audit log هش‌زنجیره‌ای دارد. | `governance.check_and_enforce()` اولین خط هر متد بیرونی؛ `KILL_SWITCH` file؛ caps در config؛ `stackctl kill [--all]`. |

> این سه قید مستقیماً با survival filter خودِ Sume هم‌راستا هستند: اگر چیزی می‌تواند کسب‌وکار را بکشد (نشت PII، خرج کنترل‌نشده، ارسال غیرمجاز)، صرف‌نظر از upside بلاک می‌شود.

---

## ۲. لایه‌ی Brushline — معماری اپلیکیشن

### ۲.۱ الگوی 00-Orchestrator

```
intent -> plan -> route -> collect -> CONSTITUTION GATE -> HUMAN APPROVE -> AUDIT LOG
```

نکته‌ی طراحی کلیدی (KB-01 s1): orchestrator در MVP **workflow-driven** است، نه autonomous. یعنی LLM فقط *محتوای* هر قدم را پر می‌کند، نه *تصمیم routing* را. مسیرها سخت‌کدِ امن‌اند:

```
Enquiry path:    F -> C -> Gate -> Queue -> (Sync اگر lead تأیید شد)
Content path:    A -> C -> D? -> E -> Gate -> Queue
Follow-up path:  C -> Gate -> Queue
```

این انتخاب آگاهانه است: autonomous routing با LLM = سطح حمله و عدم‌قطعیت بالا. fixed paths = قابل‌حسابرسی، قابل‌تست، ارزان.

### ۲.۲ شش Worker (A–F)

| Worker | نقش | مدل | وضعیت |
|---|---|---|---|
| **A — Researcher** | جست‌وجوی suburb/competitor/pricing/keyword/pre-intent از طریق Serper (۵ متد). gl=au, location=Sydney NSW. | Haiku (cheap) | **DONE** (Phase 1) |
| **B — Audience/Sentiment** | تحلیل sentiment ریویوها + شاخص فصلی تقاضا (seasonal demand index). | Haiku | **DONE** (Phase 1) |
| **C — Content** | پیش‌نویس speed-to-lead، follow-up (روز ۲/۵/۱۰)، review response، suburb page. با fallback به template سازگار + footer (sender-ID/ABN/opt-out). | Haiku + Sonnet برای key copy | **DONE** — lead-path + review + suburb (Sonnet) |
| **D — Asset/Image** | تولید/انتخاب دارایی بصری. | — | **stub** (Phase 4) |
| **E — Channel** | publish به GBP/social — فقط **DRAFT**، هرگز auto-post. | — | ✅ **DONE** (P4، 2026-07-02؛ MVP: publish=preview-only پس از approve) |
| **F — Lead-Capture** | دریافت enquiry، تشخیص consent، نگاشت به CRM. | — | ✅ **DONE** (P5، 2026-07-02؛ sync consent-gated + dry-run بدون key) |

### ۲.۳ Constitution Gate (Evaluator-Optimizer)

Gate یک agent جدا **نیست** — همان قدم evaluator است (KB-07). هر draft قبل از رسیدن به صف از اینجا رد می‌شود. در lead-path slice همه‌ی چک‌ها **deterministic** و zero-cost هستند:

- **ACL s29** — اسکن superlative ممنوع (`best`, `cheapest`, `guaranteed`, `#1`, `100%`, …) → ادعای اثبات‌نشده.
- **Spam Act 2003** — پیام مستقیم (speed-to-lead/followup): consent + ABN + opt-out. پاسخ عمومی ریویو (`review_response`): فقط ABN + ACL، بدون consent/opt-out (P1).
- **Privacy (INV-2)** — اسکن regex برای PII خام (موبایل `04xxxxxxxx`، ایمیل) در بدنه.
- **Sovereignty (INV-2)** — داده‌ی حساس AU به offshore نرود.

خروجی: `GateResult` با وضعیت `PASS` / `SOFT_FLAG` / `HARD_BLOCK`.
- **HARD_BLOCK** (consent/ABN/opt-out نبود) → draft برمی‌گردد به Content برای rewrite، تا سقف `GATE_MAX_ROUNDS=3`.
- **SOFT_FLAG** (superlative یا PII pattern) → هشدار، تصمیم با operator.

> ✅ P2 (2026-07-01): لایه‌ی **semantic ACL با Sonnet** پیاده شد -- فقط روی draftهای پرریسک marketing (`suburb_page`/`gbp_post`/`blog_outline`/`caption`)، با `check_and_enforce` قبل از فراخوان و `log_cost` بعد؛ advisory (SOFT_FLAG)، افزوده به چک deterministic نه جایگزینِ آن. offline بدون key -> gate کاملاً deterministic می‌ماند.

### ۲.۴ Governance (INV-3 enforcement)

`governance.check_and_enforce(cost_aud, agent_id)` — **اولین خط هر متدی که سرویس بیرونی صدا می‌زند** (Serper, Anthropic, sync). سه چک به ترتیب اولویت:
1. **kill switch** — وجود فایل `KILL_SWITCH` → `KillSwitchActivated`، همه‌ی اکشن‌ها halt.
2. **per-action cap** — `> SPEND_CAP_PER_ACTION_AUD` (پیش‌فرض AUD $5) → `SpendCapExceeded`.
3. **daily cap** — `today + action > SPEND_CAP_PER_DAY_AUD` (پیش‌فرض AUD $20).

هزینه‌ها در جدول `cost_events` لاگ می‌شوند؛ `get_spend_status()` داشبورد `/spend` تلگرام را تغذیه می‌کند. kill switch از تلگرام (`/kill`, `/kill_off`) با audit قبل از نوشتن فایل.

### ۲.۵ Audit Log (هش‌زنجیره‌ای، append-only)

```
entry_hash = SHA-256(prev_hash + event_type + entity_id + payload + timestamp)
genesis prev_hash = "0"*64
```

هر اکشن بیرونی یک entry تولید می‌کند. `_sanitise_payload()` فیلدهای PII (`phone`, `email`, `full_name`, `full_address`, `tax_file_number`) را به hash-ref تبدیل می‌کند (INV-2). `verify_chain()` کل زنجیره را راستی‌آزمایی می‌کند — هر دستکاری شکستِ لینک هش را آشکار می‌کند. این الگو در `stackctl` هم بازاستفاده شده (`/var/log/stackctl/audit.jsonl`).

> P9 (2026-07-01): ترتیب زنجیره از `timestamp` به **`rowid`** (ترتیب واقعی درج) تغییر کرد و `append` زیر یک lock با یک connection انجام می‌شود -- تای‌های هم‌میلی‌ثانیه و نوشتن همزمان دیگر زنجیره را نمی‌شکنند (تست concurrency، ۷۰ entry، سبز).

### ۲.۶ Human Approval Queue (INV-1)

هر draft پیش از هر اکشن بیرونی از اینجا رد می‌شود. **هیچ auto-approve نیست** — حتی انقضای SLA فقط priority را بالا می‌برد و notify می‌کند. اکشن‌های operator (از تلگرام): `APPROVE` → publish/send/sync؛ `EDIT` → محتوای جدید → **REGATE** اگر تغییر مادی بود؛ `REJECT` → دور انداختن + لاگ دلیل. وضعیت فعلی: stub با interface درست (Phase 0)؛ کارت‌های inline keyboard در Phase 3.

### ۲.۷ مدل داده و schema (SQLite)

موجودیت‌ها (`models.py`): `Lead` (تنها جایی که PII خام: name/phone/email)، `ConsentRecord` (APP7/Spam Act)، `Draft` (همیشه draft-only، بدون auto-publish)، `GateResult`، `ApprovalAction`، و enumها (`DraftType`, `GateStatus`, `ApprovalStatus`, `SyncStatus`, `ConsentMethod`, `AuditEventType`).

جداول (`database.py`): `leads`, `consent_records`, `drafts`, `gate_results`, `approval_actions`, `audit_entries`, `sync_jobs`, `cost_events`, `brushline_meta`.

> قید بحرانی: `DB_PATH` هرگز نباید با دیتابیس LANGAR یکی باشد (جداسازی سختِ Phase 0).

### ۲.۸ رابط Telegram (TG-01 — single channel)

تنها کانال کنترل operator. allow-list سخت: فقط `ALLOWED_OPERATOR_CHAT_IDS`. دستورهای فعلی: `/queue` (تأییدهای معلق)، `/spend` (خرج امروز vs caps)، `/kill` و `/kill_off` (kill switch)، `/status` (وضعیت سیستم). Phase 0: دستورهای governance سیم‌کشی‌شده؛ کارت‌های approval در Phase 3.

### ۲.۹ مدل مالی و router مدل (KB-02)

- **MODEL_CHEAP** = `claude-haiku-4-5-20251001` — Worker A/B و ~۹۰٪ فراخوان‌ها.
- **MODEL_KEY** = `claude-sonnet-4-6` — gate checks و key copy.
- **Opus** در MVP غیرفعال (هزینه).
- `BATCH_ENABLED` و `CACHE_ENABLED` = true (کاهش هزینه).
- FX: `1 USD = 1.45 AUD` (Jun 2026). caps: per-action AUD $5، per-day AUD $20.
- Serper: free tier (2500 query/ماه)؛ DataForSEO به‌عنوان alternative (async $0.0006/query, live $0.002/query).

### ۲.۱۰ Compliance (غیرقابل‌مذاکره)

- **AU Spam Act 2003**: consent لازم، opt-out ظرف ۵ روز، sender ID + ABN در همه‌ی outbound.
- **ACL s.29**: ادعای false/اثبات‌نشده ممنوع (`best`/`cheapest`/`guaranteed` بلاک).
- **Privacy Act / APP**: PII فقط hash-ref، هرگز خام در حافظه یا log.
- **Commonwealth penalty unit**: AUD $330 (indexation 1 Jul 2026 — قبل از bulk send verify شود).
- consent inferred برای enquiry مشتری‌آغازکرده (Spam Act s7) فقط برای اولین پاسخ؛ draft همچنان human-approved.

---

## ۳. لایه‌ی infra-control — معماری سرور (control plane)

### ۳.۱ هدف و الگو

یک VPS واحد که چند پروژه‌ی AI را به‌صورت container میزبانی می‌کند. GitHub منبع حقیقت؛ deploy کاملاً اتوماتیک ولی **gated** (کد خراب هرگز live نمی‌ماند). کنترل از موبایل با Telegram + یک root CLI. طراحی OSS و آماده‌ی مهاجرت به k8s (افق 2028–2035).

### ۳.۲ ساختار repo (هیبرید)

```
GitHub
├── infra-control      <- مغز: stackctl, control-bot, compose سراسری, CI, Traefik
├── brushline          <- پروژه‌ی بزرگ، repo مستقل
├── project-x          <- پروژه‌ی بزرگ بعدی، repo مستقل
└── mono-misc          <- پروژه‌های کوچک، هرکدام پوشه‌ی containerized
```

### ۳.۳ runtime: Docker Compose + Traefik

```
VPS
├── Traefik (reverse proxy)     <- TLS خودکار (Let's Encrypt/Cloudflare DNS), routing با label
├── infra-control/
│   ├── stackctl                <- root CLI کنترل (Python)
│   ├── control-bot (container) <- Telegram bot، صدا زدن stackctl
│   ├── uptime-kuma (container) <- مانیتور up/down + alert
│   └── dozzle (container)      <- لاگ همه‌ی containerها از یک UI
├── brushline (container)
└── project-x / mono-misc (containers)
```

هر سرویس `mem_limit` و `cpus` دارد (یک پروژه منابع را نبلعد). شبکه‌ی مشترک `proxy`؛ پروژه‌ها با label به Traefik وصل می‌شوند.

### ۳.۴ stackctl — تک‌منبعِ منطق کنترل

```
stackctl up|down|restart|status|logs|deploy <project>
stackctl kill <project>     # kill switch فوری (INV-3)
stackctl kill --all         # global kill switch
stackctl list
```

`projects.yaml` رجیستری مرکزی (path, compose, health_url یا container_name, health_timeout, image GHCR, description). audit هش‌زنجیره‌ای در `/var/log/stackctl/audit.jsonl` (همان الگوی Brushline). منطق deploy عمداً در `stackctl` است نه در Actions → جلوگیری از vendor lock-in.

### ۳.۵ CI/CD کاملاً اتوماتیک + gated (`ci-brushline.yml`)

```
push به main
  -> 1. test (pytest offline + AST/py_compile)
  -> 2. secret scan (gitleaks)
  -> 3. build (docker build، cache=gha)
  -> 4. push image به GHCR
  -> 5. SSH deploy: git reset --hard + stackctl deploy <project>
  -> 6. health-check (container healthy ظرف N ثانیه)
  -> 7. ناسالم؟ rollback به image قبلی + alert تلگرام
```

اتوماتیک کامل (صفر کلیک) ولی gated. این نسخه‌ی امنِ خواسته است، نه auto-pull کور.

### ۳.۶ مدیریت secret و observability

- **SOPS + age**: secretها رمزنگاری‌شده داخل `infra-control/secrets/` نسخه‌بندی؛ سرور با کلید خصوصی age رمزگشایی. (طراحی‌شده، هنوز جای .env دستی Brushline را نگرفته.)
- `.gitignore` سخت: `.env`, `data/`, `*.db`, `__pycache__`, `KILL_SWITCH`, `*.key/*.pem` (INV-2).
- **gitleaks** در CI هر push را اسکن می‌کند.
- **Uptime Kuma** + **Dozzle** = monitoring/logs؛ همه OSS، ~$0 نرم‌افزار اضافه. هزینه‌ی غالب = VPS (~AUD $35–70/ماه).

> درس commit خانه (مبنای طراحی secret): یک‌بار 327k فایل + private key اشتباهی commit شد. کل طرح SOPS+age و gitleaks پاسخ به همان درس است.

---

## ۴. وضعیت فازها (as of 2026-07-01)

| Phase | محتوا | وضعیت |
|---|---|---|
| **0** | scaffold، governance، gate stubs، audit، Telegram bot stubs | ✅ COMPLETE |
| **1** | Worker A (Serper، ۵ متد)، Worker B (Haiku sentiment + seasonal)، orchestrator، main.py، setup.sh، Makefile، .env | ✅ COMPLETE |
| **2** | lead-path + review + suburb slice: `draft_review_response` (Haiku)، `draft_suburb_page` (Sonnet + fallback)، Gate تفکیک direct/public + **لایه‌ی semantic ACL با Sonnet** روی draftهای پرریسک. تست‌ها: leadpath + reviewslice + suburbslice، همه offline سبز. | ✅ COMPLETE (2026-07-01) |
| 2 (تکمیل) | suburb slice + **semantic ACL (Sonnet)** هر دو DONE 2026-07-01. Phase 2 کامل؛ تنها شکاف compliance باز بسته شد. | ✅ DONE |
| **3** | HITL approval queue با کارت‌های inline keyboard تلگرام (queue.py واقعی: approve/reject/edit_and_regate/escalate_overdue؛ allow-list روی callbackها هم) | ✅ DONE (2026-07-01، test_phase3_approval_queue.py 47/47) |
| **4** | Worker D (Asset/Image)، Worker E (Channel publish — GBP, social DRAFT only) | ⏳ |
| **5** | Worker F (Lead capture)، sync با ServiceM8/Tradify | ⏳ |

**infra-control:** اسکلت کامل ساخته شده (stackctl, projects.yaml, docker-compose سراسری, Traefik, control-bot, ci-brushline.yml, RUNBOOK). روی VPS هنوز به‌صورت end-to-end deploy/تست نشده. SOPS+age هنوز فعال نشده.

**Deploy/Git:** git داخل sandbox روی این mount کار نمی‌کند (fuseblk، config corruption)؛ git روی Windows اجرا می‌شود. deploy از GitHub با read-only deploy key + `deploy.sh`. runbook در `DEPLOY.md`.

---

## ۵. تصمیمات کلیدی و trade-offها

| تصمیم | چرا این | چرا نه بقیه |
|---|---|---|
| **workflow-driven orchestrator** (نه autonomous LLM routing) | قابل‌حسابرسی، قابل‌تست، ارزان، سطح حمله‌ی کم | autonomous = عدم‌قطعیت + هزینه + ریسک compliance |
| **Gate به‌جای agent، evaluator step** | zero-cost deterministic برای ۹۰٪ موارد؛ Sonnet فقط جایی که لازم است | LLM-only gate = هزینه‌ی هر draft + nondeterminism |
| **Docker Compose** (نه systemd/pm2) | isolation کامل، on/off یکدست، portable، مسیر k8s باز (نمره ۸–۹) | systemd/pm2 isolation ضعیف، آماده‌ی آینده نیست |
| **CI/CD gated** (نه auto-pull) | اتوماتیک کامل + امن (نمره ۹/۹) | auto-pull کور امنیت ۳/۱۰ |
| **SOPS+age** (نه plaintext/vendor) | نسخه‌بندی + امن + بدون lock-in | Infisical/Doppler ساده‌تر ولی lock-in |
| **Haiku-first** | ~۹۰٪ فراخوان، هزینه‌ی هدف AUD $15–40/ماه | Opus/Sonnet برای همه = خرج کنترل‌نشده |

---

## ۶. ریسک‌ها و mitigation

| ریسک | اثر | mitigation موجود |
|---|---|---|
| نشت PII به memory/log/LANGAR | فاجعه‌ی privacy + جریمه | INV-2: hash-ref، sanitise، DB جدا، gitleaks |
| خرج کنترل‌نشده‌ی API | تخلیه‌ی بودجه | INV-3: per-action + per-day caps، kill switch |
| ارسال غیرمجاز (Spam Act) | جریمه‌ی penalty unit | Gate HARD_BLOCK روی consent/ABN/opt-out + HITL |
| ادعای false (ACL) | جریمه‌ی ACCC | Gate superlative scan + **Sonnet semantic (P2 ✅ done)** |
| commit خراب یک AI | پروژه down | CI test gate + health-check + auto-rollback |
| یک پروژه منابع را می‌بلعد | بقیه down | per-container mem_limit/cpus |
| ~~semantic ACL فقط deterministic~~ | ادعای ظریف رد نشود | ✅ **بسته شد (P2)**: Sonnet semantic ACL روی draftهای پرریسک |

---

## ۷. ده پرامپت برای تکمیل و بهینه‌سازی

> هر پرامپت آماده‌ی copy-paste به یک session بعدی است. همه قید مشترک دارند:
> «`check_and_enforce()` اولین خط هر متد بیرونی؛ INV-1/2/3 رعایت شود؛ فایل‌های Python با bash heredoc نوشته و با AST check تأیید شوند؛ ASCII-only داخل کد؛ تست offline سبز قبل از done.»

### بخش A — تکمیل فازها (Completion)

**P1 — Worker C: review-response slice**
> هدف: `ContentAgent.draft_review_response(review, sentiment_result)` واقعی با Haiku را پیاده کن، با template fallback سازگار. orchestrator.`kickoff_review_response` را از `sentiment_complete` به draft+Gate+Queue کامل کن (الان stub با TODO). draft_type=`review_response` outbound است → Gate باید ABN/opt-out را روی پاسخ ریویو منطقی هندل کند (پاسخ عمومی پلتفرم opt-out لازم ندارد ولی ABN/ACL آره — این تمایز را در gate لحاظ کن). Acceptance: تستی مثل `test_phase2_leadpath.py` برای review slice، sentiment منفی → SLA 2h، superlative در پاسخ → SOFT_FLAG.

**P2 — Worker C + Gate: suburb-page slice و semantic ACL با Sonnet**
> هدف: `draft_suburb_page` واقعی (از bundle تحقیق Worker A+B) + بستن شکافِ باز Gate: لایه‌ی **semantic ACL با Sonnet** (`MODEL_KEY`) که فراتر از superlative scan، ادعای ظریفِ اثبات‌نشده را می‌گیرد (~AUD $0.016/draft، KB-02 §3.1). قید: فقط روی draftهای پرریسک (suburb/marketing) صدا زده شود نه هر draft (هزینه)؛ `check_and_enforce` قبل از فراخوان Sonnet؛ خروجی به flags اضافه شود نه جایگزین deterministic. Acceptance: یک claim ظریف («painters trusted by thousands») که از superlative scan رد می‌شود توسط Sonnet گرفته شود؛ هزینه per-draft لاگ در cost_events.

**P3 — Phase 3: Human Approval Queue واقعی با inline keyboard تلگرام**
> هدف: `ApprovalQueue.submit/approve/edit/reject` واقعی + کارت تلگرام با inline keyboard (Approve/Edit/Reject). قید INV-1: هیچ auto-approve، حتی روی انقضای SLA (فقط priority بالا + notify). `EDIT` با تغییر مادی → **REGATE**. هر تصمیم → `audit.append("APPROVAL_DECISION")`. allow-list `ALLOWED_OPERATOR_CHAT_IDS` روی callbackها هم enforce شود (نه فقط messageها). Acceptance: تست چرخه‌ی کامل drafted->queued->approved/edited(regate)/rejected؛ تست رد callback از chat_id غیرمجاز.

**P4 — Phase 4: Worker E (Channel) — publish فقط DRAFT برای GBP و social**  ✅ DONE (2026-07-02، test_phase4_channel 17/17)
> هدف: `ChannelAgent` که برای Google Business Profile و social فقط **DRAFT** می‌سازد (هرگز auto-post، INV-1). integration با GBP API به‌صورت draft/preview. قید: هیچ مسیر کدی که بدون عبور از Queue منتشر کند وجود نداشته باشد — یک تست بنویس که اثبات کند هیچ متد publish بدون approval صدا زده نمی‌شود. Acceptance: draft GBP post از Gate رد شود، در Queue بنشیند؛ تلاش برای publish بدون approval → استثنا.

**P5 — Phase 5: Worker F (Lead-capture) + sync با ServiceM8/Tradify**  ✅ DONE (2026-07-02، test_phase5_leadsync 25/25)
> هدف: `LeadCaptureAgent` کامل + `sync_jobs` واقعی به ServiceM8/Tradify. قید INV-2 بحرانی: فقط sync_* tools اجازه دارند PII را push کنند، آن‌هم **بعد از consent تأییدشده**؛ PII هرگز وارد audit payload نشود (hash-ref). ConsentRecord قبل از هر sync چک شود. pricing/lock-in هر دو CRM ذکر شود. Acceptance: تست که sync بدون ConsentRecord بلاک شود؛ تست که audit entry حاوی phone/email خام نباشد (verify_chain + اسکن payload).

### بخش B — بهینه‌سازی طراحی و کد (Optimization)

**P6 — Eval framework (KB-08)**  ✅ DONE (2026-07-01، evals/run_eval.py + test_phase6_eval)
> هدف: یک eval harness بساز که کیفیت draftهای Worker C و دقت Gate را بسنجد: golden set از enquiry/review/suburb با خروجی مورد انتظار + متریک‌ها (gate precision/recall روی consent/ABN/ACL، نرخ HARD_BLOCK کاذب، هزینه‌ی per-draft). offline و قابل‌اجرا در CI. قید: بدون فراخوان واقعی API در حالت پیش‌فرض (mock/cassette). Acceptance: `make eval` گزارش متریک چاپ کند؛ regression روی gate باعث fail CI شود.

**P7 — بهینه‌سازی هزینه: فعال‌سازی واقعی prompt caching و batch**  ✅ DONE (2026-07-02، test_phase7_costopt 26/26)
> هدف: flagهای `CACHE_ENABLED`/`BATCH_ENABLED` وجود دارند ولی به فراخوان‌های Anthropic سیم نشده‌اند. prompt caching را روی بخش ثابت پرامپت‌های Worker C (template/system) و batch API را برای follow-upهای روز ۲/۵/۱۰ (که زمان‌حساس نیستند) پیاده کن. قید: `check_and_enforce` با هزینه‌ی واقعی پس از cache discount لاگ کند؛ صرفه‌جویی در cost_events قابل‌اندازه‌گیری باشد. Acceptance: مقایسه‌ی هزینه‌ی per-draft قبل/بعد؛ هدف ≥۵۰٪ کاهش روی توکن system تکراری.

**P8 — مقاوم‌سازی I/O خارجی: retry/backoff + rate-limit + idempotency**  ✅ DONE (2026-07-01، test_phase8_resilience)
> هدف: Serper و Anthropic فعلاً بدون retry/backoff هستند؛ یک شکست شبکه = شکست draft. یک wrapper مشترک با exponential backoff + jitter، احترام به `Retry-After`، و **idempotency key** برای جلوگیری از draft/charge تکراری روی retry. قید: backoff هرگز سقف per-day را دور نزند (`check_and_enforce` هر تلاش)؛ هر retry در audit. Acceptance: تست شبیه‌سازی 429/500 → backoff و موفقیت نهایی؛ تست که retry هزینه‌ی مضاعف لاگ نکند.

**P9 — بهینه‌سازی لایه‌ی داده: connection pooling + معماری DB**  ✅ DONE (2026-07-01، test_phase9_datalayer)
> هدف: الان هر `audit.append`/gate/governance یک connection باز و بسته می‌کند (هر اکشن چند بار). یک connection manager/pool یا context سبک بساز؛ همراه با ارزیابی trade-off SQLite vs Postgres برای رشد آینده (concurrency نوشتن audit). قید: append-only و hash-chain صدمه نبیند؛ `verify_chain` بعد از تغییر سبز بماند؛ DB همچنان از LANGAR جدا. Acceptance: benchmark تعداد connection per enquiry قبل/بعد؛ تست concurrency نوشتن audit بدون شکست زنجیره.

**P10 — استقرار end-to-end infra-control + فعال‌سازی SOPS+age + threat-model hardening**
> هدف: اسکلت infra-control را روی VPS به‌صورت end-to-end deploy و تست کن: `stackctl up brushline` پشت Traefik، یک چرخه‌ی کامل CI (push→test→gitleaks→build→GHCR→deploy→health→rollback)، جایگزینی `.env` دستی Brushline با **SOPS+age**، و پیاده‌سازی موارد باز `THREAT_MODEL.md`. قید: branch protection روی main؛ `stackctl kill --all` تست شود؛ هیچ secret خام در git (gitleaks سبز). Acceptance: یک deploy عمداً-خراب → auto-rollback + alert تلگرام؛ secretها فقط رمزنگاری‌شده در repo؛ runbook به‌روز.

---

## ۸. قدم بعدی (پیشنهاد، تصمیم با تو)

ترتیب با بالاترین ROI و کمترین ریسک، هم‌راستا با survival filter:
1. ✅ **P3 (Approval Queue واقعی)** — انجام شد (2026-07-01، 47/47). قلب INV-1 برقرار است؛ دیگر بالاترین اولویتِ باز نیست.
2. ✅ **P1 + P2 (review + suburb + semantic ACL)** — هر دو انجام شد (2026-07-01)؛ Phase 2 کامل و تنها شکاف compliance باز بسته شد. مسیر بعدی: **P8 + P9** (مقاوم‌سازی I/O و DB).
3. ✅ **P8 + P9** — انجام شد (2026-07-01): `resilience.call_with_retry` (backoff+jitter، Retry-After، idempotency key، `check_and_enforce` هر تلاش، `IO_RETRY` در audit) روی Serper+Anthropic؛ connection pool (thread-local، close=no-op) + audit chain-safe با **rowid + lock** (concurrency تست شد). مسیر بعدی: **P6 (eval)**.
4. ✅ **P6 (eval)** — انجام شد (2026-07-01): golden set ۱۵ موردی، متریک gate precision/recall روی consent/ABN/opt-out/ACL/PII (همه 1.0)، false-HARD_BLOCK=0، regression -> exit 1. `make eval`. مسیر بعدی: **P10** یا P4/P5/P7.
5. **P10 (infra e2e)** — وقتی اپ آماده‌ی production شد.
6. ✅ **P4 (Worker E Channel)** — انجام شد (2026-07-02): `ChannelAgent` draft-only برای GBP/social؛ تنها مسیر publish() است که بدون ApprovalAction با status=approved استثنای `ChannelError` می‌دهد (INV-1)؛ در MVP حتی پس از approve فقط PREVIEW برمی‌گرداند (`live_posted=False`، بدون API زنده). `orchestrator.kickoff_gbp_post` مسیر draft→Gate→Queue. تست 17/17. باقی‌مانده: **P5 + P7**، سپس P10.
7. ✅ **P5 (Worker F + CRM sync)** — انجام شد (2026-07-02): sync فقط از متدهای `sync_*` و فقط با ConsentRecord تأییدشده (INV-2؛ بدون consent → `SyncBlocked` + audit). payload به whitelist هشت‌فیلدی KB-01 §5 محدود است. بدون API key → **dry-run** (بدون شبکه، SyncJob persisted با status=pending). حالت live از `call_with_retry` + **idempotency key ثابت روی retryها** استفاده می‌کند (بدون رکورد تکراری در CRM). ورودی `orchestrator.sync_lead` فقط با operator در `ALLOWED_OPERATOR_CHAT_IDS` (fail-closed، INV-1). hardening: کلید `name` هم به PII_FIELDS در audit اضافه شد. تست 25/25 شامل اسکن کل audit برای PII خام + verify_chain. **قبل از اولین اجرای live، endpoint/auth دو API را با مستندات فعلی verify کن** (developer.servicem8.com / Tradify API docs).
   - **Pricing/lock-in (بررسی 2026-07، تأیید محلی لازم):** ServiceM8 (AU): قیمت flat per-business با کاربر نامحدود — Free (۳۰ job/ماه)، Starter A$29، Growing A$79، Premium A$149، Premium Plus A$349 (incl GST). Tradify: per-user ex GST — Lite $48، Pro $52، Plus $62 (+20c/SMS). برای نقاش solo با حجم کم، ServiceM8 Starter ارزان‌تر و مقیاس‌پذیرتر است (کاربر نامحدود). lock-in: هر دو export CSV دارند؛ دیتا گروگان نیست ولی automation/form/template منتقل نمی‌شود. لایه‌ی sync ما adapter-based است (`_post_servicem8`/`_post_tradify`) — سوئیچ CRM = تغییر یک adapter، نه data model.
8. ✅ **P7 (caching/batch)** — انجام شد (2026-07-02): `cache_control: ephemeral` روی بلوک ثابت system در `_haiku`/`_sonnet` (flag: CACHE_ENABLED)؛ `_cost_from_usage` هزینه‌ی واقعی پس از تخفیف را از usage برمی‌گرداند (write ×1.25، read ×0.10، batch ×0.50) و همان به `log_cost`/cost_events می‌رود (INV-3). follow-upهای روز 2/5/10 با الگوی async submit/collect به Message Batches (50% off؛ flag: BATCH_ENABLED؛ خاموش/آفلاین → fallback همان مسیر sync). draftهای batch هم از Gate→Queue می‌گذرند (INV-1)؛ item شکست‌خورده → fallback template. تست 26/26؛ صرفه‌جویی per-draft با system کش‌شده روی پروفایل تست: **66%** (هدف ≥50%). **نکته‌ی صداقت:** API فقط بلوک‌های بالای حد minimum (~1–2k token بسته به مدل) را cache می‌کند؛ پرامپت‌های فعلی Worker C کوچک‌ترند، پس wiring درست است ولی سودِ read وقتی واقعی می‌شود که بلوک ثابت بزرگ شود (مثلاً system+template صفحه‌ی suburb). حسابداری هزینه در هر دو حالت درست است چون از usage واقعی می‌خواند.
9. **P10** — تنها مورد باز؛ نیازمند دسترسی VPS.

> **باگ‌فیکس INV-3 (2026-07-02):** `get_daily_spend_aud` از `date.today()` محلی استفاده می‌کرد در حالی که cost_events با `datetime.utcnow()` مهر می‌خورد — از نیمه‌شب تا ~۱۰ صبح سیدنی، daily spend صفر خوانده می‌شد و **سقف روزانه عملاً bypass بود**. اصلاح شد: `_utc_today()` منبع واحد حقیقت در governance. همچنین target خرابِ `check` در Makefile (multi-line بدون tab) که `make eval` را می‌شکست تعمیر شد. کل suite (9 فایل تست + eval harness) سبز.

> یادداشت صداقت معرفتی: شکاف compliance که قبلاً باز بود (**semantic ACL**) با P2 بسته شد (2026-07-01). اما semantic ACL یک لایه‌ی LLM احتمالاتی و **advisory** است (SOFT_FLAG، نه HARD_BLOCK) -- می‌تواند خطا کند؛ جایگزین بازبینی انسانی نیست. INV-1 همچنان حاکم است: هر draft قبل از انتشار human-approved می‌شود.
