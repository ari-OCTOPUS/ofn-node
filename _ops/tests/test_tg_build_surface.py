#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_tg_build_surface — هدایتِ کدنویسیِ خود از DM ِ لنگر (رأیِ مالک ۰۷-۳۰).

سه چیز را قفل می‌کند:
  ۱ ثبتِ کارِ ساخت از Outer DM (و **نه** از گروه)
  ۲ وضعیتِ صادقِ هر پلهٔ حلقه — «روشن است» بی‌تفکیک ممنوع
  ۳ نمای پچ‌ها هرگز محتوای کد را echo نمی‌کند
"""
import json
import os
import sys
from pathlib import Path

import harness

ENV = harness.setup("tg-build-surface")

_OPS = Path(__file__).resolve().parent.parent
for _p in (str(_OPS / "telegram_center"), str(_OPS), str(_OPS / "cortex")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import build_cmd as bc  # noqa: E402
import input_surface_policy as isp  # noqa: E402

OWNER = 6150431610
GROUP = -1004475788460


# ── تشخیصِ نیت ──────────────────────────────────────────────────────────────
def t_build_intent_is_recognised_in_natural_persian():
    for t in ("بساز: تابعِ x را در _ops/cortex/y.py اصلاح کن",
              "بساز تابعِ کمکی اضافه کن", "کد بزن برای شمارشِ لیدها",
              "اصلاح کن: _ops/cortex/z.py", "/build چیزی"):
        assert bc.is_build_request(t), t


def t_ordinary_chat_is_not_a_build_request():
    """ضدِ بیش‌بست: هر جمله‌ای کارِ ساخت نیست، وگرنه چتِ مالک بلعیده می‌شود."""
    for t in ("الان چه هدفی داری؟", "وضعیتِ پاها چطور است؟",
              "ساختمانِ جدید خریدم", "بسازیم یا نه؟", ""):
        assert not bc.is_build_request(t), t


def t_the_prefix_is_stripped_but_the_body_survives():
    got = bc.strip_prefix("بساز: تابعِ کمکی در _ops/cortex/y.py اضافه کن")
    assert got.startswith("تابعِ کمکی"), got
    assert "_ops/cortex/y.py" in got, got


# ── ثبتِ کار ────────────────────────────────────────────────────────────────
def t_a_too_short_request_is_refused_with_a_reason():
    r = bc.enqueue("بساز")
    assert r["ok"] is False and r["note"], r


def t_a_real_request_is_queued_and_the_note_tells_the_truth():
    r = bc.enqueue("تابعِ شمارشِ لیدها را در _ops/cortex/improve.py اضافه کن")
    assert r["ok"] is True and r["id"].startswith("task-"), r
    # نکتهٔ صادق: در محیطِ تست مغز خاموش است، پس باید همین را بگوید.
    assert ("خاموش" in r["note"] or "صف" in r["note"]
            or "کارت" in r["note"]), r["note"]
    rows = [x for x in bc.queue_text().splitlines() if r["id"] in x]
    assert rows, "کار در صف دیده نمی‌شود"


def t_the_queue_view_is_honest_when_empty():
    import code_brain
    d = Path(code_brain.TASKS_DIR)
    if d.exists():
        for f in d.glob("*.json"):
            f.unlink()
    assert "خالی" in bc.queue_text()


# ── وضعیتِ صادق: هر پله جدا ─────────────────────────────────────────────────
def t_loop_status_reports_every_rung_separately():
    """«روشن است» بی‌تفکیک همان دروغی است که قرارداد ممنوع کرده."""
    s = bc.loop_status()
    for k in ("brain_flag", "has_key", "ollama", "apply_wired", "active",
              "patch_card", "tasks", "patches"):
        assert k in s, (k, s)
    assert isinstance(s["patch_card"], bool)


def t_a_dark_patch_card_is_stated_not_hidden():
    """PATCH_CARD خاموش ⇒ متن صریح بگوید کدام مسیر بسته است.

    ⚠️ نسخهٔ اولِ این بند (و خودِ متن) می‌گفت «کارتِ پچ به تو نمی‌رسد» و
    برای مسیرِ «بساز» **غلط** بود: `code_brain.tick_once` کارت را بی‌قید
    می‌فرستد؛ PATCH_CARD فقط حلقهٔ **خودتشخیصی** را گیت می‌کند. دو مسیر،
    دو گیت — قاتی‌کردنشان یعنی مالک منتظرِ کارتِ اشتباه می‌مانَد."""
    saved = os.environ.pop("OCTOPUS_WIRE_PATCH_CARD", None)
    try:
        txt = bc.status_text()
        assert "PATCH_CARD" in txt and "خاموش" in txt, txt
        assert "خودتشخیصی" in txt, "نمی‌گوید کدام مسیر بسته است"
        assert "«بساز» جداست" in txt, "مسیرِ بساز را از PATCH_CARD جدا نمی‌کند"
    finally:
        if saved is not None:
            os.environ["OCTOPUS_WIRE_PATCH_CARD"] = saved


def t_a_dark_code_brain_is_stated_too():
    """گیتِ واقعیِ مسیرِ «بساز» مغزِ کد است، نه PATCH_CARD — و باید گفته شود."""
    saved = os.environ.pop("OCTOPUS_CODE_BRAIN", None)
    try:
        txt = bc.status_text()
        assert "مغزِ کد خاموش است" in txt, txt
        assert "OCTOPUS_WIRE_CODE_BRAIN" in txt, "نمی‌گوید چه چیزی لازم است"
    finally:
        if saved is not None:
            os.environ["OCTOPUS_CODE_BRAIN"] = saved


def t_the_status_never_claims_a_producer_that_does_not_exist():
    """نه کلیدِ پولی، نه اولاما ⇒ باید بگوید «هیچ کدی تولید نمی‌شود»."""
    s = bc.loop_status()
    txt = bc.status_text()
    if not (s["has_key"] or s["ollama"]):
        assert "هیچ کدی تولید نمی‌شود" in txt, txt


# ── مرزها ───────────────────────────────────────────────────────────────────
def t_the_patch_view_never_echoes_code_content():
    """محتوای پچ در چت echo نمی‌شود — نه نویز، نه ریسکِ افشا."""
    import code_autonomy as ca
    pend = Path(ca.opslib.STATE_DIR) / "cortex" / "pending-patches"
    pend.mkdir(parents=True, exist_ok=True)
    (pend / "code-zzz.json").write_text(json.dumps({
        "id": "code-zzz", "target": "_ops/cortex/x.py",
        "intent": "نیتِ کوتاه",
        "content": "SECRET_MARKER_XYZZY = 'باید هرگز دیده نشود'"}), "utf-8")
    txt = bc.patches_text()
    assert "code-zzz" in txt and "_ops/cortex/x.py" in txt, txt
    assert "SECRET_MARKER_XYZZY" not in txt, "محتوای کد echo شد"


def t_the_module_sends_nothing_and_applies_nothing():
    """این ماژول فقط متن و صف است. اگر خودش بفرستد یا اعمال کند، همهٔ
    گیت‌ها دور می‌خورند."""
    import ast
    tree = ast.parse(Path(bc.__file__).read_text("utf-8"))
    imported = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            imported.update(a.name.split(".")[0] for a in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            imported.add(n.module.split(".")[0])
    assert not (imported & {"requests", "urllib", "socket", "http",
                            "subprocess"}), imported
    called = {getattr(n.func, "attr", None) or getattr(n.func, "id", None)
              for n in ast.walk(tree) if isinstance(n, ast.Call)}
    for bad in ("send", "send_text", "apply_approved", "consume_approvals",
                "tick", "post", "urlopen"):
        assert bad not in called, f"build_cmd خودش {bad} می‌کند"


def t_a_build_request_from_the_group_is_structurally_impossible():
    """درزِ مرکز فقط با تصمیمِ core_conversation اجرا می‌شود؛ گروه آن را
    هرگز نمی‌گیرد (پیامِ پا `leg_scoped` است)."""
    d = isp.classify(
        {"message": {"chat": {"id": GROUP, "type": "supergroup"},
                     "from": {"id": OWNER}, "text": "بساز: چیزی",
                     "message_thread_id": 22}},
        bot_role="outer", owner_id=OWNER, group_id=GROUP,
        topics={"lead": 22})
    assert d["mode"] != "core_conversation", d


def t_a_bare_build_prefix_asks_instead_of_queueing_nonsense():
    """«بساز:» ِ تنها نباید یک کارِ ساخت با محتوای «بساز:» بسازد.

    ⚠️ این باگ زنده بود: `strip_prefix` یک `... or t` داشت که بدنهٔ خالی را به
    خودِ کلمه برمی‌گردانْد. هیچ تستی نگرفتش — با یک **جهش روی راهنما** لو رفت
    (مثالِ راهنما را به «بساز:» ِ خالی عوض کردم و انتظار داشتم قرمز شود؛ سبز
    ماند و علتش این بود). قانون: نمی‌دانی ⇒ بپرس، حدس نزن."""
    assert bc.strip_prefix("بساز:") == ""
    assert bc.strip_prefix("بساز: ") == ""
    assert bc.strip_prefix("بساز:  ساخت چیزی") == "ساخت چیزی"
    # و درزِ مرکز باید بدنهٔ خالی را قبل از enqueue بگیرد
    src = (_OPS / "telegram_center" / "center.py").read_text("utf-8")
    i = src.index("_bc.is_build_request(_txb)")
    seam = src[i:i + 900]
    assert "_body = _bc.strip_prefix" in seam, "بدنه جدا نمی‌شود"
    assert seam.index("if not _body") < seam.index("_bc.enqueue"), \
        "enqueue قبل از سنجشِ خالی بودن ⇒ کارِ بی‌معنی ثبت می‌شود"
    assert "چه چیزی بسازم؟" in seam, "به‌جای پرسیدن، ساکت می‌مانَد"


def t_the_center_wires_the_build_seam_and_the_button():
    import ast
    src = (_OPS / "telegram_center" / "center.py").read_text("utf-8")
    tree = ast.parse(src)
    calls = {getattr(n.func, "attr", None) for n in ast.walk(tree)
             if isinstance(n, ast.Call)
             and getattr(getattr(n.func, "value", None), "id", None) == "_bc"}
    assert "is_build_request" in calls and "enqueue" in calls, calls
    assert "status_text" in calls, "زیرمنوی وضعیتِ حلقه وصل نیست"
    # دکمه‌ها handler دارند (درسِ کارتِ مرده)
    emitted = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if (isinstance(k, ast.Constant) and k.value == "callback_data"
                        and isinstance(v, ast.Constant)
                        and str(v.value).startswith("hm:")):
                    emitted.add(str(v.value).split(":", 1)[1])
    handler = src.split("def _handle_home_callback")[1][:4000]
    for sub in emitted:
        assert f'"{sub}"' in handler, f"hm:{sub} شاخه ندارد"


if __name__ == "__main__":
    checks = [(n, f) for n, f in sorted(globals().items()) if n.startswith("t_")]
    failed = harness.run(checks)
    print(f"\n{'✅' if not failed else '❌'} test_tg_build_surface: "
          f"{len(checks) - failed}/{len(checks)}")
    sys.exit(1 if failed else 0)
