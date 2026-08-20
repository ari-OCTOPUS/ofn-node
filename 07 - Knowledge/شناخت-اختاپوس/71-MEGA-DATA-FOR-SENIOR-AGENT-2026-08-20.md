# OCTOPUS — MEGA-DATA برای ایجنت ارشد
## همهٔ آنچه باید بدانید تا پروژه را ادامه دهید
## تاریخ: 2026-08-20 (شب) · نگارنده: ایجنت C (سشن sess_1d388c34)

---

## ۱. ماهیت پروژه

OCTOPUS یک ارگانیسم نرم‌افزاری **تک‌مالکی و محلی** است:
- **زبان:** Python 3.13.7
- **محل:** `F:\backup` — یک Obsidian vault که هم‌زمان درخت زندهٔ اجراست
- **OS:** Windows 10/11 · Shell: Git Bash + PowerShell 5.1
- **درخت زنده:** `_ops/` — پنج+ پروسهٔ Python هم‌زمان می‌دوند

### الگوی زیستی
سیستم عصبی توزیع‌شدهٔ اختاپوس، سیستم ایمنی، stigmergy مورچه، مقیاس‌بندی کلایبر. **نه AGI، نه production-ready، نه آگاه.** اسناد خودش این را صریح می‌گویند.

### هفت لایه و وضعیت واقعی

| لایه | وضعیت |
|---|---|
| Body | زنده (organism PID زنده، beat جلو می‌رود) |
| Senses | نیمه‌کور (knowledge sidecar ساخته شد؛ hook فعال نیست) |
| Memory | LIVE_READONLY (reads=3/cycle، readback=read_ok) |
| Understanding | زنده ولی شنیده‌نشده (cortex/business_brain chat را نمی‌شنوند) |
| Decision | تازه تعمیر شده (ratio model ساخته شد) |
| Action | propose-only (executable=false بدون استثنا) |
| Safety | بالغ‌ترین لایه (allowlist، lease، trust anchor) |

---

## ۲. حکمرانی فعلی (دستورهای #۱–#۱۷)

### رشتهٔ فرمان
```
#۶ → #۷ → #۸ → #۹ → #۱۰ → #۱۱ → #۱۲ → #۱۳ → #۱۴A → #۱۷(ایجنت C)
```
هر دستور بعدی قبلی را تکمیل یا تصحیح می‌کند. **مگا‌دستور #۱۳ حاکم است** (حلقهٔ بستهٔ تلگرام).

### وضعیت LIVE gates

```yaml
LIVE-A: PASS               # lease نویسندهٔ واحد فعال و fail-closed
LIVE-B: BLOCKED             # منتظر: ≥۵ رویداد تلگرام واقعی + server_created در spine
LIVE-C: PASS_WITH_INCIDENT # حافظه زنده خوانده می‌شود (۲ availability incident ثبت‌شده)
LIVE-D: SIGNED_AND_GATED   # کارت امضاشده، اجرای پشت LIVE-B
LIVE-E: BLOCKED            # دست مالک — با هیچ‌کدام از این دستورها بسته نمی‌شود
GAP-001: OPEN              # مرز نهایی — فقط مالک می‌بندد
```

### سه نقش فعلی ایجنت‌ها

| ایجنت | سشن | lane | وضعیت |
|---|---|---|---|
| **A/B** | telegram-closed-loop-20260820 | Telegram حلقهٔ بسته | فعال — lease holder |
| **C** | sess_1d388c34 (این سشن) | اندام‌ها/afferentها | کار lane تمام شد — منتظر handoff A19 |
| **موازی** | organ-map-20260820 | mapper/اندام‌ها | session قبلی C — کارش فریز شد |

### lease نویسندهٔ واحد

```yaml
path: _ops/state/locks/octopus-writer.lock
holder: ایجنت A (telegram session)
scope: telegram, owner_console, spine_emitter, router_attribution, evidence, git
ttl: 10800s (3 ساعت)
```

**قاعده:** هر write زیر lease. بدون lease فقط read-only. ایجنت C اولویت پایین‌تر از A/B دارد.

---

## ۳. امضاها و کلیدها

### لنگر اعتماد (TRUST ANCHOR)

```
algorithm: Ed25519 (pure, RFC 8032)
fingerprint_sha256: 2413e9746f13afc900b31ad4d966a6783d73662f661fa0d6dc578e9b244ab6b2
pubkey: _ops/owner-signing/octopus-owner-ed25519-public.pem
private: ~/.octopus-signing/octopus-owner-ed25519-private.pem (owner-only)
check: _ops/owner-signing/check_anchor.py (fail-closed)
```

### سه کارت امضاشده (ALL_THREE_SIGNATURES_VERIFIED)

| کارت | فراخوان | سقف | وضعیت |
|---|---|---|---|
| PRE-REG-EVENT-TIME-PROBE | ۱ | AU$0.01 | اجرا شد → PROBE_RESPONSE_INVALID |
| PRE-REG-JUDGE-BIAS-PHASE2 | ۴۸۰ | AU$0.20 | امضاشده، اجرا نشده |
| PRE-REG-FULL-LOOP-FLASH | ۱۲ | AU$0.50 | امضاشده، پشت LIVE-B |

### backup_recovery: UNKNOWN
owner-key.enc در `F:/OCTOPUS-SURVIVAL-BACKUP-2026-08-19/` — runbook آماده، اجرا فقط با مالک.

---

## ۴. زیرساخت مدل و پول

### مسیر LLM
```
DeepSeek v4-flash = مسیر اجراکنندهٔ اصلی (پیش‌فرض DEEPSEEK-AUTOMATIC-ROUTING-01)
GLM = داور خانوادهٔ متفاوت (D10 — ولی شارژ نیست)
Fugu = مغز اصلی (سهمیه 120/60 تمام شده)
qwen2.5:1.5b = live/center محلی
```

### FX
```yaml
pin: FX-PIN-20260820-01 (RBA 20-Aug، rate=0.7116)
source: CSV رسمی F11.1 (FXRUSD)
divergence_resolved: CSV=0.7116 vs HTML=0.7101 (HTML یک روز lag)
watcher: probe_when_fx_fresh2.sh — dead (پروب اجرا شد)
```

### بودجه
```
سقف ماهانه: ۳۰ AUD · human_gate: ۲۰ · hard_stop: ۲۴ · per-call: ۱
امروز خرج‌شده: ~AU$0.12 (۶۰ فراخوان K9 + پروب + ترافیک عادی)
life_credit ≠ AUD (واحد داخلی، هرگز تبدیل نمی‌شود)
```

### انتساب رسیدها
```
امروز: ۱۲۲ رسید · فقط 19.7% task_id دارند · ۹۸ بی‌انتساب
ریشه: پروسه‌های کدقدیم pre-T50
تا رفع: cognition پولی Telegram خاموش
```

---

## ۵. تلگرام (مسیر بحرانی)

### سه بات

| bot_id | username | display | توکن | poller |
|---|---|---|---|---|
| 8187434784 | @Robo2725_bot | `pi 4+1` | TELEGRAM_BOT_TOKEN | approval_channel |
| 7992324219 | @intergrade2725_Bot | `اختاپوس` | TG_CENTER_BOT_TOKEN | center.py |
| 8861821707 | @zimangiftbot | `زیمان` | TG_ZIMAN_STUDIO_BOT_TOKEN | ziman studio |

### مسیر canonical inbound
```
owner DM → center.py (PID زنده) → input_surface_policy.classify (outer-dm-owner)
→ owner_console.telegram_adapter.handle_message
  → local_commands (short-circuit: /status /health /memory /help /capabilities /remember)
  → paid-cognition pause gate (OCTOPUS_PAID_COGNITION!=1 → degraded reply)
  → collaborator/conversation (فقط اگر paid cognition روشن)
```

### دوزمانی spine (producer_2)
```
message.date (تلگرام) → occurred_at
ingest محلی → recorded_at
emitter: owner_console seam → spine (schema v2, time_precision=1s)
idempotency: tg-{chat}-{date}-{update_id}|owner-console
bot_id: از getMe کش‌شده
```

### فرمان‌های محلی (صفر مدل)
```
/status · /health · /memory · /help · /capabilities · /remember <text>
```

### وضعیت canary
```
رویدادهای تلگرام: ۴ (هر پیام +1 ✓ · message.date ✓ · precision=1s ✓)
مدل calls در پنجرهٔ /status: ۲ (FAIL — به collaborator رفت، Fugu 120/60)
رفع: local short-circuit + paid-pause → مرکز ریاستارت شد
گیت دور ۳: منتظر /status تازه از مالک
```

### شماره‌های مهم
```
120/60 = سهمیهٔ Fugu (نه خطای شمارنده)
409 = تصادم poller (بالا ↩️ approval_channel و center روی بات‌های جدا)
```

---

## ۶. حافظهٔ دوزمانی

### spine
```
path: _ops/state/spine/spine.db (SQLite, WAL)
schema_version: 2 (dual-write افزودنی)
columns: +occurred_at_real, +event_time_source, +time_precision, +legacy_no_event_time, +clock_skew
```

### producerها

| producer | منبع ساعت | precision | رویدادها |
|---|---|---|---|
| provider/router_request_ts | ساعت محلی | ms | ۱۱ |
| provider/provider_server_created | ساعت سرور | 1s | ۱ |
| telegram/telegram_message_date | ساعت تلگرام | 1s | ۴ |

### suite روی داده واقعی: PASS (n=7,296)

### ADR-043 (بلوکر واقعی)
```
دو ستون occurred/recorded روی کل جدول: median=0.01ms · stdev_max=7.03ms
یعنی: هنوز از یک ساعت می‌آیند — NOT independently meaningful
گیت VERIFIED_BITEMPORAL: نیازمند ≥۲ منبع مستقل + stdev>10ms + late-arriving واقعی
```

### read paths از decision_time
```
✓ memory_read_loop (LIVE-C)
✗ vault search — بدون decision_time
✗ vector index — بدون decision_time  
✗ knowledge graph — بدون decision_time
✗ context builder DeepSeek — بدون decision_time
```

---

## ۷. تصمیم‌های علمی کلیدی

### D6: CLOSED_NEGATIVE
```
یافته: JUDGEMENT_IS_PAIR_DEPENDENT
p_exact = 2/48620 = 4.113533525298231e-05 (Fisher دوطرفه)
پیام: هیچ داور تک‌نفره‌ای ground truth نیست
گیت رسمی: stable_under_permutation → فقط قضاوت پایدار پذیر؛ وگرنه VOID_UNSTABLE
```

### Active Inference: NOT_READY_FOR_ACTIVE_INFERENCE
```
surprise اکتشافی: GREEN=17.33 vs AMBER=17.81 nats (n_AMBER=56، ضعیف)
مدل انتقال: غایب
شبیه‌ساز: research/active_inference/ (pymdp + compat layer)
```

### Judge Bias Framework: ۷/۷ CONFIRMED (آفلاین)
```
۱۲۰ جفت · ۵ داور تزریقی · ۶۰۰ قضاوت
سه باگ واقعی رفع شد: مختصات قاطی، hash غیرقطعی، confound کیفیت×طول
```

---

## ۸. اندام‌ها (lane ایجنت C)

### ۱۴ اندام
```
LIVE=8 · SKELETON=4 · ORPHAN=0 · DEAD=0 · UNSAFE=2
```

### اتصال knowledge (اهم‌ترین)
```
sidecar: _ops/organs/knowledge_afferent.py (v3, schema v3, quality enum ۸ سطح)
hook: _ops/organs/knowledge_hook.py (flag-gated, default OFF)
ratio model: _ops/organs/ratio_model.py (pure, ۸/۸ property tests)
feedback: _ops/organs/feedback_destiny.py (state machine, ۴/۴)
loop breakers: _ops/organs/loop_breakers_impl.py (۹/۹)
```

### starvation (RIشه)
```
dominant: NO_SOURCE (weight=0.5)
counterfactual: knowledge→bus = ratio 0.17→0.50 = BORDERLINE
patch پیشنهادی: diff در broken_reader_analysis.py (PROPOSAL_ONLY — A/B اجرا کند)
```

### baseline mapper
```
epoch: mapper-epoch-20260820T2017
py_files: 24,907 · inventory_sha256: 9056c1b4… · reproducible: True
label: MAP_STALENESS_CANDIDATES=1257
```

---

## ۹. پل ارتباطی تلگرام

```
script: _ops/scripts/tg_bridge_once.py
loop: هر ۵ دقیقه (bash background)
push: فقط sendMessage (بدون getUpdates — 409-safe)
anti-spam: فقط روی تغییر یا ≥۳۰ دقیقه
```

---

## ۱۰. ریسک‌ها و تناقض‌های باز

```yaml
open_contradictions:
  C-042: starvation از گردکردن میلیواحد (REPRODUCED_OFFLINE)
  C-043: SUSPECTED_VOID
  C-044: reasons فقط برای بخشی از گذارها
  C-045: period دوگانه
  C-046: نگه‌داری نشدن شواهد per-beat
  PARALLEL_AGENT_WRITE_RISK: حل‌نشده (lease رژیم فعال ولی دو سشن می‌نویسند)

availability_incidents: ۲ (هر دو ریشهٔ C-047 — کامنت کهنهٔ bat)
crashes: ۰

dangerous_belief_active:
  "تعویض خانوادهٔ داور مشکل D6 را حل می‌کند"
  → باطل اعلام شد (pair-dependent نه family-dependent)

known_limitations:
  - daemon (brain.daemon) کدقدیم دارد و ریاستارت نشده
  - cortex/business_brain پیام chat را مستقیم نمی‌شنوند
  - ۹۸/۱۲۲ رسید امروز بی‌انتساب
  - run_all ثبت تست‌های organ نکرده
```

---

## ۱۱. فایل‌های کلیدی (path map)

```
# حکمرانی
02-DECISIONS/OWNER-DIRECTIVE-{06..14A,17,AGENT-C-PLAN}-2026-08-20.md
02-DECISIONS/PRE-REG-{EVENT-TIME-PROBE,JUDGE-BIAS-PHASE2,FULL-LOOP-FLASH}-2026-08-20.md
02-DECISIONS/PAYLOAD-{EVENT-TIME-PROBE,JUDGE-BIAS-PHASE2,FULL-LOOP-FLASH}-2026-08-20.json{,.sig}
_ops/safety/EXECUTABLE-ALLOWLIST.md
_ops/owner-signing/TRUST-ANCHOR.md

# تلگرام
research/full_loop/turn_engine.py
research/full_loop/telegram_cockpit.py
_ops/owner_console/local_commands.py
_ops/owner_console/telegram_adapter.py
_ops/telegram_center/input_surface_policy.py

# spine
_ops/spine/event_spine.py
_ops/spine/spine_adapters.py
research/bitemporal/real_data_check.py
_ops/tests/test_bitemporal_spine_spec.py

# اندام‌ها
_ops/organs/knowledge_afferent.py
_ops/organs/knowledge_hook.py
_ops/organs/ratio_model.py
_ops/organs/feedback_destiny.py
_ops/organs/loop_breakers_impl.py
_ops/organs/broken_reader_analysis.py
_ops/organs/concept_code_mapping.py

# پژوهش
research/judge_bias/framework.py
research/active_inference/efe_dashboard.py
research/event_time_probe/pipeline.py
research/event_time_probe/rba_parser.py

# پایش
research/monitor/chain_dashboard.py
research/market_watch/RATES-REPORT-2026-08-20.md
_ops/scripts/tg_bridge_once.py

# state
_ops/state/labels.json → docs/NOW.md → OCTOPUS/CURRENT-TRUTH.md
01-TRUTH/DISCOVERY-BACKLOG.md
```

---

## ۱۲. آنچه ایجنت ارشد باید بداند (سه جمله)

1. **مهم‌ترین فهم امروز:** ضعف «زمان مستقل» نبودِ فیلد نبود — دورریختنِ آن بود؛ پرسش درست «کدام ساعت؟» است نه «چه تأخیری؟».
2. **مهم‌ترین ندانسته:** آیا surprise کالیبره‌شده با رنگ arbiter رابطهٔ پایدار دارد — با صفر نمونهٔ RED و AMBER کم، داده کافی نیست.
3. **خطرناک‌ترین باور فعلی سیستم:** «suite سبز روی داده واقعی = spine دوزمانی تأییدشده» — این suite سازگاری درونی را می‌سنجد؛ تا منابع مستقل ساعت نیایند، VERIFIED نمی‌شود.

---

## ۱۳. قواعد نقض‌ناپذیر (خلاصه نهایی)

```text
۱. executable=false بدون استثنا (فقط allowlist ADR-035)
۲. هر write زیر lease
۳. رأی چت ≠ امضای Ed25519
۴. هیچ فراخوان پولی بدون کارت امضاشده + FX تازه
۵. حذف ممنوع؛ فقط انتقال
۶. git add -A هرگز
۷. secret هرگز در چت/لاگ/evidence
۸. no amend/rebase
۹. یک bot_id → یک poller
۱۰. معیار پس از دیدن نتیجه تغییر نمی‌کند
```
