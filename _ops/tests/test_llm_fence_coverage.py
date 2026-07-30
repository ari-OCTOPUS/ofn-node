#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_llm_fence_coverage.py — Sol T3: گاردِ ضدِ bypassِ خاموشِ Context Fence.

ممیزیِ Sol (claims-A) نشان داد context_fence فقط داخلِ `model_router.ask` سیم است و چند
مسیرِ مستقیمِ LLM آن را دور می‌زنند. این تست inventoryِ callerهای مستقیمِ LLM را **قفل**
می‌کند: هر callerِ نوِ `local_llm.ask(` خارج از مجموعهٔ مستند = fail — تا هیچ bypassِ جدیدی
بی‌صدا اضافه نشود. (سیم‌کشیِ fencedِ هر bypass = گامِ owner-gatedِ بعدی، per-caller.)

بردارِ `.complete()`ِ DeepSeekClient (debate_loop/governor_epoch/doctor_setpoint) در
EVIDENCE-MANIFEST جداگانه ثبت است؛ این تست بردارِ دقیقِ `local_llm.ask` را می‌بندد.
$0 آفلاین؛ فقط اسکنِ سورس.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness  # noqa: E402
harness.setup("llm-fence-coverage")

_OPS = harness.REAL_VAULT / "_ops"

# inventoryِ مستندِ callerهای مستقیمِ local_llm.ask (ممیزیِ Sol 2026-07-20):
#   model_router.py = درِ fenced (چوک؛ local_llm.ask را از داخلِ فنس صدا می‌زند) ·
#   chord/adapters/llm_adapter.py = fallbackِ bypass شناخته‌شده (shadow/advisory).
# (local_llm.py خودِ primitive است — `def ask` دارد، نه `local_llm.ask(` → caller نیست.)
# DEFECT-W4 (2026-07-25): debate/debate_loop.py هم اضافه شد — مسیرِ `_local_transport`.
#   این bypass **نیست**: تنها صداکنندهٔ آن `client.complete` است که از `_gated_call`
#   می‌آید، و _gated_call دقیقاً پیش از call، متنِ نامعتمد را با
#   `fence_adapter.screen_llm_input(f"debate.{task}", [("external", user)])` غربال
#   می‌کند (debate_loop.py، بلوکِ CONTEXT-FENCE). یعنی ورودی قبل از مغزِ محلی fenced است.
_INVENTORIED_LOCAL_LLM = {
    "cortex/model_router.py",
    "chord/adapters/llm_adapter.py",
    "debate/debate_loop.py",
}


def _rel(p: Path) -> str:
    return str(p.relative_to(_OPS)).replace("\\", "/")


def t_a_no_new_local_llm_bypass():
    """هیچ callerِ نوِ local_llm.ask خارج از inventory (وگرنه bypassِ خاموشِ فنس)."""
    rx = re.compile(r"\blocal_llm\.ask\s*\(")
    found = set()
    for py in _OPS.rglob("*.py"):
        rp = _rel(py)
        if rp.startswith("tests/") or "__pycache__" in rp:
            continue
        try:
            src = py.read_text("utf-8")
        except Exception:  # noqa: BLE001
            continue
        if rx.search(src):
            found.add(rp)
    new = found - _INVENTORIED_LOCAL_LLM
    assert not new, ("callerِ نوِ local_llm.ask خارج از inventory (bypassِ احتمالیِ فنس — "
                     "یا fencedش کن یا به inventory اضافه کن): " + ", ".join(sorted(new)))


def t_b_inventory_not_stale():
    """اگر یک bypassِ شناخته‌شده حذف/fenced شد، از inventory هم برداشته شود (لیست کهنه نماند)."""
    rx = re.compile(r"\blocal_llm\.ask\s*\(")
    for rp in _INVENTORIED_LOCAL_LLM:
        f = _OPS / rp
        assert f.exists(), f"inventoryِ کهنه: {rp} دیگر وجود ندارد"
        assert rx.search(f.read_text("utf-8")), \
            f"inventoryِ کهنه: {rp} دیگر local_llm.ask ندارد — از inventory بردار"


def t_c_fence_is_wired_in_router():
    """چوکِ اصلی (model_router.ask) هنوز فنس را صدا می‌زند (رگرسیون‌گارد آیتم۲)."""
    mr = (_OPS / "cortex" / "model_router.py").read_text("utf-8")
    assert "import context_fence" in mr and "_fence.screen(" in mr, \
        "context_fence باید در model_router.ask سیم بماند"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'OK' if not failed else 'FAIL'} test_llm_fence_coverage: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
