"""اجرای آزمون‌ها بدون نیاز به pytest.  (با pytest هم می‌شود:  pytest -q )"""
import importlib
import inspect
import sys
import tempfile
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

MODULES = [
    # 2026-08-16 (R23 debt-sweep): هم‌سنکرو با مجموعهٔ واقعیِ امروز —
    # tests.test_secrets حذف شده بود (خطای import) و پنج ماژولِ نو هم
    # ثبت نشده بودند (command_registry/dashboard/governance/ledger/
    # octopus_bridge/shadow/ziman_rbac).
    "tests.test_manager",
    "tests.test_safety",
    "tests.test_registry",
    "tests.test_authz",
    "tests.test_smoke_real",
    "tests.test_command_registry",
    "tests.test_dashboard",
    "tests.test_governance",
    "tests.test_ledger",
    "tests.test_octopus_bridge",
    "tests.test_shadow",
    "tests.test_ziman_rbac",
]

passed = failed = 0
for mname in MODULES:
    m = importlib.import_module(mname)
    for name, fn in vars(m).items():
        if name.startswith("test_") and callable(fn):
            td = Path(tempfile.mkdtemp())
            try:
                fn(td) if inspect.signature(fn).parameters else fn()
                print(f"✅ PASS  {mname}.{name}")
                passed += 1
            except Exception:
                print(f"❌ FAIL  {mname}.{name}")
                traceback.print_exc()
                failed += 1

print(f"\nنتیجه: {passed} سبز، {failed} قرمز")
sys.exit(1 if failed else 0)
