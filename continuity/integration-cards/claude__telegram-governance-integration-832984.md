# Integration Card — claude/telegram-governance-integration-832984

id: branch:claude/telegram-governance-integration-832984
path: git branch
type: branch
head: da3b0e226d109c620bd3a907e1ff28fc5aa9b3dc
merge_base_with_master: 81eb8f00a26829ad52eb28f098518214ed8925b0
ahead_of_master: 12
behind_master: 719
priority: P0/P1
lane: telegram-governance
risk: D2 کارت/contract، اجرای بعدی با تأیید
decision: DIGEST_AND_PORT_BY_INTENT
why: حجم/دامنه چندبخشی؛ باید ایده‌ها جدا وارد ستون زنده شوند
reversibility: high while unmerged; medium after staged; rollback via branch/head
external_effect: none during this card; must remain behind owner_gate/WAL if later ported

## Commit subjects
- 957deb4 — agent-checkpoint: W2 دبل‌چک — id پایدار guidance (رفع F2-1 resurface + F2-2 explicit-id) + نشانگر کهنگی دایجست پا (G7 honesty)
- ab3f14b — agent-checkpoint: W1 دبل‌چک — رفع P0 دو-پولر تلگرام (G1-1، center بازنده خاموش نبود)
- 41ba7f8 — agent-checkpoint: W3 دبل‌چک — seam اکچوایتور (رفع گاف #۱: تصمیم تاییدشده ثبت می‌شد ولی هیچ اکشنی نمی‌شد)
- b314455 — agent-checkpoint: W4 دبل‌چک — گزارش Inbox + آپدیت PROJECT/HANDOFF (سوییت زنده 119/119، validators baseline)
- 0e587a9 — agent-checkpoint: W5 دبل‌چک — فعال‌سازی خروجی واقعی پا (lead_draft): intake→draft_quote→persist→نمایش (رفع A3-1)
- d103371 — agent-checkpoint: W5 دبل‌چک — آپدیت HANDOFF/PROJECT/گزارش (فعال‌سازی خروجی پا، سوییت 120/120)
- 37f9d76 — agent-checkpoint: W6 — درِ ورودیِ واحدِ تلگرام (رأی مالک «UI از طریق اختاپوس، خودتو ببر زیرمجموعش»)
- fbad282 — agent-checkpoint: W7 — بهینه‌سازی UI تلگرام بر پایه عملکرد واقعی (رأی مالک: فلو لید دکمه‌ای + «نیاز تو» برجسته + پاکسازی نویز)
- aff5bcf — agent-checkpoint: HANDOFF جلسه ۴۹ — افزودن W6 (درِ ورودیِ واحد) + W7 (بهینه‌سازیِ UI)، سوییت 121/121
- 7a9d880 — agent-checkpoint: طراحی پایه Painting-OS (۴ ستون: کار/کوت/اینویس/ایمیل) + ۴ پرامپت تحقیقاتی
- de16794 — feat(p1-quotation): structured quoting engine + partial payment reconcile
- da3b0e2 — feat(p2p3-painting-os): invoice engine + email inbound + structured intake

## Short stat
```text
33 files changed, 3436 insertions(+), 81 deletions(-)
```

## Risk buckets
### tests (15)
- _ops/tests/harness.py
- _ops/tests/run_all.py
- _ops/tests/test_approval_actuator.py
- _ops/tests/test_email_inbound.py
- _ops/tests/test_guidance_box.py
- _ops/tests/test_invoice.py
- _ops/tests/test_lead_draft.py
- _ops/tests/test_lead_intake.py
- _ops/tests/test_lead_quote.py
- _ops/tests/test_lead_ui.py
- _ops/tests/test_pricing.py
- _ops/tests/test_telegram_poll_e2e.py
- _ops/tests/test_tg_api.py
- _ops/tests/test_tg_center.py
- _ops/tests/test_tg_render.py

### other (6)
- "00 - Inbox/\330\257\330\250\331\204\342\200\214\332\206\332\251 - \330\261\330\247\330\263\330\252\333\214\342\200\214\330\242\330\262\331\205\330\247\333\214\333\214 \331\201\333\214\332\251\330\263\342\200\214\331\207\330\247 \331\210 \330\247\332\251\332\206\331\210\330\247\333\214\330\252\331\210\330\261 (\331\276\330\247 \331\210 \331\206\331\202\330\247\330\264\333\214).md"
- _ops/budget/reconcile.py
- _ops/legs/invoice.py
- _ops/legs/pricing.py
- _ops/organism.py
- _ops/wiring.py

### outbound (5)
- "03 - Projects/Lead-\331\206\331\202\330\247\330\264\333\214/PROJECT.md"
- "03 - Projects/Lead-\331\206\331\202\330\247\330\264\333\214/\332\251\330\247\330\261\333\214\330\247\330\250\333\214/Painting-OS - \331\276\330\247\333\214\331\207\342\200\214\331\207\330\247 \331\210 \331\276\330\261\330\247\331\205\331\276\330\252\342\200\214\331\207\330\247\333\214 \330\252\330\255\331\202\333\214\331\202\330\247\330\252\333\214.md"
- _ops/legs/email_inbound.py
- _ops/legs/lead_draft.py
- _ops/legs/lead_quote.py

### telegram (4)
- _ops/budget/approval_channel.py
- _ops/telegram_center/center.py
- _ops/telegram_center/render.py
- _ops/telegram_center/tg_api.py

### tcb-self (2)
- _ops/cortex/approval_actuator.py
- _ops/cortex/guidance_box.py

### docs (1)
- 01 - Dashboard/HANDOFF.md

## Changed files
```text
A	"00 - Inbox/\330\257\330\250\331\204\342\200\214\332\206\332\251 - \330\261\330\247\330\263\330\252\333\214\342\200\214\330\242\330\262\331\205\330\247\333\214\333\214 \331\201\333\214\332\251\330\263\342\200\214\331\207\330\247 \331\210 \330\247\332\251\332\206\331\210\330\247\333\214\330\252\331\210\330\261 (\331\276\330\247 \331\210 \331\206\331\202\330\247\330\264\333\214).md"
M	01 - Dashboard/HANDOFF.md
M	"03 - Projects/Lead-\331\206\331\202\330\247\330\264\333\214/PROJECT.md"
A	"03 - Projects/Lead-\331\206\331\202\330\247\330\264\333\214/\332\251\330\247\330\261\333\214\330\247\330\250\333\214/Painting-OS - \331\276\330\247\333\214\331\207\342\200\214\331\207\330\247 \331\210 \331\276\330\261\330\247\331\205\331\276\330\252\342\200\214\331\207\330\247\333\214 \330\252\330\255\331\202\333\214\331\202\330\247\330\252\333\214.md"
M	_ops/budget/approval_channel.py
M	_ops/budget/reconcile.py
A	_ops/cortex/approval_actuator.py
M	_ops/cortex/guidance_box.py
A	_ops/legs/email_inbound.py
A	_ops/legs/invoice.py
A	_ops/legs/lead_draft.py
A	_ops/legs/lead_quote.py
A	_ops/legs/pricing.py
M	_ops/organism.py
M	_ops/telegram_center/center.py
M	_ops/telegram_center/render.py
M	_ops/telegram_center/tg_api.py
M	_ops/tests/harness.py
M	_ops/tests/run_all.py
A	_ops/tests/test_approval_actuator.py
A	_ops/tests/test_email_inbound.py
M	_ops/tests/test_guidance_box.py
A	_ops/tests/test_invoice.py
A	_ops/tests/test_lead_draft.py
A	_ops/tests/test_lead_intake.py
A	_ops/tests/test_lead_quote.py
A	_ops/tests/test_lead_ui.py
A	_ops/tests/test_pricing.py
M	_ops/tests/test_telegram_poll_e2e.py
M	_ops/tests/test_tg_api.py
M	_ops/tests/test_tg_center.py
M	_ops/tests/test_tg_render.py
M	_ops/wiring.py
```

## Proposed next action
- DIGEST_AND_PORT_BY_INTENT
- No direct merge. If valuable: extract contract, run targeted tests, then cherry-pick/port minimal patch behind flag/owner gate.
