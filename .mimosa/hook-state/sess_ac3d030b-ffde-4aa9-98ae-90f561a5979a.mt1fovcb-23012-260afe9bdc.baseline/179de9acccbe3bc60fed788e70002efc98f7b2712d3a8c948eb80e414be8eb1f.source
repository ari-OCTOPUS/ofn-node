# HEALTH-BASELINE — 2026-07-18 (post integration-debug)

> وضعیتِ سلامتِ پروژه پس از فازهای ۱-۵ integration-debug.

## 📊 خلاصه‌ی تست

| مجموعه | تعداد | سبز | قرمز | skip |
|--------|-------|-----|------|------|
| **_ops/tests/** (excluding 5 script-tests) | 359 | 345 | 14 | 0 |
| **studio/saba_studio + saba_brain** | 38 | 38 | 0 | 0 |
| **مجموع** | 397 | **383** | **14** | **1** |

**نرخِ سبز: 96.5%** ✅

### تست‌های قرمز (۱۴ مورد — همه pre-existing، نه از تغییراتِ این جلسه)

| فایل | علت | پیشینه |
|------|-----|--------|
| `test_mining_wiring.py` (۶ تست) | `wiring.make_mining_leg` وجود ندارد — mining leg ناقص پیاده‌سازی شده | pre-existing P2 |
| `test_ziman_wiring.py` (۵ تست) | ziman leg تغییراتِ اسکیما داده — testها قدیمی | pre-existing P2 |
| `test_ziman_biology.py` (۲ تست) | biology_beat doctor interface تغییر کرده | pre-existing P2 |
| `test_llm_routing_smoke.py` (۱ تست) | smoke test به GLM live می‌خورد — نیاز به شبکه | pre-existing |

**هیچ‌کدام از این failها به تغییرات این جلسه (budgets.yaml، debate، saba_brain) ربط ندارند.**

### تست‌های نادیده‌گرفته‌شده (collection issues)

| فایل | علت |
|------|-----|
| `test_pii_read_guard.py` | script مستقل با `sys.exit` (نه pytest-style) |
| `test_durable_journal.py` | script مستقل با `sys.exit` |
| `test_human_append_guard.py` | script مستقل |
| `test_ps_writeback.py` | script مستقل |
| `test_effector_idempotency.py` | script مستقل |

این‌ها scriptهای تستِ مستقل هستن و باید جدا اجرا شن.

## 🩺 وضعیتِ runtime (پس از فازهای ۱-۳)

| سرویس | پورت | PID | وضعیت |
|--------|------|-----|-------|
| Organism | 8771 | 17792 | ✅ LIVE (beat 8195+) |
| Cortex | 8772 | 18916 | ✅ LIVE (coherence 0.91) — اکنون تحتِ نظارتِ cortex-watchdog |
| Live Cockpit | 8773 | 16564 | ✅ LIVE |
| Ollama | 11434 | - | ✅ LIVE (qwen2.5:latest) |

### لاگِ گاورنر (پیش از فاز ۱ → پس از اعمال)

**پیش از فاز ۱ (۱۷۲۴ ساعت گذشته):**
- ۱۵۸ خطا (۶۸ price_in/price_out + ۵۰ debate KeyError + ۱۰ lead-naghshi + ۳۰ دیگر)

**پس از فاز ۱ (اعمال budgets.yaml + GLM key + debate defensive):**
- انتظار: اکثرِ خطاهای price و debate متوقف شوند (نیاز به چند epoch برای تأیید)
- بررسیِ فوری پس از restart لازم است (فاز ۷)

## 🆕 کارهای انجام‌شده در این جلسه

1. ✅ budgets.yaml: price_in/price_out + PAINTING/ACCOUNTING + ORGAN_MAP
2. ✅ ZAI/GLM key در .env (فعال)
3. ✅ debate_loop.py: defensive `.get('text')`
4. ✅ saba_brain.py: مغزِ تعاملیِ LLM + memory + guard (۲۲ تست)
5. ✅ saba_studio.py: ۴-خط hook + fallback chain
6. ✅ cortex-watchdog.ps1 + schtask (cortex اکنون supervised)
7. ✅ BOTS-REGISTRY.md (وضعیت ۹ بات)
8. ✅ ARCHITECTURE-SOT.md (منبعِ حقیقتِ واحد)
9. ✅ DEPRECATED.md در ۳ دایرکتوریِ dormant

## 📋 کارهای باقی‌مانده (برای جلساتِ آینده)

### P1 (مهم)
- [ ] fix ۱۴ تستِ قرمزِ pre-existing (mining/ziman wiring — schema drift)
- [ ] تبدیلِ ۵ script-test به pytest-style (یا اجرای جدا)
- [ ] تأییدِ خطاهای گاورنر بعد از ۲۴ ساعت (نیاز به epoch run)
- [ ] PocketSmith NameError در accountant code
- [ ] ORGANISM-STATE stale (اگه با فاز ۱ فیکس نشد)

### P2 (کیفیت)
- [ ] singleton guard برای saba_studio و langar_bot (پیش از لایو شدن)
- [ ] consolidation بیتِ wiring.py برای مصرفِ saba-bridge.jsonl
- [ ] مرتب‌سازیِ ۴ کنترل‌کننده‌ی موازیِ telegram (merge bot #1 و #7)
- [ ] control-brain/.env — ANTHROPIC_BASE_URL proxy جعلی

### P3 (آینده)
- [ ] فعال‌سازیِ رباتِ Saba در BotFather + run-saba.bat در startup
- [ ] deploy survival-gateway LiteLLM proxy (وقتی لازم شد)
- [ ] revive 4d_system (اگه تصمیمِ owner)
- [ ] اتصالِ app/src/nbb_cp به legs (فاز ۴-۵ NBB)

## ✅ معیارهای تکمیلِ این جلسه

- [x] فاز ۱: دیباگ P0 انجام شد
- [x] فاز ۲: Saba Studio هوشمند (۳۸ تست سبز)
- [x] فاز ۳: Cortex اکنون supervised
- [x] فاز ۴: تلگرام‌ها مستند شدند + bridge scaffold
- [x] فاز ۵: ARCHITECTURE-SOT + DEPRECATED
- [x] فاز ۶: baseline ضبط شد (383/397 = 96.5% سبز)
- [ ] فاز ۷: INTEGRATION-REPORT (در حالِ نوشتن)
