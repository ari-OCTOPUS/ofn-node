"""اجرای آزمون‌ها بدون نیاز به pytest.  (با pytest هم می‌شود:  pytest -q )"""
import importlib
import inspect
import sys
import tempfile
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

MODULES = [
    "tests.test_manager",
    "tests.test_safety",
    "tests.test_registry",
    "tests.test_secrets",
    "tests.test_authz",
    "tests.test_smoke_real",
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
