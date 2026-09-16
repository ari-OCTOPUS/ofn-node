# 06-TRUTH-VERIFIER — Truth Layer + Verifier (2026-08-12)

## ماژول: `_ops/cognitive/truth_layer.py`

### Claim Object
```json
{
  "claim_id": "claim_<uuid12>",
  "text": "BCM exists in this repo",
  "source": "_ops/neural/bcm.py",
  "locator": "_ops/neural/bcm.py",
  "confidence": 0.99,
  "evidence_refs": ["_ops/neural/bcm.py", "tests/test_bcm_forgetting.py"],
  "verification": "VERIFIED",
  "runtime_verified": true,
  "may_authorize": false
}
```

### Verification States
```
UNVERIFIED → REPORTED → VERIFIED | CONFLICT | STALE | REJECTED
```

### Verifier Logic
1. `VERIFIED`: حداقل یک evidence_ref واقعاً در دیسک وجود دارد (فایل یا تست)
2. `REPORTED`: source/locator داده شده ولی فایل پیدا نشده
3. `UNVERIFIED`: هیچ evidence_ref نیست
4. `CONFLICT`: (آینده) چند source متناقض

### Integration
- `equation_explainer.explain()` → truth_layer برای هر معادله evidence_refs را verify می‌کند
- خروجی: `runtime_verified` + `verification` در equation object

### نتایج زنده

| معادله | evidence | verification |
|--------|----------|-------------|
| BCM | `_ops/neural/bcm.py` | **VERIFIED** ✅ |
| σ legacy | `_ops/doctor/spectral.py` | **VERIFIED** ✅ |
| Pain | `_ops/neural/nociceptor.py` | **VERIFIED** ✅ |
| SOG | `_ops/heart/sog_math.py` | **VERIFIED** ✅ |
| Living-Beat | `_ops/heart/control_law.py` | **VERIFIED** ✅ |
| Chrono Rhythm | `_ops/chrono_rhythm/rhythm.py` | **VERIFIED** ✅ |

### قواعد
- مدل حق ندارد از متن خودش برای اثبات موفقیت خودش استفاده کند
- `VERIFIED` فقط با file/test evidence خارجی
- `applied=true` فقط با EXECUTION_RECEIPT
- may_authorize همیشه false
