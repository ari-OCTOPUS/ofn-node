#!/usr/bin/env python3
"""patch_freedom_broker.py — GOV-FREEDOM-V2 section 6 on the broker.

Adds providers.select(need) and api_budget.critique(): a SECOND, different
healthy provider reviews a multi-file patch. One capped call, inside the
3-calls-per-task budget, credential never exposed.
"""
import hashlib
import pathlib
import py_compile
import shutil
import sys

PROV = pathlib.Path("/home/ari/ofn/state/api-budget/providers.py")
API = pathlib.Path("/home/ari/ofn/state/api-budget/api_budget.py")
BP = PROV.with_suffix(".py.pre-freedom-v2-20260913")
BA = API.with_suffix(".py.pre-freedom-v2-20260913")

p = PROV.read_text(encoding="utf-8")
print("providers pre_image:", hashlib.sha256(p.encode()).hexdigest()[:24])
if "def select(" not in p:
    SEL = '''

# GOV-FREEDOM-V2 section 6: need-aware, health-aware provider choice.
def select(need: str = "standard") -> str:
    """Pick a live provider by need. Never returns a credential."""
    c = candidates()
    if not c:
        return ""
    pref = {"patch": ("deepseek", "openai", "anthropic", "gemini"),
            "quick": ("gemini", "deepseek", "openai", "anthropic"),
            "strong": ("openai", "anthropic", "deepseek", "gemini"),
            "review": ("anthropic", "openai", "deepseek", "gemini")}.get(need, ())
    for pid in pref:
        if pid in c:
            return pid
    return c[0]
'''
    anchor = "\ndef redacted_status() -> dict:"
    if anchor not in p:
        print("ANCHOR_MISSING providers select")
        sys.exit(3)
    p = p.replace(anchor, SEL + anchor, 1)
    if not BP.exists():
        shutil.copy2(PROV, BP)
    PROV.write_text(p, encoding="utf-8")
    py_compile.compile(str(PROV), doraise=True)
    print("providers select() added")

a = API.read_text(encoding="utf-8")
print("api_budget pre_image:", hashlib.sha256(a.encode()).hexdigest()[:24])
if "def critique(" not in a:
    CRIT = '''

def critique(content: str, exclude: str | None = None, task_id: str | None = None) -> dict:
    """GOV-FREEDOM-V2 section 6: a SECOND, different healthy provider reviews a
    patch document. Exactly one capped call; counts toward the 3-calls-per-task
    budget; the credential never leaves the broker and the content is
    pattern-screened like any prompt."""
    tid = task_id or ("critique-" + uuid.uuid4().hex[:10])
    cands = [p for p in providers.candidates() if p != exclude]
    if not cands:
        return {"ok": False, "error": "NO_SECOND_PROVIDER"}
    pid = providers.select("review") if providers.select("review") in cands else cands[0]
    prompt = ("You are an independent reviewer of a code patch document. "
              "Reply with exactly one word first: ACCEPT or REJECT. "
              "Then one short reason line. REJECT anything unsafe, secret-touching, "
              "TCB-touching or destructive. Document:\\n" + content[:4000])
    r = paid_call(tid, "second-model-critique", prompt, est_in_tok=1200,
                  max_out_tok=64, first_call_cap=0.25, provider=pid)
    if not r.get("ok"):
        return {"ok": False, "provider": pid, "error": str(r.get("error"))[:60]}
    head = (r.get("text") or "").upper()[:40]
    verdict = "REJECT" if "REJECT" in head else "ACCEPT"
    return {"ok": True, "provider": pid, "verdict": verdict,
            "cost_usd": (r.get("settle") or {}).get("cost_usd")}
'''
    if not BA.exists():
        shutil.copy2(API, BA)
    API.write_text(a + CRIT, encoding="utf-8")
    py_compile.compile(str(API), doraise=True)
    print("api_budget critique() added")

print("post: providers=%s api=%s" % (
    hashlib.sha256(PROV.read_bytes()).hexdigest()[:24],
    hashlib.sha256(API.read_bytes()).hexdigest()[:24]))
print("PATCH_BROKER_OK")
