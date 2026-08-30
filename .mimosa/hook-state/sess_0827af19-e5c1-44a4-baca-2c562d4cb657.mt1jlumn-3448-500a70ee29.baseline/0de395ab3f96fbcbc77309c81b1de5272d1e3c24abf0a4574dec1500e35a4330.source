"""test_code_brain.py — مغزِ تولیدِ patch (code_brain).

تمرکز بر قراردادِ امنیتی که نباید شکسته شود — همه با fake/monkeypatch، صفر
شبکه/LLM/git واقعی:
  - flag-off → draft_patch همیشه None (هیچ patchای بدونِ مجوزِ صریح).
  - خروجی همیشه validated در برابرِ code_autonomy.allowed_target (deny-list سخت).
  - tick_once با fake: task → patch(stub) → shadow(stub) → proposal مسیرِ درست.
  - صفِ pending-tasks: enqueue/pending/consume همگی file-based و idempotent.
"""
import io
import json
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, io.UnsupportedOperation):
        pass

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
sys.path.insert(0, str(_HERE.parent / "budget"))
sys.path.insert(0, str(_HERE.parent / "cortex"))

import harness
ENV = harness.setup("code-brain")

from cortex import code_brain as CB  # noqa: E402
from cortex import code_autonomy as CA  # noqa: E402


class _C:
    failed = 0


def check(name, cond):
    print(("PASS" if cond else "FAIL"), "-", name)
    if not cond:
        _C.failed += 1


def _clean_tasks():
    if CB.TASKS_DIR.exists():
        for f in CB.TASKS_DIR.glob("*.json"):
            f.unlink()


# ── §۱ flag-off: هیچ patchای بدونِ مجوزِ صریحِ OCTOPUS_CODE_BRAIN ───────────────────
def t_flag_off_blocks_draft():
    _clean_tasks()
    CB.draft_patch.__wrapped__ = None
    import os
    os.environ.pop("OCTOPUS_CODE_BRAIN", None)
    os.environ.pop("ANTHROPIC_API_KEY", None)
    assert CB.draft_patch("do anything") is None
    assert CB.enabled() is False


# ── §۲ deny-list سخت: target خارجِ allow-list حتی با کلید/فلگ هم رد می‌شود ─────────
def t_denylist_target_rejected():
    import os
    os.environ["OCTOPUS_CODE_BRAIN"] = "1"
    os.environ["ANTHROPIC_API_KEY"] = "sk-fake-test"
    # fake: مغز یک patch با targetِ ممنوع می‌دهد → باید None برگرداند (defense-in-depth)
    def fake_api(task, max_turns):
        return {"target": "_ops/budget/money_gate.py", "content": "evil", "intent": "x"}
    orig = CB._draft_via_api
    CB._draft_via_api = fake_api
    try:
        out = CB.draft_patch("hack the money gate")
        # target در deny-list (budget/money) → باید None، حتی اگر مغز پیشنهاد داد
        assert out is None, f"deny-list نقض شد: {out}"
    finally:
        CB._draft_via_api = orig
        os.environ.pop("OCTOPUS_CODE_BRAIN", None)
        os.environ.pop("ANTHROPIC_API_KEY", None)


# ── §۳ allow-list OK: target داخلِ allow-list پاس می‌کند ───────────────────────────
def t_allowlist_target_passes():
    import os
    os.environ["OCTOPUS_CODE_BRAIN"] = "1"
    os.environ["ANTHROPIC_API_KEY"] = "sk-fake-test"
    def fake_api(task, max_turns):
        # target داخلِ allow-list (_ops/cortex)
        return {"target": "_ops/cortex/some_file.py", "content": "# new content\n",
                "intent": "docstring fix"}
    orig = CB._draft_via_api
    CB._draft_via_api = fake_api
    try:
        out = CB.draft_patch("fix a docstring in cortex")
        assert out is not None, "allow-list target باید پاس کند"
        assert out["target"] == "_ops/cortex/some_file.py"
        assert out["content"].strip()
        assert "intent" in out
    finally:
        CB._draft_via_api = orig
        os.environ.pop("OCTOPUS_CODE_BRAIN", None)
        os.environ.pop("ANTHROPIC_API_KEY", None)


# ── §۴ صف: enqueue/pending/consume همگی file-based ────────────────────────────────
def test_queue_roundtrip():
    _clean_tasks()
    tid = CB.enqueue_task("test task roundtrip", source="test")
    assert tid.startswith("task-")
    ps = CB.pending_tasks()
    assert len(ps) == 1 and ps[0]["id"] == tid and ps[0]["task"] == "test task roundtrip"
    CB._consume_task(tid)
    ps = CB.pending_tasks()
    assert len(ps) == 0, "consume باید task را از pending حذف کند"
    _clean_tasks()


# ── §۵ tick_once: مسیرِ task→patch→shadow→proposal با fake کامل ───────────────────
def t_tick_once_hitl_path():
    _clean_tasks()
    CB.enqueue_task("fix parser robustness in telegram_center", source="test")
    # fake‌ها از طریق dependency injection (نه monkeypatch ماژول):
    def fake_draft(task):
        return {"target": "_ops/cortex/some_file.py", "content": "# fixed\n", "intent": "test"}
    def fake_tick(patch):
        return {"mood": {"verdict": "act"},
                "shadow": {"ok": True, "green": True}, "decision": "ok", "acted": True}
    def fake_propose(patch):
        return {"ok": True, "id": "code-test123"}
    out = CB.tick_once(draft_fn=fake_draft, tick_fn=fake_tick, propose_fn=fake_propose)
    assert out["processed"] == 1, out
    assert out["drafted"] == 1, out
    assert out["green"] == 1, out
    assert out["proposed"] == 1, out
    assert out["proposal_id"] == "code-test123", out
    # autoapplied نباید در مسیرِ HITL فعال باشد
    assert out.get("autoapplied", 0) == 0, out
    # task باید consume شده باشد
    assert len(CB.pending_tasks()) == 0, "task باید consume شود"
    _clean_tasks()


# ── §۶ tick_once: shadow قرمز → patch رد، درخت زنده امن، task consume ─────────────
def t_tick_once_shadow_red():
    _clean_tasks()
    CB.enqueue_task("bad change", source="test")
    def fake_draft(task):
        return {"target": "_ops/cortex/x.py", "content": "# x\n", "intent": "x"}
    def fake_tick(patch):
        return {"mood": {"verdict": "act"},
                "shadow": {"ok": True, "green": False}, "decision": "red", "acted": True}
    out = CB.tick_once(draft_fn=fake_draft, tick_fn=fake_tick)
    assert out["drafted"] == 1 and out["green"] == 0, out
    assert "red" in out.get("reason", ""), out
    assert out.get("proposed", 0) == 0, "shadow قرمز نباید پیشنهاد شود"
    assert len(CB.pending_tasks()) == 0, "task قرمز باید consume شود"
    _clean_tasks()


# ── §۷ _extract_json: parse مقاوم در برابرِ متنِ اضافی ─────────────────────────────
def t_extract_json_robust():
    assert CB._extract_json(None) is None
    assert CB._extract_json("not json") is None
    d = CB._extract_json('here is the patch: {"target": "a.py", "content": "x", "intent": "y"} done')
    assert d == {"target": "a.py", "content": "x", "intent": "y"}, d
    # JSON خالص
    assert CB._extract_json('{"a": 1}') == {"a": 1}
    # JSON با متنِ قبل و بعد
    d2 = CB._extract_json('```json\n{"target": "a.py", "content": "x", "intent": "z"}\n```')
    assert d2 == {"target": "a.py", "content": "x", "intent": "z"}, d2


for _name, _fn in list(globals().items()):
    if _name.startswith("t_") and callable(_fn):
        try:
            _fn()
        except Exception as _e:  # noqa: BLE001
            print("ERROR", "-", _name, "-", type(_e).__name__, _e)
            _C.failed += 1

print("\n" + ("ALL PASS" if _C.failed == 0 else f"{_C.failed} FAILED"))
sys.exit(1 if _C.failed else 0)
