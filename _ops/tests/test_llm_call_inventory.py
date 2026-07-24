#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_llm_call_inventory.py — Wave1-B: inventoryِ ماشین‌چکِ **تمام** call-siteهای تولیدیِ LLM.

فراتر از Sol-T3 (که فقط بردارِ local_llm.ask را قفل کرد): این تست هر سه بردارِ callِ LLM را
اسکن و طبقه‌بندی می‌کند و ادعای پوششِ فنس را ماشین‌چک نگه می‌دارد:

  بردارها:  (۱) model_router.ask (مستقیم/آلیاس/from-import)  (۲) local_llm.ask مستقیم
            (۳) .complete( روی clientهای provider (DeepSeekClient/MultiProviderClient)

  طبقه‌ها:  ROUTER_FENCED  — از model_router.ask می‌گذرد → غربالِ فنس در درِ روتر (آیتم۲)
            ADAPTER_FENCED — callِ مستقیمِ provider که fence_adapter.screen_llm_input را
                             پیش از call صدا می‌زند (Wave1-B، observe-only، flag-off=no-op)
            CHOKE/PRIMITIVE — خودِ روتر/primitiveها (داخلِ فنس یا صرفاً تعریف)
            RESIDUAL       — مسیرِ تولیدیِ بیرونِ فنس (باید خالی بماند؛ صادقانه مستند)

fail یعنی: caller نو بی‌طبقه، caller طبقه‌بندی‌شدهٔ کهنه، یا سیمِ فنس/آداپتر برداشته شده.
$0 آفلاین؛ فقط اسکنِ سورسِ همین tree (کدِ تحتِ تست).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
harness.setup("llm-call-inventory")

_OPS = Path(__file__).resolve().parent.parent          # _ops همین tree — نه REAL_VAULT

# ─── بردارهای شناسایی ─────────────────────────────────────────────────────────
RX_ROUTER_CALL = re.compile(r"\bmodel_router\.ask\s*\(")
RX_ROUTER_IMP = re.compile(r"from\s+model_router\s+import\s+ask")
RX_ROUTER_ALIAS = re.compile(r"import\s+model_router\s+as\s+(\w+)")
RX_LOCAL = re.compile(r"\blocal_llm\.ask\s*\(")
RX_COMPLETE = re.compile(r"\.complete\s*\(")
RX_CLIENT_REF = re.compile(r"DeepSeekClient|MultiProviderClient")

# ─── inventoryِ مستند (ممیزیِ Wave1-B 2026-07-21) ─────────────────────────────
ROUTER_FENCED = {
    "cortex/cortex.py",              # فکرِ ژورنال‌شده + shadow
    "cortex/improve.py",             # حلقهٔ self-improve (propose-only)
    "cortex/synthesis.py",           # سنتزِ پولی (from model_router import ask)
    "doctor/self_knowledge.py",      # خودشناسیِ دکتر — ADVISORY (تاکسونومی/گیتِ حافظه)
    "live/server.py",                # endpointِ /ask کورتکس
    "wiring.py",                     # beatِ لید (lead enrich)
    "legs/txn_categorize.py",        # دسته‌بندیِ تراکنش (و acct_review از همین در)
    "legs/ziman_leg.py",             # بدنهٔ برندِ زیمان
    "chord/adapters/llm_adapter.py",  # مسیرِ اصلی (fallbackش ADAPTER_FENCED است)
    "eval/run_adversarial.py",       # evalِ آفلاین — mr.ask آلیاس‌شده در sandbox
    "legs/speed_to_lead.py",         # Phase-D (Wave-2): _llm_draft → model_router.ask("draft",…)
}
ADAPTER_FENCED = {
    "debate/debate_loop.py",         # _gated_call → DeepSeekClient.complete
    "heart/doctor_setpoint.py",      # llm_refine → DeepSeekClient.complete
    "budget/governor_epoch.py",      # allocate_llm → DeepSeekClient.complete
    "chord/adapters/llm_adapter.py",  # فقط شاخهٔ fallbackِ local_llm.ask
}
CHOKE_PRIMITIVES = {
    "cortex/model_router.py",        # چوکِ fenced — local_llm.ask/cli.complete داخلِ فنس
    "cortex/local_llm.py",           # primitive (def ask — caller نیست)
    "debate/client.py",              # primitive provider (def complete — caller نیست)
    # M7 (now_moves 2026-07-24): سایدکارِ observabilityِ روتر — LLM صدا نمی‌زند (فقط tierِ
    # انتخاب‌شده را log می‌کند). تطبیقِ اسکنر یک false-positiveِ رشته‌ای است: عبارتِ
    # "model_router.ask" فقط در docstringِ ROLLBACK می‌آید و `\s*` روی newline به "(" وصل می‌شود.
    "now_moves/route_scorer_shadow_log.py",
}
# مسیرِ تولیدیِ شناخته‌شدهٔ بیرونِ فنس: هیچ. (اگر روزی لازم شد، با file:line + دلیل این‌جا
# مستند شود — پنهان‌کاری ممنوع.)
RESIDUAL: dict = {}


def _rel(p: Path) -> str:
    return str(p.relative_to(_OPS)).replace("\\", "/")


def _iter_prod_sources():
    for py in _OPS.rglob("*.py"):
        rp = _rel(py)
        if rp.startswith("tests/") or "__pycache__" in rp:
            continue
        try:
            yield rp, py.read_text("utf-8")
        except Exception:  # noqa: BLE001
            continue


def _vectors(src: str) -> set:
    v = set()
    if RX_ROUTER_CALL.search(src) or RX_ROUTER_IMP.search(src):
        v.add("router")
    for alias in RX_ROUTER_ALIAS.findall(src):
        if re.search(rf"\b{re.escape(alias)}\.ask\s*\(", src):
            v.add("router")
    if RX_LOCAL.search(src):
        v.add("local")
    if RX_CLIENT_REF.search(src) and RX_COMPLETE.search(src):
        v.add("complete")
    return v


def t_a_every_caller_classified():
    """هر فایلِ تولیدی با بردارِ LLM باید در inventory باشد (caller نوِ بی‌طبقه = fail)."""
    known = ROUTER_FENCED | ADAPTER_FENCED | CHOKE_PRIMITIVES | set(RESIDUAL)
    found = {rp for rp, src in _iter_prod_sources() if _vectors(src)}
    new = found - known
    assert not new, ("callerِ LLMِ نو خارج از inventory — یا از model_router.ask ببرش، یا "
                     "fence_adapter.screen_llm_input را سیم کن، یا صادقانه در RESIDUAL "
                     "مستند کن: " + ", ".join(sorted(new)))


def t_b_inventory_not_stale():
    """هر مدخلِ inventory باید هنوز وجود داشته و بردارش را داشته باشد (لیستِ کهنه = fail)."""
    for rp in sorted(ROUTER_FENCED | ADAPTER_FENCED):
        f = _OPS / rp
        assert f.exists(), f"inventoryِ کهنه: {rp} دیگر وجود ندارد"
        v = _vectors(f.read_text("utf-8"))
        if rp in ROUTER_FENCED:
            assert "router" in v or rp in ADAPTER_FENCED, \
                f"inventoryِ کهنه: {rp} دیگر از model_router.ask نمی‌گذرد"
        if rp in ADAPTER_FENCED:
            assert v & {"local", "complete"}, \
                f"inventoryِ کهنه: {rp} دیگر callِ مستقیمِ provider ندارد — از ADAPTER_FENCED بردار"
    for rp in sorted(CHOKE_PRIMITIVES):
        assert (_OPS / rp).exists(), f"primitive غایب: {rp}"


def t_c_adapter_fenced_actually_wired():
    """هر callerِ مستقیمِ provider باید fence_adapter.screen_llm_input را صدا بزند
    (ماشین‌چکِ «straggler از چوکِ مشترک می‌گذرد»)."""
    for rp in sorted(ADAPTER_FENCED):
        src = (_OPS / rp).read_text("utf-8")
        assert "fence_adapter.screen_llm_input(" in src, \
            f"{rp}: سیمِ fence_adapter برداشته/فراموش شده (bypassِ خاموشِ فنس)"


def t_d_router_choke_intact():
    """چوکِ اصلی (model_router.ask) هنوز فنس را صدا می‌زند (رگرسیون‌گاردِ آیتم۲)."""
    mr = (_OPS / "cortex" / "model_router.py").read_text("utf-8")
    assert "import context_fence" in mr and "_fence.screen(" in mr, \
        "context_fence باید در model_router.ask سیم بماند"


def t_e_fence_layer_pure_no_network():
    """لایهٔ فنس (context_fence + fence_adapter) باید بدونِ شبکه/provider/subprocess بماند."""
    banned = re.compile(r"\b(urllib|requests|socket|http\.client|httpx|subprocess)\b")
    for name in ("context_fence.py", "fence_adapter.py"):
        src = (_OPS / "cortex" / name).read_text("utf-8")
        m = banned.search(src)
        assert not m, f"{name}: importِ ممنوع در لایهٔ فنس: {m.group(0)}"


def t_f_residual_is_empty_and_honest():
    """ادعای پوشش: هیچ مسیرِ تولیدیِ شناخته‌شدهٔ بیرونِ فنس. اگر RESIDUAL پر شد، هر مدخل
    باید دلیل (رشتهٔ ناخالی) داشته باشد — طبقه‌بندیِ صادقانه، نه تظاهر به بسته‌بودن."""
    for rp, why in RESIDUAL.items():
        assert isinstance(why, str) and why.strip(), f"RESIDUAL بدونِ دلیل: {rp}"
        assert (_OPS / rp).exists(), f"RESIDUALِ کهنه: {rp}"
    assert not RESIDUAL, "RESIDUAL باید خالی بماند مگر با دلیلِ مستندِ owner-visible"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_llm_call_inventory: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
