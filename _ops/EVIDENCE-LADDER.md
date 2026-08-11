# EVIDENCE-LADDER — سلسله‌مراتب ادعای قابلیت

> هر ادعای «می‌توانم X» باید سطح شاهد داشته باشد. ارتقا بدون شاهد ممنوع.

## سطوح

| سطح | معنی | نمونه |
|---|---|---|
| **STRUCTURAL** | کد موجود است، خوانده می‌شود، ولی هیچ شاهدِ اجرا | `dark_capabilities.py: DARK` |
| **TESTED** | تست offline/mock سبز؛ SUT واقعی به‌کار taken شده | `test_ti_router_snapshot: 8/8` |
| **SHADOW** | در سایه روی داده/پروسهٔ واقعی اجرا شده، بدون اثر خارجی | `collab_sim.run_simulation` |
| **ARMED** | فلگ روشن، در مسیر زنده فعال، شاهدِ restart خوانده | نیازمند arm + boot snapshot |

## وضعیت فعلی قابلیت‌های کلیدی

| قابلیت | سطح | شاهد | مسیر |
|---|---|---|---|
| **model_router three-tier** | TESTED | `test_ti_router_snapshot: 8/8` | `cortex/model_router.py` |
| **circuit_breaker** | TESTED | `test_ti_breaker_chaos: 10/10` | `budget/circuit_breaker.py` |
| **fugu_quota** | TESTED | `test_paid_timeout_chain: 60/60` | `cortex/fugu_quota.py` |
| **kill_seam** | TESTED | `test_kill_seam_wire: 8/8` | `budget/opslib.py` |
| **collaborator** | TESTED | `test_ti_collab_security: 12/12` + `test_api_collab: 17/17` | `owner_console/collaborator.py` |
| **collab_memory** | TESTED | `test_collab_components: 23/23` | `owner_console/collab_memory.py` |
| **context_bundle** | TESTED | `test_ti_context_bundle_contract: 13/13` | `context_bundle.py` |
| **control_contracts** | TESTED | `test_control_contracts_v2: 10/10` | `control_contracts.py` |
| **outbound_https** | TESTED | `test_outbound_https: 14/14` + `test_outbound_https_approval_port: 18/18` | `integrations/outbound_https.py` |
| **approval_store** | TESTED | `test_tg_approval_store: 17/17` | `telegram_center/approval_store.py` |
| **MiniApp gateway** | TESTED | `test_miniapp_cockpit_ui: 11/11` + `test_miniapp_lifecycle_view: 16/16` | `telegram_center/miniapp_gateway.py` |
| **dark_capabilities** | STRUCTURAL | `test_dark_capabilities: 18/18` (scanner logic) | `dark_capabilities.py` |
| **discovery** | TESTED | `test_ti_discovery_eval: 9/9` | `test_intelligence/discovery.py` |
| **policy_oracle** | TESTED | `test_ti_policy_oracle: 9/9` | `test_intelligence/policy_oracle.py` |
| **red-team injection** | TESTED | `test_ti_redteam_injection: 3/3 (25/25 cases)` | `test_intelligence/redteam_cases.yaml` |

## قواعد ارتقا

1. **STRUCTURAL → TESTED**: تست offline سبز با SUT واقعی
2. **TESTED → SHADOW**: اجرا در سایه روی دادهٔ واقعی، ۷ روز بدون حادثه
3. **SHADOW → ARMED**: فلگ روشن + boot snapshot تأیید + restart موفق

## ممنوع

- ادعای ARMED بدون boot snapshot
- ادعای SHADOW بدون ۷ روز شاهد
- ارتقای سطح بدون مستند در این جدول
