import sys, traceback
sys.path.insert(0, r"F:\backup\03 - Projects\research-spec-compiler\body_bridge")
sys.path.insert(0, r"F:\backup\03 - Projects\research-spec-compiler\body_bridge\tests")

import adr_feed
import test_adr_feed

results = []
for attr in sorted(dir(test_adr_feed)):
    if attr.startswith("test_"):
        fn = getattr(test_adr_feed, attr)
        try:
            fn()
            results.append((attr, "PASS", None))
            print(f"PASS: {attr}")
        except Exception as e:
            results.append((attr, "FAIL", str(e)))
            print(f"FAIL: {attr}: {e}")
            traceback.print_exc()

passed = sum(1 for _, status, _ in results if status == "PASS")
failed = sum(1 for _, status, _ in results if status == "FAIL")
print(f"=== {passed} passed, {failed} failed ===")
