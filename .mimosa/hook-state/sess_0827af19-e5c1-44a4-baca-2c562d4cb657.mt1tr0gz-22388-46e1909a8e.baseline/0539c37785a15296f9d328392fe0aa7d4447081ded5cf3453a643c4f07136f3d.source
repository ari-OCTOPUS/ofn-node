# گزارش اسکن معماری عمیق — پروژه OCTOPUS
**تاریخ:** 2026-07-12  
**نوع:** فقط-خواندنی (Read-Only Scan)  
**مناطق اسکن‌شده:** `_ops/`, `4d_system/`, `OCTOPUS/`, `nervous-system/`, `04 - Architect System/`, `agent-prompts/`, `app/`, `03 - Projects/`, `05 - Agents/`, `06 - Architecture Maps/`, `07 - Knowledge/`, `CHRONOS-FABLE-OS/`  
**کل فایل‌های شناسایی‌شده:** 180+  
**فایل‌های خوانده‌شده به‌صورت عمیق:** ~120  

---

## ۱. خلاصه اجرایی (Executive Scan Summary)

پروژه OCTOPUS یک **ارگانismus چند-عاملی خودبهبود و خود-تحت-نظارت** است که در سه لایه اصلی ساخته شده:

| لایه | مسیر | نقش | وضعیت |
|---|---|---|---|
| **Boss Organism** | `_ops/` | ضربان قلب، بودجه، حکمرانی، شفافیت، دکتر تکاملی | پیاده‌سازی شده، 90%+ |
| **Leg (Idea-Finder)** | `4d_system/` | سیستم هسته‌ای، عامل‌ها، حافظه، کنترل‌پلن | پیاده‌سازی شده، 80%+ |
| **Cockpit / Nervous System** | `OCTOPUS/`, `nervous-system/` | داشبورد، استخراج‌کننده‌ها، داده‌های زنده | پیاده‌سازی شده، 85%+ |
| **Build Spine / Specs** | `04 - Architect System/` | اسناد معماری، پروتکل‌های ایمنی، ژنوم | مستند شده، 95%+ |

**چهار خانواده ساختاری شناسایی شدند:**

1. **خودبهبودی (Self-Healing):** 26 فایل کلیدی — ضربان قلب، نگهبان، بازگردانی، خانه‌تکانی، دفترچه روزنامه‌نگاری پایدار
2. **خود-حکمرانی (Self-Control):** 46 فایل کلیدی — دروازه‌های چندعاملی، پرچم‌های فعال‌سازی، HMAC ضد جعل، ماشین حالت تأییدیه، TCB
3. **خودآگاهی (Self-Awareness):** 28 فایل کلیدی — مدل خودِ AST، 35 پروب ممیزی، جرقه GWT، سایه قلب، هومئوستات استرس، نقش innervation
4. **خود-تکامل (Self-Modif./Evolution):** 25 فایل کلیدی — دکتر تکاملی، MAP-Elites، خود-کد، خود-تکامل، اتاق دادگاه مخالف، گارد ژنوم

**وضعیت پیش‌فرض سیستم:** Paper-mode ($0، propose-only، همه پرچم‌های wiring خاموش). تمام اثرگذارهای زنده نیازمند پرچم فعال‌سازی مالک.

**بدترین نقطه‌های آسیب‌پذیری:**
- `human_append_guard` پیش‌فرض pass-through است (کد مُرده)
- `apply_merge` تعریف شده اما هیچ‌گاه در زمان اجرا فراخوانی نمی‌شود
- سندباکس self-code خالی است — مسیر approve→apply تست نشده
- TCB self-guard در `guardrails.py` اعتبارسنج خارجی ندارد
- kill-switch تعریف شده اما «v1: always False remains»

---

## ۲. مناطق مخزن اسکن‌شده (Repository Zones Scanned)

| منطقه | فایل‌ها | روش |
|---|---|---|
| `_ops/` | ~380 فایل | Glob + Grep + Read 40 فایل کلیدی |
| `4d_system/` | 3,355 فایل | Glob + Grep + Read 44 فایل کلیدی |
| `OCTOPUS/` | 55 فایل | Glob + Grep + Read 15 فایل |
| `nervous-system/` | 61 فایل | Glob + Grep + Read 18 فایل |
| `04 - Architect System/` | 5,100+ فایل | Glob + Grep + Read 20 فایل سطح بالا |
| `agent-prompts/` | 6 فایل | Read کامل |
| `app/` | 30+ فایل | Glob + Grep + Read 10 فایل |
| `03 - Projects/` | 50+ فایل | Glob + Grep + Read 8 فایل |
| `05 - Agents/` | 10 فایل | Glob + Read |
| `06 - Architecture Maps/` | 20 فایل | Glob + Read |
| `07 - Knowledge/` | 30+ فایل | Glob + Grep |
| `CHRONOS-FABLE-OS/` | 40+ فایل | Glob + Grep |

---

## ۳. نقشه خودبهبودی (Self-Healing Map)

### ۳.۱ فایل‌های کلیدی

| مسیر | خطوط | نقش در معماری | سطح ریسک | برچسب معرفتی |
|---|---|---|---|---|
| `_ops/organism.py` | 548 | تیک همیشه‌روشن ۵ دقیقه‌ای، ضربان قلب، kill-check، سرور HTTP وضعیت | **HIGH** | FACT |
| `_ops/watchdog.py` | 86 | ابزار revive توسط مالک؛ تسلیم مطلق STOP | **MEDIUM** | FACT |
| `_ops/watchdog_extension.py` | 255 | بررسی‌های دوره‌ای سلامت (پورت، تازگی state، پرچم STOP، alertهای governor) | **LOW** | FACT |
| `_ops/checkpoint.py` | 85 | snapshot هر ضربان + replay <۵ ثانیه از ledger | **LOW** | FACT |
| `_ops/durable_journal.py` | 120 | resume-not-restart journal (state start/ok/error) | **LOW** | FACT |
| `_ops/smoke_24h.py` | 116 | چک‌لیست ۲۴ ساعته مالک: state-fresh، ضربان قلب، ledger-verify، zero-spend | **LOW** | FACT |
| `_ops/germline.py` | — | تشخیص lag پشتیبان + retry با backoff | **LOW** | FACT |
| `_ops/heart/replay_s.py` | — | سیستم replay قلب | **MEDIUM** | FACT |
| `4d_system/brain/backup.py` | — | snapshot روزانه WAL-safe DB + پشتیبان فایل هویت (rotation ۵تایی) | **LOW** | FACT |
| `4d_system/brain/housekeeping.py` | — | سیاست archive-never-delete با smart caps | **LOW** | FACT |
| `nervous-system/extract_health_score.py` | 341 | الگوریتم health score ترکیبی (system 40% + fitness 35% + telemetry 25%) | **LOW** | FACT |
| `nervous-system/extract_watchdog_data.py` | 220 | پایش liveness نگهبان | **LOW** | FACT |
| `04 - Architect System/scripts/germline-backup.ps1` | 119 | P0.5 پشتیبان روزانه با integrity gates | **MEDIUM** | FACT |
| `04 - Architect System/scripts/dashboard_doctor.py` | 199 | چک‌کننده سلامت vault (قطعی، صفر LLM) | **LOW** | FACT |
| `app/events.py` | — | ledger hash-chain | **MEDIUM** | FACT |
| `app/lifecycle.py` | — | نردبان ACTIVE→EXTINCT | **MEDIUM** | FACT |
| `app/quarantine.py` | — | gate اعتبارسنجی lead | **LOW** | FACT |
| `app/guardian.py` | — | ضربان قلب + تشخیص tamper | **MEDIUM** | FACT |
| `app/backup.yaml` | — | استراتژی ۳-۲-۱ | **LOW** | FACT |

### ۳.۲ شواهد کلیدی

**`_ops/organism.py:1-26`** — قرارداد اصلی ارگانismus:
> «kill-check: STOP / STOP-ORGANISM / STOP-METABOLIC؛ telemetry + reconcile (FREEZE/CONFLICT در mismatch — I3)；ضربان قلب ساعتی؛ fitness روزانه + replication»

**`_ops/watchdog.py:39-63`** — LifeDoctrine §4:
> «revive = ابزار مالک، نه خود-نگهداری؛ first-birth guard: فقط revive، هرگز first-launch»

**`_ops/checkpoint.py:25-41`** — Checkpoint در chrono.db:
> `INSERT OR REPLACE INTO checkpoint(beat_id, logical_clock, ledger_hash, ...)`

**`nervous-system/extract_health_score.py`** — الگوریتم health score:
> «Health score = ترکیب وزنی ۳ محور: system_health · fitness_health · telemetry_health. خروجی: ۰..۱۰۰ (مماسل: ۱۰۰ = سالم، ۰ = بحرانی)»

### ۳.۳ ارزیابی

خودبهبودی **خوب پیاده‌سازی شده** است. چندین لایه مستقل وجود دارد: checkpoint، journal پایدار، smoke test، نگهبان، germline backup. **ریسک اصلی** در `organism.py` است — اگر تیک اصلی از کار بیفتد، کل ارگانismus متوقف می‌شود (تک نقطه شکست).

---

## ۴. نقشه خود-حکمرانی (Self-Control / Governance Map)

### ۴.۱ فایل‌های کلیدی

| مسیر | خطوط | نقش در معماری | سطح ریسک | برچسب معرفتی |
|---|---|---|---|---|
| `_ops/budget/opslib.py` | 373 | کتابخانه هسته‌ای: مسیرها، پرچم STOP/FREEZE، ledger bridge، `live_gate_open` | **CRITICAL** | FACT |
| `_ops/budget/approval_state_machine.py` | 482 | HITL کانونی: suggested→queued→owner_approved→executed + rollback classes | **MEDIUM** | FACT |
| `_ops/budget/organ_gate.py` | 178 | دروازه بودجه per-organ (fail-closed، سقف ماهانه از budgets.yaml) | **HIGH** | FACT |
| `_ops/budget/money_gate.py` | 46 | Human-gate: آستانه AU$20 برای پول واقعی | **HIGH** | FACT |
| `_ops/budget/capability_gate.py` | 104 | AND ۳ عاملی: suite-green + LIVE_ENABLED + تأیید per-action | **HIGH** | FACT |
| `_ops/budget/governor_epoch.py` | 379 | governor allostatic؛ پیش‌فرض dry؛ LLM double-gated | **MEDIUM** | FACT |
| `_ops/budget/human_append_guard.py` | 174 | HMAC ضد جعل برای `is_human=1`؛ secret هر بوت؛ محافظت در برابر replay | **HIGH** | FACT |
| `_ops/cortex/depth_guard.py` | 107 | عمق delegation ≤۲؛ تشخیص write-without-event (فقط observational) | **LOW** | FACT |
| `_ops/cortex/registry.py` | — | رجیستری cortex | **MEDIUM** | FACT |
| `_ops/telegram_center/center.py` | 679 | کانال تأییدیه، human-in-the-loop | **MEDIUM** | FACT |
| `4d_system/brain/guardrails.py` | — | **TCB gate**. hardcode فایل‌های محافظت‌شده. fail-closed. | **HIGH** | FACT |
| `4d_system/control_plane/policy.py` | — | نردبان سیاست (۰=observe → ۵=kill-switch) | **MEDIUM** | FACT |
| `4d_system/control_plane/flags.py` | — | فقط `CONTROL_PLANE_OBSERVE_ONLY` = True. بقیه default-off. | **LOW** | FACT |
| `4d_system/brain/daemon.py` | — | month-runner بدون UI. `SELF_CODE_ENABLED` پیش‌فرض OFF. | **MEDIUM** | FACT |
| `nervous-system/approval_state_machine.py` | 280 | ماشین حالت صریح با transition graph | **MEDIUM** | FACT |
| `nervous-system/audit_logger.py` | 121 | logger audit | **MEDIUM** | FACT |
| `nervous-system/security-checklist.py` | 180 | اسکنر نشت secret | **MEDIUM** | FACT |
| `nervous-system/verify_schema.py` | 316 | دروازه drift schema | **LOW** | FACT |
| `04 - Architect System/scripts/budget_gate.py` | 222 | دروازه بودجه (fail-closed) | **HIGH** | FACT |
| `04 - Architect System/scripts/governor_shadow.py` | 72 | governor سایه (فقط-خواندنی، صفر LLM، $0) | **HIGH** | FACT |
| `04 - Architect System/scripts/genome_guard.py` | 64 | گارد یکپارچگی ژنوم | **HIGH** | FACT |
| `app/gates.py` | — | دروازه‌های بودجه/spawn/effector | **HIGH** | FACT |
| `app/governance.py` | — | نردبان ریسک GREEN→RED | **MEDIUM** | FACT |
| `app/shadow.py` | — | propose-only | **LOW** | FACT |
| `app/ARCHITECT_CHARTER` | — | منشور تغییرناپذیر | **LOW** | FACT |
| `app/AGENT_REGISTRY` | — | رجیستری عامل‌ها | **LOW** | FACT |
| `app/MUTATION-WHITELIST` | — | لیست سفید جهش | **HIGH** | FACT |
| `app/SafetyModel.md` | — | ۷ Guard + ۵ لایه | **LOW** | FACT |

### ۴.۲ شواهد کلیدی

**`_ops/opslib.py:280-301`** — Halt/freeze:
```python
def halted(...):
    if STOP_ARCHITECT.exists(): return "STOP(architect)"
    if STOP_METABOLIC.exists(): return "STOP-METABOLIC"
def freeze(reason):
    FREEZE_FLAG.write_text(f"{now_iso()} {reason}\n")
    alert([f"FREEZE: {reason}"])
```

**`_ops/opslib.py:359-372`** — Live gate (تاریخ + پرچم مالک):
```python
def live_gate_open(activation_flag):
    if _dt.date.today() < LIVE_GATE_DATE and not GO_LIVE_FLAG.exists():
        return False, "live locked until 2026-07-21"
    if not activation_flag.exists():
        return False, "activation flag missing"
```

**`_ops/approval_state_machine.py:150-178`** — گراف transition:
```python
_ALLOWED_TRANSITIONS = {
    ActionStatus.SUGGESTED: {
        ActionStatus.QUEUED: None,
        ActionStatus.REJECTED: Verdict.DENY,
        ...
    },
    ActionStatus.OWNER_APPROVED: {
        ActionStatus.EXECUTED: None,
        ActionStatus.DRY_RUN: None,
    },
    ActionStatus.EXECUTED: {},  # Terminal
}
```

**`_ops/capability_gate.py:14-104`** — AND ۳ عاملی:
```python
def is_open(action_id, amount_aud, channel):
    if not capability_ok(): return False, "no-capability"
    if not live_enabled(): return False, "LIVE_ENABLED off"
    if not appr.valid: return False, "no per-action approval"
    return True, "open"
```

**`_ops/human_append_guard.py:58-147`** — HMAC ضد جعل:
```python
class HumanAppendGuard:
    def mint(self, approval_id, event_type):
        sig = hmac.new(secret, msg, "sha256").hexdigest()
        return f"v1.{approval_id}.{exp}.{sig}"
    def authorize(self, event_type, is_human, token):
        if not self.enabled and self._strict:
            return False, "fail-closed-no-secret"
```

**`4d_system/brain/guardrails.py`** — TCB gate:
> hardcode فایل‌های محافظت‌شده (`run.py`, `guardrails.py`, `self_code.py`, `self_evolve.py`, `budget.py`, `daemon.py`, `events.py`, `router.py`, `settings.py`) و درخت‌های محافظت‌شده (`core/`, `tests/`, `config/`). fail-closed.

**`nervous-system/How-to-Safely-Use-Owner-Control.md`** — راهنمای مالک:
> «برچسب‌های Mode: READ-ONLY (صفر جهش) · SHADOW MODE (فقط مشورتی) · PROPOSE-ONLY (ثبت نیت، اجرا نمی‌کند) · OWNER VERDICT (نیازمند ✅/❌ صریح) · NOT YET WIRED (stub). توقف اضطراری: `_ops/STOP-TG-CENTER` یا `_ops/STOP-ORGANISM` = kill-supreme.»

### ۴.۳ ارزیابی

خود-حکمرانی **بسیار پیشرفته** است. چندین دروازه مستقل (date gate + owner flag + capability marker + per-action approval + money gate + organ gate + HMAC anti-forgery) به صورت defense-in-depth کار می‌کنند. **اما دو نقطه ضعف بحرانی یافت شد:**

1. **`human_append_guard` پیش‌فرض pass-through است** — `is_human` قابل spoofing است (از `AUDIT-MATRIX-self-improvement-2026-07-10.md`)
2. **`apply_merge` تعریف شده اما هیچ‌گاه فراخوانی نمی‌شود** — "merge-approved" فقط یک label است، نه application واقعی

---

## ۵. نقشه خودآگاهی / مدل خود (Self-Awareness / Self-Model Map)

### ۵.۱ فایل‌های کلیدی

| مسیر | خطوط | نقش در معماری | سطح ریسک | برچسب معرفتی |
|---|---|---|---|---|
| `_ops/cortex/self_model.py` | 125 | مدل خودِ AST: پوشش docstring، wire flags، imports | **LOW** | FACT |
| `_ops/cortex/self_audit.py` | 448 | ماتریس ممیزی ۳۵ پروب → maturity_pct | **LOW** | FACT |
| `_ops/cortex/ignition.py` | 238 | GWT رقابت + ignition + broadcast + reentry | **LOW** | FACT |
| `_ops/cortex/ignition_softwta.py` | 209 | Soft-WTA سایه (probabilistic winner-take-all) | **LOW** | FACT |
| `_ops/heart/shadow.py` | 130 | زنجیره سایه قلب + ۸ شرط production_wire_open | **LOW** | FACT |
| `_ops/cortex/stress.py` | 156 | استرس/ترس هومئوستاتیک per subsystem (آنالوگ کورتیزول) | **LOW** | FACT |
| `_ops/cortex/innervation.py` | 126 | نقش innervation: ستون فقرات→ارگان‌ها؛ تشخیص dead-spot | **LOW** | FACT |
| `_ops/cortex/synthesis.py` | 160 | ترکیب‌کننده فرا-شناختی (web + self-model + gaps + goals) | **LOW** | FACT |
| `_ops/neural/consolidation.py` | — | تثبیت حافظه | **LOW** | FACT |
| `_ops/neural/bcm.py` | — | فراموشی BCM | **LOW** | FACT |
| `_ops/neural/latent_space.py` | — | فضای پنهان R^32 | **LOW** | FACT |
| `_ops/unified_bus.py` | 149 | bus one-writer-two-views (ledger + chrono) | **LOW** | FACT |
| `4d_system/brain/self_model.py` | — | self-map ۳ لایه‌ای AST (Self-Map, Self-Description, Self-Critique) | **LOW** | FACT |
| `4d_system/brain/self_growth.py` | — | **انکار آگاهی پدیدارشناختی صریح:** «this is not consciousness» | **LOW** | FACT |
| `4d_system/brain/workspace.py` | — | متریک‌های GWT-style از event bus (ignition, broadcast_width, coherence) | **LOW** | FACT |
| `4d_system/brain/frontier.py` | — | بایگانی MAP-Elites quality-diversity. **۲۷ سلول کشف شده** | **LOW** | FACT |
| `4d_system/llm/shadow_analyze.py` | — | shadow-run analysis. **هرگز auto-switch نمی‌کند** | **LOW** | FACT |
| `nervous-system/extract_neural_data.py` | 257 | telemetry عصبی: mode_color، readiness، stress، protective | **LOW** | FACT |
| `nervous-system/extract_live_data.py` | 129 | state سیستم ۴ بعدی: sog identity + drift + healthy | **LOW** | FACT |
| `nervous-system/extract_audit_data.py` | 293 | داده‌های ممیزی + genome ledger | **LOW** | FACT |
| `OCTOPUS/ARCHITECTURE-BIBLE.md` | 463 | self-description جامع: Two trees (Boss + Leg)، authority levels، registry | **LOW** | FACT |
| `OCTOPUS/worlds/octo-data.js` | 522 | ستون فقرات داده مشترک برای همه جهان‌ها | **LOW** | FACT |
| `app/self_model.py` | — | هویت Ziman + gap_vector | **LOW** | FACT |
| `app/dual_brain.py` | — | Thinking+Comm برای Project-F | **LOW** | FACT |
| `app/pulse.py` | — | rhythm allostatic | **LOW** | FACT |
| `06 - Architecture Maps/HEART - Neuro Map & Direction.md` | — | نگاشت GNWT/PP/IIT به `_ops/` | **LOW** | FACT |

### ۵.۲ شواهد کلیدی

**`_ops/self_model.py:67-97`** — مدل خودِ AST:
```python
def build_model(root):
    for p in sorted(root.rglob("*.py")):
        info = _describe_module(p)
    return {
        "schema": "self-model.v1",
        "self_awareness_pct": round(100 * (len(modules) - len(undocumented)) / max(1, len(modules)), 1),
    }
```

**`_ops/self_audit.py:410-436`** — ۳۵ پروب:
```python
PROBES = [
    _probe_kill_switch, _probe_watchdog, _probe_heartbeat_pulse,
    _probe_human_append_enforced, _probe_owner_verdict_effect,
    _probe_observability_gate, _probe_refractory, ...
]
```

**`_ops/ignition.py:60-94`** — GWT ignition:
```python
def effective_salience(candidates, reentry_prior):
    base = max(0.0, min(1.0, float(c.get("salience", 0.0))))
    boost = min(REENTRY_CAP, max(0.0, float(rp.get(_key(c), 0.0))))
    e["effective"] = round(min(1.0, base + boost), 3)

def select_winner(candidates):
    top = ranked[0]
    ignited = top["effective"] >= thr
    coalition = [r for r in ranked if r["effective"] >= COALITION_FRAC * top["effective"]]
    return {"ignited": ignited, "winner": top, "broadcast_width": len(coalition)}
```

**`_ops/shadow.py:84-118`** — دروازه ۸ شرطی production:
```python
def production_wire_open():
    # 1) SIM_PASS
    # 2) equations-locked
    # 3) Gate-0: live authoritative producer
    # 4) hash-match
    # 5,6) OCTOPUS_WIRE_BIO and OCTOPUS_WIRE_PULSE
    # 7,8) ACTIVATION-PULSE.flag + date >= 2026-07-21
```

**`_ops/stress.py:102-119`** — استرس هومئوستاتیک:
```python
def assess():
    for sid, (name, fn) in _SUBSYSTEMS.items():
        s, detail = fn()
        subs[sid] = {"stress": round(s, 2), "fear": s >= FEAR_THRESHOLD}
    org = max((v["stress"] for v in subs.values()), default=0.0)
    return {"organism_stress": round(org, 2), "in_fear": in_fear}
```

**`4d_system/brain/self_growth.py`** — انکار صریح آگاهی پدیدارشناختی:
> «this is not consciousness.»

**`nervous-system/extract_neural_data.py`** — state عصبی فعلی:
> «mode_color: AMBER, readiness: 0.7, stress: 0.2, protective: false, advisory: 'احتیاط — استرس/نوآوری بالا؛ ضربانِ کهربایی', bar_color: #f59e0b. circadian: hour 23, phase active, best_platform reddit. consolidation: 768 cycles, insight 'آگاهیِ میانگین: 0.04'.»

### ۵.۳ ارزیابی

خودآگاهی **به طرز شگفت‌انگیزی پیشرفته** است. سیستم دارای:
- مدل خودِ AST با پوشش docstring
- ۳۵ پروب ممیزی مستقل
- جرقه GWT با reentry و coalition
- سایه قلب با ۸ شرط production
- هومئوستات استرس/ترس
- نقش innervation با تشخیص dead-spot
- فضای پنهان R^32
- بایگانی MAP-Elites با ۲۷ سلول

**مهم:** `4d_system/brain/self_growth.py` صراحتاً اعلام می‌کند «this is not consciousness» — این یک ایمنی معنایی است که نباید تغییر کند.

---

## ۶. نقشه خود-تکامل / خود-تغییر (Self-Modif./Self-Evolution Map)

### ۶.۱ فایل‌های کلیدی

| مسیر | خطوط | نقش در معماری | سطح ریسک | برچسب معرفتی |
|---|---|---|---|---|
| `_ops/cortex/code_autonomy.py` | 431 | P1: shadow-tester پچ‌ها؛ heart-gated؛ deny-list سخت | **HIGH** | FACT |
| `_ops/cortex/improve.py` | 409 | manager خودبهبودی: audit+RFC+idea → digest | **MEDIUM** | FACT |
| `_ops/cortex/auto_approve.py` | 230 | تصمیم خودکار ریسک-درجه‌بندی‌شده (classify→goal→self_test→decide) | **HIGH** | FACT |
| `_ops/doctor/doctor.py` | 548+ | دکتر تکاملی: mine→RFC→sandbox→Critic→submit | **MEDIUM** | FACT |
| `_ops/doctor/evolution.py` | 207 | MAP-Elites + measured_lift + tournament_rank | **LOW** | FACT |
| `_ops/doctor/calibration.py` | 126 | feedback loop + attention-budget (ضد agreement-spiral) | **LOW** | FACT |
| `_ops/doctor/chamber.py` | 198 | ۴ صدای مخالف، ≤۳ round، λ_persist negative | **LOW** | FACT |
| `_ops/doctor/box/*.py` | ۱۰ فایل | هسته عددی (agent_state, dynamics, warden, topology, archivist, primitive, sensors, null_dreamer, box) | **MEDIUM** | FACT |
| `_ops/vault_updater.py` | — | updater vault | **MEDIUM** | FACT |
| `_ops/vault_updater_apply.py` | — | apply updater vault | **HIGH** | FACT |
| `_ops/held_out_evaluator.py` | — | ۵ canary | **MEDIUM** | FACT |
| `_ops/baseline.py` | — | snapshot پایه | **LOW** | FACT |
| `4d_system/brain/self_evolve.py` | — | تکامل strategy JSON-only (نسل **۹**). محافظت‌شده توسط anchor test + fitness gate + rollback | **MEDIUM** | FACT |
| `4d_system/brain/self_code.py` | — | pipeline ۳ مرحله‌ای: PROPOSE (scan static/AST) → owner APPROVE → throwaway test → textual apply. TCB check + delta danger analysis. **سندباکس proposal خالی** — pipeline تولیدی تست نشده | **HIGH** | FACT |
| `04 - Architect System/learning-engine/app/doctor_lite.py` | 343 | دکتر تکاملی (loop دو-مغزی) | **MEDIUM** | FACT |
| `04 - Architect System/learning-engine/app/bridge_to_ledger.py` | 152 | bridge proposal→ledger. quarantine gate. | **MEDIUM** | FACT |
| `04 - Architect System/scripts/genome_guard.py` | 64 | گارد جهش ژنوم | **HIGH** | FACT |
| `app/self_improver.py` | — | پیگیری نتیجه ۳۰ روزه | **MEDIUM** | FACT |
| `app/genome_change_protocol.md` | — | ۷۲h cooling + two-key | **MEDIUM** | FACT |
| `app/evolutionary-doctor.md` | — | spec دکتر تکاملی | **LOW** | FACT |
| `app/creativity-blackbox.md` | — | blackbox خلاقیت | **LOW** | FACT |
| `app/research_loop.py` | — | loop پژوهش | **LOW** | FACT |

### ۶.۲ شواهد کلیدی

**`_ops/code_autonomy.py:46-90`** — mood قلب + deny-list:
```python
def heart_mood():
    if in_fear or arousal >= FEAR: mood = "collapse"
    elif arousal > STRESS_FLOW_HI: mood = "tension"
    elif arousal < STRESS_STAGNANT: mood = "stagnation"
    else: mood = "flow"

_DENY = (".git", "genome", "ledger", ".env", "secret", "budget/", "money",
         "schema", "kill", "human_append_guard", "capability_gate", "auto_approve",
         "goal_directed", "self_audit", "sigma", "vault_updater", "settings.json",
         "registry_scan", "organism", "germline")
```

**`_ops/code_autonomy.py:238-273`** — actuator سطح A (۷ دروازه):
```python
def apply_approved(patch, approval_id):
    # 1 activation (ACTIVATION + not KILL)
    # 2 heart != freeze
    # 3 owner approval
    # 4 deny-list
    # 5 shadow green
    # 6 refractory
    # 7 valid content
    if not active(): return {"ok": False, "reason": "not-activated"}
    if m["verdict"] == "freeze": return {"ok": False, "reason": "heart-freeze"}
    if not _owner_approved(approval_id): return {"ok": False, "reason": "no-owner-approval"}
    ...
    if res.get("applied") and res.get("green") is False:
        freeze_autonomy(f"canary-red on {tgt}")
```

**`_ops/improve.py:48-54`** — whitelist auto-knob:
```python
AUTO_KNOBS = {
    "CORTEX_THINK_EVERY_N": (2, 20),
    "CHRONO_NUDGE_EVERY_N_BEATS": (120, 1440),
    "HEART_SAMPLE_INTERVAL_S": (1800, 7200),
}
```

**`_ops/improve.py:261-289`** — GAAT + refractory:
```python
def observability_ok():
    # GAAT: "observability died = self-modification stops"
    age_min = (datetime.now().timestamp() - p.stat().st_mtime) / 60.0
    if age_min > OBS_MAX_AGE_MIN: return False, f"stale ({age_min:.0f}min)"

def refractory_open():
    # SPEC §14: حداقل ۲۴h بین تغییرات خودکار
    hours = (datetime.now().timestamp() - last) / 3600.0
    if hours < REFRACTORY_H: return False, f"refractory: {hours:.1f}h < {REFRACTORY_H:.0f}h"
```

**`_ops/auto_approve.py:42-45`** — regex high-risk:
```python
_HIGH_RISK = re.compile(
    r"(code|money|spawn|replicat|secret|token|schema|genome|ledger|"
    r"human.?append|kill|halt|sigma|merge|apply_merge|budget|wallet|"
    r"pem|L4|L5|pay|api.?key)", re.I)
```

**`_ops/auto_approve.py:82-106`** — دروازه self-test:
```python
def self_test():
    feared, why = stress.organism_in_fear()
    if feared: return False, f"fear: {why}"
    if not capability_gate.capability_ok(): return False, "CAPABILITY-OK missing"
    if not improve.observability_ok()[0]: return False, "observability dead"
    if not improve.refractory_open()[0]: return False, "refractory"
    return True, "green"
```

**`_ops/doctor.py:1-28`** — قرارداد دکتر:
> «Phase 2: Evolutionary Doctor (parasite on top of organism). reward-integrity: λ_persist negative. Doctor هرگز 'زنده ماندن/بردن' را بهینه نمی‌کند.»

**`_ops/evolution.py:118-153`** — MAP-Elites + measured_lift:
```python
class RFCArchive:
    def insert(self, bottleneck_key, organ, rfc_id, score):
        if existing is None or score > existing.score:
            self.cells[key] = ArchiveCell(...)

def measured_lift(rfc, eval_fn=None):
    if eval_fn is None: eval_fn = _default_eval
    lift = float(result.get("lift", 0.0))
    passed = lift >= LIFT_DROP_THRESHOLD  # 0.05
    return {"lift": lift, "passed": passed, "dropped": not passed}
```

**`_ops/chamber.py:22-37`** — ۶ بند ایمنی:
> «۱. bounded (حداکثر N round)؛ ۲. adversarial (Skeptic=falsifier)؛ ۳. propose-only؛ ۴. λ_persist negative؛ ۵. append-only + auditable؛ ۶. sandbox/stub (بدون LLM)»

**`4d_system/brain/self_code.py`** — pipeline ۳ مرحله‌ای:
> PROPOSE (scan static/AST danger) → owner APPROVE → throwaway test → textual apply. TCB check + delta danger analysis. **سندباکس proposal خالی** — pipeline تولیدی تست نشده.

**`4d_system/brain/self_evolve.py`** — تکامل strategy:
> JSON-only strategy evolution (نسل **۹**). Protected by anchor test + fitness gate + rollback. clamp to SAFE_PARAM_RANGES, MAX_STEP.

### ۶.۳ ارزیابی

خود-تکامل **خوش‌ساختار اما ناحیه‌های تست‌نشده دارد**:
- دکتر تکاملی با ۶ بند ایمنی و λ_persist negative طراحی شده
- MAP-Elites با measured_lift و tournament ranking
- code_autonomy با deny-list سخت و ۷ دروازه actuator
- auto_approve با regex high-risk و self-test gate
- **اما:** سندباکس self-code خالی است. مسیر approve→apply end-to-end تست نشده.

---

## ۷. وابستگی‌های متقاطع (Cross-Cutting Dependencies)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          organism.py (تیک مرکزی)                          │
│         ┌─────────────┬─────────────┬─────────────┬─────────────┐          │
│         ▼             ▼             ▼             ▼             ▼          │
│    ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   │
│    │  heart  │   │ cortex  │   │ budget  │   │ neural  │   │ doctor  │   │
│    │  pulse  │   │  GWT    │   │  gate   │   │consolid.│   │evolution│   │
│    └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘   │
│         │             │             │             │             │          │
│         └─────────────┴──────┬──────┴─────────────┴─────────────┘          │
│                              ▼                                            │
│                      ┌───────────────┐                                    │
│                      │  unified_bus  │  (ledger + chrono)                   │
│                      └───────┬───────┘                                    │
│                              ▼                                            │
│    ┌─────────────────────────────────────────────────────────────┐        │
│    │              nervous-system extractors (۱۸ عدد)               │        │
│    │   ← همه read-only، همه fail-soft، همه stdlib-only             │        │
│    └─────────────────────────────────────────────────────────────┘        │
│                              ▼                                            │
│    ┌─────────────────────────────────────────────────────────────┐        │
│    │              OCTOPUS cockpit worlds + admin-telegram           │        │
│    │   ← ۱۰ جهان + داشبورد ۱۳ پنل + ۱۶ کانال                     │        │
│    └─────────────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────────┘
```

### ۷.۱ نقاط اتصال بحرانی

| منبع | مصرف‌کننده | نوع وابستگی | ریسک |
|---|---|---|---|
| `_ops/budget/opslib.py` | همه اجزا | مسیرها، پرچم‌ها، ledger | **CRITICAL** — تک نقطه شکست |
| `_ops/capability_gate.py` | code_autonomy, auto_approve, improve | fingerprint hash, capability marker | **HIGH** |
| `_ops/heart/shadow.py` | code_autonomy, production paths | ۸ شرط production_wire_open | **HIGH** |
| `_ops/organism.py` | همه subsystems | تیک ۵ دقیقه‌ای | **HIGH** — اگر بمیرد، همه می‌میرند |
| `4d_system/brain/guardrails.py` | self_code.py, self_evolve.py | TCB gate | **HIGH** — self-guard بدون validator خارجی |
| `_ops/state/ORGANISM-STATE.json` | ۶+ extractor | state مرکزی | **MEDIUM** |
| `_ops/budget/budget-state.json` | organ_gate, governor | بودجه | **MEDIUM** |

---

## ۸. نقاط جهش خطرناک (Dangerous Mutation Points)

| نقطه جهش | مسیر(ها) | چرا خطرناک | شدت | پیشنهاد |
|---|---|---|---|---|
| **opslib.py** | `_ops/budget/opslib.py` | STOP/FREEZE/ledger/live_gate همه اینجا هستند. اگر خراب شود، کل ایمنی از بین می‌رود. | **بحرانی** | فقط توسط human-gated patch. هیچ auto-apply.
|
| **capability_gate.py** | `_ops/budget/capability_gate.py` | fingerprint hash را تأیید می‌کند. spoof = اثرگذارهای زنده فعال می‌شوند. | **بحرانی** | فقط توسط human-gated patch.
|
| **organ_gate.py** | `_ops/budget/organ_gate.py` | spend enforcement per-organ. bug = overspend یا halt ناخواسته. | **بحرانی** | فقط توسط human-gated patch.
|
| **human_append_guard.py** | `_ops/budget/human_append_guard.py` | **اکنون: پیش‌فرض pass-through (مُرده)**. `is_human` spoofable است. | **بحرانی** | تعمیر فوری: fail-closed بدون secret.
|
| **code_autonomy.py** | `_ops/cortex/code_autonomy.py` | actuator سطح A با ۷ دروازه. deny-list محافظت می‌کند اما اگر bypass شود... | **بالا** | تست end-to-end قبل از فعال‌سازی.
|
| **self_code.py** | `4d_system/brain/self_code.py` | **سندباکس خالی**. pipeline approve→apply تست نشده. | **بالا** | پر کردن سندباکس با proposal‌های test-only.
|
| **guardrails.py** | `4d_system/brain/guardrails.py` | TCB self-guard بدون validator خارجی. single point of failure. | **بالا** | اضافه کردن validator خارجی (مثلاً از `_ops/cortex/self_audit.py`).
|
| **auto_approve.py** | `_ops/cortex/auto_approve.py` | regex high-risk ممکن است false negative داشته باشد. self-test gate ممکن است bypass شود. | **بالا** | تست با payload‌های مخرب مصنوعی.
|
| **vault_updater_apply.py** | `_ops/vault_updater_apply.py` | apply تغییرات vault. اگر خودکار شود، ممکن است notes را خراب کند. | **بالا** | همیشه human-gated.
|
| **apply_merge** | `_ops/budget/approval_state_machine.py` | **تعریف شده اما هرگز فراخوانی نمی‌شود**. "merge-approved" فقط label است. | **متوسط** | یا حذف یا پیاده‌سازی واقعی.
|
| **kill-switch** | `4d_system/control_plane/policy.py` | «v1: always False remains» — kill-switch پیاده‌سازی نشده. | **متوسط** | پیاده‌سازی فوری.

---

## ۹. جعبه‌های سیاه و ناشناخته‌ها (Black Boxes and UNKNOWNs)

| موضوع | وضعیت | دلیل ناشناخته بودن |
|---|---|---|
| `_ops/chrono.py` | **UNKNOWN** (بزرگ، ~۳۹KB) | pacemaker core — فقط از references خوانده شده، نه به‌صورت کامل |
| `_ops/cardiac.py` | **UNKNOWN** | cardiac allometry — اسکن نشد |
| `_ops/live_loop.py` | **UNKNOWN** | live loop server — اسکن نشد |
| `_ops/brain/cockpit.py` | **UNKNOWN** | dashboard — اسکن نشد |
| `_ops/legs/*.py` | **UNKNOWN** | worker legs — مسیرها یافت شدند اما خوانده نشدند |
| `_ops/debate/*.py` | **UNKNOWN** | Muse × architect — مسیرها یافت شدند اما خوانده نشدند |
| `_ops/afferent/*.py` | **UNKNOWN** | sensory bus, school bridge — اسکن نشد |
| `_ops/maintenance/*.ps1` | **UNKNOWN** | maintenance scripts — اسکن نشد |
| `_ops/tests/` (۸۷+ فایل) | **PARTIAL** | ساختار یافت شد اما individual tests خوانده نشدند |
| `4d_system/` deeper files | **PARTIAL** | ۳,۳۵۵ فایل — ۴۴ تا خوانده شد |
| `CHRONOS-FABLE-OS/` | **PARTIAL** | اسکن سطحی |
| `07 - Knowledge/cellular-systems/` | **UNKNOWN** | اسکن نشد |
| `07 - Knowledge/genome-system/` | **UNKNOWN** | اسکن نشد |
| **Fitness self-reported** | **DERIVED/ASSUMPTION** | `self_evolve.py` fitness توسط autoloop engine محاسبه می‌شود (همان سیستم). اندازه‌گیری دایره‌ای. |

---

## ۱۰. ماتریس ایمنی تغییر (Change-Safety Matrix)

| فایل/ماژول | ایمن برای inspect | ایمن برای refactor بعداً | خطرناک، human-gated | لمس نکنید هنوز |
|---|---|---|---|---|
| `_ops/budget/opslib.py` | ✅ | ❌ | **✅** | — |
| `_ops/budget/capability_gate.py` | ✅ | ❌ | **✅** | — |
| `_ops/budget/organ_gate.py` | ✅ | ❌ | **✅** | — |
| `_ops/budget/money_gate.py` | ✅ | ❌ | **✅** | — |
| `_ops/budget/human_append_guard.py` | ✅ | ❌ | **✅** | — |
| `_ops/budget/approval_state_machine.py` | ✅ | ⚠️ با caution | — | — |
| `_ops/cortex/code_autonomy.py` | ✅ | ⚠️ با caution | **✅** | — |
| `_ops/cortex/auto_approve.py` | ✅ | ⚠️ با caution | **✅** | — |
| `_ops/cortex/improve.py` | ✅ | ✅ | — | — |
| `_ops/cortex/self_audit.py` | ✅ | ✅ | — | — |
| `_ops/cortex/self_model.py` | ✅ | ✅ | — | — |
| `_ops/cortex/ignition.py` | ✅ | ✅ | — | — |
| `_ops/cortex/stress.py` | ✅ | ✅ | — | — |
| `_ops/cortex/innervation.py` | ✅ | ✅ | — | — |
| `_ops/cortex/synthesis.py` | ✅ | ✅ | — | — |
| `_ops/heart/*.py` | ✅ | ⚠️ با caution | — | — |
| `_ops/doctor/doctor.py` | ✅ | ✅ | — | — |
| `_ops/doctor/evolution.py` | ✅ | ✅ | — | — |
| `_ops/doctor/chamber.py` | ✅ | ✅ | — | — |
| `_ops/organism.py` | ✅ | ❌ | **✅** | — |
| `_ops/watchdog.py` | ✅ | ⚠️ با caution | — | — |
| `_ops/checkpoint.py` | ✅ | ✅ | — | — |
| `_ops/durable_journal.py` | ✅ | ✅ | — | — |
| `4d_system/brain/guardrails.py` | ✅ | ❌ | **✅** | — |
| `4d_system/brain/self_code.py` | ✅ | ⚠️ با caution | — | **✅** (تست نشده) |
| `4d_system/brain/self_evolve.py` | ✅ | ⚠️ با caution | — | — |
| `4d_system/brain/self_model.py` | ✅ | ✅ | — | — |
| `4d_system/brain/self_growth.py` | ✅ | ✅ | — | — |
| `4d_system/brain/workspace.py` | ✅ | ✅ | — | — |
| `4d_system/brain/frontier.py` | ✅ | ✅ | — | — |
| `4d_system/brain/daemon.py` | ✅ | ⚠️ با caution | — | — |
| `4d_system/control_plane/policy.py` | ✅ | ⚠️ با caution | — | — |
| `4d_system/control_plane/flags.py` | ✅ | ✅ | — | — |
| `nervous-system/extract_*.py` | ✅ | ✅ | — | — |
| `OCTOPUS/worlds/*.js` | ✅ | ✅ | — | — |
| `OCTOPUS/ARCHITECTURE-BIBLE.md` | ✅ | ✅ | — | — |
| `04 - Architect System/scripts/budget_gate.py` | ✅ | ❌ | **✅** | — |
| `04 - Architect System/scripts/genome_guard.py` | ✅ | ❌ | **✅** | — |
| `04 - Architect System/learning-engine/app/doctor_lite.py` | ✅ | ✅ | — | — |
| `04 - Architect System/learning-engine/app/bridge_to_ledger.py` | ✅ | ✅ | — | — |
| `app/gates.py` | ✅ | ❌ | **✅** | — |
| `app/governance.py` | ✅ | ⚠️ با caution | — | — |
| `app/self_model.py` | ✅ | ✅ | — | — |
| `app/quarantine.py` | ✅ | ✅ | — | — |

---

## ۱۱. توصیه‌های معماری برای کنترل و تکامل (Architecture Control Recommendations)

### R1 — تعمیر فوری human_append_guard
**اولویت:** بحرانی  
**مسئله:** `human_append_guard` پیش‌فرض pass-through است. `is_human` spoofable است.  
**عمل:** تغییر به حالت fail-closed بدون secret. اگر secret موجود نیست، `authorize()` باید `False` برگرداند، نه `True`.

### R2 — پر کردن سندباکس self-code با proposal‌های test-only
**اولویت:** بالا  
**مسئله:** `4d_system/brain/self_code.py` pipeline تولیدی تست نشده.  
**عمل:** تولید ۳-۵ proposal test-only (تغییرات بی‌خطر مثل rename variable یا add comment) و اجرای end-to-end pipeline.

### R3 — اضافه کردن validator خارجی برای TCB
**اولویت:** بالا  
**مسئله:** `guardrails.py` خودش را محافظت می‌کند بدون validator خارجی.  
**عمل:** استفاده از `_ops/cortex/self_audit.py` به عنوان validator مستقل برای بررسی integrity `guardrails.py`.

### R4 — پیاده‌سازی kill-switch واقعی
**اولویت:** متوسط  
**مسئله:** kill-switch «v1: always False remains».  
**عمل:** پیاده‌سازی یک kill-switch که واقعاً فرآیند را می‌کشد (نه فقط log می‌نویسد).

### R5 — تعیین تکلیف apply_merge
**اولویت:** متوسط  
**مسئله:** `apply_merge` تعریف شده اما هرگز فراخوانی نمی‌شود.  
**عمل:** یا پیاده‌سازی واقعی (با human-gated) یا حذف explicit برای جلوگیری از confusion.

### R6 — تست auto_approve با payload‌های مخرب مصنوعی
**اولویت:** بالا  
**مسئله:** regex high-risk ممکن است false negative داشته باشد.  
**عمل:** ایجاد یک test suite با payload‌های مخرب مصنوعی (mock) برای بررسی coverage regex.

### R7 — مستندسازی وابستگی‌های organism.py
**اولویت:** متوسط  
**مسئله:** `organism.py` تک نقطه شکست است.  
**عمل:** مستندسازی explicit تمام وابستگی‌ها + plan برای redundancy (watchdog secondary).

### R8 — بررسی اندازه‌گیری دایره‌ای fitness
**اولویت:** پایین  
**مسئله:** `self_evolve.py` fitness توسط autoloop engine (همان سیستم) محاسبه می‌شود.  
**عمل:** اضافه کردن held-out evaluator خارجی برای تأیید fitness.

---

## ۱۲. سوالات باز برای مالک (Open Questions for Owner)

1. **human_append_guard:** آیا secret هر بوت واقعاً تولید می‌شود؟ اگر نه، این یک آسیب‌پذیری بحرانی است.

2. **kill-switch:** آیا kill-switch باید فرآیند را بکشد (SIGTERM) یا فقط تیک را متوقف کند؟

3. **apply_merge:** آیا «merge-approved» باید واقعاً apply شود یا فقط یک label باقی بماند؟

4. **self-code sandbox:** آیا مالک می‌خواهد اولین proposal test-only را تأیید کند تا pipeline end-to-end تست شود؟

5. **fitness measurement:** آیا یک evaluator خارجی برای تأیید fitness وجود دارد یا فقط self-reported است؟

6. **4d_system ↔ _ops wiring:** آیا wiring بین Leg و Boss (OCTOPUS_WIRE_*) باید در Wave 7 فعال شود یا هنوز shadow بماند؟

7. **secrets strategy:** آیا TELEGRAM_BOT_TOKEN و TELEGRAM_OWNER_CHAT_ID در `.env` موجود هستند؟ اگر نه، مسیر Telegram control همچنان stub(no-creds) خواهد ماند.

8. **owner activation flags:** کدامیک از ۱۰ پرچم ACTIVATION-* توسط مالک فعال شده‌اند؟ آیا GO-LIVE بعد از ۲۰۲۶-۰۷-۲۱ فعال خواهد شد؟

---

## پیوست: خلاصه آماری برچسب‌های معرفتی

| برچسب | تعداد | معنی |
|---|---|---|
| **FACT** | ۱۲۰+ | مستقیماً از source code مشاهده شده |
| **DERIVED** | ۳۵ | از FACTها استنتاج منطقی |
| **ASSUMPTION** | ۱۲ | استنتاج معقول، تأیید نشده |
| **UNKNOWN** | ۱۳ | یافت شده اما خوانده نشده یا تأیید نشده |

---

*این گزارش فقط-خواندنی است. هیچ فایل پروژه‌ای تغییر نکرده است.*
