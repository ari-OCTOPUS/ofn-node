# Fugu Usage Policy — Canonical Provider Map

> **تاریخ:** 2026-08-02 · **وضعیت:** active policy
> **هدف:** پایان‌دادن به drift ناشی از چندین مسیر مستقل Fugu. تعیین provider‌های canonical.
> **قانون آهنین:** هیچ provider سومی ساخته نمی‌شود. caller‌های غیر-canonical به‌تدریج migrate می‌شوند.

---

## مشکل: ۳ مسیر Fugu مستقل (DRIFT)

قبل از این سند، Fugu از ۳ مسیر کاملاً مستقل صدا زده می‌شد، هرکدام با budget guard و HTTP client و error handling جداگانه:

| # | مسیر | زبان | HTTP | Budget guard | Circuit breaker | Cache |
|---|---|---|---|---|---|---|
| 1 | `4d_system/llm/fugu_client.py` + `router.py` | Python | httpx | `brain/budget.py` (daily cap 1000) | ❌ | ❌ |
| 2 | `_ops/cortex/model_router.py` + `cortex/fugu_quota.py` | Python | urllib (via `debate/client.py`) | `fugu_quota.py` (60/day) + `organ_gate` | ✅ (3 fail) | ❌ |
| 3 | `wlos/packages/fugu-provider/` | TypeScript | fetch | `TokenBudget` interface | ✅ (3 fail) | ❌ |

همچنین دو caller تک‌نسخه‌ای (کپی منطق):
- `_ops/debate/client.py` — `MultiProviderClient` مستقیم (دلیل وجود مسیر ۲)
- `03 - Projects/اونلی فنز/studio/creator_brain.py` — نسخهٔ چهارم با `urllib.request`

**نتیجهٔ drift:** double-counting بودجه، رفتار خطای ناسازگار، هدررفت اشتراک $200/month.

---

## تصمیم: ۲ Canonical Provider (نه ساخت سوم)

| Canonical | زبان | برای چه caller‌هایی | مسیر |
|---|---|---|---|
| **Python canonical** | Python | 4D daemon + (آینده) cortex _ops | `4d_system/llm/router.py` + `fugu_client.py` |
| **TypeScript canonical** | TypeScript | WLOS + Node gateway | `wlos/packages/fugu-provider/` |

### Migration map (caller → canonical)

| Caller فعلی | Canonical هدف | اقدام |
|---|---|---|
| `4d_system/llm/fugu_client.py` | (خودش canonical) | ✅ حفظ |
| `4d_system/llm/router.py` | (خودش canonical) | ✅ حفظ |
| `wlos/packages/fugu-provider/` | (خودش canonical) | ✅ حفظ |
| `_ops/cortex/model_router.py` | Python canonical | 🟡 migrate: استفاده از shared budget file یا delegate به 4D router |
| `_ops/cortex/fugu_quota.py` | merge با `brain/budget.py` | 🟡 بعد از migration model_router |
| `_ops/debate/client.py` | Python canonical | 🟠 deprecate به‌نفع model_router |
| `creator_brain.py` | Python canonical یا TS canonical | 🟠 refactor در Wave بعدی |

---

## قراردادهای LLM (FuguCallContract)

هر call به Fugu باید یک contract صریح داشته باشد:

```typescript
type FuguCallContract = {
  taskId: string;
  brain: string;                    // کدام مغز صدا می‌زند
  model: "fugu" | "fugu-ultra" | "fugu-cyber";
  purpose: string;                  // logged
  expectedArtifact: string;         // خروجی مورد انتظار
  risk: "low" | "medium" | "high";
  importance: "low" | "medium" | "high" | "critical";
  containsSecrets: boolean;         // اگر true → local only یا redacted
  estimatedInputTokens: number;
  estimatedOutputTokens: number;
  cacheKey: string;                 // برای dedup
  allowUltra: boolean;              // فقط importance=critical
};
```

---

## سیاست Tier (مصرف)

### Tier 0 — Local ($0، نباید Fugu مصرف کنند)
```
regex search · file tree scan · link extraction · tag extraction
checklist extraction · hash/cache lookup · duplicate detection
raw graph construction · secret scan اولیه · diff ساده
```

### Tier 1 — `fugu` (استاندارد)
```
semantic tagging · summary · classification · draft plan
note clustering · تبدیل notes به checklist · توضیح رابطه‌های ساده
```

### Tier 2 — `fugu` با effort بالا
```
architecture comparison · dependency analysis
mapping notes به ۱۵ اصل OMEGA-PARITY · experiment design · multi-step planning
```

### Tier 3 — `fugu-ultra` (فقط critical)
```
deep diagnosis · full audit · weekly synthesis · final architecture review
حل contradictionهای مهم · تصمیم‌های معماری irreversible · طراحی core module
```
**ممنوع اگر:** context فشرده نشده · artifact مشخص نیست · کار search/regex است · secret redacted نشده.

### Cyber Tier — `fugu-cyber` (redacted فقط)
```
security audit · prompt injection review · redacted secret report
API key hygiene · threat modeling
```
**هرگز خام ارسال نمی‌شود:** raw secret · API key · `.env` خام · private token · log حساس.

---

## Routing rule

```
containsSecrets=true → local only یا redacted cyber
cache hit            → cache
deterministic       → local
semantic ساده       → fugu (Tier 1)
architecture/audit  → fugu-ultra (Tier 3)
security            → fugu-cyber (redacted)
write/patch/commit  → Gate + git diff + approval
```

---

## بودجهٔ مرکزی (هدف نهایی)

الان دو budget مستقل داریم:
- `4d_system/outputs/llm_budget.json` — cap روزانه 1000 (4D)
- `_ops/state/fugu-quota.json` — cap روزانه 60 (cortex)

**هدف کوتاه‌مدت:** 4D و cortex از یک shared budget file بخوانند تا double-counting نشود.
**هدف میان‌مدت:** یک `BudgetGuard` مرکزی که هر دو canonical provider از آن عبور کنند.

---

## مصنوعات مرتبط (برای ساختن)
```
docs/fugu_call_ledger.md       — لاگ همهٔ call‌ها (purpose, model, tokens, cost)
docs/fugu_roi_report.md        — ROI هفتگی per brain
docs/octopus_brain_registry.md — ۱۰ مغز ← ۷ موجود + ۳ جدید
```
