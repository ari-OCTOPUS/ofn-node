"""
test_redteam.py — تست‌های ابطال: هر تست تلاشِ دورزدنِ کرنل را می‌گیرد و باید
آن تلاش شکست بخورد. (red-team بیرونی، نه نوشتنِ Critic.)
"""
import sys, os, json, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from client import KernelClient, ActuationGate, PermitDenied

PASS, FAIL = "✅", "❌"
results = []

def check(name, cond):
    results.append((name, cond))
    print(f"  {PASS if cond else FAIL} {name}")

def fresh_state():
    d = tempfile.mkdtemp(prefix="igk_")
    shutil.copy(os.path.join(os.path.dirname(__file__), "held_out.json"),
                os.path.join(d, "held_out.json"))
    return d

# ---------- ۰) مسیرِ سالم: permit→consume→act کار می‌کند ----------
d = fresh_state(); k = KernelClient(d)
gate = ActuationGate(k, "researcher")
out = gate.act("web_search", lambda: "نتیجه")
check("۰: مسیرِ مجاز (با permit) اجرا می‌شود", out == "نتیجه")
check("۰: audit پس از actuation سالم verify می‌شود", k.verify().get("ok") is True)

# ---------- ۱) جعلِ audit بدون کلید → باید لو برود ----------
ap = os.path.join(d, "audit.jsonl")
with open(ap, "a", encoding="utf-8") as f:
    f.write(json.dumps({"seq": 999, "ts": 0, "event": "fake_finalize",
                        "actor": "rogue", "data": {}, "prev": "X",
                        "sig": "deadbeef"}, ensure_ascii=False) + "\n")
v = k.verify()
check("۱: ورودیِ جعلیِ audit (بدونِ کلید) رد می‌شود", v.get("ok") is False)
k.close()

# ---------- ۲) kill-switch بیرونی: STOP → fail-closed ----------
d2 = fresh_state(); k2 = KernelClient(d2)
open(os.path.join(d2, "STOP"), "w").close()   # انسان از بیرون STOP می‌سازد
gate2 = ActuationGate(k2, "researcher")
blocked = False
try:
    gate2.act("web_search", lambda: "نباید اجرا شود")
except PermitDenied:
    blocked = True
check("۲: با STOP، actuation fail-closed می‌شود (permit رد)", blocked)

# ---------- ۳) permitِ جعلی → consume رد می‌کند ----------
forged = {"action": "finalize", "actor": "rogue", "nonce": "x", "exp": 9999999999, "sig": "00"}
c = k2.consume(forged)
check("۳: permitِ جعلی در consume رد می‌شود", c.get("ok") is False)

# ---------- ۴) هیچ verbـی برای تغییرِ کلید/invariant نیست ----------
r = k2._call(verb="set_key", key="hack")
r2 = k2._call(verb="set_invariant", name="human_above", value="off")
check("۴: verbـی برای دستکاریِ کلید/invariant وجود ندارد",
      r.get("ok") is False and r2.get("ok") is False)
k2.close()

# ---------- ۵) grounding: ادعای بی‌لنگر مکانیکاً رد می‌شود ----------
d3 = fresh_state(); k3 = KernelClient(d3)
g_bad = k3.ground(["پایتخت استرالیا سیدنی است و جمعیت بسیار زیاد دارد"], "researcher")
g_ok = k3.ground(["پایتخت استرالیا کانبرا است"], "researcher")
check("۵الف: ادعای ناسازگار با held-out رد می‌شود", g_bad.get("ok") is False)
check("۵ب: ادعای سازگار با held-out پذیرفته می‌شود", g_ok.get("ok") is True)
k3.close()

print("\n" + "=" * 50)
ok = sum(1 for _, c in results if c)
print(f"نتیجه: {ok}/{len(results)} سبز")
sys.exit(0 if ok == len(results) else 1)
