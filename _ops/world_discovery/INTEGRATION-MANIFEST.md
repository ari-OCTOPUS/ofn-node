# INTEGRATION-MANIFEST — WORLD DISCOVERY ↔ OCTOPUS
# سند اتصال اندام کشف به بدن زندهٔ اختاپوس

> [FACT] این سند «سوکت» را توصیف می‌کند. ایجنت ارشد تصمیم می‌گیرد چه زمانی وصل کند.
> [FACT] هیچ‌چیز در این سند به‌عنوان مجوز خرج/ارسال/deploy تلقی نمی‌شود.
> [FACT] تا پذیرش ایجنت ارشد: status = `IMPLEMENTED_NOT_INTEGRATED`.

---

## 1. وضعیت فعلی

| مورد | مقدار |
|---|---|
| namespace مستقل | `_ops/world_discovery/` |
| فایل‌های ممنوع ویرایش‌شده | **۰** (هیچ‌کدام) |
| runtime state نوشته‌شده | **۰** byte |
| فلگ اضافه‌شده به OCTOPUS-flags.cmd | **۰** |
| caller اضافه‌شده به organism/wiring | **۰** |
| تست‌های PASS | ۸۵/۸۵ |
| external_effect_count | ۰ |
| spend_amount | ۰ |
| hard invariant violations | ۰ |

---

## 2. public API اندام (input/output contract)

### 2.1 caller پیشنهادی
```python
from world_discovery import octopus_adapter as wd

direction = wd.load_direction()                  # از WORLD-DISCOVERY-CHARTER
result = wd.discover(direction.as_dict())        # کل حلقهٔ کشف
info = wd.write_report(result, output_dir)       # report + bundle
```

### 2.2 input contract
```python
Direction = {
    "mission_id": str,
    "domain": str,                 # "ai-competition"
    "geography": str,              # "global"
    "horizon_days": int,           # 7
    "competitors": list[str],      # 5 رقیب
    "min_sources": int,            # 2
    "action_level": str,           # "L3"
    ...
}
```

### 2.3 output contract (`world-discovery.discover.v1`)
```json
{
  "schema": "world-discovery.discover.v1",
  "status": "DISCOVERY_VALIDATED | NO_VALID_DISCOVERY | CONTESTED | BLOCKED_BY_OWNER | IMPLEMENTED_NOT_INTEGRATED",
  "discovery": { ... } | null,
  "experiment": { ... },
  "opportunity": { ... },
  "competitor_matrix": { ... },
  "asymmetry_hypotheses": [ ... ],
  "owner_action_cards": [ ... ],          // همگی BLOCKED_BY_OWNER
  "metrics": { ... },
  "telegram_draft_brief": "string",       // متن آمادهٔ ارسال (ولی ارسال‌نشده)
  "hard_invariant_violations": []
}
```

### 2.4 pure-data guarantees
- JSON serializable ✓
- versioned schema (`world-discovery.*.v1`) ✓
- secret ندارد ✓
- path مطلق بیرونی ندارد ✓
- side-effect بیرونی ندارد ✓
- source URLs را نگه می‌دارد ✓
- confidence + uncertainty را ثبت می‌کند ✓
- result را به success تحمیل نمی‌کند (`no-valid-discovery` پشتیبانی می‌شود) ✓

---

## 3. اتصال تلگرام (L3 — ارسال فقط با رأی مالک)

### 3.1 نقطهٔ اتصال canonical (read-only، موجود)
```
_ops/budget/approval_channel.py
  class TelegramApprovalChannel(ApprovalChannel):    # line 373
    def send_text(self, text, reply_markup=None, ...):  # line 1578
```
- env موردنیاز: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_OWNER_CHAT_ID`
- این کلاس dirty است (ایجنت ارشد روی آن کار می‌کند) → **ویرایش نمی‌شود**.

### 3.2 سوکت مستقلِ اندام (ساخته‌شده، فعال‌نشده)
```
_ops/world_discovery/action_boundary.py
  class OwnerGate(Protocol):            # interface
      def request(card: OwnerActionCard) -> {approved, vote_id, reason}
  class NoOpOwnerGate:                  # default → BLOCKED_BY_OWNER
  def compose_telegram_brief(...)        # متن draft (ارسال‌نشده)
```

### 3.3 patch پیشنهادی برای اتصال (اعمال‌نشده)
وقتی ایجنت ارشد پذیرفت، یک **فایل جدید مستقل** (نه ویرایش approval_channel) بسازد:

```python
# _ops/world_discovery/telegram_owner_gate.py  (پیشنهادی، هنوز نساخته‌شده)
from .action_boundary import OwnerGate, OwnerActionCard

class TelegramOwnerGate:
    """پیاده‌سازی زندهٔ OwnerGate با approval_channel.send_text.

    فقط با رأی مالک ارسال می‌کند. NoOpOwnerGate جایگزین می‌شود.
    """
    def __init__(self, channel):
        self._channel = channel   # TelegramApprovalChannel instance

    def request(self, card: OwnerActionCard) -> dict:
        # ارسال draft به مالک + انتظار برای callback رأی
        ...
```

**نکتهٔ مهم**: این فایل فقط پس از رأی مالک ساخته/فعال می‌شود.

---

## 4. cadence پیشنهادی
- **نه poller دائمی.** اندام on-demand صدا زده می‌شود.
- پیشنهاد: هفتگی یا هنگام درخواست مالک.
- timeout: یک اجرای discover ≤ ۶۰ ثانیه (rate-limited web fetch).

---

## 5. required flag (پیشنهادی، اعمال‌نشده)
```
OCTOPUS_WIRE_WORLD_DISCOVERY   (default: 0)
```
فعال‌سازی فقط با رأی مالک + پذیرش ایجنت ارشد. تا آن زمان، اندام offline است.

---

## 6. cost behavior
- خرج = ۰ (طبق رأی مالک).
- retriever پیش‌فرض: stdlib-only (DuckDuckGo HTML) یا reuse از cortex.web_research (رایگان).
- هیچ API پولی استفاده نمی‌شود.

---

## 7. state destination پیشنهادی (اعمال‌نشده)
```
_ops/state/world_discovery/
├── latest.json          # آخرین result (atomic)
└── history/YYYY-MM-DD/  # آرشیو روزانه
```
تا پذیرش ایجنت ارشد، خروجی فقط در `_ops/world_discovery/{artifacts,reports}`.

---

## 8. duplicate suppression
- `make_discovery_id(claim, mission_id)` → deterministic SHA.
- همان ادعا + همان مأموریت → همان ID → suppressed.
- تست: `test_multiple_runs_same_discovery_id` (PASS).

---

## 9. failure behavior
- retriever fail → `NO_VALID_DISCOVERY` (صادقانه).
- contradiction retriever fail → `INSUFFICIENT-EVIDENCE` (نه PASS).
- corrupt artifact → `fail closed` (`load_bundle_check` raises).
- هر exception در discover → bubble up به caller (نه吞).

---

## 10. rollback
- کل `_ops/world_discovery/` مستقل است؛ حذفش هیچ اثر runtime ندارد.
- هیچ فایل مشترکی ویرایش نشده → rollback ای به فایل‌های ایجنت ارشد وجود ندارد.

---

## 11. فایل‌های دقیق موردنیاز برای integration (پس از پذیرش)
```
NEW:  _ops/world_discovery/telegram_owner_gate.py    (ایجنت ارشد می‌سازد)
NEW:  _ops/state/world_discovery/                     (directory)
EDIT: _ops/OCTOPUS-flags.cmd                          (افزودن OCTOPUS_WIRE_WORLD_DISCOVERY)
EDIT: _ops/organism.py یا wiring.py                   (افزودن caller on-demand)
```
**همهٔ EDIT‌ها فقط با رأی مالک + پذیرش ایجنت ارشد.**

---

## 12. قاعدهٔ نهایی
```
من socket (interface + NoOpGate + draft composer + manifest) را ساختم.
ایجنت ارشد تصمیم می‌گیرد چه زمانی TelegramOwnerGate را بسازد و به runtime وصل کند.
تا آن زمان: هر ارسالی BLOCKED_BY_OWNER است.
```
