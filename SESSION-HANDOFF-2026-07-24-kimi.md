# SESSION HANDOFF — 2026-07-24 (kimi, synapse session) — START HERE
### چه شد، کجاست، چه نشد، و پلنِ سریِ بعدیِ چت. برای ایجنتِ بعدی.

> منبعِ حقیقتِ کد: `master @ ff33af0` (P5 ادغام‌شده). درختِ زنده‌ی F:\backup روی
> `claude/octopus-event-bridge-aligned` می‌دود. **فایل‌های این جلسه روی همین درختِ زنده
> نوشته شدند و uncommitted‌اند** — ایجنتِ بعدی (با git) آن‌ها را review و به master
> چری‌پیک/مرج کند. ارگانیسم در این جلسه زنده بود (beat ~10851)؛ هیچ restart/deploy/فلپی نشد.

## ۱. حسابرسیِ اهدافِ جلسه

| # | هدف | وضعیت | محل |
|---|---|---|---|
| 1 | SENSE: SOG روی تله‌متریِ خودِ ارگانیسم (پیشنهادِ الف) | ✅ ساخته شد | `_ops/synapse/sense.py` |
| 2 | دیکشنریِ کاملِ استعاره→ریاضی (پیشنهادِ ج) | ✅ ۱۲ استعاره | `06 - Architecture Maps/METAPHOR-MATH-DICTIONARY-v1.md` |
| 3 | نقشه‌ی پتانسیل‌ها (فاز صفرِ سنتز) | ✅ ۱۲ پتانسیل | `06 - Architecture Maps/POTENTIALS-MAP-2026-07-24.md` |
| 4 | P3 trajectory monitor (containment) | ✅ ماژول + طراحیِ wiring | `_ops/synapse/trajectory_monitor.py` |
| 5 | P1 egress deny-by-default (containment) | ✅ policy-as-data | `_ops/synapse/egress_policy.py` |
| 6 | پاسخِ قانون‌مند به «تبدیل به AGI» + نقشه‌ی راه | ✅ | `_program-deliverables/AGI-CAPABILITY-GAP-ROADMAP-2026-07-24.md` |
| 7 | پلنِ سریِ بعدیِ چت (بخشِ ناتمامِ درخواست) | ✅ | §۴ همین سند + roadmap §۲ |
| 8 | ثبت در SOT + صف‌ها | ✅ | الحاق‌های انتهایی |

## ۲. فایل‌های ساخته‌شده (همه additive، flag-off، propose-only)

- `_ops/synapse/{__init__,sense,trajectory_monitor,egress_policy}.py` + `README.md` + `out/`
- `_ops/tests/test_synapse_sense.py`
- `06 - Architecture Maps/{POTENTIALS-MAP-2026-07-24,METAPHOR-MATH-DICTIONARY-v1}.md`
- `_program-deliverables/AGI-CAPABILITY-GAP-ROADMAP-2026-07-24.md`
- الحاق: `ARCHITECTURE-SOT.md` (ثبتِ synapse) · `VERDICT_QUEUE.md` (VQ-SYN/TRAJ/EGR/AGI) · `00 - Inbox/AGENT_QUESTIONS.md`

**ناوردها:** صفر تغییر در فایلِ موجودِ runtime · صفر نوشتن در genome/.env/budget/state · مصرف LLM=۰ · هر سه فلگ پیش‌فرض خاموش · fail-closed · self_test آفلاین در هر ماژول.

## ۳. محدودیت‌های صادقانه‌ی این جلسه

- **ابزارِ اجرا (shell/pytest/git) نداشتم** → تست‌ها نوشته شدند ولی **اجرا نشدند [UNKNOWN]**؛
  اولین کارِ فنیِ سریِ بعدی: `python _ops/synapse/sense.py` (self_test) + `python -m pytest _ops/tests/test_synapse_sense.py -v`.
- `_ops/arm_gate.py` در این worktree نیست (P5 روی master است) — سازگار با وضعیتِ برنچ‌ها، نه تناقض.
- wiring هیچ‌کدام به رانتایم انجام نشد (همه tapِ مالک).

## ۴. پلنِ سریِ بعدیِ چت (به‌ترتیب — از roadmap §۲)

1. اجرای تست‌ها (سبز/قرمز) → فیکس اگر لازم.
2. **deploy master** (tapِ مالک) + بوتِ سالم.
3. L2: روشن‌کردنِ R5 context_fence.
4. L3: «منبع ۵» event_bridge ← trajectory-alerts (patch کوچک روی center.py).
5. L4: حافظه‌ی v2 write-beat · L5: روترِ parallel.
6. L6: اولین لیدِ واقعی (Ziman/Lead) — C5 از NOT_MET خارج شود.
7. L7: P2 twin → اولین transplantِ twin-tested.
8. distill loop (roadmap §۳) + خودنگاره‌ی واحد (پتانسیلِ ۱۱).
9. propagation-lab (۲۶ تستِ failِ پارک‌شده) — فقط اگر مالک بگوید مهم است.

## ۵. قواعدِ سخت (بدونِ تغییر)
ژنوم/.env/budget/kill-switch دست‌نخوردنی · propose-only تا tap · هر ادعا با شاهد یا برچسب ·
AGI فرضیه‌ی ابطال‌پذیر است، نه هویت · مهار همیشه جلوتر از توانمندی.

**اسنادِ مرجع:** همین سند · AGI-CAPABILITY-GAP-ROADMAP-2026-07-24 · SESSION-HANDOFF-2026-07-24-opus (جلسه‌ی قبل) · CONTAINMENT-PLAN-2026-07-24.
