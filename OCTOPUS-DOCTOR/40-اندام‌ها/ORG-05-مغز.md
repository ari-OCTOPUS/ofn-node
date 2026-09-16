---
type: "organ"
id: "ORG-05"
status: "🟡"
code: "doctor/fugu.py"
tags:
  - اندام
scan: "2026-07-29"
---

# ORG-05 — مغز 🟡

> [!abstract] استعاره → کد
> **مغز** ⟶ `doctor/fugu.py` (Sakana Fugu) — جزئیات در [[BRAIN-fugu]]

سه لایه: `fast` (fugu / high) · `deep` (fugu-ultra-v1.1 / max) · `cyber` (fugu-cyber / xhigh).

## fail-closed

بدونِ `SAKANA_API_KEY` مغز **هیچ متنی تولید نمی‌کند** — نه mock، نه حدس، نه «احتمالاً».
تست ثابت می‌کند سهمیه هم با شکستِ کلید مصرف نمی‌شود.

## سقف

۶۰ فراخوان در روز، رسید در `paid-calls.jsonl`. `triage` کاملاً آفلاین است و همیشه کار می‌کند —
یعنی نبودِ مغز، دکتر را از کار نمی‌اندازد؛ فقط از حرف‌زدن می‌اندازد.

> [!warning] `[UNKNOWN]`های API
> نرخِ محدودیت، پنجرهٔ context، و اینکه `reasoning_effort` روی `/chat/completions`
> معتبر است یا فقط responses API — هیچ‌کدام تأیید نشده. ← `RESEARCH-PROMPTS` پرامپتِ ۱ و ۲.

---
مرتبط: [[MOC-اندام‌ها]] · [[HOME]]
