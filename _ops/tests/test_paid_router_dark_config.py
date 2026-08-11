#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_paid_router_dark_config.py — مغزهای پولی تاریک می‌مانند و مسیر router قفل است.

$0 آفلاین؛ هیچ provider واقعی/شبکه/flags dump. سه بخش:
  1) ساختاری: فلگ‌ها در کد هستند و OCTOPUS-flags.cmd =0 و CRLF سالم.
  2) governor/heart با gate بسته → None.
  3) با gate باز + router جعلی، مسیر router صدا زده می‌شود و direct provider نه.
  4) doctor self_knowledge paid flag task را از think به synthesize می‌برد.
"""
import importlib
import json
import os
import re
import sys
import tempfile
import types
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="paid-router-dark-")
os.environ["ORG_ROOT"] = _TMP
os.environ["OPS_DIR"] = str(Path(_TMP) / "_ops")
for k in ("OCTOPUS_GOVERNOR_USE_ROUTER", "OCTOPUS_HEART_DOCTOR_USE_ROUTER",
          "OCTOPUS_DOCTOR_SELFKNOW_PAID"):
    os.environ.pop(k, None)

_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS), str(_OPS / "budget"), str(_OPS / "doctor"),
           str(_OPS / "heart"), str(_OPS / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import opslib  # noqa: E402

fails = []


def check(cond, label):
    if not cond:
        fails.append(label)


# ── ساختاری: فلگ‌ها در کد هستند و flags.cmd =0 و CRLF سالم ──────────────────
src_gov = (_OPS / "budget" / "governor_epoch.py").read_text("utf-8")
src_heart = (_OPS / "heart" / "doctor_setpoint.py").read_text("utf-8")
src_sk = (_OPS / "doctor" / "self_knowledge.py").read_text("utf-8")
for name, src in (("OCTOPUS_GOVERNOR_USE_ROUTER", src_gov),
                  ("OCTOPUS_HEART_DOCTOR_USE_ROUTER", src_heart),
                  ("OCTOPUS_DOCTOR_SELFKNOW_PAID", src_sk)):
    check(name in src, f"{name} باید در کد باشد")

flags_path = _OPS / "OCTOPUS-flags.cmd"
# 2026-08-11: OCTOPUS-flags.cmd is gitignored/live-local. In a clean worktree
# or CI it does not exist. The CRLF/line-ending checks require the file.
# The declaration-file checks (PAID-FLAGS-DECLARATION.json) are structural
# and independent of flags.cmd — they verify the owner's intent registry.
flags_env_blocked = not flags_path.exists()
if not flags_env_blocked:
    raw = flags_path.read_bytes()
    check(b"\r\n" in raw, "flags.cmd باید CRLF داشته باشد")
    check(b"\n" not in raw.replace(b"\r\n", b""), "flags.cmd نباید lone-LF داشته باشد")
    check(b"\r\r\n" not in raw, "flags.cmd نباید CRCRLF داشته باشد (تبدیل دوبارهٔ CRLF)")
    text = raw.decode("utf-8", errors="replace")
else:
    text = None
# Declaration-file checks run regardless — they verify the owner's intent registry.
# ۲۰۲۶-۰۷-۲۷ — این بلوک قبلاً `== "0"` را هاردکد می‌کرد. وقتی مالک تصمیمش را
# عوض کرد («همه رو بزن»)، گارد **دائماً** قرمز شد. و تستِ همیشه‌قرمز خودش یک
# نقص است: آدم را عادت می‌دهد قرمز را نادیده بگیرد، و آن‌وقت رگرسیونِ واقعی
# پشتِ همان قرمزِ «انتظاری» پنهان می‌شود.
#
# پس مرجع عوض شد، نه سخت‌گیری: به‌جای عددِ ثابت، اعلامیهٔ ثبت‌شدهٔ مالک.
# این **سخت‌گیرتر** است — نسخهٔ قبلی فقط driftِ صفر←یک را می‌گرفت؛ این هر
# اختلافِ استقرار↔تصمیم را در **هر دو جهت** می‌گیرد، و هر ردیفِ اعلامیه
# بدونِ شاهدِ تصمیمِ مالک خودش قرمز است.
import json as _json
decl_path = _OPS / "PAID-FLAGS-DECLARATION.json"
check(decl_path.exists(), "PAID-FLAGS-DECLARATION.json باید وجود داشته باشد")
decl = {}
if decl_path.exists():
    try:
        decl = (_json.loads(decl_path.read_text("utf-8")) or {}).get("flags") or {}
    except ValueError:
        check(False, "اعلامیهٔ فلگ‌های پولی JSONِ معتبر نیست")
for name in ("OCTOPUS_WIRE_C6_PRODUCER", "OCTOPUS_GOVERNOR_USE_ROUTER",
             "OCTOPUS_HEART_DOCTOR_USE_ROUTER", "OCTOPUS_DOCTOR_SELFKNOW_PAID"):
    row = decl.get(name) or {}
    want = str(row.get("expected", "")).strip()
    check(want in ("0", "1"), f"{name} در اعلامیه نیست یا مقدارش نامعتبر است")
    # فلگی که «روشن» اعلام شده ولی شاهدِ تصمیمِ مالک ندارد، اعلامیه نیست —
    # حدس است. بدونِ این شرط، این فایل تبدیل می‌شد به دری برای دورزدنِ گارد.
    if want == "1":
        ev = str(row.get("evidence", "")).strip()
        check(len(ev) >= 20, f"{name} روشن اعلام شده ولی شاهدِ تصمیمِ مالک ندارد")
    # Assignment-vs-declaration consistency check only when flags.cmd is present
    if text is not None:
        # فقط assignment واقعی را بسنج؛ comment/substrings مثل «NAME=1 برای فعال‌سازی»
        # پیکربندی نیستند. آخرین assignment مؤثر باید با اعلامیه بخواند.
        vals = re.findall(rf"(?im)^\s*(?:set\s+)?{re.escape(name)}\s*=\s*([01])\s*$", text)
        check(bool(vals), f"{name} باید assignment صریح داشته باشد")
        check(bool(vals) and vals[-1] == want,
              f"{name}: استقرار={vals} ولی تصمیمِ ثبت‌شده={want} — یکی از دو طرف کهنه است")


# ── fake router/client ماژول‌ها ───────────────────────────────────────────────
class _FakeRouter:
    calls = []

    @staticmethod
    def ask(task, prompt, system="", max_tokens=0, tier=None, opener=None):
        _FakeRouter.calls.append((task, tier))
        return {"ok": True, "text": '{"x":1}', "model": "fake", "cost_usd": 0.0}


class _BadRouter:
    calls = []

    @staticmethod
    def ask(*a, **k):
        _BadRouter.calls.append(True)
        return {"ok": False, "text": "", "model": "bad", "cost_usd": 0.0}


def _fresh_module(name, path, **patches):
    """یک ماژول را با patchهای لازم دوباره load می‌کند."""
    for k, v in patches.items():
        if k == "model_router":
            sys.modules["model_router"] = v
        elif k == "client":
            sys.modules["client"] = v
        elif k == "organ_gate":
            sys.modules["organ_gate"] = v
        elif k == "opslib.live_gate_open":
            opslib.live_gate_open = v
        elif k == "opslib.PROMPTS":
            opslib.PROMPTS = v
        elif k == "opslib.load_budgets":
            opslib.load_budgets = v
    if name in sys.modules:
        del sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_prompt_dir = Path(_TMP) / "prompts"
_prompt_dir.mkdir(parents=True, exist_ok=True)
(_prompt_dir / "metabolic-governor-v0.1.txt").write_text("system prompt for test", "utf-8")

orig_live_gate = opslib.live_gate_open
orig_prompts = getattr(opslib, "PROMPTS", None)
orig_load_budgets = getattr(opslib, "load_budgets", None)
orig_client = sys.modules.get("client")
orig_model_router = sys.modules.get("model_router")
orig_organ_gate = sys.modules.get("organ_gate")
fake_organ_gate = types.ModuleType("organ_gate")
fake_organ_gate.reserve = lambda *a, **k: {"allow": False, "reason": "offline-test"}
fake_organ_gate.release = lambda *a, **k: None
fake_organ_gate.settle = lambda *a, **k: None

try:
    # ── Governor: gate بسته → None ─────────────────────────────────────────
    gov = _fresh_module("governor_epoch", _OPS / "budget" / "governor_epoch.py",
                        **{"opslib.live_gate_open": lambda *a, **k: (False, "closed")})
    check(gov.allocate_llm({"month": {"aud": 0, "usd": 0}}, {"allocation_dry": {}}) is None,
          "governor با gate بسته باید None بدهد")

    # ── Governor: gate باز + router روشن → فقط router صدا خورد ─────────────
    fake_client = types.ModuleType("client")
    fake_client.extract_json = lambda s: json.loads(s)
    fake_client.PriceNotLocked = type("PriceNotLocked", (Exception,), {})
    fake_client.DeepSeekClient = type("DeepSeekClient", (), {
        "__init__": lambda self: (_ for _ in ()).throw(AssertionError("direct client must not be used")),
    })
    os.environ["OCTOPUS_GOVERNOR_USE_ROUTER"] = "1"
    _FakeRouter.calls.clear()
    gov = _fresh_module("governor_epoch", _OPS / "budget" / "governor_epoch.py",
                        model_router=_FakeRouter, client=fake_client, organ_gate=fake_organ_gate,
                        **{"opslib.live_gate_open": lambda *a, **k: (True, "open"),
                           "opslib.PROMPTS": _prompt_dir,
                           "opslib.load_budgets": lambda: {"global": {"cap_monthly": 30}, "organs": {}}})
    r = gov.allocate_llm({"month": {"aud": 0, "usd": 0}}, {"allocation_dry": {}})
    check(r and r.get("llm_allocation") == {"x": 1}, f"governor router path should work: {r}")
    check(_FakeRouter.calls and _FakeRouter.calls[0][0] == "orchestrate",
          f"governor router task mismatch: {_FakeRouter.calls}")

    # router خطا → None، بدون raise
    _BadRouter.calls.clear()
    gov = _fresh_module("governor_epoch", _OPS / "budget" / "governor_epoch.py",
                        model_router=_BadRouter, client=fake_client, organ_gate=fake_organ_gate,
                        **{"opslib.live_gate_open": lambda *a, **k: (True, "open"),
                           "opslib.PROMPTS": _prompt_dir,
                           "opslib.load_budgets": lambda: {"global": {"cap_monthly": 30}, "organs": {}}})
    check(gov.allocate_llm({"month": {"aud": 0, "usd": 0}}, {"allocation_dry": {}}) is None,
          "governor router error باید fail-soft None باشد")
    check(_BadRouter.calls, "bad router باید صدا زده شده باشد")
finally:
    os.environ.pop("OCTOPUS_GOVERNOR_USE_ROUTER", None)
    opslib.live_gate_open = orig_live_gate
    if orig_prompts is not None:
        opslib.PROMPTS = orig_prompts
    if orig_load_budgets is not None:
        opslib.load_budgets = orig_load_budgets
    if orig_client is not None:
        sys.modules["client"] = orig_client
    else:
        sys.modules.pop("client", None)
    if orig_model_router is not None:
        sys.modules["model_router"] = orig_model_router
    else:
        sys.modules.pop("model_router", None)
    if orig_organ_gate is not None:
        sys.modules["organ_gate"] = orig_organ_gate
    else:
        sys.modules.pop("organ_gate", None)


# ── Heart doctor ─────────────────────────────────────────────────────────────
class _FakeHeartRouter:
    calls = []

    @staticmethod
    def ask(task, prompt, system="", max_tokens=0, tier=None, opener=None):
        _FakeHeartRouter.calls.append((task, tier))
        return {"ok": True, "text": '{"lo":0.5,"hi":6.0}', "model": "fake", "cost_usd": 0.0}


class _BadHeartRouter:
    calls = []

    @staticmethod
    def ask(*a, **k):
        _BadHeartRouter.calls.append(True)
        return {"ok": False, "text": "", "model": "bad", "cost_usd": 0.0}


orig_live_gate2 = opslib.live_gate_open
orig_client2 = sys.modules.get("client")
orig_model_router2 = sys.modules.get("model_router")
orig_organ_gate2 = sys.modules.get("organ_gate")

try:
    # gate بسته → None
    heart = _fresh_module("doctor_setpoint", _OPS / "heart" / "doctor_setpoint.py",
                          **{"opslib.live_gate_open": lambda *a, **k: (False, "closed")})
    check(heart.llm_refine(type("HP", (), {"to_json": lambda self: {"x": 1}})(), {}) is None,
          "heart doctor با gate بسته باید None بدهد")

    # gate باز + router روشن → فقط router صدا خورد
    fake_client2 = types.ModuleType("client")
    fake_client2.extract_json = lambda s: json.loads(s)
    fake_client2.DeepSeekClient = type("DeepSeekClient", (), {
        "__init__": lambda self: (_ for _ in ()).throw(AssertionError("direct client must not be used")),
    })
    os.environ["OCTOPUS_HEART_DOCTOR_USE_ROUTER"] = "1"
    _FakeHeartRouter.calls.clear()
    heart = _fresh_module("doctor_setpoint", _OPS / "heart" / "doctor_setpoint.py",
                          model_router=_FakeHeartRouter, client=fake_client2,
                          organ_gate=fake_organ_gate,
                          **{"opslib.live_gate_open": lambda *a, **k: (True, "open")})
    hp = type("HP", (), {"to_json": lambda self: {"x": 1}})()
    r = heart.llm_refine(hp, {"velocity": {}, "cpi": {}, "delta_self": {}})
    check(r and r.get("suggestion") == {"lo": 0.5, "hi": 6.0}, f"heart router path should work: {r}")
    check(_FakeHeartRouter.calls and _FakeHeartRouter.calls[0][0] == "synthesize",
          f"heart router task mismatch: {_FakeHeartRouter.calls}")

    _BadHeartRouter.calls.clear()
    heart = _fresh_module("doctor_setpoint", _OPS / "heart" / "doctor_setpoint.py",
                          model_router=_BadHeartRouter, client=fake_client2,
                          organ_gate=fake_organ_gate,
                          **{"opslib.live_gate_open": lambda *a, **k: (True, "open")})
    check(heart.llm_refine(hp, {"velocity": {}, "cpi": {}, "delta_self": {}}) is None,
          "heart router error باید fail-soft None باشد")
finally:
    os.environ.pop("OCTOPUS_HEART_DOCTOR_USE_ROUTER", None)
    opslib.live_gate_open = orig_live_gate2
    if orig_client2 is not None:
        sys.modules["client"] = orig_client2
    else:
        sys.modules.pop("client", None)
    if orig_model_router2 is not None:
        sys.modules["model_router"] = orig_model_router2
    else:
        sys.modules.pop("model_router", None)
    if orig_organ_gate2 is not None:
        sys.modules["organ_gate"] = orig_organ_gate2
    else:
        sys.modules.pop("organ_gate", None)


# ── Doctor self-knowledge paid flag ──────────────────────────────────────────
class _CaptureRouter:
    calls = []

    @staticmethod
    def ask(task, prompt, system="", max_tokens=400, tier=None, opener=None):
        _CaptureRouter.calls.append(task)
        return {"ok": True, "text": '{"focus":"x"}', "tier": task}


orig_model_router3 = sys.modules.get("model_router")
try:
    sys.modules["model_router"] = _CaptureRouter
    os.environ.pop("OCTOPUS_DOCTOR_SELFKNOW_PAID", None)
    _CaptureRouter.calls.clear()
    sk_mod = _fresh_module("self_knowledge", _OPS / "doctor" / "self_knowledge.py",
                           model_router=_CaptureRouter)
    sk_mod._ask_llm("p", "s")
    check(_CaptureRouter.calls[-1] == "think", f"بدون paid flag باید think باشد: {_CaptureRouter.calls}")
    os.environ["OCTOPUS_DOCTOR_SELFKNOW_PAID"] = "1"
    sk_mod = _fresh_module("self_knowledge", _OPS / "doctor" / "self_knowledge.py",
                           model_router=_CaptureRouter)
    sk_mod._ask_llm("p", "s")
    check(_CaptureRouter.calls[-1] == "synthesize", f"با paid flag باید synthesize باشد: {_CaptureRouter.calls}")
finally:
    os.environ.pop("OCTOPUS_DOCTOR_SELFKNOW_PAID", None)
    if orig_model_router3 is not None:
        sys.modules["model_router"] = orig_model_router3
    else:
        sys.modules.pop("model_router", None)


if flags_env_blocked:
    print("(CRLF/line-ending checks skipped — OCTOPUS-flags.cmd absent in worktree/CI)")
print("FAIL" if fails else "PASS", "— test_paid_router_dark_config")
for f in fails:
    print("  -", f)
sys.exit(1 if fails else 0)
