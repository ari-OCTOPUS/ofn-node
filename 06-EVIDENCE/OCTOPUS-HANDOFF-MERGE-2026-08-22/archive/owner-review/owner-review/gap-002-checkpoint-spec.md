# gap-002-checkpoint-spec

GAP-002 روی برد **بسته نمی‌شود** تا لپ‌تاپ با **existing root-v2** امضا کند و برد **فقط verify** کند.

عبارت دقیق: `octopus-audit-ledger checkpoint anchored at seq=266`  
عبارت ممنوع: `ledger head = 266`

امضا، حتی اگر موفق باشد، فقط provenance تاریخی تا seq 266 را لنگر می‌کند. Doctor، GAP-001 و T4 را سبز نمی‌کند و به‌تنهایی اجازهٔ `OA-T7` نمی‌دهد.

## وضعیت

- gap status: `DEFERRED_TO_WAVE1`
- `chain_id`: `octopus-audit-ledger`
- `anchored_through_seq`: `266`
- `represents_latest_state`: `false`
- record hash **کامل**: `sha256:ec98f51753c6565d845acd6734c052e2c929383469c8a2755d88dcfbb24b7fc2`
- digest فایل unsigned: `sha256:3b60751b3759698b4982ccda035a008539cc0014cb086d96f516fc274142c150`
- `root_v2_signed`: `false`
- `creates_authority`: `false`
- Reflex ledger: مستقل، seq=1، `same_as_audit_ledger=false`

## آنچه برد صادر کرده

`export_checkpoint()` بدون restart.  
فایل: `/var/lib/octopus/inbound/TO-LAPTOP/OCTOPUS-AUDIT-CHECKPOINT/checkpoint.unsigned.json`  
`signed: false` و `gap_002_closed: false`.

## ترتیب لپ‌تاپ (بعد از گام ۱ Doctor و گام ۲ GAP-001 در NEXT_ACTIONS)

1. بسته را با `verify_owner_review_pack.py` بررسی کن (digest ≠ امضا).
2. hash کامل رکورد ۲۶۶ را با audit ledger تطبیق بده؛ خلاصهٔ `ec98f517…` evidence نیست.
3. `scp` پوشهٔ `OCTOPUS-AUDIT-CHECKPOINT` به Windows.
4. **هرگز** `make-root-v2.bat` را اجرا نکن.
5. با existing root-v2 امضا کن (`sign-checkpoint.bat` / `sign_checkpoint.py`). fingerprint باید `sha256:a20d836d1f461482c76c4d3ed6c6de301d38b3e8e0ef4707e87d7b45e2223a40` باشد.
6. `scp SIGNED-CHECKPOINT-BUNDLE/*` به `/var/lib/octopus/inbound/SIGNED-CHECKPOINT-BUNDLE/` (بدون `private/`).
7. روی برد **فقط verify**. امضا authority نمی‌سازد. actuator_authority باید NONE بماند.
8. اگر live head بعد از ۲۶۶ رشد کرده، این رشد بازنویسی نیست. امضای ۲۶۶ headهای بعدی را پوشش نمی‌دهد.
9. اگر hash رکورد ۲۶۶ تغییر کرده باشد → `STOPPED_SAFE`.

اتصال آیندهٔ Audit و Reflex فقط با checkpoint صریح؛ فعلاً مستقل‌اند.
