#!/usr/bin/env python3
"""Patch api_budget.py: explicit provider mapping + multi-provider paid_call.

Run on node 138. Writes a pre-image backup, applies anchored replacements,
refuses to continue if any anchor is missing, then byte-compiles the result.
No credential value is read, written, printed or moved by this script.
"""
import hashlib
import pathlib
import py_compile
import shutil
import sys

TARGET = pathlib.Path("/home/ari/ofn/state/api-budget/api_budget.py")
BACKUP = pathlib.Path("/home/ari/ofn/state/api-budget/api_budget.py.pre-multiprovider-20260913")

src = TARGET.read_text(encoding="utf-8")
orig_sha = hashlib.sha256(src.encode()).hexdigest()
print("pre_image_sha256:", orig_sha[:24])

if BACKUP.exists():
    print("backup already exists, not overwriting:", BACKUP.name)
else:
    shutil.copy2(TARGET, BACKUP)
    print("backup written:", BACKUP.name, hashlib.sha256(BACKUP.read_bytes()).hexdigest()[:24])


def must_replace(old: str, new: str, label: str) -> None:
    global src
    if old not in src:
        print("ANCHOR_MISSING:", label)
        sys.exit(3)
    if src.count(old) != 1:
        print("ANCHOR_NOT_UNIQUE:", label, src.count(old))
        sys.exit(3)
    src = src.replace(old, new, 1)
    print("patched:", label)


# --- 1. import the explicit provider registry -------------------------------
must_replace(
    'VERSION = "octopus-api-budget-broker/1.0.0"',
    'VERSION = "octopus-api-budget-broker/1.1.0-multiprovider"\n'
    '\n'
    '# Explicit multi-provider registry (no first-match key scan).\n'
    '_HERE = Path(__file__).resolve().parent\n'
    'if str(_HERE) not in sys.path:\n'
    '    sys.path.insert(0, str(_HERE))\n'
    'import providers  # noqa: E402',
    "providers import",
)

# --- 2. provider-aware model resolution ------------------------------------
must_replace(
    'def c_model() -> str:\n'
    '    return (contract() or {}).get("model_allowlist", ["fugu"])[0]',
    'def c_model(provider: str | None = None) -> str:\n'
    '    """Contract allowlist wins for the default route; otherwise the\n'
    '    provider\'s own explicit model variable."""\n'
    '    if provider:\n'
    '        m = providers.model(provider)\n'
    '        if m:\n'
    '            return m\n'
    '    return (contract() or {}).get("model_allowlist", ["fugu"])[0]',
    "c_model",
)

# --- 3. load_key: explicit mapping, no first-match --------------------------
OLD_LOAD = '''def load_key() -> str:
    """Key never leaves this process (not returned by any API of this module
    except the internal one-shot runner)."""
    for l in SECRETS.read_text(encoding="utf-8").splitlines():
        m = re.match(r"(?:OFN_REMOTE_API_KEY|SAKANA_API_KEY|FUGU_API_KEY)=(.+)", l.strip())
        if m:
            return m.group(1).strip().strip('"')
    return ""'''
NEW_LOAD = '''def load_key(provider: str | None = None) -> str:
    """EXPLICIT provider -> variable mapping.

    This replaces the old first-match scan (defect F-2: a stale key sitting
    above a fresh one silently won). Keys never leave this process and are
    never returned by any public API of this module; the child process receives
    them over stdin, never in argv.
    """
    if provider:
        return providers._key(provider)
    for pid in providers.provider_ids():
        if providers.REGISTRY[pid]["paid"] and providers.enabled(pid) \\
                and providers._key(pid):
            return providers._key(pid)
    return ""'''
must_replace(OLD_LOAD, NEW_LOAD, "load_key")

# --- 4. reserve() records the real provider/model ---------------------------
must_replace(
    'def reserve(task_id: str, purpose: str, est_in_tok: int, max_out_tok: int,\n'
    '            route_reason: str, ctx_hash: str, now: float | None = None) -> dict:',
    'def reserve(task_id: str, purpose: str, est_in_tok: int, max_out_tok: int,\n'
    '            route_reason: str, ctx_hash: str = "", provider: str = "sakana-fugu",\n'
    '            model: str | None = None, now: float | None = None) -> dict:',
    "reserve signature",
)
must_replace(
    '                   "task_id": task_id, "purpose": purpose, "provider": "sakana-fugu",\n'
    '                   "model": c_model(), "route_reason": route_reason,',
    '                   "task_id": task_id, "purpose": purpose, "provider": provider,\n'
    '                   "model": model or c_model(), "route_reason": route_reason,',
    "reserve row provider",
)

# --- 5. paid_call: provider-aware, stdin key handoff ------------------------
must_replace(
    'def paid_call(task_id: str, purpose: str, prompt: str, est_in_tok: int = 1500,\n'
    '              max_out_tok: int = 700, first_call_cap: float | None = None) -> dict:',
    'def paid_call(task_id: str, purpose: str, prompt: str, est_in_tok: int = 1500,\n'
    '              max_out_tok: int = 700, first_call_cap: float | None = None,\n'
    '              provider: str | None = None, model: str | None = None) -> dict:',
    "paid_call signature",
)

START = '    r = reserve(task_id, purpose, est_in_tok, max_out_tok, "local-insufficient")'
END = ('        return {"ok": False, "error": "PROVIDER_UNAVAILABLE",\n'
       '                "detail": type(exc).__name__}\n')
if START not in src:
    print("ANCHOR_MISSING: paid_call body start")
    sys.exit(3)
if END not in src:
    print("ANCHOR_MISSING: paid_call body end")
    sys.exit(3)
i0 = src.index(START)
i1 = src.index(END) + len(END)
NEW_BODY = '''    if provider is None:
        provider = next((p for p in providers.provider_ids()
                         if providers.REGISTRY[p]["paid"] and providers.enabled(p)
                         and providers.key_present(p)), "")
    if not provider or not providers.key_present(provider):
        return {"ok": False, "error": "PAID_API_BLOCKED_PROVIDER_UNVERIFIED",
                "provider": provider}
    mdl = model or providers.model(provider)
    r = reserve(task_id, purpose, est_in_tok, max_out_tok, "local-insufficient",
                provider=provider, model=mdl)
    if not r.get("ok"):
        return r
    if first_call_cap is not None and r["est_max_usd"] > first_call_cap:
        return {"ok": False, "error": "FIRST_CALL_CAP",
                "est": r["est_max_usd"]}
    t0 = time.time()
    res = providers.call(provider, mdl, prompt, max_tokens=min(int(max_out_tok), 512),
                         timeout_s=180)
    if not res.get("ok"):
        # attempt consumed: reservation stays counted, no double bill
        settle(r["request_id"], 0, 0, round(time.time() - t0, 3),
               hashlib.sha256(str(res.get("error")).encode()).hexdigest(), False,
               "provider-error:" + str(res.get("error"))[:60])
        return {"ok": False, "error": "PROVIDER_UNAVAILABLE", "provider": provider,
                "detail": str(res.get("error"))[:80],
                "http_status": res.get("http_status")}
    _u = res.get("usage") or {}
    out = {"text": res.get("text", ""), "visible": int(_u.get("in", 0) or 0),
           "orch": int(_u.get("out", 0) or 0), "served": res.get("served"),
           "insufficient": not res.get("text")}
'''
src = src[:i0] + NEW_BODY + src[i1:]
print("patched: paid_call body")

must_replace(
    '    return {"ok": True, "request_id": r["request_id"], "text": out.get("text", ""),\n'
    '            "served_model": out.get("served"), "settle": s, "redaction_clean": redacted,\n'
    '            "executable": False}',
    '    return {"ok": True, "request_id": r["request_id"], "text": out.get("text", ""),\n'
    '            "provider": provider, "served_model": out.get("served"),\n'
    '            "settle": s, "redaction_clean": redacted, "executable": False}',
    "paid_call return provider",
)

# --- 6. canary helper: at most one call, capped per provider ----------------
src += '''

def canary(provider: str, prompt: str = "Reply with the single word: ok") -> dict:
    """At most ONE sanitized canary per provider, capped at
    OCTOPUS_API_CANARY_MAX_USD_PER_PROVIDER (default 0.25 USD).

    No repository content, no customer data, no secret is placed in the prompt.
    """
    cap = float(providers.env().get("OCTOPUS_API_CANARY_MAX_USD_PER_PROVIDER",
                                    "0.25") or 0.25)
    if not providers.enabled(provider):
        return {"ok": False, "error": "PROVIDER_NOT_ENABLED", "provider": provider}
    if not providers.key_present(provider):
        return {"ok": False, "error": "PROVIDER_NO_KEY", "provider": provider}
    return paid_call("canary-" + provider, "provider-canary", prompt,
                     est_in_tok=64, max_out_tok=16, first_call_cap=cap,
                     provider=provider)
'''

TARGET.write_text(src, encoding="utf-8")
new_sha = hashlib.sha256(TARGET.read_bytes()).hexdigest()
print("post_image_sha256:", new_sha[:24])
try:
    py_compile.compile(str(TARGET), doraise=True)
    print("py_compile: OK")
except py_compile.PyCompileError as exc:
    print("PY_COMPILE_FAILED:", exc)
    print("restoring pre-image")
    shutil.copy2(BACKUP, TARGET)
    sys.exit(4)
print("PATCH_OK")
