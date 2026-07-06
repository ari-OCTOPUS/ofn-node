# الگوهای معماری — مرجعِ سریع (Quick Reference)

## ۱۲ الگو بنیادی

```
1️⃣  Mycelial Topology          — شبکهٔ بدون‌مرکز با backbone
2️⃣  Autonomy Ladder L0-L3      — پلکانِ تصمیم با whitelist
3️⃣  EffectorGate               — تنها درب side-effect
4️⃣  Anchor Ledger              — append-only source-of-truth
5️⃣  RATIFIED-TASKS             — پرامپت+cron کنار هم
6️⃣  Evaporation/TTL            — archive خودکار + برگشت‌پذیری
7️⃣  Spawn & Select Fleet       — تکاملِ ناوگان
8️⃣  Dual-Score Doctor          — سلامت+جهش+حلقهٔ فکری
9️⃣  Two-Brain Control          — انسان+دکتر
🔟 HEARTBEAT Watchdog           — beat دوطرفه
1️⃣1️⃣ Reflexion Cycle           — Actor→Evaluator→درس
1️⃣2️⃣ Approve-First Queue       — هیچ L2 بدون verdict
```

## نقاطِ تقاطع برای v2

| الگو | فاز ۳ | فاز ۴ | فایل |
|---|---|---|---|
| Mycelial | core.db hub | — | ARCHITECTURE.md §۱ |
| Autonomy | L2 bounded | L3 auto | AUTONOMY-LADDER |
| EffectorGate | gateway.py | — | MASTER-SPEC §۲ |
| Anchor Ledger | briefs/outbox | mutation ledger | LEDGER schema |
| RATIFIED-TASKS | scheduler | — | RATIFIED-TASKS.md |
| Evaporation | TTL 7d | TTL 30d | ratified::consolidator |
| Spawn & Select | per-business | new hypothesis scouts | fleet-selection |
| Dual-Score | validator | doctor 3 columns | DOCTOR-PROMPT |
| Two-Brain | admin approve/reject | — | TWO-BRAIN-BLUEPRINT |
| HEARTBEAT | sqlite heartbeat | — | AUTONOMY §۵ |
| Reflexion | feedback table | Fugu loop | MASTER-SPEC §۷ |
| Approve-First | draft→approved→sent | mutation→branch | ARCHITECTURE §۶ |

## سه توصیهٔ فوری برای فاز ۴

```
✅ شروع Reflexion از feedback جدول (نه خام Fugu)
   → استخراج درسِ قطعی، بعد Fugu escalation

✅ TTL 30 روز برای جهش‌های quarantined
   → auto-revert + ledger entry «TTL-expired»

✅ Kill-switch سه‌سطحی
   - Pause (resume‌شونده)
   - Kill (quarantined ماندگار)
   - Revert (git rollback N جهش)
```

## ریسک‌های اصلی و کاهش

| ریسک | الگوی کاهش | اقدام |
|---|---|---|
| Drift doc↔runtime | Anchor Ledger + Mycelial | همهٔ read از FS + SYSTEM-STATE |
| خزش self-verdict | Autonomy + Dual-Score | معیار 4گانه + halt فوری |
| فراموشی جهش | Mutation Ledger + TTL | 30d expire + HEARTBEAT |
| Secret در output | EffectorGate + Approve-First | quarantine + never echo |
| SPOF admin | Mycelial + Spawn & Select | multiple admins; core.db shared |
| تبخیرِ شواهد | Evaporation | in-place archive (برگشت‌پذیر) |

## فایلهای اصلی

```
📄 MYCELIAL-ARCHITECTURE-vfinal.md        — الگوهای ۱,۲,۳,۴
📄 AUTONOMY-LADDER.md                     — الگوی ۲,۱۰,۱۲
📄 RATIFIED-TASKS.md                      — الگوهای ۵,۶,۷
📄 Evolutionary Doctor Prompt             — الگوی ۸
📄 TWO-BRAIN-CONTROL-BLUEPRINT.md         — الگوی ۹
📄 MYCELIAL-MASTER-SPEC.md                — الگوهای ۱۱,۳,۴
📄 _launchpad/second-brain-live/          — v2 implementation
    ARCHITECTURE.md                       — نگاشت کامل فاز۳
    INVENTORY.md                          — دارایی‌های موجود
```

---

**تاریخ:** 2026-07-06  
**حجم:** 12 الگو + 4 فاز + 3 توصیه + 6 ریسک  
**وضعیت:** Ready برای فاز ۳ و ۴
