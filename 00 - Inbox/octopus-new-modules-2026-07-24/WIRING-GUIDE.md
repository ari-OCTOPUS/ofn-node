---
type: runbook
status: draft
# status پیشین: proposed — propose-only — اجرا فقط دستِ مالک، در worktree، پس از ری‌استارت
created: 2026-07-24
updated: 2026-07-29
tags: [octopus, wiring]
owner: ari
# scope: "نصبِ ۳ ماژولِ نو + وصلِ seamهای موجود — همه در worktree، هیچ ویرایشِ زندهٔ سندباکسی"
# honesty: "[FACT] از رجیستری/کد دیدم · [verify@wire] امضای دقیقِ تابع را با git show تأیید کن"
---

# 🔌 راهنمای وایرینگ — ۳ ماژولِ نو + seamهای موجود

> **این سند دستورالعمل است، نه اجرا.** من (از سندباکس) درختِ زنده را ویرایش نکردم و هیچ فلگی نزدم.
> هر گامِ زیر را **تو در worktree روی ویندوز** انجام می‌دهی، طبق پروتکلِ ایمنِ بخشِ D.

## چه چیزی تحویل گرفتی

| فایل | مقصدِ پیشنهادی | نقش | تست |
|---|---|---|---|
| `rules_store.py` | `_ops/doctor/rules_store.py` | انبارِ قوانینِ رفتاریِ ماندگار (G1/P3) | ✅ ۱۱/۱۱ |
| `approval_fatigue.py` | `_ops/budget/approval_fatigue.py` | تشخیصِ خستگیِ تأییدکننده (امنیت) | ✅ ۱۰/۱۰ |
| `output_guard.py` | `_ops/output_guard.py` | گاردِ خروجیِ غیراجرایی (ضدِ فرار) | ✅ ۱۴/۱۴ |

هر سه **stdlib خالص، inert تا import، بدونِ side-effect**. تا وقتی هیچ فایلِ زنده‌ای import‌شان نکند، **صفر اثر** روی ارگانیسم دارند (همان الگوی `mission_contract.py` و `chord/`).

> ⚠️ **چرا فقط ۳ تا و نه بیشتر؟** نردبانِ ریسک و route-mapper و PEP و capability و circuit-breaker و DIGEST و human-guard **از قبل در `chord/` و `budget/` هستند** (repair_policy.assess، capability_gate.py، circuit_breaker.py، human_append_guard.py، needs_digest.py). ساختنِ دوبارهٔ آن‌ها = نقضِ Freeze + split-brain. این ۳ تنها موارد واقعاً غایب‌اند.

---

## Part A — نصبِ فایل‌ها (بی‌ریسک، additive)

```powershell
# در worktree ایزوله (نه درختِ زنده تا وقتی تست نگرفتی)
copy rules_store.py       "F:\backup\_ops\doctor\rules_store.py"
copy approval_fatigue.py  "F:\backup\_ops\budget\approval_fatigue.py"
copy output_guard.py      "F:\backup\_ops\output_guard.py"

# راستی‌آزمایی درجا (روی ویندوزِ 3.13 تو هم سبز است)
cd F:\backup\_ops
python doctor\rules_store.py        # → rules_store smoke ok
python budget\approval_fatigue.py   # → approval_fatigue smoke ok
python output_guard.py              # → output_guard smoke ok
```

چون فایل‌های **جدید** با Write فوری و سالم sync می‌شوند (طبقِ vault-quirks)، این گام حتی از سندباکس هم امن بود؛ ولی چون درختِ زنده روی `event-bridge-aligned` است، بهتر است در worktree بماند تا با بقیه یک‌جا merge شود.

---

## Part B — وصلِ نازکِ ۳ ماژولِ نو (هرکدام پشتِ یک فلگِ خاموش)

هر وصل، یک تماسِ کوچک در فایلِ موجود است — **پشتِ فلگِ خاموش، flag-off = رفتارِ قبلی**. امضاهای دقیقِ توابعِ میزبان `[verify@wire]`اند؛ الگو را می‌دهم، تو با `git show` لنگر را قطعی کن.

### B1) rules_store → حلقهٔ دکتر (فلگ `OCTOPUS_WIRE_RULES`)
- **کجا:** همان‌جا که `doctor.advance_rfcs()` یک RFC را `owner-accepted` می‌کند.
- **چه:** بعد از accept → `rules_store.add_rule(Rule(error_class=…, never_again=…, check=…, source_trace=trace_id, added_by="owner"))`.
- **و:** هرجا یک failure ثبت می‌شود → `rules_store.record_occurrence(error_class, trace_id)` (سنجهٔ `rule_recurrence`).
- **نمایش:** `rules_store.metrics()` را به صفحهٔ ⑤/صفحهٔ یادگیریِ تلگرام بده.

```python
import os
if os.environ.get("OCTOPUS_WIRE_RULES") == "1":
    from doctor import rules_store            # [verify@wire] مسیرِ import پکیج
    rules_store.add_rule(rules_store.Rule(
        error_class=rfc.error_class, never_again=rfc.lesson,
        check=rfc.check_hint, source_trace=rfc.trace_id, added_by="owner"))
```

### B2) approval_fatigue → مسیرِ approval (فلگ `OCTOPUS_WIRE_FATIGUE`)
- **کجا:** درست قبل از نمایشِ کارتِ تأیید در `budget/approval_channel.py` یا `approval_state_machine.py` `[verify@wire]`.
- **چه:** `d = approval_fatigue.assess_request(now, recent_events_for_source, risk)`.
  - `d.decision == CUTOFF` → کارت را نشان نده؛ درخواست‌های غیرread-onlyِ این منبع را تعلیق کن؛ به تو یک هشدارِ **واحد** بده (نه اسپم).
  - `THROTTLE/COOLDOWN` → صف کن، پینگ نده، `retry_after_seconds` را رعایت کن.
- `recent_events` را از همان صف/state موجودِ approval بساز (لیستی از `ApprovalEvent(ts, risk, verdict_ts)`).

```python
if os.environ.get("OCTOPUS_WIRE_FATIGUE") == "1":
    from budget import approval_fatigue as af  # [verify@wire]
    d = af.assess_request(time.time(), recent, risk)
    if d.decision == af.CUTOFF:
        return _suspend_source(source_id, reason=d.reasons)   # fail-closed
```

### B3) output_guard → نویسندهٔ artifact (فلگ `OCTOPUS_WIRE_OUTPUT_GUARD`)
- **کجا:** هر نقطه‌ای که ایجنت/`code_autonomy` می‌خواهد یک artifact/patch **بنویسد** `[verify@wire]`.
- **چه:** `v = output_guard.check_output(target_path, content)`؛ اگر `not v.allowed` → ننویس، به مالک ارجاع بده، در ledger ثبت کن.

```python
if os.environ.get("OCTOPUS_WIRE_OUTPUT_GUARD") == "1":
    from output_guard import check_output       # [verify@wire] _ops روی sys.path
    v = check_output(target_path, content)
    if not v.allowed:
        raise PermissionError(f"output_guard blocked: {v.reasons}")  # هرگز اجرایی به host
```

---

## Part C — seamهای موجود (کد هست؛ فقط فلگ + ری‌استارت) `[FACT از رجیستری]`

این‌ها را نمی‌سازیم — از قبل ساخته و تست‌شده‌اند؛ فقط در worktree روشن + ری‌استارت، **به‌ترتیب**:

| گام | کار | فلگ/اقدام | ریسک |
|---|---|---|---|
| P1a | `mission_runner`→bus (🧪 واقعی) | `set OCTOPUS_WIRE_MISSION_RUNNER=1` | پایین |
| P1b | MERGE `code_autonomy` پشتِ mission (یک صف) | پچِ رشته‌ای (الگوی D) `[verify@wire]` | متوسط |
| P1c | CHORD در حالتِ shadow | `set OCTOPUS_WIRE_CHORD_SHADOW=1` | پایین |
| P3a | `doctor.advance_rfcs()`→tick | `set OCTOPUS_WIRE_DOCTOR_ADVANCE=1` | متوسط |
| P3d | observability→governor epoch + صفحهٔ ① | (GLM-C) `[verify@wire]` | پایین |
| SEC | سخت‌سازیِ HTTP | `set OCTOPUS_HTTP_AUTH=1` | پایین |
| SEC★ | **ARM R5 context_fence** (ضدِ prompt-injection) | تصمیمِ فعال‌سازیِ تو | — |
| P5 | یکسان‌سازیِ approval + `content_sha256` (GLM-D) | فلگِ apply | متوسط |

> **پول/`LIVE-ENABLED` = P7 — اصلاً در این بسته نیست.** دست‌نخورده می‌ماند.

---

## Part D — پروتکلِ ویرایشِ ایمن (از vault-sandbox-quirks)

برای هر گامی که **فایلِ موجود** را عوض می‌کند (P1b و هر وصلِ Part B):

1. **ارگانیسم را خاموش کن** (`/panic` یا بستنِ ترمینال)؛ فریزِ `state/pulse/*` را تأیید کن.
2. فقط در **worktreeِ ایزوله**: `git worktree add ../oct-wire <branch>`.
3. ویرایشِ فایلِ موجود = **پچِ رشته‌ایِ درجا** (نه Edit-toolِ رنگی)، با گاردِ سه‌گانه:
   ```python
   s = open(p, encoding="utf-8").read()
   assert s.count(OLD) == 1, "anchor not unique"      # لنگرِ یکتا
   s2 = s.replace(OLD, NEW)
   compile(s2, p, "exec")                              # سینتکس سالم
   open(p, "w", encoding="utf-8").write(s2)
   ```
4. git از سندباکس timeout/lock می‌دهد → مسیرِ `add`→`write-tree`→`commit-tree`→`update-ref`؛ قفلِ `*.lock` که unlink نمی‌شود → `mv` نه `rm`.
5. **ری‌استارت** (تنها راهِ زنده‌شدنِ سیم‌کشی). فلگ‌ها را همان‌جا `set` کن.

---

## Part E — چک‌لیستِ راستی‌آزمایی بعد از هر وصل

- [ ] `python <module>.py` سبز (هر سه).
- [ ] `python -c "import ast; ast.parse(open(F).read())"` روی فایلِ ویرایش‌شده.
- [ ] `git show HEAD:<path>` = همان چیزی که انتظار داری (نه truncate).
- [ ] flag-off → رفتارِ دقیقاً قبلی (رگرسیونِ صفر).
- [ ] `run_all` (۲۰۳ تست) کفِ رگرسیون سبز.
- [ ] `rules_store.verify_chain()` و `chord` ledger سالم.
- [ ] هیچ فایلِ اجرایی/config در خروجیِ ایجنت (تستِ `output_guard` روی نمونه‌های واقعی).

---

## کارت‌های تصمیمِ تو (owner-gated)
1. ترتیبِ arming: **R5 اول**؟ بعد HTTP_AUTH؟ بعد فلگ‌های P1→P3؟
2. deploy `master f9a8d48` (checkout + restart) تا `advance_rfcs`/`verify_scope`/event_bridge زنده شوند.
3. کلیدِ LLM (`DEEPSEEK`/GLM، owner-only) برای مغزِ heart/governor.
4. تأیید: این ۳ ماژول در worktree merge شوند و بقیه فقط فلگ بخورند (نه ساختِ ماژولِ جدید).

*هیچ کدِ زنده‌ای در ساختِ این بسته تغییر نکرد. امضاهای `[verify@wire]` را قبل از هر وصل با `git show` قطعی کن.*
