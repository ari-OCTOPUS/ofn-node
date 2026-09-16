---
type: proposal
status: draft
# priority: P0
created: 2026-07-09
updated: 2026-07-29
created_by: agent
# domain: architect / _ops
tags: [proposal, gap-report, E16, integrity, restore, human-append]
sources:
  - "[[06 - Architecture Maps/MASTER-ARCHITECTURE-2026-07-09]]"
  - "[[_ops/ORGANISM-SPEC]]"
  - "[[01 - Dashboard/HANDOFF]]"
---

# PROPOSAL — بازیابیِ هستهٔ بریده + سیم‌کشیِ گاردِ human-append (E16)

> همه propose-only. تصمیم/اجرا با آری (D-01). چیزی روی money/live-gate/genome/charter دست نخورده.

## TL;DR
اجرای META-PROMPT (Base-Map v0→v1 + رفرشِ MASTER-ARCHITECTURE) دو چیز داد: (۱) **یک P0ِ integrity کشف شد** — ۷ فایلِ هستهٔ `_ops/` در working-tree **بریده‌اند** ولی نسخهٔ سالمشان در git HEAD امن است؛ (۲) **رفعِ E16** به‌صورتِ کدِ واقعیِ تست‌شده ساخته شد (`human_append_guard.py`، ۱۰/۱۰ سبز). فوری‌ترین کارِ پیش از live-gate (۲۰۲۶-۰۷-۲۱، ~۱۲ روز): بازیابیِ هسته + review سیم‌کشیِ گارد.

---

## §A — P0: هستهٔ بریدهٔ `_ops/` (integrity)

**یافته `[FACT]`:** این ۷ فایل در working-tree خوانده‌شده بریده‌اند و در پایتون compile نمی‌شوند؛ نسخهٔ commit‌شدهٔ HEAD سالم است (`git show HEAD:<file>` → parse OK):

| فایل | worktree (خط) | git HEAD (خط) | worktree بایت | git blob بایت |
|---|---|---|---|---|
| `_ops/wiring.py` | 127 | 488 | 6137 | 25916 |
| `_ops/organism.py` | 209 | 315 | 10301 | 17705 |
| `_ops/doctor/doctor.py` | 440 | 734 | 26133 | 43748 |
| `_ops/unified_bus.py` | 114 | 141 | — | — |
| `_ops/live_loop.py` | 200 | 214 | — | — |
| `_ops/chrono.py` | 606 | 620 | 29751 | 30359 |
| `_ops/doctor/box/sensors.py` | 106 | 122 | — | — |

بقیهٔ ۵۶ فایلِ `_ops/*.py` سالم compile شدند. `git status` تمیز گزارش شد — که با بریدگیِ working-tree ناسازگار است؛ یعنی یا (الف) working-tree واقعاً روی دیسک بریده و git از stat-cache تمیز دیده، یا (ب) آرتیفکتِ لایهٔ mountِ این محیط در خواندنِ همین چند فایل است. **objectهای git دست‌نخورده‌اند** — بازیابی بی‌ریسک است.

### Runbook بازیابی (روی ویندوزِ واقعی، خودت اجرا کن)
```powershell
cd F:\backup
# ۱) صحت‌سنجیِ واقعی (آیا فایل روی دیسک هم بریده است؟)
python -c "import ast; ast.parse(open(r'_ops\wiring.py',encoding='utf-8').read()); print('wiring OK')"
# اگر خطای SyntaxError داد → بریده است. objectهای git سالم‌اند:
git fsck --full
git status
# ۲) بازیابیِ فقط همان ۷ فایل از HEAD (بی‌ریسک؛ genome/charter دست نمی‌خورد)
git restore -- "_ops/wiring.py" "_ops/organism.py" "_ops/unified_bus.py" ^
  "_ops/live_loop.py" "_ops/chrono.py" "_ops/doctor/doctor.py" "_ops/doctor/box/sensors.py"
# ۳) اثبات
python -m pytest _ops\tests -q    # یا: python -X utf8 _ops\tests\run_all.py
```
اگر `git status` قبل از restore این فایل‌ها را «modified» نشان نداد ولی `ast.parse` شکست، یعنی بریدگی از mount/کپیِ بکاپ است نه commit — یک `git checkout -- <file>` یا کلونِ تازه از HEAD کافی است.

**چرا P0:** این ۷ فایل ستون‌فقراتِ همیشه-روشن‌اند (heart/bus/wiring/doctor). تا وقتی این‌طور بمانند، هیچ اجرای live یا سوئیتِ کامل ممکن نیست — و پیش از live-gate باید سبز باشند.

---

## §B — رفعِ E16 (is_human جعل‌پذیر) — کدِ ساخته‌شده و تست‌شده

**مسئله `[FACT: 07 - Knowledge/genome-system/ledger/ledger.py:184]`:** `Ledger.append(..., is_human=True)` روی هر caller ای mortal `age_tick` را +۱ می‌کند. ژنوم فریز است → گارد باید در لایهٔ ارگانیسم روی گلوگاهِ `unified_bus.publish` بنشیند.

**تحویل‌شده (اجرا شد، ۱۰/۱۰ سبز `[FACT]`):**
- `_ops/budget/human_append_guard.py` — گاردِ HMAC-SHA256؛ فقط approval_channel با راز token می‌سازد؛ token به `approval_id + event_type + انقضا` bind است؛ محافظتِ replay؛ **پیش‌فرض DISABLED (passthrough)** تا چیزی نشکند.
- `_ops/tests/test_human_append_guard.py` — standalone، بدونِ pytest، بدونِ importِ هستهٔ بریده.

اجرا: `python3 _ops/tests/test_human_append_guard.py` → `== 0 failure(s) ==`.

### Patch سیم‌کشی (propose-only — بعد از §A restore اعمال شود)
روی نسخهٔ **سالمِ** `_ops/unified_bus.py` (HEAD)؛ backward-compatible (پارامترهای جدید optional؛ گاردِ disabled = رفتارِ فعلی):

```diff
--- a/_ops/unified_bus.py
+++ b/_ops/unified_bus.py
@@
+from budget import human_append_guard as _hag   # یا: import human_append_guard as _hag
@@
-    def publish(self, event_type: str, payload: dict, actor: str = "system",
-                is_human: bool = False, beat: bool = False) -> dict:
+    def publish(self, event_type: str, payload: dict, actor: str = "system",
+                is_human: bool = False, beat: bool = False,
+                human_token: str | None = None,
+                approval_id: str | None = None) -> dict:
@@
         if not isinstance(payload, dict):
             raise TypeError("payload must be dict")
         lg = self._lg()
+        # E16: is_human باید توسطِ approval_channel امضا شده باشد؛ وگرنه downgrade.
+        if is_human:
+            guard = getattr(self, "_guard", None) or _hag.default_guard()
+            allowed, reason = guard.authorize(event_type, True,
+                                              token=human_token, approval_id=approval_id)
+            if not allowed and guard.enabled:
+                is_human = False
+                try:
+                    self._note("HUMAN_APPEND_REJECTED",
+                               {"event_type": event_type, "actor": actor, "reason": reason})
+                except Exception:  # noqa: BLE001
+                    pass
         # ۱) genome ledger = source of truth (اولین، همیشه)
         entry = lg.append(event_type, payload, actor=actor,
                           is_human=is_human, beat=beat)
```

**نکتهٔ مهمِ مسیرِ دوم `[FACT: _ops/chrono.py:414]`:** تابعِ `_human_judgment` مستقیم `lg.append(..., is_human=True)` می‌زند و از `unified_bus` رد نمی‌شود. یا باید این هم از گارد رد شود، یا رسماً «تنها minterِ داخلیِ مورداعتماد» علامت بخورد (تصمیم با آری). تا آن زمان E16 کاملاً بسته نیست — گارد فقط مسیرِ bus را پوشش می‌دهد.

**فعال‌سازی:** `approval_channel` هنگامِ وصلِ واقعیِ تلگرام `human_append_guard.configure(secret)` را با رازِ store (هرگز hardcode) صدا بزند و در approve/deny یک token `mint` کند. تا آن لحظه گارد passthrough می‌ماند (صفر شکست).

---

## §C — Gap-Report (Δ-checks مِتا-پرامپت، گراند‌شده)

| # | Δ-check | یافته | تگ |
|---|---|---|---|
| 1 | P1 «commit مانده»؟ | git tree تمیز، HEAD=`6a12197` روی master؛ بدونِ uncommitted | `[FACT]` بسته |
| 2 | protective_override پیش از epoch؟ | commit `c67c591` در history | `[FACT]` بسته |
| 3 | E16 is_human هنوز جعل‌پذیر؟ | بله؛ `approval_channel.py` هست ولی is_human را از تلگرامِ واقعی نمی‌گیرد (interface pluggable). **رفع در §B** | `[FACT]` → mitigated (propose) |
| 4 | باگ `mean_awareness()` fix؟ | `test_canonical_consolidation.py` وجود دارد و رفعِ متد را assert می‌کند (کدِ committed) — **اما در این محیط اجرا نشد چون هستهٔ بریده import را می‌شکند** | `[FACT: test present]` / `[OPEN: run]` |
| 5 | consolidation wired؟ | commit `c77238b` «wire canonical_consolidation into live loop (behind flag)» | `[FACT]` |
| 6 | تصادمِ LANGAR؟ | `LANGAR-ALIAS-REGISTRY.md` موجود؛ به‌روزرسانی/reconcile هنوز `[OPEN]` | `[OPEN]` |
| 7 | money_gate هنوز shadow/$0؟ | `live_gate_open` در کد تا `LIVE_GATE_DATE` (۲۰۲۶-۰۷-۲۱) قفل | `[FACT]` |
| 8 | ledger هنوز v0.4.6؟ | `unified_bus.py`=`0.4.6` ولی `test_chrono_langar.py`=`0.4.5` → **drift** | `[FACT]` drift |
| 9 | §Security Gate هنوز LIFTED؟ | بله (۲۰۲۶-۰۷-۰۶)؛ ۱۴ ردیفِ HIGH/MEDIUM backlog | `[FACT]` |
| 10 | Project-F guard از UI به کد رفت؟ | شواهدِ کدیِ enforce پیدا نشد؛ هنوز `[OPEN]` | `[OPEN]` |

**[BLOCKED]:** اجرای سوئیتِ کاملِ `_ops/tests` در این محیط — به‌خاطرِ §A (هستهٔ بریده) + نبودِ pytest/شبکه. بعد از restore روی ویندوز اجرا شود.

---

## §D — پیشنهادهای اولویت‌دار (propose-only)

- **P0-1** `git restore` هفت فایلِ هسته + اجرای سوئیت (§A). پیش‌نیازِ هر کارِ live.
- **P0-2** «Pre-Live-Gate Checklist» بساز (۱۲ روز مانده): تأییدِ money_gate=$0، live_gate flag نبودن، تست‌های money/exposure سبز، E16 بسته، Δ۸ ledger-version یکی‌شده. (نبودش خودش ریسکِ P0.)
- **P1-1** review + اعمالِ patchِ §B؛ سپس تصمیمِ مسیرِ `chrono._human_judgment` (گارد یا trusted-minter).
- **P1-2** رفعِ drift نسخهٔ ledger (`0.4.5`↔`0.4.6`) در تست/کد.
- **P2-1** reconcileِ تصادمِ نامِ LANGAR در `LANGAR-ALIAS-REGISTRY`.
- **P2-2** بردنِ Project-F guard از UI به enforceِ کدی.

## Sources
[[06 - Architecture Maps/MASTER-ARCHITECTURE-2026-07-09]] · [[_ops/ORGANISM-SPEC]] · [[05 - Agents/AGENT_REGISTRY]] · [[ROTATION_CHECKLIST]] · `git log` (HEAD `6a12197`) · `_ops/budget/opslib.py` · `07 - Knowledge/genome-system/ledger/ledger.py`
