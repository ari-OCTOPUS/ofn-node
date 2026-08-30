#!/usr/bin/env python3
"""
test_igk_integration.py — اتصالِ orchestrator به IGK (فاز ۲).
اثبات می‌کند enforcement از cooperative به external/fail-closed منتقل شده:
  ۱) مسیرِ سالم با IGK به finalize می‌رسد.
  ۲) STOPِ بیرونی اجرا را fail-closed متوقف می‌کند (finalize نمی‌شود).
  ۳) با GROUNDING_REQUIRED، خروجیِ بی‌لنگر finalize نمی‌شود.
اجرا:  python test_igk_integration.py
"""
import os, sys, json, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from src.orchestrator import Orchestrator

results = []
def check(n, c): results.append((n, c)); print(f"  {'✅' if c else '❌'} {n}")

def fresh():
    d = tempfile.mkdtemp(prefix="igk_int_")
    config.IGK_STATE_DIR = os.path.join(d, "igk_state")
    config.STOP_FILE = os.path.join(d, "STOP")
    config.AUDIT_LOG_PATH = os.path.join(d, "audit.jsonl")
    os.makedirs(config.IGK_STATE_DIR, exist_ok=True)
    return d

# ۱) مسیرِ سالم
fresh()
r = Orchestrator(hitl_approver=lambda a, c: True, use_igk=True).run("اثر هوش مصنوعی بر بازار کار ۲۰۲۶")
check("۱: مسیرِ سالم با IGK به finalize می‌رسد", r["status"] == "finalized")

# ۲) STOPِ بیرونی → fail-closed
fresh()
open(config.STOP_FILE, "w").close()      # انسان از بیرون STOP می‌سازد
r = Orchestrator(hitl_approver=lambda a, c: True, use_igk=True).run("هر موضوعی")
check("۲: STOPِ بیرونی اجرا را fail-closed متوقف می‌کند",
      r["status"] == "halted" and r.get("interrupted") is True)

# ۳) GROUNDING_REQUIRED + held-outِ ناسازگار → halt پیش از finalize
fresh()
json.dump({"facts": [{"subject": "پایتخت استرالیا", "value": "کانبرا"}]},
          open(os.path.join(config.IGK_STATE_DIR, "held_out.json"), "w", encoding="utf-8"),
          ensure_ascii=False)
config.GROUNDING_REQUIRED = True
r = Orchestrator(hitl_approver=lambda a, c: True, use_igk=True).run("هر موضوعی")
check("۳: با GROUNDING_REQUIRED خروجیِ بی‌لنگر finalize نمی‌شود", r["status"] == "halted")
config.GROUNDING_REQUIRED = False

print("\n" + "=" * 50)
ok = sum(1 for _, c in results if c)
print(f"نتیجه: {ok}/{len(results)} سبز")
sys.exit(0 if ok == len(results) else 1)
